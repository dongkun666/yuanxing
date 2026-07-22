import pytest
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8001"


@pytest.fixture(scope="module")
def http_client():
    return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


@pytest.mark.asyncio
async def test_auth_health(http_client: httpx.AsyncClient):
    response = await http_client.get("/api/auth/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_register(http_client: httpx.AsyncClient):
    response = await http_client.post("/api/auth/register", json={
        "email": f"test_{int(datetime.now().timestamp())}@example.com",
        "password": "Test@123456",
        "name": "测试律师",
    })
    assert response.status_code in [201, 409]


@pytest.mark.asyncio
async def test_login(http_client: httpx.AsyncClient):
    response = await http_client.post("/api/auth/login", json={
        "email": "demo@example.com",
        "password": "password123",
    })
    assert response.status_code in [200, 401, 423]


@pytest.mark.asyncio
async def test_refresh_token(http_client: httpx.AsyncClient):
    response = await http_client.post("/api/auth/refresh", json={
        "refresh_token": "invalid_token",
    })
    assert response.status_code in [401]


@pytest.mark.asyncio
async def test_logout(http_client: httpx.AsyncClient):
    response = await http_client.post("/api/auth/logout", json={
        "refresh_token": "invalid_token",
    })
    assert response.status_code in [400, 401]


@pytest.mark.asyncio
async def test_me_endpoint(http_client: httpx.AsyncClient):
    response = await http_client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_email_send(http_client: httpx.AsyncClient):
    response = await http_client.post("/api/auth/email/send", json={
        "purpose": "verify_email",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_email_verify(http_client: httpx.AsyncClient):
    response = await http_client.post("/api/auth/email/verify", json={
        "token": "invalid_token",
    })
    assert response.status_code in [400, 429]


@pytest.mark.asyncio
async def test_totp_setup(http_client: httpx.AsyncClient):
    response = await http_client.post("/api/auth/totp/setup", json={
        "password": "test_password",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_totp_verify(http_client: httpx.AsyncClient):
    response = await http_client.post("/api/auth/totp/verify", json={
        "code": "123456",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_totp_disable(http_client: httpx.AsyncClient):
    response = await http_client.post("/api/auth/totp/disable", json={
        "password": "test_password",
        "code": "123456",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_license_upload(http_client: httpx.AsyncClient):
    response = await http_client.post("/api/auth/lawyer-license/upload", json={
        "image_base64": "data:image/png;base64,iVBORw0KGgo=",
        "filename": "license.png",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_license_status(http_client: httpx.AsyncClient):
    response = await http_client.get("/api/auth/lawyer-license/status")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_license_review(http_client: httpx.AsyncClient):
    response = await http_client.post("/api/auth/lawyer-license/review", json={
        "profile_id": 1,
        "decision": "approved",
        "reason": "测试审核",
    })
    assert response.status_code == 401
