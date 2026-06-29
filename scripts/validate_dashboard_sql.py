#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
W13 C1 dashboard 7 SQL 验证脚本 (lex-coder · 2026-06-30)
- 验证 docs/marketing/dashboard_w11.md §6 的 7 SQL 在 SQLite 上语法正确
- 即使 tracking_events 表不存在 (7/26 公测前), SQL 也能 parse
- 同时跑一个 mock server (port 8001) 返回 dashboard_w11 FALLBACK_TARGETS,
  让前端 dashboard 切换到 API 实时数据源
"""
import sqlite3
import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

DB_PATH = Path(r"E:\元枢法智前端\yuanxing\backend\cases-crawler\lexprime.db")

# dashboard_w11.md §6.1-6.7 的 7 SQL (转换为 SQLite 兼容语法)
SQL_QUERIES = [
    {
        "name": "6.1 注册转化率 (trial_started / invite_redeemed)",
        "sql": """SELECT DATE(t2.created_at) AS day,
  COUNT(DISTINCT t2.user_id) AS invite_redeemed,
  COUNT(DISTINCT t3.user_id) AS trial_started,
  ROUND(COUNT(DISTINCT t3.user_id) * 100.0 / NULLIF(COUNT(DISTINCT t2.user_id), 0), 1) AS reg_cvr_pct
FROM tracking_events t2
LEFT JOIN tracking_events t3 ON t2.user_id = t3.user_id
  AND t3.event = 'trial_started'
  AND t3.created_at >= t2.created_at
WHERE t2.event = 'invite_redeemed'
  AND t2.created_at >= '2026-07-26'
GROUP BY DATE(t2.created_at);"""
    },
    {
        "name": "6.2 试用转化率 (invite_redeemed / landing_viewed)",
        "sql": """SELECT DATE(t1.created_at) AS day,
  COUNT(DISTINCT t1.user_id) AS landing_viewed,
  COUNT(DISTINCT t2.user_id) AS invite_redeemed,
  ROUND(COUNT(DISTINCT t2.user_id) * 100.0 / NULLIF(COUNT(DISTINCT t1.user_id), 0), 1) AS trial_cvr_pct
FROM tracking_events t1
LEFT JOIN tracking_events t2 ON t1.user_id = t2.user_id
  AND t2.event = 'invite_redeemed'
  AND t2.created_at >= t1.created_at
WHERE t1.event = 'landing_viewed'
  AND t1.created_at >= '2026-07-26'
GROUP BY DATE(t1.created_at);"""
    },
    {
        "name": "6.3 付费转化率 (paid_converted / trial_started)",
        "sql": """SELECT strftime('%Y-%m', t3.created_at) AS month,
  COUNT(DISTINCT t3.user_id) AS total_trial,
  COUNT(DISTINCT t4.user_id) AS paid_converted,
  ROUND(COUNT(DISTINCT t4.user_id) * 100.0 / NULLIF(COUNT(DISTINCT t3.user_id), 0), 1) AS paid_cvr_pct
FROM tracking_events t3
LEFT JOIN tracking_events t4 ON t3.user_id = t4.user_id
  AND t4.event = 'paid_converted'
  AND t4.created_at >= t3.created_at
WHERE t3.event = 'trial_started'
  AND t3.created_at >= '2026-07-26'
GROUP BY strftime('%Y-%m', t3.created_at);"""
    },
    {
        "name": "6.4 创史转化率 (advocate_promoted / trial_started)",
        "sql": """SELECT DATE(t3.created_at) AS day,
  COUNT(DISTINCT t3.user_id) AS trial_started,
  COUNT(DISTINCT t5.user_id) AS advocate_promoted,
  ROUND(COUNT(DISTINCT t5.user_id) * 100.0 / NULLIF(COUNT(DISTINCT t3.user_id), 0), 1) AS advocate_cvr_pct
FROM tracking_events t3
LEFT JOIN tracking_events t5 ON t3.user_id = t5.user_id
  AND t5.event = 'advocate_promoted'
  AND t5.created_at >= t3.created_at
WHERE t3.event = 'trial_started'
  AND t3.created_at >= '2026-07-26'
GROUP BY DATE(t3.created_at);"""
    },
    {
        "name": "6.5 创史招募率 (advocate_promoted / 80 席目标)",
        "sql": """SELECT DATE(t5.created_at) AS day,
  COUNT(DISTINCT t5.user_id) AS cumulative_advocate,
  ROUND(COUNT(DISTINCT t5.user_id) * 100.0 / 80, 1) AS recruitment_rate_pct
FROM tracking_events t5
WHERE t5.event = 'advocate_promoted'
  AND t5.created_at >= '2026-07-26'
  AND json_extract(t5.form_fields, '$.channel') = 'founding_member'
GROUP BY DATE(t5.created_at);"""
    },
    {
        "name": "6.6 创史群活跃 (feedback_completed_day_N / advocate_promoted)",
        "sql": """SELECT DATE(t7.created_at) AS day,
  json_extract(t7.form_fields, '$.feedback_day') AS day_label,
  COUNT(DISTINCT t7.user_id) AS feedback_completed,
  COUNT(DISTINCT t5.user_id) AS advocate_promoted_total,
  ROUND(COUNT(DISTINCT t7.user_id) * 100.0 / NULLIF(COUNT(DISTINCT t5.user_id), 0), 1) AS engagement_rate_pct
FROM tracking_events t7
LEFT JOIN tracking_events t5 ON t7.user_id = t5.user_id
  AND t5.event = 'advocate_promoted'
WHERE t7.event = 'feedback_completed'
  AND json_extract(t7.form_fields, '$.channel') = 'founding_member'
  AND t7.created_at >= '2026-07-26'
GROUP BY DATE(t7.created_at), json_extract(t7.form_fields, '$.feedback_day');"""
    },
    {
        "name": "6.7 创史付费转化 (paid_converted is_founding_member=True / advocate_promoted)",
        "sql": """SELECT strftime('%Y-%W', t4.created_at) AS week,
  COUNT(DISTINCT t4.user_id) AS founding_paid,
  COUNT(DISTINCT t5.user_id) AS total_founding,
  ROUND(COUNT(DISTINCT t4.user_id) * 100.0 / NULLIF(COUNT(DISTINCT t5.user_id), 0), 1) AS founding_paid_rate_pct
FROM tracking_events t4
LEFT JOIN tracking_events t5 ON t5.event = 'advocate_promoted'
  AND t5.user_id = t4.user_id
WHERE t4.event = 'paid_converted'
  AND json_extract(t4.form_fields, '$.is_founding_member') = 'true'
  AND t4.created_at >= '2026-07-26'
GROUP BY strftime('%Y-%W', t4.created_at);"""
    },
]


def validate_sql():
    """验证 7 SQL 在 SQLite 上 parse 正确 (即使表不存在)"""
    print("=" * 70)
    print(f"📊 W13 C1 dashboard 7 SQL 验证 · DB: {DB_PATH}")
    print("=" * 70)

    if not DB_PATH.exists():
        print("⚠️  DB 不存在, 用 memory 临时 DB 验证 parse")
        conn = sqlite3.connect(":memory:")
    else:
        conn = sqlite3.connect(str(DB_PATH))

    cur = conn.cursor()

    # 创建临时 tracking_events (空表) 模拟公测 7/26 前的状态
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tracking_events (
            id INTEGER PRIMARY KEY,
            event TEXT,
            user_id TEXT,
            created_at TEXT,
            form_fields TEXT
        )
    """)

    passed = 0
    failed = []
    for i, q in enumerate(SQL_QUERIES, 1):
        try:
            # 用 sqlite3 内部 validate (prepare 阶段)
            cur.execute("EXPLAIN " + q["sql"])
            cur.fetchall()  # drain
            print(f"  [{i}/7] ✓ {q['name'][:60]}")
            passed += 1
        except Exception as e:
            print(f"  [{i}/7] ✗ {q['name'][:60]}: {e}")
            failed.append((i, q["name"], str(e)))

    conn.close()

    print()
    print("=" * 70)
    print(f"📈 验证结果: {passed}/7 SQL parse PASS")
    print("=" * 70)
    if failed:
        for i, name, err in failed:
            print(f"  ✗ [{i}] {name}")
            print(f"     {err}")
        return 1
    return 0


def run_mock_server():
    """Mini mock server 返回 dashboard FALLBACK_TARGETS"""
    from urllib.parse import urlparse, parse_qs

    # 加载 frontend dashboard/index.html 的 FALLBACK_TARGETS (内嵌 JS)
    # 为简化, 直接构造结构 (跟 FALLBACK_TARGETS 对齐)
    payload = {
        "meta": {
            "campaign_window": "2026-07-26 ~ 2026-08-24",
            "goal_window": "30 天 + 8 月底",
            "data_source": "mock_server (W13 C1 follow-up 验证)",
            "last_updated": "2026-06-30 05:56 CST",
            "invite_codes_total": 1115,
            "founding_seats_total": 80,
            "founding_seats_remaining": 80,
        },
        "metrics": {
            "registration_cvr": {"target_pct": 80, "numerator": 0, "denominator": 0,
                                  "numerator_label": "试用律师", "denominator_label": "兑换律师"},
            "trial_cvr": {"target_pct": 15, "numerator": 0, "denominator": 0,
                           "numerator_label": "兑换律师", "denominator_label": "landing 访问"},
            "paid_cvr": {"target_pct": 25, "numerator": 0, "denominator": 0,
                         "numerator_label": "付费律师", "denominator_label": "试用律师"},
            "advocate_cvr": {"target_pct": 60, "numerator": 0, "denominator": 0,
                              "numerator_label": "创史律师", "denominator_label": "试用律师"},
            "founding_recruit": {"target_pct": 100, "numerator": 0, "denominator": 80,
                                  "numerator_label": "已发创史席", "denominator_label": "80 席目标"},
            "founding_engagement": {"target_pct": 80, "numerator": 0, "denominator": 0,
                                     "numerator_label": "反馈完成", "denominator_label": "创史律师"},
            "founding_paid": {"target_pct": 30, "numerator": 0, "denominator": 0,
                               "numerator_label": "创史付费", "denominator_label": "创史律师"},
        },
        "cumulative_target": {
            "landing_viewed": 1025,
            "invite_redeemed": 235,
            "trial_started": 199,
            "paid_converted": 51,
            "advocate_promoted": 191,
        },
        "daily_trend": [
            {"day": "07-26", "landing": 0, "redeemed": 0, "trial": 0, "paid": 0, "advocate": 0, "feedback": 0},
            {"day": "07-27", "landing": 0, "redeemed": 0, "trial": 0, "paid": 0, "advocate": 0, "feedback": 0},
            {"day": "07-28", "landing": 0, "redeemed": 0, "trial": 0, "paid": 0, "advocate": 0, "feedback": 0},
            {"day": "07-29", "landing": 0, "redeemed": 0, "trial": 0, "paid": 0, "advocate": 0, "feedback": 0},
            {"day": "07-30", "landing": 0, "redeemed": 0, "trial": 0, "paid": 0, "advocate": 0, "feedback": 0},
            {"day": "07-31", "landing": 0, "redeemed": 0, "trial": 0, "paid": 0, "advocate": 0, "feedback": 0},
            {"day": "08-01", "landing": 0, "redeemed": 0, "trial": 0, "paid": 0, "advocate": 0, "feedback": 0},
        ],
        "channels": [
            {"name": "评审律师 (5)", "reach": 5, "landing": 5, "redeemed": 5, "trial": 5, "paid": 3, "advocate": 5, "cvr_paid": 50},
            {"name": "微信群律师 (10)", "reach": 10, "landing": 20, "redeemed": 10, "trial": 8, "paid": 2, "advocate": 5, "cvr_paid": 20},
            {"name": "创史公开段 (95)", "reach": 95, "landing": 95, "redeemed": 76, "trial": 68, "paid": 22, "advocate": 76, "cvr_paid": 30},
            {"name": "律协推荐 (100)", "reach": 100, "landing": 100, "redeemed": 80, "trial": 72, "paid": 22, "advocate": 80, "cvr_paid": 30},
            {"name": "公开报名 (800+)", "reach": 800, "landing": 800, "redeemed": 60, "trial": 42, "paid": 2, "advocate": 21, "cvr_paid": 5},
            {"name": "加权平均", "reach": 1010, "landing": 1020, "redeemed": 231, "trial": 195, "paid": 49, "advocate": 187, "cvr_paid": 25},
        ],
        "alerts": [
            {"name": "试用转化率", "condition": "< 10% (目标 15%)", "level": "红色", "response": "12h"},
            {"name": "注册转化率", "condition": "< 60% (目标 80%)", "level": "红色", "response": "12h"},
            {"name": "付费转化率", "condition": "< 15% (目标 25%)", "level": "黄色", "response": "24h"},
            {"name": "创史转化率", "condition": "< 40% (目标 60%)", "level": "黄色", "response": "24h"},
            {"name": "创史招募率", "condition": "< 80% (8/23 前)", "level": "红色", "response": "12h"},
            {"name": "创史群活跃", "condition": "< 50% (Day 7/14/23/30)", "level": "黄色", "response": "24h"},
            {"name": "创史付费转化", "condition": "< 15% (目标 30%)", "level": "红色", "response": "24h"},
            {"name": "邀请码激活停滞", "condition": "单日变化 < 5 (连续 3 天)", "level": "黄色", "response": "12h"},
        ],
    }

    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/api/dashboard/w11":
                qs = parse_qs(parsed.query)
                period = (qs.get("period") or ["current"])[0]
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
                print(f"  [200] /api/dashboard/w11?period={period} ({len(body)} bytes)")
            elif parsed.path == "/health":
                body = b'{"status":"ok","server":"dashboard-mock"}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, fmt, *args):
            pass  # 静音

    port = 8001
    httpd = HTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"🚀 Dashboard mock server: http://127.0.0.1:{port}/api/dashboard/w11")
    print("   按 Ctrl+C 停止")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹  Server stopped")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        sys.exit(validate_sql())
    elif len(sys.argv) > 1 and sys.argv[1] == "server":
        run_mock_server()
    else:
        print("Usage:")
        print("  python validate_dashboard_sql.py validate  # 验证 7 SQL 语法")
        print("  python validate_dashboard_sql.py server    # 启 mock server :8001")