"""
国家企业信用信息公示系统爬虫 (免费官方)
2026-06-28 · 数据源: https://www.gsxt.gov.cn (国家市场监督管理总局)

数据: 企业基本信息 / 股东 / 高管 / 变更记录 / 经营异常 / 严重违法
字段: 统一社会信用代码 / 名称 / 法人 / 注册资本 / 成立日期 / 经营状态 / 注册地址
"""
import asyncio
from typing import List, Dict, Any
from loguru import logger

from crawlers.sources.base import BaseSource
from core.config import settings
from core.sanitize import sanitize_person_name, sanitize_address


class GsxtSource(BaseSource):
    source_name = "gsxt"

    async def crawl(self, query: str = "", max_pages: int = 50) -> List[Dict[str, Any]]:
        """
        爬取企业信息
        query: 企业名称 / 统一社会信用代码 / 法人
        """
        results = []
        try:
            list_url = f"{settings.gsxt_api_url}search"
            for page in range(1, max_pages + 1):
                resp = await self.fetch(
                    list_url,
                    params={"page": page, "size": 20, "keyword": query},
                )
                if not resp:
                    break
                data = resp.json()
                items = data.get("data", [])
                if not items:
                    break

                for item in items:
                    detail = await self._fetch_detail(item.get("id"))
                    if detail:
                        results.append(detail)
                        self.stats["items"] += 1

                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"[{self.source_name}] Crawl failed: {e}")
        finally:
            self.report()
        return results

    async def _fetch_detail(self, company_id: str) -> Dict[str, Any]:
        """拉企业详情"""
        url = f"{settings.gsxt_api_url}companyDetail"
        resp = await self.fetch(url, params={"id": company_id})
        if not resp:
            return None
        data = resp.json().get("data", {})

        # 脱敏: 法人姓名 + 注册地址
        legal_rep = data.get("legalRep", "")
        registered_address = data.get("address", "")

        return {
            "unified_id": data.get("unifiedId"),
            "company_name": data.get("name"),
            "company_type": data.get("type"),
            "legal_rep": sanitize_person_name(legal_rep) if legal_rep else None,
            "registered_capital": data.get("registeredCapital"),
            "paid_capital": data.get("paidCapital"),
            "establish_date": data.get("establishDate"),
            "business_status": data.get("status"),
            "registered_address": sanitize_address(registered_address, level="district"),
            "business_scope": data.get("scope"),
            "industry": data.get("industry"),
            "region": data.get("region"),
            "source": "gsxt",
            "source_url": f"{settings.gsxt_base_url}/company/{company_id}",
        }
