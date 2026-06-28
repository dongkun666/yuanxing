"""
4 个免费数据源调度器
2026-06-28 · 统一入口, 按优先级 + 频率运行
"""
import asyncio
from typing import List, Dict, Any
from loguru import logger

from crawlers.sources.npc_laws import NpcLawsSource
from crawlers.sources.court_cases import CourtCasesSource
from crawlers.sources.zhixing import ZhixingSource
from crawlers.sources.gsxt import GsxtSource
from core.db import Database, ESClient
from core.models import Law, Company
from core.config import settings


class CrawlerDispatcher:
    """4 个免费数据源调度器"""

    def __init__(self):
        self.sources = {
            "npc_laws": NpcLawsSource(),
            "court_cases": CourtCasesSource(),
            "zhixing": ZhixingSource(),
            "gsxt": GsxtSource(),
        }

    async def init(self):
        for src in self.sources.values():
            await src.init()
        await Database.init()
        await ESClient.init()

    async def close(self):
        for src in self.sources.values():
            await src.close()
        await Database.close()
        await ESClient.close()

    async def run_all(self):
        """依次跑 4 个数据源 (按优先级)"""
        await self.init()
        try:
            # 1. 人民法院案例库 (最优先, 案例质量高)
            logger.info(">>> 人民法院案例库")
            results = await self.sources["court_cases"].crawl(case_type="guide")
            await self._save_laws_or_cases(results, "case")
            await self._index_to_es(results, "case")

            # 2. 国家法律法规数据库
            logger.info(">>> 国家法律法规数据库")
            results = await self.sources["npc_laws"].crawl()
            await self._save_laws_or_cases(results, "law")
            await self._index_to_es(results, "law")

            # 3. 国家企业信用信息公示系统
            logger.info(">>> 国家企业信用")
            results = await self.sources["gsxt"].crawl()
            await self._save_laws_or_cases(results, "company")
            await self._index_to_es(results, "company")

            # 4. 中国执行信息公开网 (失信) - 增量更新
            logger.info(">>> 中国执行信息公开网")
            results = await self.sources["zhixing"].crawl()
            await self._update_zxgk(results)

        finally:
            await self.close()

    async def _save_laws_or_cases(self, items: List[Dict], type_: str):
        """保存到 PG"""
        if not items:
            return
        try:
            async with Database.session() as session:
                for item in items:
                    if type_ == "law":
                        session.add(Law(**item))
                    elif type_ == "company":
                        session.add(Company(**item))
                await session.commit()
            logger.info(f"Saved {len(items)} {type_}s to PG")
        except Exception as e:
            logger.error(f"PG save {type_} failed: {e}")

    async def _index_to_es(self, items: List[Dict], type_: str):
        """索引到 ES"""
        if not items:
            return
        try:
            es = ESClient.get()
            index_name = {
                "law": settings.es_index_laws,
                "case": settings.es_index_cases,
                "company": settings.es_index_companies,
            }[type_]
            actions = []
            for item in items:
                actions.append({"index": {"_index": index_name, "_id": item.get("id") or item.get("law_id") or item.get("unified_id") or item.get("doc_id")}})
                actions.append(item)
            await es.bulk(operations=actions, refresh=False)
            logger.info(f"Indexed {len(items)} {type_}s to ES")
        except Exception as e:
            logger.warning(f"ES index {type_} failed: {e}")

    async def _update_zxgk(self, items: List[Dict]):
        """更新企业失信状态"""
        if not items:
            return
        from sqlalchemy import update
        try:
            async with Database.session() as session:
                for item in items:
                    stmt = (
                        update(Company)
                        .where(Company.unified_id == item["unified_id"])
                        .values(is_zxgk=True, source=item.get("source"))
                    )
                    await session.execute(stmt)
                await session.commit()
            logger.info(f"Updated {len(items)} companies zxgk status")
        except Exception as e:
            logger.error(f"ZXGK update failed: {e}")


async def main():
    dispatcher = CrawlerDispatcher()
    await dispatcher.run_all()


if __name__ == "__main__":
    asyncio.run(main())
