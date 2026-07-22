import pytest
import httpx

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def api_client():
    return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


@pytest.mark.asyncio
async def test_clients_health(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/clients/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "service" in data


@pytest.mark.asyncio
async def test_clients_stats(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/clients/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_type" in data
    assert "by_grade" in data
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_clients_list(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/clients")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data


@pytest.mark.asyncio
async def test_clients_list_pagination(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/clients", params={
        "page": 1,
        "page_size": 10,
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 10


@pytest.mark.asyncio
async def test_clients_list_search(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/clients", params={
        "search": "李明",
    })
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_clients_list_filter_type(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/clients", params={
        "client_type": "personal",
    })
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_clients_list_filter_grade(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/clients", params={
        "grade": "A",
    })
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_client_get(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/clients/CL-001")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert "id" in data
        assert "client_id" in data
        assert "name" in data


@pytest.mark.asyncio
async def test_client_get_not_found(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/clients/CL-INVALID")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_client_create(api_client: httpx.AsyncClient):
    response = await api_client.post("/api/clients", json={
        "name": "测试客户",
        "client_type": "personal",
        "phone": "13800009999",
        "email": "test@example.com",
        "grade": "B",
        "firm_id": "firm-001",
    })
    assert response.status_code == 200
    data = response.json()
    assert "client_id" in data
    assert data["name"] == "测试客户"


@pytest.mark.asyncio
async def test_client_update(api_client: httpx.AsyncClient):
    response = await api_client.put("/api/clients/CL-001", json={
        "name": "更新后的客户名",
        "grade": "A",
    })
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert data["name"] == "更新后的客户名"


@pytest.mark.asyncio
async def test_client_update_not_found(api_client: httpx.AsyncClient):
    response = await api_client.put("/api/clients/CL-INVALID", json={
        "name": "更新名",
    })
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_client_delete(api_client: httpx.AsyncClient):
    response = await api_client.delete("/api/clients/CL-001")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert data["deleted"] is True


@pytest.mark.asyncio
async def test_client_delete_not_found(api_client: httpx.AsyncClient):
    response = await api_client.delete("/api/clients/CL-INVALID")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_client_conflict_check(api_client: httpx.AsyncClient):
    response = await api_client.post("/api/clients/CL-001/conflict-check")
    assert response.status_code == 200
    data = response.json()
    assert "has_conflict" in data
    assert "conflicts" in data
    assert "risk_level" in data
    assert "disclaimer" in data
