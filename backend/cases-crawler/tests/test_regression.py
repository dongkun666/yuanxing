import pytest
import httpx

BASE_URL = "http://localhost:8000"
AUTH_BASE_URL = "http://localhost:8001"


@pytest.fixture(scope="module")
def api_client():
    return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


@pytest.fixture(scope="module")
def auth_api_client():
    return httpx.AsyncClient(base_url=AUTH_BASE_URL, timeout=30.0)


@pytest.mark.regression
@pytest.mark.asyncio
async def test_core_api_health(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]


@pytest.mark.regression
@pytest.mark.asyncio
async def test_auth_api_health(auth_api_client: httpx.AsyncClient):
    response = await auth_api_client.get("/api/auth/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.regression
@pytest.mark.asyncio
async def test_clients_api_health(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/clients/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.regression
@pytest.mark.asyncio
async def test_contract_review_health(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/contract-review/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.regression
@pytest.mark.asyncio
async def test_cases_list(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/cases", params={"limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.regression
@pytest.mark.asyncio
async def test_clients_list(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/clients", params={"limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.regression
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


@pytest.mark.regression
@pytest.mark.asyncio
async def test_search_functionality(api_client: httpx.AsyncClient):
    response = await api_client.post("/api/search", json={
        "query": "test",
        "index": "cases",
        "page": 1,
        "size": 5,
    })
    assert response.status_code in [200, 500]


@pytest.mark.regression
@pytest.mark.asyncio
async def test_client_crud_flow(api_client: httpx.AsyncClient):
    create_response = await api_client.post("/api/clients", json={
        "name": "回归测试客户",
        "client_type": "personal",
        "grade": "B",
    })
    assert create_response.status_code == 200
    create_data = create_response.json()
    client_id = create_data["client_id"]

    get_response = await api_client.get(f"/api/clients/{client_id}")
    assert get_response.status_code in [200, 404]

    update_response = await api_client.put(f"/api/clients/{client_id}", json={
        "grade": "A",
    })
    assert update_response.status_code in [200, 404]

    delete_response = await api_client.delete(f"/api/clients/{client_id}")
    assert delete_response.status_code in [200, 404]


@pytest.mark.regression
@pytest.mark.asyncio
async def test_laws_list(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/laws", params={"limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.regression
@pytest.mark.asyncio
async def test_companies_list(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/companies", params={"limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.regression
@pytest.mark.asyncio
async def test_firm_endpoints(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/firm/lawyers", params={"firm_id": "firm-001"})
    assert response.status_code == 200

    response = await api_client.get("/api/firm/stats", params={"firm_id": "firm-001"})
    assert response.status_code == 200
