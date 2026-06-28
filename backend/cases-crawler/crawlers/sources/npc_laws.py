"""
国家法律法规数据库爬虫 (免费)
2026-06-28 · 数据源: https://flk.npc.gov.cn

数据: 法律/行政法规/地方性法规/司法解释/部门规章
字段: 标题 / 法规编号 / 制定机关 / 公布日期 / 生效日期 / 全文
"""
from typing import List, Dict, Any
from loguru import logger

from crawlers.sources.base import BaseSource
from core.config import settings


class NpcLawsSource(BaseSource):
    source_name = "npc_laws"

    async def crawl(self, law_type: str = "all", max_pages: int = 100) -> List[Dict[str, Any]]:
        """
        爬取国家法律法规数据库
        law_type: all / law / administrative / local / judicial_interp / departmental
        """
        results = []
        try:
            # 法规列表 API
            list_url = f"{settings.npc_laws_api_url}lawList"
            for page in range(1, max_pages + 1):
                resp = await self.fetch(
                    list_url,
                    params={"page": page, "size": 50, "type": law_type},
                )
                if not resp:
                    break
                data = resp.json()
                items = data.get("data", {}).get("list", [])
                if not items:
                    break

                for item in items:
                    # 拉详情
                    detail = await self._fetch_detail(item.get("id"))
                    if detail:
                        results.append(detail)
                        self.stats["items"] += 1

        except Exception as e:
            logger.error(f"[{self.source_name}] Crawl failed: {e}")
        finally:
            self.report()
        return results

    async def _fetch_detail(self, law_id: str) -> Dict[str, Any]:
        """拉法规详情"""
        url = f"{settings.npc_laws_api_url}lawDetail"
        resp = await self.fetch(url, params={"id": law_id})
        if not resp:
            return None
        data = resp.json().get("data", {})
        return {
            "law_id": data.get("id") or law_id,
            "title": data.get("title"),
            "law_number": data.get("number"),
            "law_type": data.get("type"),
            "issuing_organ": data.get("issueOrgan"),
            "issue_date": data.get("issueDate"),
            "effective_date": data.get("effectiveDate"),
            "status": data.get("status", "有效"),
            "summary": data.get("summary"),
            "full_text": data.get("content"),
            "level": self._get_level(data.get("type")),
            "source": "npc_laws",
            "source_url": f"{settings.npc_laws_base_url}/detail2.html?MmM5MDlmZGQ2NzhiZjIyMzAxN2E2NTdkYzY3MDg2M2M{law_id}",
        }

    def _get_level(self, law_type: str) -> int:
        """法规层级 (1 宪法 / 2 法律 / 3 行政法规 / 4 司法解释 / 5 部门规章)"""
        mapping = {
            "宪法": 1,
            "法律": 2,
            "行政法规": 3,
            "司法解释": 4,
            "部门规章": 5,
            "地方性法规": 5,
        }
        return mapping.get(law_type, 5)
