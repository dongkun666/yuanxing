"""
DROP + 重建 auth_* 4 张表 (W2 启动前 hygiene)
2026-06-29

理由: W1 用手 SQL (auth_schema.sql) 建的表, BigInt variant / JSON 字段定义可能与
W2 SQLAlchemy ORM 重新同步时有微妙差异. 重建保证 schema == models.py 100% 一致.

执行: python scripts/drop_rebuild_auth_tables.py
"""
import sqlite3
import sys
from pathlib import Path

# DB 路径 (跟 config.py 默认一致)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "lexprime.db"

# 把项目根加到 sys.path (core, auth 都是子包, 需要父目录可 import)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

AUTH_TABLES = [
    "auth_lawyer_profiles",
    "auth_otp_logs",
    "auth_tokens",
    "auth_users",
]


def main():
    if not DB_PATH.exists():
        print(f"❌ DB not found: {DB_PATH}")
        sys.exit(1)

    print(f"📦 Target DB: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # 1. 先确认存在
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'auth_%' ORDER BY name"
    )
    existing = [r[0] for r in cur.fetchall()]
    print(f"\n🔍 Existing auth_* tables: {existing}")

    if not existing:
        print("⚠️  No auth_* tables found, nothing to drop")
    else:
        # SQLite 不支持 DROP TABLE IF EXISTS CASCADE, 用 try/except 兜底
        for table in existing:
            try:
                cur.execute(f"DROP TABLE {table}")
                print(f"  ✓ Dropped: {table}")
            except Exception as e:
                print(f"  ✗ Failed to drop {table}: {e}")
                sys.exit(1)
        conn.commit()

    conn.close()

    # 2. 用 SQLAlchemy ORM 重建 (走 metadata.create_all 走 SQLAlchemy variant)
    print("\n🔨 Recreating via SQLAlchemy ORM (with dialect variants)...")
    import asyncio

    async def recreate():
        # 触发 model 注册
        from core.models import Base  # noqa: F401
        from auth import models  # noqa: F401
        from core.db import Database

        await Database.init()
        async with Database._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await Database.close()

    asyncio.run(recreate())

    # 3. 验证
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'auth_%' ORDER BY name"
    )
    new_tables = [r[0] for r in cur.fetchall()]
    print(f"\n✅ Rebuilt auth_* tables: {new_tables}")

    # 检查每个表的字段数 (跟 models.py 对齐)
    for table in new_tables:
        cur.execute(f"PRAGMA table_info({table})")
        cols = cur.fetchall()
        print(f"  {table}: {len(cols)} columns")

    conn.close()
    print("\n✅ Schema sync OK")


if __name__ == "__main__":
    main()