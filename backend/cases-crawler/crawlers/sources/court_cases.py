"""
人民法院案例库爬虫 (免费)
2026-06-28 · 数据源: https://rmfyalk.court.gov.cn (最高法 2024 重启)

数据: 指导性案例 + 典型案例 + 参考案例
字段: 案号 / 案件名称 / 法院 / 案由 / 裁判规则 / 全文
"""
import asyncio
from typing import List, Dict, Any
from loguru import logger

from crawlers.sources.base import BaseSource
from core.config import settings
from core.sanitize import classify_cause, html_to_plain, sanitize_full_text


class CourtCasesSource(BaseSource):
    source_name = "court_cases"

    async def crawl(self, case_type: str = "guide", max_pages: int = 50) -> List[Dict[str, Any]]:
        """
        爬取人民法院案例库
        case_type: guide (指导性案例) / typical (典型案例) / reference (参考案例)
        """
        results = []
        try:
            # 案例列表 API
            list_url = f"{settings.court_cases_api_url}caseList"
            for page in range(1, max_pages + 1):
                resp = await self.fetch(
                    list_url,
                    params={"page": page, "size": 30, "type": case_type},
                )
                if not resp:
                    break
                data = resp.json()
                items = data.get("data", {}).get("list", [])
                if not items:
                    break

                for item in items:
                    detail = await self._fetch_detail(item.get("id"))
                    if detail:
                        results.append(detail)
                        self.stats["items"] += 1

                # 礼貌等待
                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"[{self.source_name}] Crawl failed: {e}")
        finally:
            self.report()
        return results

    async def _fetch_detail(self, case_id: str) -> Dict[str, Any]:
        """拉案例详情"""
        url = f"{settings.court_cases_api_url}caseDetail"
        resp = await self.fetch(url, params={"id": case_id})
        if not resp:
            return None
        data = resp.json().get("data", {})

        full_text = sanitize_full_text(data.get("content", ""))
        cause = data.get("cause", "").strip()
        cause_category, cause_color = classify_cause(cause)

        return {
            "doc_id": case_id,
            "case_id": data.get("caseNo"),
            "case_name": data.get("caseName"),
            "court": data.get("court"),
            "case_type": data.get("caseType"),
            "procedure": data.get("procedure"),
            "judgment_date": data.get("judgmentDate"),
            "public_date": data.get("publishDate"),
            "parties": data.get("parties"),
            "cause": cause,
            "cause_category": cause_category,
            "cause_color": cause_color,
            "legal_basis": data.get("legalBasis"),
            "full_text": full_text,
            "full_text_plain": html_to_plain(full_text),
            "source": "court_cases",
            "source_url": f"{settings.court_cases_base_url}/caseDetail?caseId={case_id}",
            "lex_score": 90 if case_id.startswith("guide") else 70,  # 指导性案例高优
            "lex_tags": ["人民法院案例库", case_id.startswith("guide") and "指导性案例" or "典型案例"],
        }
