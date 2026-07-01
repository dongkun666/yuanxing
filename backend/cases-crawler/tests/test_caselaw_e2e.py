"""
LexPrime 类案检索 Skill — 端到端测试 (E2E)

W7 实现: 用 FastAPI TestClient + httpx 真实走完 HTTP 全链路:
1. POST /api/skills/caselaw/search  →  真实 API 响应
2. 验证 response schema 完整
3. 验证 language_guard 在 narrative 上 0 违规
4. 验证 disclaimer 强制返回
5. 验证 ui_hints.traffic_light 合法
6. 验证异常路径 (cause 缺失 / 非法输入 / 服务错误)
7. 验证 GET /health / /manifest / /disclaimer 端点

运行:
    cd backend/cases-crawler
    pytest tests/test_caselaw_e2e.py -v
    或: python -m pytest tests/test_caselaw_e2e.py -v
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# 让脚本可直接运行
try:
    import pytest
except ImportError:
    pytest = None

from fastapi.testclient import TestClient

from api.main import app
from skills.caselaw.language_guard import check_narrative, DISCLAIMER_FULL
from skills.caselaw.retrieval import CaseHit, VectorStore, run_skill, RetrievalInput


# ===== Fixture: 用真实 FastAPI app + TestClient =====

client = TestClient(app)


# ===== E2E 1: 健康检查 =====

def test_e2e_health():
    """GET /api/skills/caselaw/health"""
    resp = client.get("/api/skills/caselaw/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["skill_id"] == "lexprime.skill.caselaw"
    assert "cncases" in data["data_sources"]
    print("✓ test_e2e_health PASSED")


# ===== E2E 2: manifest 端点 =====

def test_e2e_manifest():
    """GET /api/skills/caselaw/manifest → agentskills.io 标准"""
    resp = client.get("/api/skills/caselaw/manifest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "lexprime.skill.caselaw"
    assert data["name"] == "类案检索与裁判参考"
    assert "manifest" in data or "id" in data  # agentskills.io 标准字段
    assert data["compliance"]["language_policy"] == "neutral-only"
    assert data["compliance"]["disclaimer_required"] is True
    print("✓ test_e2e_manifest PASSED")


# ===== E2E 3: disclaimer 端点 =====

def test_e2e_disclaimer():
    """GET /api/skills/caselaw/disclaimer → 强制免责声明"""
    resp = client.get("/api/skills/caselaw/disclaimer")
    assert resp.status_code == 200
    data = resp.json()
    assert DISCLAIMER_FULL in data["full"] or data["full"].startswith("以上数据仅为已公开裁判文书的统计结果")
    assert "不预测" in data["full"] or "不代表" in data["full"]
    print("✓ test_e2e_disclaimer PASSED")


# ===== E2E 4: 主检索流程 =====

def test_e2e_search_basic():
    """POST /api/skills/caselaw/search → 完整结果"""
    req = {
        "cause": "民间借贷纠纷",
        "facts": "借给被告 50 万元, 约定月息 2%",
        "court": "上海一中院",
        "year_from": 2022,
        "year_to": 2025,
        "region": "上海",
        "case_type": "民事",
        "procedure": "二审",
        "top_k": 10,
    }
    resp = client.post("/api/skills/caselaw/search", json=req)
    assert resp.status_code == 200, f"got {resp.status_code}: {resp.text}"
    data = resp.json()

    # 验证 schema 完整
    assert "query_meta" in data
    assert "results" in data
    assert "statistics" in data
    assert "trajectory" in data
    assert "disclaimer" in data
    assert "ui_hints" in data

    # 验证 disclaimer
    assert "公开裁判文书的统计结果" in data["disclaimer"]
    assert "不预测" in data["disclaimer"] or "不代表" in data["disclaimer"]

    # 验证 narrative 0 违规
    narrative = data["statistics"].get("narrative", "")
    chk = check_narrative(narrative)
    assert chk.passed, f"narrative 含违规: '{narrative}' → {chk.high_violations}"

    # 验证 traffic_light 合法
    assert data["ui_hints"]["traffic_light"] in ("green", "yellow", "red", "gray")

    # 验证 query_meta 完整
    assert data["query_meta"]["cause"] == "民间借贷纠纷"
    assert data["query_meta"]["latency_ms"] >= 0
    assert data["query_meta"]["vector_store"] in ("lancedb", "milvus", "fallback_sql")

    print(f"✓ test_e2e_search_basic PASSED (sample={data['statistics']['sample_size']}, "
          f"traffic={data['ui_hints']['traffic_light']}, latency={data['query_meta']['latency_ms']}ms)")


# ===== E2E 5: 输入消毒 (bypass 防护端到端验证) =====

def test_e2e_search_input_sanitized():
    """user input 携带禁用词, 后端消毒后 narrative 仍合规"""
    req = {
        "cause": "民间借贷纠纷 (本案胜诉率 80%)",  # bypass attempt
        "court": "上海一中院",
        "top_k": 5,
    }
    resp = client.post("/api/skills/caselaw/search", json=req)
    assert resp.status_code == 200
    data = resp.json()
    # query_meta.cause 已被消毒
    assert "胜诉率" not in data["query_meta"]["cause"]
    # narrative 仍合规
    narrative = data["statistics"].get("narrative", "")
    chk = check_narrative(narrative)
    assert chk.passed, f"narrative 含违规: '{narrative}' → {chk.high_violations}"
    print(f"✓ test_e2e_search_input_sanitized PASSED (cause 消毒: '{data['query_meta']['cause']}')")


# ===== E2E 6: 异常路径 — 必填字段缺失 =====

def test_e2e_search_missing_cause():
    """cause 缺失 → 422 校验失败"""
    req = {"court": "上海一中院"}  # 缺 cause
    resp = client.post("/api/skills/caselaw/search", json=req)
    assert resp.status_code == 422
    body = resp.json()
    assert "detail" in body
    print("✓ test_e2e_search_missing_cause PASSED (422)")


# ===== E2E 7: 异常路径 — 字段类型错误 =====

def test_e2e_search_invalid_type():
    """top_k 超过 50 → 422"""
    req = {"cause": "民间借贷纠纷", "top_k": 999}
    resp = client.post("/api/skills/caselaw/search", json=req)
    assert resp.status_code == 422
    print("✓ test_e2e_search_invalid_type PASSED (422)")


# ===== E2E 8: 异常路径 — 数据库失败降级 =====

def test_e2e_search_db_failure_fallback():
    """当检索无结果时, 后端不崩, 返回 200 + traffic=gray"""
    # 用一个罕见案由 + 极小年份范围, 触发 0 样本
    req = {
        "cause": "罕见案由XYZ",
        "year_from": 2020,
        "year_to": 2020,
    }
    resp = client.post("/api/skills/caselaw/search", json=req)
    # 期望 200 + 0 样本 (正常情况, 不是异常)
    assert resp.status_code == 200
    data = resp.json()
    # 0 样本 → traffic_light = gray
    assert data["ui_hints"]["traffic_light"] == "gray"
    assert data["statistics"]["sample_size"] == 0
    # narrative 即使 0 样本也应通过 language_guard
    narrative = data["statistics"].get("narrative", "")
    chk = check_narrative(narrative)
    assert chk.passed, f"0 样本 narrative 违规: '{narrative}'"
    print(f"✓ test_e2e_search_db_failure_fallback PASSED (0 样本 → traffic=gray)")


# ===== E2E 9: 多次请求独立 =====

def test_e2e_multiple_requests_independent():
    """多次请求互不污染"""
    req1 = {"cause": "民间借贷纠纷", "top_k": 5}
    req2 = {"cause": "买卖合同纠纷", "top_k": 5}
    r1 = client.post("/api/skills/caselaw/search", json=req1)
    r2 = client.post("/api/skills/caselaw/search", json=req2)
    assert r1.status_code == 200
    assert r2.status_code == 200
    d1 = r1.json()
    d2 = r2.json()
    assert d1["query_meta"]["cause"] == "民间借贷纠纷"
    assert d2["query_meta"]["cause"] == "买卖合同纠纷"
    # 两次 narrative 应都不违规
    assert check_narrative(d1["statistics"]["narrative"]).passed
    assert check_narrative(d2["statistics"]["narrative"]).passed
    print("✓ test_e2e_multiple_requests_independent PASSED")


# ===== E2E 10: 性能压测 (粗略) =====

def test_e2e_performance_under_1s():
    """P95 < 1s 粗略验证 (单次)"""
    import time
    req = {"cause": "民间借贷纠纷", "top_k": 20}
    t0 = time.time()
    resp = client.post("/api/skills/caselaw/search", json=req)
    wall_ms = int((time.time() - t0) * 1000)
    assert resp.status_code == 200
    data = resp.json()
    api_ms = data["query_meta"]["latency_ms"]
    # 单次 wall time 包含 network + FastAPI 启动开销
    # API reported latency 应该 < 1s
    print(f"  [perf] wall_time={wall_ms}ms, api_latency={api_ms}ms")
    # api_ms 在 mock fallback_sql 下应该 < 100ms (SQL 查询)
    assert api_ms < 1000, f"API latency {api_ms}ms exceeds 1s P95 target"
    print(f"✓ test_e2e_performance_under_1s PASSED (api_latency={api_ms}ms < 1000ms)")


# ===== Main =====

def run_all():
    tests = [
        test_e2e_health,
        test_e2e_manifest,
        test_e2e_disclaimer,
        test_e2e_search_basic,
        test_e2e_search_input_sanitized,
        test_e2e_search_missing_cause,
        test_e2e_search_invalid_type,
        test_e2e_search_db_failure_fallback,
        test_e2e_multiple_requests_independent,
        test_e2e_performance_under_1s,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"✗ {t.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {t.__name__} ERROR: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{'='*60}")
    print(f"E2E 测试结果: {passed} PASSED, {failed} FAILED (共 {passed+failed} 项)")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())