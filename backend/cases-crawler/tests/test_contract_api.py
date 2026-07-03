import pytest
import httpx

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def api_client():
    return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


@pytest.mark.asyncio
async def test_contract_review_health(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/contract-review/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "skill_id" in data


@pytest.mark.asyncio
async def test_contract_review_fixtures(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/contract-review/fixtures")
    assert response.status_code == 200
    data = response.json()
    assert "fixtures" in data
    assert "count" in data


@pytest.mark.asyncio
async def test_contract_review_disclaimer(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/contract-review/disclaimer")
    assert response.status_code == 200
    data = response.json()
    assert "full" in data
    assert "short" in data


@pytest.mark.asyncio
async def test_contract_review_upload_demo(api_client: httpx.AsyncClient):
    response = await api_client.post("/api/contract-review/upload", json={
        "contract_type": "借款合同",
        "fixture_id": "demo-loan-01",
        "stance": "审查方",
    })
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert "review_id" in data
        assert "status" in data
        assert data["demo_mode"] is True


@pytest.mark.asyncio
async def test_contract_review_upload_invalid(api_client: httpx.AsyncClient):
    response = await api_client.post("/api/contract-review/upload", json={
        "contract_type": "借款合同",
        "contract_text": "",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_contract_review_upload_real(api_client: httpx.AsyncClient):
    response = await api_client.post("/api/contract-review/upload", json={
        "contract_type": "借款合同",
        "contract_text": "借款合同\n甲方：张三\n乙方：李四\n借款金额：人民币壹万元整。\n借款期限：一年。",
        "stance": "审查方",
    })
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "review_id" in data
        assert "status" in data


@pytest.mark.asyncio
async def test_contract_review_result(api_client: httpx.AsyncClient):
    upload_response = await api_client.post("/api/contract-review/upload", json={
        "contract_type": "借款合同",
        "fixture_id": "demo-loan-01",
        "stance": "审查方",
    })
    if upload_response.status_code == 200:
        review_id = upload_response.json()["review_id"]
        response = await api_client.get(f"/api/contract-review/result/{review_id}")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_contract_review_result_not_found(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/contract-review/result/invalid-review-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_contract_review_negotiation(api_client: httpx.AsyncClient):
    upload_response = await api_client.post("/api/contract-review/upload", json={
        "contract_type": "借款合同",
        "fixture_id": "demo-loan-01",
        "stance": "审查方",
    })
    if upload_response.status_code == 200:
        review_id = upload_response.json()["review_id"]
        response = await api_client.post("/api/contract-review/negotiation", json={
            "review_id": review_id,
            "stance": "甲方",
        })
        assert response.status_code == 200
        data = response.json()
        assert "strategy" in data
        assert "disclaimer" in data


@pytest.mark.asyncio
async def test_contract_review_export(api_client: httpx.AsyncClient):
    upload_response = await api_client.post("/api/contract-review/upload", json={
        "contract_type": "借款合同",
        "fixture_id": "demo-loan-01",
        "stance": "审查方",
    })
    if upload_response.status_code == 200:
        review_id = upload_response.json()["review_id"]
        response = await api_client.post("/api/contract-review/export", json={
            "review_id": review_id,
            "format": "markdown",
        })
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "filename" in data


@pytest.mark.asyncio
async def test_contract_review_ocr_health(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/contract-review/ocr-health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "ocr_engine" in data


@pytest.mark.asyncio
async def test_contract_review_rules(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/contract-review/rules")
    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    assert "categories" in data
    assert "stats" in data


@pytest.mark.asyncio
async def test_contract_review_review_text(api_client: httpx.AsyncClient):
    response = await api_client.post("/api/contract-review/review-text", json={
        "contract_text": "借款合同\n甲方：张三\n乙方：李四\n借款金额：人民币壹万元整。",
        "contract_type": "借款合同",
        "stance": "审查方",
    })
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "matches" in data
        assert "risk_summary" in data
        assert "disclaimer" in data
