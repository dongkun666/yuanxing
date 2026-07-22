"""
LexPrime 数据库连接 (SQLite dev + PostgreSQL prod + ES in-memory)
2026-06-28 · 支持零依赖演示 + 生产切换

优先级:
1. 环境变量 DATABASE_URL 显式指定 → 严格按其执行
2. 默认 SQLite (dev/demo) → 零依赖, 即开即跑
3. PostgreSQL (prod) → 需要 docker-compose
4. ES: 本地文件 / 内存 mock (dev) + 真 ES (prod)
5. Neo4j: 可选, 没有时跳过图查询

连接池配置:
- PostgreSQL: pool_size=20, max_overflow=10, pool_timeout=30, pool_recycle=3600
- SQLite: pool_size=5, max_overflow=0 (SQLite 单连接限制)
"""
import os
import json
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from loguru import logger

from .config import settings


class ConnectionPoolStats:
    """连接池监控统计"""
    _pool_stats = {
        "connections_created": 0,
        "connections_checked_out": 0,
        "connections_checked_in": 0,
        "connections_errors": 0,
        "peak_connections": 0,
        "last_reset": time.time(),
    }

    @classmethod
    def increment(cls, key: str):
        cls._pool_stats[key] = cls._pool_stats.get(key, 0) + 1
        if key == "connections_checked_out":
            current = cls._pool_stats["connections_checked_out"] - cls._pool_stats["connections_checked_in"]
            if current > cls._pool_stats["peak_connections"]:
                cls._pool_stats["peak_connections"] = current

    @classmethod
    def get_stats(cls) -> dict:
        stats = cls._pool_stats.copy()
        stats["current_connections"] = (
            stats["connections_checked_out"] - stats["connections_checked_in"]
        )
        stats["uptime_seconds"] = int(time.time() - stats["last_reset"])
        return stats

    @classmethod
    def reset(cls):
        cls._pool_stats = {
            "connections_created": 0,
            "connections_checked_out": 0,
            "connections_checked_in": 0,
            "connections_errors": 0,
            "peak_connections": 0,
            "last_reset": time.time(),
        }


def detect_db_backend() -> str:
    """自动检测 DB 后端: sqlite / postgres"""
    db_url = settings.database_url.lower()
    if "sqlite" in db_url:
        return "sqlite"
    if "postgres" in db_url or "postgresql" in db_url:
        return "postgres"
    # 默认 SQLite
    return "sqlite"


# ========== PostgreSQL / SQLite 抽象层 ==========
class Database:
    _engine = None
    _session_factory = None
    _backend: str = "sqlite"

    @classmethod
    async def init(cls):
        if cls._engine is not None:
            return

        cls._backend = detect_db_backend()
        logger.info(f"Database backend: {cls._backend}")

        if cls._backend == "sqlite":
            await cls._init_sqlite()
        else:
            await cls._init_postgres()

    @classmethod
    async def _init_sqlite(cls):
        """SQLite dev 模式 - 用 aiosqlite + 文件数据库"""
        try:
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        except ImportError:
            raise RuntimeError("需要安装 SQLAlchemy: pip install sqlalchemy[asyncio] aiosqlite")

        # 强制使用 aiosqlite 驱动
        # 警告: 简单的 replace 会被 `aiosqlite://` 中的 `sqlite://` 子串干扰
        url = settings.database_url
        if not url.startswith("sqlite+aiosqlite://"):
            if url.startswith("sqlite://"):
                url = "sqlite+aiosqlite://" + url[len("sqlite://"):]
            else:
                # 兜底, 强制追加
                url = "sqlite+aiosqlite://" + url

        # 确保目录存在
        if ":memory:" not in url:
            # 提取 db 文件路径: 跳过 `sqlite+aiosqlite:///`
            prefix = "sqlite+aiosqlite:///"
            if url.startswith(prefix):
                db_file = url[len(prefix):]
            else:
                db_file = url
            if db_file and db_file != ":memory:":
                os.makedirs(os.path.dirname(os.path.abspath(db_file)) or ".", exist_ok=True)

        cls._engine = create_async_engine(
            url,
            echo=settings.api_debug,
            pool_pre_ping=False,
            pool_size=5,
            max_overflow=0,
            pool_timeout=10,
        )
        cls._session_factory = async_sessionmaker(
            cls._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info(f"✓ SQLite engine initialized: {url}")
        logger.info(f"  Pool config: pool_size=5, max_overflow=0, pool_timeout=10")

    @classmethod
    async def _init_postgres(cls):
        """PostgreSQL 生产模式"""
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        cls._engine = create_async_engine(
            settings.database_url,
            echo=settings.api_debug,
            pool_size=20,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
        )
        cls._session_factory = async_sessionmaker(
            cls._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info(f"✓ PostgreSQL engine initialized: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
        logger.info(f"  Pool config: pool_size=20, max_overflow=10, pool_timeout=30, pool_recycle=3600, pool_pre_ping=True")

    @classmethod
    async def close(cls):
        if cls._engine:
            await cls._engine.dispose()
            cls._engine = None
            logger.info("Database engine closed")

    @classmethod
    @asynccontextmanager
    async def session(cls) -> AsyncGenerator:
        if cls._session_factory is None:
            await cls.init()
        async with cls._session_factory() as session:
            ConnectionPoolStats.increment("connections_checked_out")
            try:
                yield session
                await session.commit()
            except Exception:
                ConnectionPoolStats.increment("connections_errors")
                await session.rollback()
                raise
            finally:
                ConnectionPoolStats.increment("connections_checked_in")

    @classmethod
    def get_pool_stats(cls) -> dict:
        """获取连接池统计信息"""
        stats = ConnectionPoolStats.get_stats()
        if cls._engine:
            try:
                pool = cls._engine.pool
                if pool:
                    stats["pool_size"] = pool.size()
                    stats["pool_overflow"] = pool.overflow()
            except Exception:
                pass
        return stats


# ========== Elasticsearch 抽象层 (含 in-memory fallback) ==========
class ESClient:
    _client = None
    _use_real: bool = False
    _memory_store: dict = {}  # index -> {id: doc}
    _available: bool = True  # 标记 ES 是否可用

    @classmethod
    async def init(cls):
        if cls._client is not None:
            return

        # 尝试连接真实 ES
        try:
            from elasticsearch import AsyncElasticsearch
            cls._client = AsyncElasticsearch(
                hosts=[{
                    "scheme": settings.es_scheme,
                    "host": settings.es_host,
                    "port": settings.es_port,
                }],
                basic_auth=(settings.es_user, settings.es_password),
                request_timeout=3,
                max_retries=1,
            )
            # 测试连接
            await cls._client.info()
            cls._use_real = True
            logger.info(f"✓ Elasticsearch connected: {settings.es_host}:{settings.es_port}")
        except Exception as e:
            logger.warning(f"⚠️  Elasticsearch not available: {e}")
            logger.warning(f"   Falling back to in-memory mock (dev only)")
            cls._use_real = False
            cls._client = None
            cls._memory_store = {}

    @classmethod
    async def close(cls):
        if cls._client and cls._use_real:
            await cls._client.close()
        cls._client = None
        logger.info("ES client closed")

    @classmethod
    def is_mock(cls) -> bool:
        return not cls._use_real

    @classmethod
    async def index_doc(cls, index: str, doc_id: str, body: dict):
        """索引文档"""
        if cls._use_real:
            await cls._client.index(index=index, id=doc_id, document=body)
        else:
            cls._memory_store.setdefault(index, {})
            cls._memory_store[index][doc_id] = body

    @classmethod
    async def bulk_index(cls, index: str, docs: list, id_field: str = "id"):
        """批量索引"""
        if cls._use_real:
            actions = []
            for d in docs:
                doc_id = d.get(id_field)
                actions.append({"index": {"_index": index, "_id": doc_id}})
                actions.append(d)
            await cls._client.bulk(operations=actions, refresh=False)
        else:
            cls._memory_store.setdefault(index, {})
            for d in docs:
                doc_id = d.get(id_field)
                cls._memory_store[index][doc_id] = d

    @classmethod
    async def search(cls, index: str, body: dict) -> dict:
        """搜索"""
        if cls._use_real:
            return await cls._client.search(index=index, body=body)
        else:
            # 内存 mock: 简单 contains 搜索
            return cls._memory_search(index, body)

    @classmethod
    def _memory_search(cls, index: str, body: dict) -> dict:
        """内存搜索 (仅 dev 演示) - 简单 contains"""
        all_docs = list(cls._memory_store.get(index, {}).values())
        query = body.get("query", {})
        query_str = ""

        if isinstance(query, dict):
            if "multi_match" in query:
                query_str = query["multi_match"].get("query", "")
            elif "bool" in query:
                for must_clause in query["bool"].get("must", []):
                    if "multi_match" in must_clause:
                        query_str = must_clause["multi_match"].get("query", "")
                        break
            elif "match_all" in query:
                query_str = ""

        # 简单过滤
        if query_str:
            q_lower = query_str.lower()
            results = [d for d in all_docs if q_lower in json.dumps(d, ensure_ascii=False).lower()]
        else:
            results = all_docs

        from_ = body.get("from", 0)
        size = body.get("size", 20)
        hits = results[from_:from_ + size]

        return {
            "hits": {
                "total": {"value": len(results)},
                "hits": [{"_id": d.get("id"), "_source": d} for d in hits]
            }
        }


# ========== Neo4j (可选) ==========
class Neo4jClient:
    _driver = None
    _available: bool = True

    @classmethod
    async def init(cls):
        if cls._driver is not None:
            return
        try:
            from neo4j import AsyncGraphDatabase
            cls._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                max_connection_pool_size=10,
            )
            async with cls._driver.session() as session:
                await session.run("RETURN 1").single()
            logger.info(f"✓ Neo4j connected: {settings.neo4j_uri}")
        except Exception as e:
            logger.warning(f"⚠️  Neo4j not available: {e}, skipping graph features")
            cls._driver = None
            cls._available = False

    @classmethod
    async def close(cls):
        if cls._driver:
            await cls._driver.close()
            cls._driver = None
        logger.info("Neo4j driver closed")

    @classmethod
    def get(cls):
        return cls._driver

    @classmethod
    def is_available(cls) -> bool:
        return cls._driver is not None
