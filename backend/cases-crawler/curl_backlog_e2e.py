"""A1 4 端点 e2e 验证"""
import json
import sqlite3
from urllib import request, error

BASE = "http://127.0.0.1:8000"
DB = "data/lexprime.db"


def reset_state():
    """清理 e2e 残留: 删 id>42 (mock from-question 累积) + 还原 bid=2 + 清 review_questions"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM prd_backlog WHERE id > 42")
    cur.execute("DELETE FROM sqlite_sequence WHERE name = 'prd_backlog'")
    cur.execute(
        "UPDATE prd_backlog SET owner='lex-coder', priority='P0', status='open' "
        "WHERE id = 2"
    )
    cur.execute("DELETE FROM review_questions")
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM prd_backlog")
    print(f"  ✓ reset: 删 id>42 mock + sqlite_sequence 重置 + 还原 bid=2 + 清 review_questions (total={cur.fetchone()[0]})")
    conn.close()


def final_reset():
    """e2e 跑完后再清理一次, 让 DB 回到 42 ticket 全 open"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM prd_backlog WHERE id > 42")
    cur.execute("DELETE FROM sqlite_sequence WHERE name = 'prd_backlog'")
    cur.execute(
        "UPDATE prd_backlog SET owner='lex-coder', priority='P0', status='open' "
        "WHERE id = 2"
    )
    cur.execute("DELETE FROM review_questions")
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM prd_backlog")
    print(f"  ✓ final reset done (total={cur.fetchone()[0]})")
    conn.close()


def http(method, path, body=None):
    url = f"{BASE}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        return e.code, e.read().decode("utf-8")[:500]
    except Exception as e:
        return -1, str(e)


def section(title):
    print(f"\n{'=' * 70}")
    print(f" {title}")
    print("=" * 70)


# ===== 1. GET /api/backlog/health =====
section("PRE: reset state (idempotent)")
reset_state()

section("0. health (precondition)")
status, body = http("GET", "/api/backlog/health")
print(f"  status={status}")
print(f"  body={json.dumps(body, ensure_ascii=False, indent=2)}")
assert status == 200, f"health failed: {status}"
assert body["total_tickets"] == 42

# ===== 2. GET /api/backlog/list (no filter) =====
section("2.1 GET /api/backlog/list (no filter)")
status, body = http("GET", "/api/backlog/list")
print(f"  status={status}, total={body.get('total') if isinstance(body, dict) else 'N/A'}")
if isinstance(body, dict):
    print(f"  by_priority: {body['by_priority']}")
    print(f"  by_category: {body['by_category']}")
    print(f"  by_owner: {body['by_owner']}")
    print("  first 3 tickets:")
    for t in body["tickets"][:3]:
        print(f"    [{t['id']}] {t['priority']}/{t['category']}/{t['owner']} {t['title'][:50]}")
assert status == 200
assert body["total"] == 42

# ===== 2.2 GET /api/backlog/list?priority=P0 =====
section("2.2 GET /api/backlog/list?priority=P0")
status, body = http("GET", "/api/backlog/list?priority=P0")
print(f"  status={status}, total={body['total']}")
assert status == 200
assert body["total"] == 17
assert body["by_priority"]["P0"] == 17

# ===== 2.3 GET /api/backlog/list?category=产品 =====
section("2.3 GET /api/backlog/list?category=产品")
status, body = http("GET", "/api/backlog/list?category=%E4%BA%A7%E5%93%81")  # URL-encoded 产品
print(f"  status={status}, total={body['total']}")
assert status == 200
assert body["total"] == 18

# ===== 2.4 GET /api/backlog/list?owner=lex-ai =====
section("2.4 GET /api/backlog/list?owner=lex-ai")
status, body = http("GET", "/api/backlog/list?owner=lex-ai")
print(f"  status={status}, total={body['total']}")
assert status == 200
assert body["total"] == 27

# ===== 2.5 GET /api/backlog/list?status=open =====
section("2.5 GET /api/backlog/list?status=open")
status, body = http("GET", "/api/backlog/list?status=open")
print(f"  status={status}, total={body['total']}")
assert status == 200
assert body["total"] == 42

# ===== 3. POST /api/backlog/from-question =====
section("3. POST /api/backlog/from-question (W7 review_questions 当前 0 行)")
# review_questions 表当前 0 行, 期望 404
status, body = http("POST", "/api/backlog/from-question",
                    {"review_question_id": 999})
print(f"  status={status}, body={body}")
assert status == 404, f"expected 404 for non-existent question, got {status}"

# happy path 需要先插入 review_questions 表, 后续 W9 评审真实落档后覆盖
section("3.b POST /api/backlog/from-question happy path (mock review_question)")

# 临时插入 review_question 用于测试
conn = sqlite3.connect(DB)
cur = conn.cursor()
# 先看 review_questions schema
cur.execute("PRAGMA table_info(review_questions)")
cols = cur.fetchall()
print("  review_questions schema:", [c[1] for c in cols])

# 用 SQLAlchemy 模型插入更安全, 但为简化直接 SQL
# 字段假设: id, lawyer_id, category, question_text, context, created_at
cur.execute(
    "INSERT INTO review_questions (lawyer_id, category, question_text, context, status, created_at) "
    "VALUES (?, ?, ?, ?, ?, datetime('now'))",
    ("L1", "产品", "W9 A1 测试问题: 跨 Skill 引用真实测试", "e2e from-question 测试", "open"),
)
qid = cur.lastrowid
conn.commit()
print(f"  ✓ inserted review_question id={qid}")

# 现在 POST from-question
status, body = http("POST", "/api/backlog/from-question",
                    {"review_question_id": qid, "priority": "P1", "owner": "lex-coder"})
print(f"  status={status}, body={json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
assert status == 201, f"expected 201, got {status}"
assert body["priority"] == "P1"
assert body["owner"] == "lex-coder"
assert body["category"] == "产品"

# 重复 POST 应该 409
status, body = http("POST", "/api/backlog/from-question",
                    {"review_question_id": qid})
print(f"  duplicate from-question status={status}, body={body[:100]}")
assert status == 409

# 清理 mock review_question (不删 backlog, 让 backlog=43 反映真实测试)
cur.execute("DELETE FROM review_questions WHERE id = ?", (qid,))
conn.commit()
conn.close()
print(f"  ✓ cleaned up review_question id={qid}")

# ===== 4. POST /api/backlog/{id}/assign =====
section("4. POST /api/backlog/1/assign (change status)")
status, body = http("POST", "/api/backlog/1/assign", {"status": "in_progress"})
print(f"  status={status}, body={json.dumps(body, ensure_ascii=False, indent=2)}")
assert status == 200
assert body["status"] == "in_progress"
assert "status" in body["changed_fields"]

# 还原
section("4.b POST /api/backlog/1/assign (revert to open)")
status, body = http("POST", "/api/backlog/1/assign", {"status": "open"})
print(f"  status={status}, changed_fields={body['changed_fields']}")
assert status == 200
assert body["status"] == "open"

# 多字段同时改
section("4.c POST /api/backlog/2/assign (owner + priority + status)")
status, body = http("POST", "/api/backlog/2/assign",
                    {"owner": "lex-pm", "priority": "P3", "status": "deferred"})
print(f"  status={status}, body={json.dumps(body, ensure_ascii=False, indent=2)}")
assert status == 200
assert body["owner"] == "lex-pm"
assert body["priority"] == "P3"
assert body["status"] == "deferred"

# 不存在的 backlog_id
section("4.d POST /api/backlog/9999/assign (404)")
status, body = http("POST", "/api/backlog/9999/assign", {"owner": "lex-pm"})
print(f"  status={status}, body={body}")
assert status == 404

# ===== 5. GET /api/backlog/board =====
section("5. GET /api/backlog/board")
status, body = http("GET", "/api/backlog/board")
print(f"  status={status}")
print(f"  summary: {json.dumps(body['summary'], ensure_ascii=False, indent=2)}")
print(f"  by_status: {body['by_status']}")
print(f"  by_priority: {body['by_priority']}")
print(f"  by_owner keys: {list(body['by_owner'].keys())}")
print(f"  by_category keys: {list(body['by_category'].keys())}")
print(f"  by_source_lawyer keys: {list(body['by_source_lawyer'].keys())}")
print(f"  recent_tickets count: {len(body['recent_tickets'])}")
assert status == 200
assert body["summary"]["total_tickets"] == 43  # 42 + 1 mock from-question
assert body["by_status"]["open"] == 42
assert body["by_status"]["deferred"] == 1
assert body["by_priority"]["P0"] == 16  # bid=2 was P0, changed to P3
assert body["by_priority"]["P3"] == 1

print(f"\n{'=' * 70}")
print(" ✅ ALL 4 ENDPOINTS PASSED")
print(f"{'=' * 70}")

# 最终 reset, 让 DB 回到 42 ticket 干净状态
print("\n=== final reset ===")
final_reset()