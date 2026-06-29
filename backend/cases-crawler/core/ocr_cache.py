"""
LexPrime OCR 缓存 + 两步拆分 (W10 A1 · lex-ai · 2026-06-29)

D4 producer (W8 D4 plan_5dcb8424) 报 blocker #1: OCR + BGE 加载耗时长, 单合同 OCR
~30s (首次模型加载) + BGE 19s = 50s. 完整 5 合同 E2E 跑 ~5min, 易超 30min plan budget.

本模块把 OCR 调用拆成两步:
  Step 1 (run_ocr_with_cache): 文件 → OCR → OcrResult
    - SQLite ocr_cache 表, key = sha256(file_bytes), value = OcrResult.to_dict()
    - 5 分钟 TTL, 缓存 hit 直接返回 (跳过 OCR 主调用, 省 30s+)
    - 可选 venv312 桥接 (LEX_OCR_BRIDGE=1): subprocess 调
      scripts/w8/ocr_via_venv312.py, 解决主 Python 3.14 paddle wheel ABI 不兼容
  Step 2 (postprocess_ocr_text): raw_text → PII 脱敏 → 段落解析 → Skill 2 接管
    - 复用 core.pii.sanitize_for_review (W5 Track B 已实现)
    - 段落解析: 按 \\n\\n 切, 输出 [{idx, text, char_count, pii_masked?}, ...]
    - Skill 2 接管入口: postprocess_for_skill2_review(raw_text, contract_type)
      内部 sanitize + 段落 + 返回 ReviewerInput-ready dict

设计原则:
- 零联网: 全部走本地 OCR + 本地 SQLite
- 缓存独立: 即使 OCR 引擎升级/降级, 缓存不变 (key = file_hash)
- 桥接可选: 默认走主进程 get_ocr_engine(); LEX_OCR_BRIDGE=1 走 venv312 subprocess
- 兜底完备: 缓存表不可用 / OCR 失败 / 桥接失败 → 都不影响主流程

依赖 (跟 core.ocr.py 一致, 复用):
- paddlepaddle==3.3.1 + paddleocr==3.7.0 (生产, venv312)
- pytesseract + Tesseract binary (fallback)
- python-docx 已在 requirements
- aiosqlite + sqlite3 (缓存)
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from core.ocr import (
    OcrResult,
    OcrUnsupportedFormatError,
    detect_mime,
    get_ocr_engine,
)


# ===== 默认配置 =====

CACHE_DB_PATH_DEFAULT = "data/ocr_cache.db"  # 相对 cases-crawler/ 启
CACHE_TTL_SECONDS_DEFAULT = 300  # 5 分钟 (PRD: 评审现场短时高频上传)
BRIDGE_SCRIPT_RELATIVE = "scripts/w8/ocr_via_venv312.py"  # venv312 桥接
BRIDGE_PYTHON_RELATIVE = "venv312/python.exe"  # venv312 子进程解释器
BRIDGE_TIMEOUT_SECONDS_DEFAULT = 120


def _cases_crawler_root() -> Path:
    """绝对路径根: backend/cases-crawler/core/ocr_cache.py → backend/cases-crawler/
    不依赖 cwd, 任意 cwd 都能跑 (跟 reviewer.py _get_risk_index 修复同思路)
    """
    return Path(__file__).resolve().parent.parent


def _default_cache_db_path() -> Path:
    """默认缓存 SQLite 路径 (绝对), 跟代码同级 data/ 目录"""
    root = _cases_crawler_root()
    db_dir = root / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "ocr_cache.db"


# ===== 缓存表 schema =====

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ocr_cache (
    file_hash TEXT PRIMARY KEY,
    filename  TEXT NOT NULL,
    mime      TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    engine    TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ocr_cache_expires_at ON ocr_cache(expires_at);
"""


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(CREATE_TABLE_SQL)
    conn.commit()


# ===== Step 1 数据结构 =====

@dataclass
class CachedOcrResult:
    """Step 1 输出 (OCR + 缓存命中信息)"""
    ocr_result: OcrResult
    file_hash: str
    cache_hit: bool
    engine: str
    file_size: int
    mime: str
    filename: str
    cache_age_seconds: float = 0.0  # 命中时的缓存年龄 (TTL 内才有效)
    source: str = "primary"  # primary / bridge_subprocess / cache


@dataclass
class PostprocessedText:
    """Step 2 输出 (PII 脱敏 + 段落解析)"""
    sanitized_text: str
    pii_report: Dict[str, Any]
    paragraphs: List[Dict[str, Any]] = field(default_factory=list)
    skill2_input: Optional[Dict[str, Any]] = None  # 给 Skill 2 接管用


# ===== 缓存层 =====

class OcrCache:
    """OCR 结果缓存 (SQLite, key = sha256(file_bytes))

    用法:
        cache = OcrCache()  # 默认 data/ocr_cache.db
        cache.set(file_bytes, "test.png", "image/png", "paddle", result_dict)
        hit = cache.get(file_hash)
        cache.purge_expired()
    """

    def __init__(self, db_path: Optional[Path] = None, ttl_seconds: int = CACHE_TTL_SECONDS_DEFAULT):
        self.db_path = Path(db_path) if db_path else _default_cache_db_path()
        self.ttl_seconds = ttl_seconds
        # check_same_thread=False 让 FastAPI 跨 thread 复用 (Python 3.14 默认较严)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=10.0)
        _ensure_schema(self._conn)
        logger.info(f"[ocr-cache] init db={self.db_path} ttl={self.ttl_seconds}s")

    @staticmethod
    def hash_file_bytes(file_bytes: bytes) -> str:
        """sha256 of file_bytes, hex, 取前 32 字符"""
        return hashlib.sha256(file_bytes).hexdigest()[:32]

    def get(self, file_hash: str) -> Optional[Tuple[Dict[str, Any], float]]:
        """获取缓存, 返回 (result_dict, age_seconds) 或 None (miss / expired)"""
        now = time.time()
        cur = self._conn.execute(
            "SELECT result_json, created_at, expires_at FROM ocr_cache WHERE file_hash = ?",
            (file_hash,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        result_json, created_at, expires_at = row
        if expires_at <= now:
            # 已过期 (TTL 内再次提交不主动 purge, 留 purge_expired 批处理)
            return None
        try:
            return json.loads(result_json), (now - created_at)
        except (json.JSONDecodeError, TypeError):
            return None

    def set(self,
             file_hash: str,
             filename: str,
             mime: str,
             file_size: int,
             engine: str,
             result_dict: Dict[str, Any]) -> None:
        """写入缓存, ttl = now + ttl_seconds"""
        now = time.time()
        self._conn.execute(
            """INSERT OR REPLACE INTO ocr_cache
               (file_hash, filename, mime, file_size, engine, result_json, created_at, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (file_hash, filename, mime, file_size, engine,
             json.dumps(result_dict, ensure_ascii=False), now, now + self.ttl_seconds),
        )
        self._conn.commit()

    def purge_expired(self) -> int:
        """清理过期缓存, 返回删除条数"""
        cur = self._conn.execute(
            "DELETE FROM ocr_cache WHERE expires_at <= ?", (time.time(),)
        )
        self._conn.commit()
        deleted = cur.rowcount
        if deleted:
            logger.info(f"[ocr-cache] purged {deleted} expired entries")
        return deleted

    def stats(self) -> Dict[str, Any]:
        """缓存统计"""
        cur = self._conn.execute(
            "SELECT COUNT(*), SUM(file_size), MIN(created_at), MAX(expires_at) "
            "FROM ocr_cache"
        )
        count, total_size, oldest, newest_expiry = cur.fetchone()
        return {
            "db_path": str(self.db_path),
            "ttl_seconds": self.ttl_seconds,
            "entry_count": count or 0,
            "total_file_bytes": total_size or 0,
            "oldest_created_at": oldest,
            "newest_expires_at": newest_expiry,
        }

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass


# ===== Singleton (懒加载) =====

_CACHE_SINGLETON: Optional[OcrCache] = None


def get_ocr_cache(db_path: Optional[Path] = None,
                  ttl_seconds: int = CACHE_TTL_SECONDS_DEFAULT) -> OcrCache:
    """获取 OCR 缓存单例 (同 db_path 复用)"""
    global _CACHE_SINGLETON
    target_path = Path(db_path) if db_path else _default_cache_db_path()
    if _CACHE_SINGLETON is None or _CACHE_SINGLETON.db_path != target_path:
        _CACHE_SINGLETON = OcrCache(db_path=target_path, ttl_seconds=ttl_seconds)
    return _CACHE_SINGLETON


def reset_ocr_cache() -> None:
    """重置缓存单例 (测试用)"""
    global _CACHE_SINGLETON
    if _CACHE_SINGLETON is not None:
        _CACHE_SINGLETON.close()
    _CACHE_SINGLETON = None


# ===== venv312 桥接 (subprocess 调 scripts/w8/ocr_via_venv312.py) =====

def _bridge_script_path() -> Path:
    return _cases_crawler_root() / BRIDGE_SCRIPT_RELATIVE


def _bridge_python_path() -> Path:
    return _cases_crawler_root() / BRIDGE_PYTHON_RELATIVE


def run_ocr_via_bridge(file_bytes: bytes, filename: str = "",
                        timeout_seconds: int = BRIDGE_TIMEOUT_SECONDS_DEFAULT) -> Optional[Dict[str, Any]]:
    """通过 venv312 subprocess 跑 OCR (主 Python 3.14 paddle wheel ABI 不兼容时)

    返回 dict {ok, engine, raw_text, confidence, lines, line_count, page_count,
               detected_mime, error?}
    失败 → 返回 None (让 caller 降级到主进程 OCR)

    协议: 把 file_bytes 写临时文件 → venv312/python.exe scripts/w8/ocr_via_venv312.py <path>
         → stdout JSON
    """
    bridge_py = _bridge_python_path()
    bridge_script = _bridge_script_path()
    if not bridge_py.exists():
        logger.debug(f"[ocr-bridge] venv312 python not found: {bridge_py}")
        return None
    if not bridge_script.exists():
        logger.debug(f"[ocr-bridge] bridge script not found: {bridge_script}")
        return None

    # 写临时文件 (用 tempfile, 自动 cleanup)
    tmp_dir = _cases_crawler_root() / "data" / "ocr_bridge_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(suffix=Path(filename).suffix or ".bin", dir=str(tmp_dir))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(file_bytes)
        # 调 venv312
        proc = subprocess.run(
            [str(bridge_py), str(bridge_script), tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env={**os.environ,
                 "FLAGS_use_mkldnn": "0",
                 "FLAGS_use_onednn": "0"},
        )
        if proc.returncode != 0:
            logger.warning(f"[ocr-bridge] subprocess failed: rc={proc.returncode} stderr={proc.stderr[:200]}")
            return None
        # 解析 stdout (取最后一行, 兼容主进程可能也 print log)
        out_line = ""
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.startswith("{"):
                out_line = line
        if not out_line:
            logger.warning(f"[ocr-bridge] no JSON in stdout: {proc.stdout[:200]}")
            return None
        try:
            return json.loads(out_line)
        except json.JSONDecodeError as e:
            logger.warning(f"[ocr-bridge] JSON decode failed: {e}")
            return None
    except subprocess.TimeoutExpired:
        logger.warning(f"[ocr-bridge] subprocess timeout after {timeout_seconds}s")
        return None
    except Exception as e:
        logger.exception(f"[ocr-bridge] unexpected: {e}")
        return None
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ===== Step 1: OCR 识别 (含缓存) =====

def run_ocr_with_cache(file_bytes: bytes,
                        filename: str = "",
                        mime_type: str = "",
                        use_cache: bool = True,
                        use_bridge: Optional[bool] = None,
                        cache: Optional[OcrCache] = None,
                        timeout_seconds: int = BRIDGE_TIMEOUT_SECONDS_DEFAULT) -> CachedOcrResult:
    """Step 1: OCR 识别 (含 SQLite 缓存)

    Args:
        file_bytes: 文件二进制
        filename: 文件名 (MIME 推断用)
        mime_type: 显式 MIME (可选)
        use_cache: 是否用缓存 (默认 True)
        use_bridge: 是否走 venv312 桥接 (None = 跟环境变量 LEX_OCR_BRIDGE)
        cache: 自定义缓存实例 (测试注入)
        timeout_seconds: 桥接超时秒数

    Returns:
        CachedOcrResult (含 OcrResult + 缓存命中信息)

    流程:
        1) 算 file_hash
        2) cache.get(file_hash) → 命中 → 直接返回 (skip OCR)
        3) miss:
           - use_bridge → run_ocr_via_bridge()
           - 否则 → 主进程 get_ocr_engine().run()
        4) cache.set()
        5) 返回 CachedOcrResult
    """
    if not file_bytes:
        raise OcrUnsupportedFormatError("empty file_bytes")

    mime = mime_type or detect_mime(file_bytes, filename)
    file_hash = OcrCache.hash_file_bytes(file_bytes)
    file_size = len(file_bytes)
    # use_cache=False → 完全跳过缓存层 (既不读也不写), 即使传入了 cache 实例
    cache_obj = (cache if cache else get_ocr_cache()) if use_cache else None
    bridge_flag = use_bridge if use_bridge is not None else os.getenv("LEX_OCR_BRIDGE", "0").lower() in ("1", "true", "yes")

    # 1) 缓存命中
    if cache_obj is not None:
        hit = cache_obj.get(file_hash)
        if hit is not None:
            result_dict, age = hit
            try:
                ocr_result = _dict_to_ocr_result(result_dict)
            except Exception as e:
                logger.warning(f"[ocr-cache] deserialize failed: {e}, fallback to re-OCR")
            else:
                logger.info(f"[ocr-cache] HIT hash={file_hash} age={age:.1f}s engine={ocr_result.source_engine}")
                return CachedOcrResult(
                    ocr_result=ocr_result,
                    file_hash=file_hash,
                    cache_hit=True,
                    engine=ocr_result.source_engine,
                    file_size=file_size,
                    mime=mime,
                    filename=filename,
                    cache_age_seconds=age,
                    source="cache",
                )

    # 2) 桥接优先 (主 Python paddle 装不上时)
    if bridge_flag:
        bridge_result = run_ocr_via_bridge(file_bytes, filename=filename,
                                            timeout_seconds=timeout_seconds)
        if bridge_result is not None and bridge_result.get("ok"):
            ocr_result = _bridge_dict_to_ocr_result(bridge_result)
            if cache_obj is not None:
                cache_obj.set(file_hash, filename, mime, file_size,
                              ocr_result.source_engine, ocr_result.to_dict())
            logger.info(f"[ocr-bridge] OK hash={file_hash} engine={ocr_result.source_engine}")
            return CachedOcrResult(
                ocr_result=ocr_result,
                file_hash=file_hash,
                cache_hit=False,
                engine=ocr_result.source_engine,
                file_size=file_size,
                mime=mime,
                filename=filename,
                source="bridge_subprocess",
            )

    # 3) 主进程 OCR (fallback)
    engine = get_ocr_engine()
    ocr_result = engine.run(file_bytes, filename=filename, mime_type=mime)

    if cache_obj is not None:
        cache_obj.set(file_hash, filename, mime, file_size,
                      ocr_result.source_engine, ocr_result.to_dict())

    logger.info(
        f"[ocr-primary] OK hash={file_hash} engine={ocr_result.source_engine} "
        f"conf={ocr_result.confidence:.3f} lines={len(ocr_result.lines)}"
    )
    return CachedOcrResult(
        ocr_result=ocr_result,
        file_hash=file_hash,
        cache_hit=False,
        engine=ocr_result.source_engine,
        file_size=file_size,
        mime=mime,
        filename=filename,
        source="primary",
    )


def _dict_to_ocr_result(d: Dict[str, Any]) -> OcrResult:
    """OcrResult.to_dict() → OcrResult (不带 lines 详情, 用于缓存查)"""
    return OcrResult(
        raw_text=d.get("raw_text", ""),
        confidence=d.get("confidence", 0.0),
        lines=[],  # 缓存只保留元信息 (line_count), 不保留逐行 bbox
        page_count=d.get("page_count", 1),
        source_engine=d.get("source_engine", "unknown"),
        detected_mime=d.get("detected_mime", ""),
    )


def _bridge_dict_to_ocr_result(d: Dict[str, Any]) -> OcrResult:
    """venv312 桥接返回的 dict → OcrResult (lines 保留完整, 缓存省略)"""
    from core.ocr import OcrLine
    lines_data = d.get("lines") or []
    lines = [OcrLine(text=ln.get("text", ""), confidence=ln.get("confidence", 0.0))
             for ln in lines_data if ln.get("text")]
    return OcrResult(
        raw_text=d.get("raw_text", ""),
        confidence=d.get("confidence", 0.0),
        lines=lines,
        page_count=d.get("page_count", 1),
        source_engine=d.get("engine", "unknown"),
        detected_mime=d.get("detected_mime", ""),
    )


# ===== Step 2: 文本后处理 =====

def postprocess_ocr_text(raw_text: str,
                          skip_pii: bool = False,
                          paragraph_min_length: int = 10) -> PostprocessedText:
    """Step 2: OCR 文本后处理 (PII 脱敏 + 段落解析)

    Args:
        raw_text: OCR 识别原文
        skip_pii: 跳过 PII 脱敏 (调试用, 默认 False)
        paragraph_min_length: 段落最短字符数 (低于此值合并)

    Returns:
        PostprocessedText
    """
    if not raw_text:
        return PostprocessedText(sanitized_text="", pii_report={}, paragraphs=[])

    # 1) PII 脱敏 (复用 core.pii, W5 Track B)
    if skip_pii:
        sanitized = raw_text
        pii_dict: Dict[str, Any] = {"skipped": True, "total": 0}
    else:
        from core.pii import sanitize_for_review
        sanitized, pii_report = sanitize_for_review(raw_text)
        pii_dict = pii_report.to_dict()

    # 2) 段落解析 (按 \\n\\n 切, 短段合并)
    raw_paragraphs = [p.strip() for p in sanitized.split("\n\n") if p.strip()]
    paragraphs: List[Dict[str, Any]] = []
    buffer = ""
    for p in raw_paragraphs:
        # 短段累积 (中文常见段位)
        if len(p) < paragraph_min_length:
            buffer = (buffer + " " + p).strip() if buffer else p
            continue
        if buffer:
            p = (buffer + " " + p).strip()
            buffer = ""
        paragraphs.append({
            "idx": len(paragraphs) + 1,
            "text": p,
            "char_count": len(p),
            "pii_masked": pii_dict.get("total", 0) > 0,
        })
    if buffer:
        paragraphs.append({
            "idx": len(paragraphs) + 1,
            "text": buffer,
            "char_count": len(buffer),
            "pii_masked": pii_dict.get("total", 0) > 0,
        })

    return PostprocessedText(
        sanitized_text=sanitized,
        pii_report=pii_dict,
        paragraphs=paragraphs,
    )


def postprocess_for_skill2_review(raw_text: str,
                                   contract_type: str = "其他",
                                   skip_pii: bool = False,
                                   paragraph_min_length: int = 10) -> PostprocessedText:
    """Step 2 (Skill 2 接管): OCR 文本 → 后处理 + 构造 Skill 2 入参字典

    Args:
        raw_text: OCR 原文
        contract_type: 合同类型 (8 大类之一, 兜底 = "其他")
        skip_pii: 跳过 PII 脱敏
        paragraph_min_length: 段落最短

    Returns:
        PostprocessedText.skill2_input 含 ReviewerInput-ready dict:
        {
            "contract_type": "房屋租赁",
            "contract_text": "已脱敏文本...",
            "stance": "审查方",
            "industry": "",
            "amount": null,
            "jurisdiction": "",
            "focus_areas": [],
            "paragraph_count": 5,
            "pii_total": 0,
            "ready_for_review": True,
        }
    """
    pp = postprocess_ocr_text(raw_text, skip_pii=skip_pii,
                               paragraph_min_length=paragraph_min_length)
    # contract_type 校验
    from skills.contract_review.reviewer import CONTRACT_TYPES
    if contract_type not in CONTRACT_TYPES:
        contract_type = "其他"

    pp.skill2_input = {
        "contract_type": contract_type,
        "contract_text": pp.sanitized_text,
        "stance": "审查方",
        "industry": "",
        "amount": None,
        "jurisdiction": "",
        "focus_areas": [],
        "paragraph_count": len(pp.paragraphs),
        "pii_total": pp.pii_report.get("total", 0),
        "ready_for_review": bool(pp.sanitized_text and len(pp.sanitized_text.strip()) >= 50),
    }
    return pp


# ===== CLI 自检 =====

if __name__ == "__main__":  # pragma: no cover
    print("=== LexPrime OCR 缓存两步拆分自检 ===\n")

    # 1) 缓存初始化
    cache = get_ocr_cache()
    print(f"[1] cache db: {cache.db_path}")
    print(f"    stats: {cache.stats()}\n")

    # 2) Step 1 跑 OCR (mock)
    fake_bytes = b"fake-image-bytes-for-test" * 100
    file_hash = OcrCache.hash_file_bytes(fake_bytes)
    print(f"[2] file_hash = {file_hash}")

    # 第一次: miss → OCR → 缓存
    r1 = run_ocr_with_cache(fake_bytes, filename="test_ocr_1.png")
    print(f"    run #1: cache_hit={r1.cache_hit} engine={r1.engine} conf={r1.ocr_result.confidence:.2f}")

    # 第二次: hit
    r2 = run_ocr_with_cache(fake_bytes, filename="test_ocr_1.png")
    print(f"    run #2: cache_hit={r2.cache_hit} age={r2.cache_age_seconds:.3f}s")

    # 3) Step 2 跑后处理
    pp = postprocess_for_skill2_review(r1.ocr_result.raw_text, contract_type="房屋租赁")
    print(f"\n[3] postprocess: pii_total={pp.pii_report.get('total')} "
          f"paragraphs={len(pp.paragraphs)} "
          f"ready={pp.skill2_input['ready_for_review']}")

    cache.purge_expired()
    cache.close()
    print("\n[done]")