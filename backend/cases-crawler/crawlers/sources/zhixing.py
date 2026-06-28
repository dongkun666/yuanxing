"""
中国执行信息公开网爬虫 (免费, 公开查询)
2026-06-28 · 数据源: https://zxgk.court.gov.cn

数据: 失信被执行人 / 限制高消费 / 终本案件 / 裁判文书
字段: 姓名/名称 / 身份证号(脱敏) / 执行法院 / 执行案号 / 立案时间 / 失信情形
"""
import asyncio
from typing import List, Dict, Any
from loguru import logger

from crawlers.sources.base import BaseSource
from core.config import settings
from core.sanitize import sanitize_id_card, sanitize_person_name


class ZhixingSource(BaseSource):
    source_name = "zhixing"

    async def crawl(self, query: str = "", max_pages: int = 50) -> List[Dict[str, Any]]:
        """
        爬取失信被执行人
        query: 自然人姓名 / 法人名称
        """
        results = []
        try:
            # 失信被执行人查询
            list_url = f"{settings.zhixing_base_url}/shixin/search"
            for page in range(1, max_pages + 1):
                resp = await self.fetch(
                    list_url,
                    params={"page": page, "size": 20, "keyword": query},
                )
                if not resp:
                    break
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}

                items = data.get("data", [])
                if not items:
                    break

                for item in items:
                    # 同步到 companies 表 (如果失信方是企业)
                    results.append(self._parse_to_company(item))
                    self.stats["items"] += 1

                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"[{self.source_name}] Crawl failed: {e}")
        finally:
            self.report()
        return results

    def _parse_to_company(self, item: Dict) -> Dict[str, Any]:
        """解析为 companies 表更新"""
        is_company = item.get("type") == "company"  # company / person
        return {
            "unified_id": item.get("unifiedId") or f"zxgk_{item.get('id')}",
            "company_name": item.get("name") if is_company else item.get("name"),  # 自然人也存 name
            "is_zxgk": True,
            "source": "zhixing",
            "source_url": f"{settings.zhixing_base_url}/shixin/detail?id={item.get('id')}",
            # 失信情形
            # 'dishonest_reason': item.get('reason'),
            # 'enforce_court': item.get('court'),
            # 'case_no': item.get('caseNo'),
        }
