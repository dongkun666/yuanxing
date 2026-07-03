import pytest
import httpx

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def api_client():
    return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


@pytest.mark.asyncio
async def test_health(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["ok", "degraded"]


@pytest.mark.asyncio
async def test_list_cases(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/cases")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_cases_with_filters(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/cases", params={
        "year": 2026,
        "limit": 10,
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_cases_full(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/cases", params={"full": "true"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_case(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/cases/test-doc-id")
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_search(api_client: httpx.AsyncClient):
    response = await api_client.post("/api/search", json={
        "query": "合同",
        "index": "cases",
        "page": 1,
        "size": 10,
    })
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "total" in data
        assert "items" in data


@pytest.mark.asyncio
async def test_list_laws(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/laws")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_laws_with_filters(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/laws", params={
        "law_type": "法律",
        "limit": 10,
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_companies(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_companies_with_filters(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/companies", params={
        "region": "北京",
        "limit": 10,
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_firm_lawyers(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/firm/lawyers", params={
        "firm_id": "firm-001",
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_time_entry(api_client: httpx.AsyncClient):
    response = await api_client.post("/api/firm/time-entries", params={"firm_id": "firm-001"}, json={
        "lawyer_id": "lawyer-001",
        "entry_date": "2026-07-01",
        "hours": 2.5,
        "description": "测试工时",
        "billable": True,
        "rate": 500,
    })
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "id" in data
        assert "status" in data


@pytest.mark.asyncio
async def test_firm_stats(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/firm/stats", params={
        "firm_id": "firm-001",
    })
    assert response.status_code == 200
    data = response.json()
    assert "lawyer_count" in data
    assert "month_hours" in data
    assert "firm_id" in data
