"""
LexPrime Cases Crawler - 数据库初始化脚本 (SQLite + PG 双模式)
2026-06-28

用法:
    python scripts/init_db.py             # 默认 SQLite + 自动检测 ES/Neo4j
    python scripts/init_db.py --seed      # 初始化 + 种子数据
    python scripts/init_db.py --reset     # ⚠️ 删表重建
    python scripts/init_db.py --backend postgres  # 强制 PG (需 docker-compose up)
"""
import asyncio
import argparse
import os
import sys
from pathlib import Path
from loguru import logger

# 把父目录加入 sys.path (因为 scripts/ 子目录运行)
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import settings
from core.db import Database, ESClient, Neo4jClient, detect_db_backend
from core.models import Base, Firm, Lawyer


async def init_database(reset: bool = False):
    """初始化数据库 schema"""
    await Database.init()
    backend = Database._backend
    logger.info(f"Init database ({backend})...")

    if reset:
        logger.warning(f"⚠️  Dropping all tables ({backend})!")
        async with Database._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async with Database._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info(f"✓ {backend} schema initialized")


async def init_elasticsearch():
    """初始化 ES 索引 (如果可用)"""
    await ESClient.init()
    if ESClient.is_mock():
        logger.info("ℹ️  ES in-memory mode (dev) - skipping real index creation")
        return

    es = ESClient.get()
    indices_path = Path(__file__).parent.parent / "db" / "elasticsearch_indices.json"
    config = json.loads(indices_path.read_text(encoding="utf-8"))

    for index_name, index_config in config["indices"].items():
        try:
            exists = await es.indices.exists(index=index_name)
            if not exists:
                await es.indices.create(
                    index=index_name,
                    settings=index_config.get("settings", {}),
                    mappings=index_config.get("mappings", {}),
                )
                logger.info(f"✓ Created ES index: {index_name}")
            else:
                logger.info(f"  ES index exists: {index_name}")
        except Exception as e:
            logger.error(f"Failed to create ES index {index_name}: {e}")


async def init_neo4j():
    """初始化 Neo4j 约束"""
    await Neo4jClient.init()
    if not Neo4jClient.is_available():
        logger.info("ℹ️  Neo4j not available - skipping graph constraints")
        return

    cypher_path = Path(__file__).parent.parent / "db" / "neo4j_constraints.cypher"
    cypher = cypher_path.read_text(encoding="utf-8")
    statements = [s.strip() for s in cypher.split(";") if s.strip() and not s.strip().startswith("//")]

    async with Neo4jClient.get().session() as session:
        for stmt in statements:
            try:
                await session.run(stmt)
            except Exception as e:
                logger.warning(f"Neo4j statement failed: {e}")
    logger.info("✓ Neo4j constraints initialized")


async def seed_demo_data():
    """种子数据 - 律所版 0.1 demo"""
    logger.info("Seeding demo data...")

    firm = Firm(
        id="firm-demo-001",
        name="示例律师事务所",
        unified_id="53310000XXXXXXXXX",
        license_no="XXXXXXXXX",
        region="北京市",
        address="北京市朝阳区建国路 88 号",
        contact_phone="010-12345678",
        contact_email="contact@example-law.com",
        firm_size="medium",
        subscription_tier="pro",
        settings={
            "default_cause_categories": ["合同纠纷", "婚姻家事", "知识产权"],
            "brand_color": "#165DFF",
            "enable_internal_cases": True,
        },
    )

    lawyers = [
        Lawyer(id="u-1", firm_id="firm-demo-001", name="张律师", license_no="XXXXXXXX-A",
               email="zhang@example-law.com", phone="13800000001", role="partner",
               specialties=["民商事", "知识产权"], bio="20 年律师经验, 合伙人", is_active=True),
        Lawyer(id="u-demo-002", firm_id="firm-demo-001", name="李律师", license_no="XXXXXXXX-B",
               email="li@example-law.com", phone="13800000002", role="senior",
               specialties=["刑事", "行政"], bio="高级律师, 刑事辩护专家", is_active=True),
        Lawyer(id="u-demo-003", firm_id="firm-demo-001", name="王律师", license_no="XXXXXXXX-C",
               email="wang@example-law.com", phone="13800000003", role="lawyer",
               specialties=["婚姻家事", "合同纠纷"], bio="律师, 婚姻家事方向", is_active=True),
        Lawyer(id="u-demo-004", firm_id="firm-demo-001", name="赵律师", license_no="XXXXXXXX-D",
               email="zhao@example-law.com", phone="13800000004", role="lawyer",
               specialties=["劳动争议", "工伤"], bio="律师, 劳动法方向", is_active=True),
        Lawyer(id="u-demo-005", firm_id="firm-demo-001", name="陈律师", license_no="XXXXXXXX-E",
               email="chen@example-law.com", phone="13800000005", role="assistant",
               specialties=["民商事"], bio="律师助理", is_active=True),
        Lawyer(id="u-demo-006", firm_id="firm-demo-001", name="林律师", license_no="XXXXXXXX-F",
               email="lin@example-law.com", phone="13800000006", role="senior",
               specialties=["公司治理", "股权纠纷"], bio="高级律师, 公司法方向", is_active=False),
    ]

    async with Database.session() as session:
        session.add(firm)
        for l in lawyers:
            session.add(l)
        await session.commit()
    logger.info(f"✓ Seeded 1 firm + {len(lawyers)} lawyers")


async def main():
    parser = argparse.ArgumentParser(description="LexPrime DB Init")
    parser.add_argument("--reset", action="store_true", help="Drop all tables first")
    parser.add_argument("--seed", action="store_true", help="Insert demo data")
    parser.add_argument("--backend", choices=["sqlite", "postgres", "auto"], default="auto",
                        help="Database backend (default: auto-detect)")
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("LexPrime DB Initialization")
    logger.info("=" * 50)

    if args.backend != "auto":
        # 强制 backend
        if args.backend == "postgres":
            os.environ["DATABASE_URL"] = settings.database_url.replace("sqlite", "postgresql")
        else:
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/lexprime.db"

    await init_database(reset=args.reset)
    await init_elasticsearch()
    await init_neo4j()

    if args.seed:
        await seed_demo_data()

    # Close
    await Database.close()
    await ESClient.close()
    await Neo4jClient.close()

    logger.info("=" * 50)
    logger.info(f"✓ All done! Backend: {detect_db_backend()}")
    logger.info("=" * 50)


if __name__ == "__main__":
    import json  # noqa
    asyncio.run(main())
