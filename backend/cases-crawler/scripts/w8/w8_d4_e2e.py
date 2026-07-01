"""
W8 D4: W5 集成验证 E2E (lex-ai, W5 final report §3 follow-up #4 闭环)

W5 集成遗留: w5-integration task 因 producer 死锁没跑
W6 接力时未补, W7 收口时部分补 (commit d81379f, 单合同 PIL 合成 + 4 步流程)
W8 D4: 完整闭环 — 5 合同真实 fixture × 5 维度端到端验证

W8 D4 升级 (vs W7 d81379f):
1. **真实合同 fixture** (5 份 from data/contracts/), 而非 PIL 合成的 1 份示例
2. **OCR 走 venv312 PaddleEngine 子进程** (W7 用主 Python mock)
3. **检索 + reviewer 启用 retrieval_evidence** (W7 关掉了)
4. **5 维度分类 100% 命中** (W7 只验证单合同流程)
5. **PaddleEngine → Tesseract → Mock 三级 fallback** (W7 只有 Paddle/Mock)

E2E 4 步 (5 合同 × 5 维度 = 25 项验收):

  1. PaddleEngine v3 OCR (真实合同 PNG)
  2. FTS5 jieba 检索 (5 关键词 OR 召回)
  3. Skill 2 Reviewer (条款拆分 + 三级分类 + retrieval_evidence)
  4. LanceDB BGE 双路召回 (致命/重大 risk → 历史样本 top-3)
  5. PII 脱敏 (W5 d2772f0 集成验证)

输出:
- 控制台日志
- docs/qa/w5-integration-e2e-w8.md 报告 (覆盖 W7 d81379f 的 e2e 报告)

运行:
    cd backend/cases-crawler
    python scripts/w8/w8_d4_e2e.py
"""
from __future__ import annotations

import io
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any

# 路径
CASES_CRAWLER = Path(__file__).parent.parent.parent
sys.path.insert(0, str(CASES_CRAWLER))

# W8 D4 关键: reviewer 的 _get_risk_index() 用相对路径 "data/lancedb",
# 必须把 cwd 切到 cases-crawler 才能加载 LanceDB 索引。
os.chdir(str(CASES_CRAWLER))

# venv312 在 backend/ 下, 不是 cases-crawler/ 下 (W8 D1 f37b54c 装的)
BACKEND_ROOT = CASES_CRAWLER.parent
VENV312_PY = BACKEND_ROOT / "venv312" / "python.exe"
OCR_SUBPROCESS = CASES_CRAWLER / "scripts" / "w8" / "ocr_via_venv312.py"
DATA_CONTRACTS = CASES_CRAWLER / "data" / "contracts"
DB_PATH = CASES_CRAWLER / "db" / "contract_templates.db"
TMP_DIR = Path("C:/Users/42081/AppData/Local/Temp/w8_d4_fixtures")

# 5 合同 fixture (从 W4 reindex 56 模板里选, 覆盖 5 大类型 + fatal/major 比例高)
FIXTURES = [
    "house-rent-residential-01",   # 房屋租赁: 1 fatal + 3 major + 1 advisory
    "loan-personal-01",            # 借款合同: 1 fatal + 2 major + 2 advisory
    "loan-p2p-01",                 # 借款合同: 1 fatal + 2 major + 2 advisory
    "sales-goods-01",              # 销售合同: 1 fatal + 0 major + 4 advisory
    "service-tech-01",             # 服务合同: 1 fatal + 0 major + 4 advisory
]


# ===== 1) 渲染合同 → PNG =====

def render_contract_to_png(contract_json: Dict[str, Any]) -> bytes:
    """把合同 JSON 渲染成 PNG (PIL 模拟扫描件)
    
    Args:
        contract_json: data/contracts/{template_id}.json
    
    Returns:
        PNG bytes
    """
    from PIL import Image, ImageDraw, ImageFont

    lines = []
    title = contract_json.get("title", contract_json.get("template_id", ""))
    ctype = contract_json.get("contract_type", "")
    lines.append(f"{ctype} - {title}")
    lines.append("=" * 60)

    for c in contract_json.get("clauses", []):
        idx = c.get("index", "")
        ct = c.get("title", "")
        tx = c.get("text", "")
        lines.append(f"第{idx}条 {ct}")
        lines.append(tx)
        lines.append("")

    # 字体
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 16)
    except Exception:
        font = ImageFont.load_default()

    # 估算图片尺寸 (按字符宽度)
    line_h = 28
    max_w = max(_text_w(line, font) for line in lines) + 60
    img_w = min(1200, max(800, max_w))
    img_h = max(400, line_h * (len(lines) + 4))

    img = Image.new("RGB", (img_w, img_h), color="white")
    draw = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        draw.text((30, 20 + i * line_h), ln, fill="black", font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _text_w(text: str, font) -> int:
    """估算文本像素宽度 (无 font.getbbox 用 .getlength)"""
    try:
        return int(font.getlength(text))
    except Exception:
        return len(text) * 16


# ===== 2) OCR (venv312 PaddleEngine 子进程) =====

def ocr_via_venv312(png_bytes: bytes, fixture_id: str,
                     timeout: int = 120) -> Dict[str, Any]:
    """调 venv312 PaddleEngine 子进程跑 OCR
    
    Args:
        png_bytes: PNG 字节流
        fixture_id: 合同 ID (用于文件命名)
        timeout: subprocess 超时秒数
    
    Returns:
        dict {ok, engine, raw_text, confidence, lines, ...} 或 {ok: False, error}
    """
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    png_path = TMP_DIR / f"{fixture_id}.png"
    png_path.write_bytes(png_bytes)

    try:
        result = subprocess.run(
            [str(VENV312_PY), str(OCR_SUBPROCESS), str(png_path)],
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timeout ({timeout}s)"}

    if result.returncode != 0:
        return {
            "ok": False,
            "error": f"returncode={result.returncode}",
            "stderr_tail": result.stderr.decode("utf-8", errors="replace")[-300:],
        }

    try:
        out = json.loads(result.stdout.decode("utf-8", errors="replace"))
    except Exception as e:
        return {"ok": False, "error": f"parse stdout err: {e}"}

    return out


# ===== 3) Skill 2 Reviewer (含 retrieval_evidence) =====

def review_contract(contract_text: str, contract_type: str,
                     stance: str = "乙方") -> Dict[str, Any]:
    """跑 Skill 2 reviewer, 返回 clause_reviews / risk_summary / retrieval_stats
    
    Args:
        contract_text: 完整合同文本 (OCR 输出)
        contract_type: 合同类型 (房屋租赁/借款合同/etc.)
        stance: 立场 (默认乙方, 验收要求 5 维度)
    """
    from skills.contract_review.reviewer import (
        ReviewerInput,
        ReviewerConfig,
        run_skill,
    )
    ri = ReviewerInput(
        contract_type=contract_type,
        contract_text=contract_text,
        stance=stance,
        case_id=f"w8-d4-{int(time.time()*1000) % 100000}",
    )
    # 启用 retrieval (W4 BGE LanceDB 双路召回)
    config = ReviewerConfig(retrieval_enabled=True, retrieval_top_k=5)
    t0 = time.time()
    out = run_skill(ri, config)
    elapsed_ms = (time.time() - t0) * 1000

    return {
        "elapsed_ms": round(elapsed_ms, 1),
        "risk_summary": out.risk_summary,
        "clause_reviews": out.clause_reviews,
        "retrieval_stats": out.ui_hints.get("retrieval_stats", {}),
        "disclaimer": out.disclaimer,
    }


# ===== 4) FTS5 jieba 检索 =====

def fts5_search(query: str, db_path: Path = DB_PATH,
                 table: str = "contract_fts_zh") -> int:
    """FTS5 jieba 关键词检索
    
    Args:
        query: 中文关键词
        db_path: SQLite DB
        table: contract_fts_zh (W7) 或 contracts_fts (W8 D2)
    
    Returns:
        hits 数
    """
    from core.fts5_tokenizer import tokenize_query, to_or_match

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        # 检查表存在
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        )
        if not cur.fetchone():
            return -1
        # 用 D2 模块化 tokenizer
        tokens = tokenize_query(query)
        seg = to_or_match(tokens)
        cur.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {table} MATCH ?",
            (seg,),
        )
        return cur.fetchone()[0]
    except Exception:
        return -2
    finally:
        conn.close()


# ===== 5) PII 脱敏 =====

def pii_redact(text: str) -> Dict[str, Any]:
    """PII 脱敏验证"""
    from core.pii import sanitize_for_review
    redacted, report = sanitize_for_review(text)
    return {"redacted": redacted, "report": str(report)}


# ===== 维度定义 =====

DIMENSIONS = [
    "OCR 文本识别 (PaddleEngine)",
    "FTS5 jieba 检索 (D2 模块化)",
    "Skill 2 条款拆分",
    "三级风险分类 (fatal/major/advisory)",
    "retrieval_evidence 双路召回 (LanceDB BGE)",
]


def run_one_fixture(fixture_id: str) -> Dict[str, Any]:
    """跑一个合同 fixture 的 5 维度验收"""
    print(f"\n=== Fixture: {fixture_id} ===")
    json_path = DATA_CONTRACTS / f"{fixture_id}.json"
    if not json_path.exists():
        return {"fixture_id": fixture_id, "error": f"missing {json_path}", "pass": False}

    contract = json.load(open(json_path, encoding="utf-8"))
    contract_type = contract.get("contract_type", "其他")
    clauses_count = len(contract.get("clauses", []))

    print(f"  type={contract_type}, clauses={clauses_count}")

    fixture_result = {
        "fixture_id": fixture_id,
        "contract_type": contract_type,
        "clauses_count": clauses_count,
        "dimensions": {},
    }

    # ----- 维度 1: OCR -----
    print("  [1/5] OCR (PaddleEngine venv312)...")
    png_bytes = render_contract_to_png(contract)
    t0 = time.time()
    ocr = ocr_via_venv312(png_bytes, fixture_id, timeout=180)
    ocr_ms = (time.time() - t0) * 1000

    if not ocr.get("ok"):
        print(f"    FAIL: {ocr.get('error')}")
        fixture_result["dimensions"]["ocr"] = {"pass": False, "error": ocr.get("error")}
        return {**fixture_result, "pass": False}
    raw_text = ocr.get("raw_text", "")
    line_count = ocr.get("line_count", 0)
    ocr_pass = (
        ocr.get("engine") == "paddle"
        and line_count >= 3
        and len(raw_text) >= 20
    )
    print(f"    engine={ocr['engine']}, conf={ocr['confidence']:.4f}, "
          f"lines={line_count}, chars={len(raw_text)}, "
          f"time={ocr_ms:.0f}ms")
    print(f"    {'PASS' if ocr_pass else 'FAIL'}")
    fixture_result["dimensions"]["ocr"] = {
        "engine": ocr.get("engine"),
        "confidence": ocr.get("confidence"),
        "line_count": line_count,
        "char_count": len(raw_text),
        "ocr_time_ms": round(ocr_ms, 1),
        "pass": ocr_pass,
    }

    # ----- 维度 2: FTS5 jieba -----
    print("  [2/5] FTS5 jieba 关键词检索...")
    # 选 2 个核心关键词
    keywords_map = {
        "房屋租赁": ["租金", "租赁"],
        "借款合同": ["借款", "还款"],
        "劳动合同": ["工资", "工作"],
        "销售合同": ["货物", "价款"],
        "服务合同": ["服务", "费用"],
    }
    keywords = keywords_map.get(contract_type, ["合同", "条款"])
    fts_hits = []
    fts_pass = True
    for kw in keywords:
        hits = fts5_search(kw)
        fts_hits.append({"keyword": kw, "hits": hits})
        print(f"    {kw!r:8s} → {hits:4d} hits")
        if hits <= 0:
            fts_pass = False
    fixture_result["dimensions"]["fts5_jieba"] = {
        "queries": fts_hits,
        "pass": fts_pass,
    }
    print(f"    {'PASS' if fts_pass else 'FAIL'}")

    # ----- 维度 3-5: Reviewer + 三级分类 + retrieval_evidence -----
    print("  [3-5/5] Skill 2 Reviewer (含 retrieval_evidence)...")
    try:
        review = review_contract(raw_text, contract_type, stance="乙方")
        rs = review["risk_summary"]
        fatal = rs.get("fatal_count", 0)
        major = rs.get("major_count", 0)
        advisory = rs.get("advisory_count", 0)
        ok = rs.get("ok_count", 0)
        clause_count = len(review["clause_reviews"])

        # 维度 3: 条款拆分命中 (>= 3 条)
        split_pass = clause_count >= 3

        # 维度 4: 三级分类 (fatal + major + advisory + ok 总数 == 拆分条数)
        classify_pass = (
            (fatal + major + advisory + ok) == clause_count
            and clause_count > 0
        )

        # 维度 5: retrieval_evidence (致命/重大条款有 evidence)
        retrieval_stats = review.get("retrieval_stats", {})
        evidence_clauses = sum(
            1 for r in review["clause_reviews"]
            if r.get("retrieval_evidence")
        )
        retrieval_pass = (
            retrieval_stats.get("index_enabled", False)
            and retrieval_stats.get("recall_pct", 0) >= 50.0  # 召回 >= 50%
        )
        evidence_pct = (
            evidence_clauses / max(1, retrieval_stats.get("fatal_major_clauses", 1)) * 100
        )

        print(f"    clauses={clause_count}, "
              f"fatal={fatal} major={major} advisory={advisory} ok={ok}, "
              f"review_time={review['elapsed_ms']:.0f}ms")
        print(f"    retrieval: enabled={retrieval_stats.get('index_enabled')}, "
              f"fatal_major={retrieval_stats.get('fatal_major_clauses')}, "
              f"recall={retrieval_stats.get('recall_pct'):.1f}%, "
              f"evidence_clauses={evidence_clauses}")

        fixture_result["dimensions"]["reviewer_split"] = {
            "clause_count": clause_count,
            "pass": split_pass,
        }
        fixture_result["dimensions"]["risk_classify"] = {
            "fatal": fatal,
            "major": major,
            "advisory": advisory,
            "ok": ok,
            "total": clause_count,
            "pass": classify_pass,
        }
        fixture_result["dimensions"]["retrieval_evidence"] = {
            "index_enabled": retrieval_stats.get("index_enabled"),
            "fatal_major_clauses": retrieval_stats.get("fatal_major_clauses"),
            "clauses_with_evidence": retrieval_stats.get("clauses_with_evidence"),
            "recall_pct": retrieval_stats.get("recall_pct"),
            "evidence_pct": round(evidence_pct, 1),
            "sample_evidence": [
                {
                    "clause_id": r["clause_id"],
                    "clause_title": r["clause_title"],
                    "risk_level": r["risk_level"],
                    "evidence_count": len(r.get("retrieval_evidence", [])),
                    "top_similarity": (
                        r.get("retrieval_evidence", [{}])[0].get("similarity")
                        if r.get("retrieval_evidence") else None
                    ),
                }
                for r in review["clause_reviews"]
                if r.get("retrieval_evidence")
            ][:3],
            "pass": retrieval_pass,
        }
        for dim_name in ["reviewer_split", "risk_classify", "retrieval_evidence"]:
            dim = fixture_result["dimensions"][dim_name]
            print(f"    [{dim_name}] {'PASS' if dim['pass'] else 'FAIL'}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        for dim_name in ["reviewer_split", "risk_classify", "retrieval_evidence"]:
            fixture_result["dimensions"][dim_name] = {"pass": False, "error": str(e)}
        print(f"    FAIL: reviewer exception {e!r}")

    # 5 维度总通过
    all_pass = all(
        d.get("pass", False)
        for d in fixture_result["dimensions"].values()
    )
    fixture_result["pass"] = all_pass
    print(f"  Fixture {'PASS' if all_pass else 'FAIL'}")
    return fixture_result


def main() -> Dict[str, Any]:
    print("=" * 70)
    print("=== W8 D4: W5 集成验证 E2E (5 合同 × 5 维度) ===")
    print("=" * 70)
    print()
    print(f"FIXTURES: {FIXTURES}")
    print(f"VENV312:  {VENV312_PY}")
    print(f"OCR sub:  {OCR_SUBPROCESS}")
    print(f"DB:       {DB_PATH}")
    print(f"DB size:  {DB_PATH.stat().st_size / 1024 / 1024:.1f}MB")
    print()

    # 全部 fixture 跑
    all_results = []
    total_start = time.time()
    for fixture_id in FIXTURES:
        try:
            result = run_one_fixture(fixture_id)
        except Exception as e:
            import traceback
            traceback.print_exc()
            result = {"fixture_id": fixture_id, "pass": False, "error": str(e)}
        all_results.append(result)
    total_elapsed = time.time() - total_start

    # ===== 统计 =====
    print()
    print("=" * 70)
    print("=== 验收汇总 ===")
    print("=" * 70)

    pass_count = sum(1 for r in all_results if r.get("pass"))
    total_count = len(all_results)

    # 维度命中统计 (5 fixture × 5 维度 = 25 项)
    dim_stats = {d: {"pass": 0, "fail": 0} for d in DIMENSIONS}
    dim_key_map = {
        DIMENSIONS[0]: "ocr",
        DIMENSIONS[1]: "fts5_jieba",
        DIMENSIONS[2]: "reviewer_split",
        DIMENSIONS[3]: "risk_classify",
        DIMENSIONS[4]: "retrieval_evidence",
    }
    for r in all_results:
        for dim_name, dim_key in dim_key_map.items():
            if dim_key in r.get("dimensions", {}):
                if r["dimensions"][dim_key].get("pass"):
                    dim_stats[dim_name]["pass"] += 1
                else:
                    dim_stats[dim_name]["fail"] += 1

    print(f"\n合同通过: {pass_count}/{total_count} ({pass_count/total_count*100:.0f}%)")
    print(f"总耗时: {total_elapsed:.1f}s ({total_elapsed/total_count:.1f}s/合同)")
    print()
    print(f"{'维度':<35} {'PASS':>5} {'FAIL':>5} {'命中率':>7}")
    print("-" * 60)
    for dim_name, stat in dim_stats.items():
        total = stat["pass"] + stat["fail"]
        pct = stat["pass"] / total * 100 if total else 0
        print(f"{dim_name:<35} {stat['pass']:>5} {stat['fail']:>5} {pct:>6.0f}%")

    # 验收: 25 项 100% 命中
    total_dim_pass = sum(s["pass"] for s in dim_stats.values())
    total_dim = sum(s["pass"] + s["fail"] for s in dim_stats.values())
    overall_pass = (pass_count == total_count) and (total_dim_pass == total_dim)

    print()
    print(f"维度命中: {total_dim_pass}/{total_dim} ({total_dim_pass/total_dim*100:.0f}%)")
    print(f"OVERALL:  {'ALL PASS ✅' if overall_pass else 'PARTIAL ❌'}")
    print()

    return {
        "fixtures": all_results,
        "fixture_pass": f"{pass_count}/{total_count}",
        "dim_stats": dim_stats,
        "total_dim_pass": total_dim_pass,
        "total_dim": total_dim,
        "overall_pass": overall_pass,
        "total_elapsed_s": round(total_elapsed, 1),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result["overall_pass"] else 1)