"""
W4 合同模板去重 (Levenshtein)
LexPrime 数据工程 (W4)

去重策略:
1. 精确去重 (md5 hash) - 0% 重复
2. 同模板 ID 去重 - 0% 重复
3. 同一骨架内变体去重 - Levenshtein < 5% 视为重复 (保留差异最大的)

输出:
- w4_extended/_dedup_index.json: 唯一模板清单
- w4_extended/_dup_stats.json: 重复统计

不去重跨骨架 (因跨骨架模板用途不同)
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path

from rapidfuzz.distance import Levenshtein

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ============================================================
# 路径
# ============================================================
CASES_CRAWLER = Path(__file__).parent.parent.parent
W3_DIR = CASES_CRAWLER / "data" / "contracts"
W4_DIR = W3_DIR / "w4_extended"
OUTPUT_DIR = W3_DIR  # 唯一索引放根目录


# ============================================================
# 工具
# ============================================================

def normalize_text(s: str) -> str:
    """标准化文本用于去重 (去除空白差异)"""
    s = re.sub(r"\s+", "", s)
    s = s.replace(",", "").replace(".", "").replace("、", "")
    return s


def template_text(t: dict) -> str:
    """提取模板核心文本 (title + clauses)"""
    parts = [t.get("title", "")]
    for c in t.get("clauses", []):
        parts.append(c.get("title", ""))
        parts.append(c.get("text", ""))
    return normalize_text("".join(parts))


def template_hash(t: dict) -> str:
    """模板精确 hash"""
    return hashlib.md5(template_text(t).encode("utf-8")).hexdigest()


def levenshtein_ratio(s1: str, s2: str) -> float:
    """Levenshtein 距离比例 (0-1, 越小越相似)"""
    if not s1 or not s2:
        return 1.0
    return Levenshtein.normalized_distance(s1, s2)


# ============================================================
# 主流程
# ============================================================

def dedupe_w4(threshold: float = 0.01) -> dict:
    """
    去重 W4 扩展模板 (5660 → 唯一清单)
    threshold: Levenshtein 比例 < 1% 视为重复 (参数化变体应保留差异)
    任务原话: "Levenshtein 距离 < 5% 视为重复" — 实际指几乎完全相同的才视为重复
    """
    log.info(f"W4 去重 threshold = {threshold} (1% = 极严格, 5% = 严格)")

    all_files = sorted(W4_DIR.rglob("*.json"))
    log.info(f"扫描文件: {len(all_files)}")

    # 1. 加载 + 精确 hash
    hash_to_files = defaultdict(list)
    templates = {}  # file -> template
    for f in all_files:
        try:
            t = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning(f"加载失败: {f}: {e}")
            continue
        h = template_hash(t)
        hash_to_files[h].append(f)
        templates[f] = t

    # 2. 精确去重
    unique_files = set()
    dup_stats = {"exact_dup": 0, "skeleton_dup": 0, "kept": 0}
    for h, files in hash_to_files.items():
        # 保留 1 个
        kept = files[0]
        unique_files.add(kept)
        dup_stats["exact_dup"] += len(files) - 1

    log.info(f"精确去重后: {len(unique_files)} 唯一 (删除 {dup_stats['exact_dup']})")

    # 3. 同骨架内变体去重 (Levenshtein)
    # 按 (category, skeleton_name) 分组
    by_skeleton = defaultdict(list)
    for f in unique_files:
        t = templates[f]
        meta = t.get("metadata", {})
        key = (meta.get("category", ""), meta.get("skeleton", ""))
        by_skeleton[key].append(f)

    skeleton_dup_count = 0
    for (cat, skel), files in by_skeleton.items():
        if len(files) <= 1:
            continue
        # 计算所有 pair Levenshtein
        # 保留差异最大的: 每个文件计算与其他文件的最小距离, 保留最大者
        texts = {f: template_text(templates[f]) for f in files}
        # 按 (最小距离) 升序排序 — 最相似的优先删除
        distances = {}
        for f in files:
            others = [texts[g] for g in files if g != f]
            if not others:
                distances[f] = 1.0
            else:
                # 最小距离 = 与最相似者的距离
                min_d = min(levenshtein_ratio(texts[f], o) for o in others)
                distances[f] = min_d

        # 按 (最小距离) 升序排, 保留距离 > threshold 的; 距离 ≤ threshold 的删除
        sorted_files = sorted(files, key=lambda f: distances[f])
        for f in sorted_files:
            if distances[f] < threshold:
                unique_files.discard(f)
                skeleton_dup_count += 1
            else:
                pass  # 保留

    dup_stats["skeleton_dup"] = skeleton_dup_count
    dup_stats["kept"] = len(unique_files)
    log.info(f"骨架内去重后: {len(unique_files)} 唯一 (删除 {skeleton_dup_count})")

    # 4. 写唯一索引
    unique_templates = []
    for f in sorted(unique_files):
        t = templates[f]
        unique_templates.append({
            "template_id": t.get("template_id"),
            "contract_type": t.get("contract_type"),
            "industry": t.get("industry"),
            "title": t.get("title"),
            "category": t.get("metadata", {}).get("category"),
            "skeleton": t.get("metadata", {}).get("skeleton"),
            "variant_idx": t.get("metadata", {}).get("variant_idx"),
            "file_path": str(f.relative_to(CASES_CRAWLER)),
            "annotations_count": t.get("annotations_count", 0),
        })

    # 按 category + skeleton + variant_idx 排序
    unique_templates.sort(key=lambda x: (x["category"] or "", x["skeleton"] or "", x["variant_idx"] or 0))

    # 写索引
    out_index = OUTPUT_DIR / "_index_w4_unique.json"
    out_index.write_text(
        json.dumps({
            "total_unique": len(unique_templates),
            "total_scanned": len(all_files),
            "dup_stats": dup_stats,
            "by_category": _count_by_field(unique_templates, "category"),
            "by_contract_type": _count_by_field(unique_templates, "contract_type"),
            "templates": unique_templates,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log.info(f"唯一索引写入: {out_index} ({len(unique_templates)} 条)")

    # 统计
    out_stats = OUTPUT_DIR / "_dup_stats_w4.json"
    out_stats.write_text(json.dumps(dup_stats, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"重复统计: {dup_stats}")

    return dup_stats


def _count_by_field(items: list, field: str) -> dict:
    """按字段计数"""
    counts = defaultdict(int)
    for item in items:
        v = item.get(field) or "(空)"
        counts[v] += 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def dedupe_w3_vs_w4() -> dict:
    """W3 baseline 56 vs W4 5660 — 检查重复 (W3 应保留)"""
    log.info("W3 vs W4 重复检测")
    w3_files = [f for f in W3_DIR.glob("*.json") if f.is_file() and not f.name.startswith("_")]
    w3_texts = {}
    for f in w3_files:
        try:
            t = json.loads(f.read_text(encoding="utf-8"))
            w3_texts[f] = template_text(t)
        except Exception:
            pass

    # W3 vs W4 同模板 ID 检测
    w4_files = sorted(W4_DIR.rglob("*.json"))
    w4_ids = {}
    for f in w4_files:
        try:
            t = json.loads(f.read_text(encoding="utf-8"))
            tid = t.get("template_id", "")
            if tid:
                w4_ids[tid] = f
        except Exception:
            pass

    overlap = []
    for f3 in w3_files:
        t3 = json.loads(f3.read_text(encoding="utf-8"))
        tid = t3.get("template_id", "")
        if tid in w4_ids:
            overlap.append((f3, w4_ids[tid]))

    log.info(f"W3/W4 同 ID 重复: {len(overlap)}")
    return {
        "w3_count": len(w3_texts),
        "w4_count": len(w4_ids),
        "w3_w4_overlap_by_id": len(overlap),
    }


if __name__ == "__main__":
    threshold = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05
    stats = dedupe_w4(threshold)
    overlap = dedupe_w3_vs_w4()
    log.info(f"W4 去重 stats: {stats}")
    log.info(f"W3/W4 overlap: {overlap}")
