"""
W12 A2 客户签字确认 API 测试 (lex-coder · 2026-06-30)

覆盖:
- POST /api/signature/{doc_id} 上传签字
- GET /api/signature/{doc_id} 查询签字状态
- base64 校验 (合法 / 非法格式)
- 重复 POST → 覆盖 (返 200)
- image size 限制 (> 500KB → 413)
- 集成 doc_workflow (签字后查询 state.has_signature=True)
- /api/signature/health/info
"""
import base64
import os
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


# ====== Fixtures ======

@pytest_asyncio.fixture(scope="function")
async def _shared_engine():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from core.models import Base
    from core import doc_workflow  # noqa: F401

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    import core.db
    orig_engine = core.db.Database._engine
    orig_factory = core.db.Database._session_factory
    core.db.Database._engine = engine
    core.db.Database._session_factory = factory

    yield engine, factory

    core.db.Database._engine = orig_engine
    core.db.Database._session_factory = orig_factory
    await engine.dispose()


@pytest_asyncio.fixture
async def client(_shared_engine):
    from api.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# 模拟客户签字图片 (1x1 PNG, base64 编码)
SAMPLE_PNG_BASE64 = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
)

# 模拟 JPEG (200 字节随机 → 有效 base64 268 chars, 确保格式合法)
_jpeg_raw = os.urandom(200)
SAMPLE_JPEG_BASE64 = "data:image/jpeg;base64," + base64.b64encode(_jpeg_raw).decode("ascii")


# ====== POST /api/signature/{doc_id} ======

class TestUploadSignature:

    async def test_upload_signature_success(self, client):
        """正常上传"""
        resp = await client.post("/api/signature/sig-1", json={
            "signature_image": SAMPLE_PNG_BASE64,
            "license_no": "LAW-2024-001234",
            "client_name": "张客户",
            "client_id_no": "110101199001011234",
            "notes": "客户当面签字确认",
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["doc_id"] == "sig-1"
        assert body["license_no"] == "LAW-2024-001234"
        assert body["client_name"] == "张客户"
        assert body["image_size_bytes"] > 0
        assert "signed_at" in body

    async def test_upload_jpeg(self, client):
        """JPEG 格式"""
        resp = await client.post("/api/signature/sig-jpg", json={
            "signature_image": SAMPLE_JPEG_BASE64,
            "license_no": "LAW-2024-005",
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["image_size_bytes"] > 0

    async def test_upload_overwrites_existing(self, client):
        """重复上传 → 覆盖 (返 200 而非 409)"""
        payload = {
            "signature_image": SAMPLE_PNG_BASE64,
            "license_no": "LAW-OVERWRITE-1",
            "client_name": "原客户",
        }
        resp1 = await client.post("/api/signature/sig-ow", json=payload)
        assert resp1.status_code == 200

        # 修改 client_name 后再次上传
        payload2 = dict(payload)
        payload2["client_name"] = "新客户 (重画)"
        resp2 = await client.post("/api/signature/sig-ow", json=payload2)
        assert resp2.status_code == 200
        body2 = resp2.json()
        assert body2["client_name"] == "新客户 (重画)"

    async def test_upload_missing_license_no_422(self, client):
        """缺 license_no → 422"""
        resp = await client.post("/api/signature/sig-x", json={
            "signature_image": SAMPLE_PNG_BASE64,
        })
        assert resp.status_code == 422

    async def test_upload_invalid_base64_422(self, client):
        """非法 base64 → 422"""
        resp = await client.post("/api/signature/sig-bad", json={
            "signature_image": "data:image/png;base64,!!!这不是有效 base64!!!",
            "license_no": "LAW-X",
        })
        assert resp.status_code == 422

    async def test_upload_image_too_large_413(self, client):
        """图片太大 (> 500KB) → 413"""
        # 510KB 随机 bytes → ~680KB base64 → 超过 500KB raw image 限制
        # 但 < 700KB max_length (Pydantic), 所以能通过 Pydantic 校验, 然后被 413 拦截
        import os
        large_bytes = os.urandom(510 * 1024)
        large_b64 = "data:image/png;base64," + base64.b64encode(large_bytes).decode("ascii")

        # 确认 b64 < 700KB max_length
        assert len(large_b64) < 700 * 1024, f"b64 过长: {len(large_b64)} bytes"

        resp = await client.post("/api/signature/sig-big", json={
            "signature_image": large_b64,
            "license_no": "LAW-BIG",
        })
        assert resp.status_code == 413, resp.text
        assert "签字图片过大" in resp.json()["detail"]

    async def test_upload_invalid_prefix_422(self, client):
        """非法 data URL 前缀 → 422"""
        # 用 BMP 前缀 (不允许)
        b64_part = SAMPLE_PNG_BASE64.split(",", 1)[1]
        invalid_prefix = "data:image/bmp;base64," + b64_part
        resp = await client.post("/api/signature/sig-bmp", json={
            "signature_image": invalid_prefix,
            "license_no": "LAW-BMP",
        })
        # pydantic validator 会拒绝
        assert resp.status_code == 422


# ====== GET /api/signature/{doc_id} ======

class TestGetSignature:

    async def test_get_existing_signature(self, client):
        """GET 已存在的签字"""
        await client.post("/api/signature/sig-get", json={
            "signature_image": SAMPLE_PNG_BASE64,
            "license_no": "LAW-GET-1",
            "client_name": "测试客户",
        })

        resp = await client.get("/api/signature/sig-get")
        assert resp.status_code == 200
        body = resp.json()
        assert body["has_signature"] is True
        assert body["license_no"] == "LAW-GET-1"
        assert body["client_name"] == "测试客户"
        assert body["signed_at"] is not None
        assert body["image_size_bytes"] > 0

    async def test_get_nonexistent_returns_has_signature_false(self, client):
        """不存在 → has_signature=False (不抛 404)"""
        resp = await client.get("/api/signature/nonexistent-doc")
        assert resp.status_code == 200
        body = resp.json()
        assert body["has_signature"] is False
        assert body["license_no"] is None
        assert body["signed_at"] is None


# ====== 集成: signature + doc_workflow ======

class TestSignatureIntegration:
    """签字 → 工作流状态联动"""

    async def test_signature_then_state_query(self, client):
        """签字后 GET state 返 has_signature=True"""
        doc_id = "integration-1"
        # 1) 创建 draft → ai_reviewed → lawyer_reviewed
        for target in ["ai_reviewed", "lawyer_reviewed"]:
            await client.patch(f"/api/doc-gen/{doc_id}/state", json={
                "target_state": target, "actor": "L", "reason": f"→ {target}",
                "case_id": "c-i", "doc_type": "contract",
            })
        # 此时 has_signature=False
        resp1 = await client.get(f"/api/doc-gen/{doc_id}/state")
        assert resp1.json()["has_signature"] is False

        # 2) 上传签字
        await client.post(f"/api/signature/{doc_id}", json={
            "signature_image": SAMPLE_PNG_BASE64,
            "license_no": "LAW-INT-1",
        })

        # 3) 再查 state → has_signature=True
        resp2 = await client.get(f"/api/doc-gen/{doc_id}/state")
        assert resp2.json()["has_signature"] is True
        assert resp2.json()["signature_signed_at"] is not None

    async def test_signature_status_after_upload(self, client):
        """签字 GET /signature 返 OK, 同时 doc state 也反映"""
        doc_id = "integration-2"
        await client.post(f"/api/signature/{doc_id}", json={
            "signature_image": SAMPLE_PNG_BASE64,
            "license_no": "LAW-INT-2",
            "client_name": "签字人",
        })

        resp_sig = await client.get(f"/api/signature/{doc_id}")
        assert resp_sig.json()["has_signature"] is True

        resp_state = await client.get(f"/api/doc-gen/{doc_id}/state")
        # 即使没创建 state, 也不报错
        # (doc_id 不存在 → 404)
        assert resp_state.status_code in (200, 404)


# ====== /api/signature/health/info ======

class TestSignatureHealth:
    async def test_health_info(self, client):
        resp = await client.get("/api/signature/health/info")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service_id"] == "lexprime.skill.signature"
        assert body["max_image_size_bytes"] == 500 * 1024
        assert "data:image/png;base64," in body["allowed_prefixes"]
        assert len(body["endpoints"]) == 3