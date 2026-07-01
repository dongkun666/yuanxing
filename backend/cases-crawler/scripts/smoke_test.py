"""冒烟测试 - 验证 imports + routes"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auth.main import app
from auth.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    TokenInvalidError,
)

print("[1/4] imports OK")

print("\n[2/4] routes:")
for r in app.routes:
    if hasattr(r, "path") and r.path.startswith("/api/auth"):
        methods = ",".join(sorted(r.methods or [])) if hasattr(r, "methods") else "?"
        print(f"  {methods:10} {r.path}")

print("\n[3/4] security self-check:")
h = hash_password("test12345")
assert h.startswith("$2"), f"bcrypt format unexpected: {h[:5]}"
assert verify_password("test12345", h)
assert not verify_password("wrong", h)
print("  bcrypt hash/verify OK")

access, access_exp = create_access_token(42, role="lawyer")
refresh, refresh_exp = create_refresh_token(42)
print(f"  access TTL: {access_exp}s, refresh TTL: {refresh_exp}s")
payload = decode_token(access, expected_type="access")
assert payload["sub"] == "42"
assert payload["type"] == "access"
try:
    decode_token(refresh, expected_type="access")
    raise AssertionError("should reject refresh as access")
except TokenInvalidError:
    print("  JWT type separation OK")

try:
    decode_token("not.a.token", expected_type="access")
    raise AssertionError("should reject malformed")
except TokenInvalidError:
    print("  JWT malformed detection OK")

print("\n[4/4] ALL OK")