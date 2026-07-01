"""
W5 集成验证 E2E (W7 收口)

W5 死锁遗留的 w5-integration task (plan-05-w5-final-report § 3 已知 follow-up #4)
W6 接力时未补, W7 收口。

流程 (端到端):
1. PaddleEngine v3 (PP-OCRv6) 中文识别
2. FTS5 jieba 中文检索 (vs W4 unicode61 0 hits)
3. Skill 2 Reviewer 跑合同审查 (致命/重大/建议)
4. PII 脱敏 (W5 d2772f0 集成验证)

输出:
- 控制台日志
- docs/qa/w5-integration-e2e.md 报告

运行:
    venv312/python.exe scripts/w5/w5_integration_e2e.py
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

CASES_CRAWLER = Path(__file__).parent.parent.parent
sys.path.insert(0, str(CASES_CRAWLER))


def main() -> dict:
    print("=" * 60)
    print("=== W5 集成验证 E2E (W7 收口报告) ===")
    print("=" * 60)
    print()

    stats = {}

    # 1. PaddleEngine v3 中文识别
    print("--- 1. PaddleEngine v3 中文识别 (PP-OCRv6) ---")
    from core.ocr import get_ocr_engine  # noqa: E402

    from PIL import Image, ImageDraw, ImageFont  # noqa: E402

    img = Image.new("RGB", (900, 450), color="white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 18)
        font_h = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 22)
    except Exception:
        font = ImageFont.load_default()
        font_h = font

    contract_lines = [
        ("房屋租赁合同", font_h),
        ("第一条 租赁标的", font),
        ("甲方将位于北京市朝阳区建国路 88 号的房屋出租给乙方使用。", font),
        ("第二条 租赁期限", font),
        ("租赁期限为 12 个月, 自 2026 年 1 月 1 日起至 2026 年 12 月 31 日止。", font),
        ("第三条 租金及支付方式", font),
        ("月租金为人民币 8000 元整, 乙方应于每月 5 日前支付当月租金。", font),
        ("第四条 违约责任", font),
        ("乙方逾期支付租金的, 每逾期一日按月租金 5% 加收违约金。", font),
        ("第五条 争议管辖", font),
        ("本合同争议, 任一方均有权向甲方住所地人民法院提起诉讼。", font),
    ]
    for i, (line, f) in enumerate(contract_lines):
        draw.text((20, 20 + i * 38), line, fill="black", font=f)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    t0 = time.time()
    engine = get_ocr_engine()
    result = engine.run(img_bytes, filename="contract.png")
    ocr_elapsed = (time.time() - t0) * 1000
    print(f"  engine = {result.source_engine}")
    print(f"  confidence = {result.confidence:.4f}")
    print(f"  lines = {len(result.lines)}, pages = {result.page_count}")
    print(f"  OCR time: {ocr_elapsed:.0f}ms")
    print()
    stats["paddle_engine"] = {
        "name": result.source_engine,
        "confidence": round(result.confidence, 4),
        "lines_recognized": len(result.lines),
        "ocr_time_ms": round(ocr_elapsed, 1),
        "pass": result.confidence > 0.5 and len(result.lines) >= 5,
    }

    # 2. FTS5 jieba 检索
    print("--- 2. FTS5 jieba 中文检索 ---")
    import sqlite3  # noqa: E402
    from scripts.w4.rebuild_fts5_index import (  # noqa: E402
        _pre_tokenize,
        _to_or_match,
    )
    db_path = CASES_CRAWLER / "db" / "contract_templates.db"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    queries = ["房屋租赁合同", "违约金", "管辖不利", "借款", "劳动合同"]
    fts_stats = []
    for q in queries:
        seg = _to_or_match(_pre_tokenize(q))
        t0 = time.time()
        cur.execute(
            "SELECT COUNT(*) FROM contract_fts_zh WHERE contract_fts_zh MATCH ?",
            (seg,),
        )
        n = cur.fetchone()[0]
        elapsed = (time.time() - t0) * 1000
        fts_stats.append({"q": q, "seg": seg, "hits": n, "ms": elapsed})
        print(f"  {q!r:20s} -> {seg!r:30s} -> {n:4d} hits ({elapsed:.1f}ms)")
    print()
    conn.close()
    stats["fts5_jieba"] = {
        "queries": fts_stats,
        "total_hits": sum(s["hits"] for s in fts_stats),
        "pass": all(s["hits"] > 0 for s in fts_stats[:3]),
    }

    # 3. Skill 2 Reviewer
    print("--- 3. Skill 2 Reviewer ---")
    try:
        from skills.contract_review.reviewer import (  # noqa: E402
            ReviewerInput,
            ReviewerConfig,
            run_skill,
        )
        # 用真实合同文本 (不调 LLM, 走 demo 路径)
        test_text = """
房屋租赁合同
第一条 违约责任
乙方逾期支付租金的, 每逾期一日按月租金 5% 加收违约金, 甲方有权单方解除合同并不退还已付款项。
第二条 争议管辖
本合同争议由甲方住所地人民法院管辖。
第三条 知识产权
乙方提供服务产生的所有工作成果, 知识产权均归甲方所有。
"""
        ri = ReviewerInput(
            contract_type="房屋租赁",
            contract_text=test_text,
            stance="乙方",
            industry="",
            amount=None,
            jurisdiction="",
            include_suggestion=True,
            include_negotiation_strategy=True,
            case_id="w5-integration-e2e",
        )
        # retrieval 关掉避免 LanceDB 依赖 (W7 收口只验证流程 + OCR + FTS5)
        config = ReviewerConfig(retrieval_enabled=False)

        t0 = time.time()
        result = run_skill(ri, config)
        reviewer_elapsed = (time.time() - t0) * 1000
        print(f"  Reviewer time: {reviewer_elapsed:.0f}ms")
        print(
            f"  fatal={result.risk_summary.get('fatal_count', 0)}, "
            f"major={result.risk_summary.get('major_count', 0)}, "
            f"advisory={result.risk_summary.get('advisory_count', 0)}"
        )
        print()
        stats["reviewer"] = {
            "fatal_count": result.risk_summary.get("fatal_count", 0),
            "major_count": result.risk_summary.get("major_count", 0),
            "elapsed_ms": round(reviewer_elapsed, 1),
            "pass": reviewer_elapsed < 5000,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"  [skip] reviewer 不可用: {e}")
        stats["reviewer"] = {"error": str(e), "pass": False}

    # 4. PII 脱敏
    print("--- 4. PII 脱敏 (W5 d2772f0 集成) ---")
    try:
        from core.pii import sanitize_for_review  # noqa: E402
        pii_text = "张三 (身份证号 110101199003078811) 借给李四 (13812345678) 人民币 500000 元"
        redacted, report = sanitize_for_review(pii_text)
        print(f"  原: {pii_text}")
        print(f"  脱: {redacted}")
        print(f"  report: {report}")
        print()
        stats["pii"] = {
            "redacted": redacted,
            "report": str(report),
            "pass": (
                "110101199003078811" not in redacted
                and "13812345678" not in redacted
            ),
        }
    except Exception as e:
        print(f"  [skip] pii 不可用: {e}")
        stats["pii"] = {"error": str(e), "pass": False}

    # 5. 总结
    print("--- 5. W5 集成验证总结 ---")
    all_pass = all(v.get("pass", True) for v in stats.values())
    stats["all_pass"] = all_pass
    stats["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print()
    print("=" * 60)
    print(f"ALL PASS: {all_pass}")
    return stats


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result.get("all_pass") else 1)