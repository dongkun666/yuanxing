"""
e2e curl 验证 - 5 个 Auth endpoint
2026-06-29

执行: python scripts/curl_e2e.py (需要先启动 uvicorn: uvicorn auth.main:app --port 8001)
"""
import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8001"


def post(path, body, extra_headers=None):
    """POST JSON, 返回 (status, body_str)"""
    data = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def get(path, extra_headers=None):
    """GET, 返回 (status, body_str)"""
    req = urllib.request.Request(
        f"{BASE}{path}",
        headers=extra_headers or {},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def section(title):
    print()
    print("=" * 60)
    print(title)


def main():
    ts = int(time.time())

    section("1) GET /api/auth/health")
    status, body = get("/api/auth/health")
    print(f"   HTTP {status}: {body}")
    assert status == 200 and '"ok"' in body

    section("2) POST /api/auth/register (新用户)")
    email = f"smoke_{ts}@lexprime.com"
    license_no = f"SMOKE-{ts}"
    phone = f"1390{ts % 100000000:08d}"
    status, body = post("/api/auth/register", {
        "email": email,
        "password": "smokepass123",
        "name": "Smoke Test",
        "license_no": license_no,
        "phone": phone,
    })
    print(f"   HTTP {status}: {body}")
    assert status == 201
    me_data = json.loads(body)
    assert me_data["email"] == email
    assert me_data["profile"]["name"] == "Smoke Test"
    assert "password_hash" not in body
    print(f"   ok user_id={me_data['id']}, license_status={me_data['profile']['license_status']}")

    section("3) POST /api/auth/register (重复 -> 409)")
    status, body = post("/api/auth/register", {
        "email": email, "password": "smokepass123", "name": "Dup",
    })
    print(f"   HTTP {status}: {body}")
    assert status == 409 and "email_already_registered" in body

    section("4) POST /api/auth/login")
    status, body = post("/api/auth/login", {
        "email": email, "password": "smokepass123",
    })
    print(f"   HTTP {status}: {body[:200]}...")
    assert status == 200
    token_data = json.loads(body)
    access = token_data["access_token"]
    refresh = token_data["refresh_token"]
    assert token_data["token_type"] == "bearer"
    assert token_data["expires_in"] == 900
    print(f"   ok access={access[:30]}..., refresh={refresh[:30]}...")

    section("5) POST /api/auth/login (密码错 -> 401)")
    status, body = post("/api/auth/login", {
        "email": email, "password": "wrong",
    })
    print(f"   HTTP {status}: {body}")
    assert status == 401

    section("6) GET /api/auth/me (用 access token)")
    status, body = get("/api/auth/me", {"Authorization": f"Bearer {access}"})
    print(f"   HTTP {status}: {body}")
    assert status == 200
    me2 = json.loads(body)
    assert me2["email"] == email
    assert me2["profile"]["license_no"] == license_no
    print(f"   ok me.id={me2['id']}, profile.license_no={me2['profile']['license_no']}")

    section("7) GET /api/auth/me (无 token -> 401)")
    status, body = get("/api/auth/me")
    print(f"   HTTP {status}: {body}")
    assert status == 401

    section("8) POST /api/auth/refresh (轮转 refresh token)")
    status, body = post("/api/auth/refresh", {"refresh_token": refresh})
    print(f"   HTTP {status}: {body[:200]}...")
    assert status == 200
    new_token = json.loads(body)
    new_access = new_token["access_token"]
    new_refresh = new_token["refresh_token"]
    assert new_access != access  # 新 access
    assert new_refresh != refresh  # refresh 轮转 (single-use)
    print("   ok old_refresh revoked, new pair issued")

    section("9) POST /api/auth/refresh (重放旧 token -> 401 + 全撤销)")
    status, body = post("/api/auth/refresh", {"refresh_token": refresh})
    print(f"   HTTP {status}: {body}")
    assert status == 401

    section("10) POST /api/auth/refresh (新 refresh 也应被撤销 -> 401)")
    status, body = post("/api/auth/refresh", {"refresh_token": new_refresh})
    print(f"   HTTP {status}: {body}")
    assert status == 401

    section("11) POST /api/auth/logout")
    email2 = f"logout_{ts}@lexprime.com"
    phone2 = f"1391{ts % 100000000:08d}"
    status, body = post("/api/auth/register", {
        "email": email2, "password": "logoutpass123", "name": "Logout", "phone": phone2,
    })
    assert status == 201
    status, body = post("/api/auth/login", {"email": email2, "password": "logoutpass123"})
    assert status == 200
    tok2 = json.loads(body)
    status, body = post(
        "/api/auth/logout",
        {"refresh_token": tok2["refresh_token"]},
        extra_headers={"Authorization": f"Bearer {tok2['access_token']}"},
    )
    print(f"   HTTP {status}: {body}")
    assert status == 200

    status, body = post("/api/auth/refresh", {"refresh_token": tok2["refresh_token"]})
    print(f"   POST-revoke refresh: HTTP {status}")
    assert status == 401

    print()
    print("=" * 60)
    print("ALL 11 e2e cases PASSED")


if __name__ == "__main__":
    main()