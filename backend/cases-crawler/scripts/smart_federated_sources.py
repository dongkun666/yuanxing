"""
4 个免费数据源 智能适配器 (smart fallback)
2026-06-28 · B 任务

发现: 4 个公开数据源全有强反爬 (Cloudflare 521 / timeout / 内部 API)
策略: 尝试爬取 → 失败 fallback 到"跳转官方查询"模式 (联邦)

LexPrime 角色: 客户端 + 数据管理 (用户查到的判例/法规/企业, 可手动录入系统)
- 不自建大型数据, 避免合规风险
- 提供"查询 + 收藏"工作流
- 真实数据来源: cncases 102GB (按需下载) + 律所内部录入 + 公开查询跳转
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))

from crawlers.sources.base import BaseSource


# ===== 联邦模式: 跳转到公开查询页 =====
JUMP_URLS = {
    "npc_laws": {
        "name": "国家法律法规数据库",
        "search_url": "https://flk.npc.gov.cn/search.html?keyword={kw}",
        "detail_url": "https://flk.npc.gov.cn/detail2.html?id={id}",
        "fallback_msg": "官网需要登录验证 / 反爬保护。LexPrime 提供跳转查询模式。",
    },
    "court_cases": {
        "name": "人民法院案例库",
        "search_url": "https://rmfyalk.court.gov.cn/caseSearch?keyword={kw}",
        "detail_url": "https://rmfyalk.court.gov.cn/caseDetail?caseId={id}",
        "fallback_msg": "官网需要登录 + 内网 API。LexPrime 推荐 cncases 102GB 种子 (全量本地) 或跳转公开查询。",
    },
    "zhixing": {
        "name": "中国执行信息公开网",
        "search_url": "https://zxgk.court.gov.cn/shixin/search?keyword={kw}",
        "detail_url": "https://zxgk.court.gov.cn/shixin/detail?id={id}",
        "fallback_msg": "公开查询无需登录, 但无 JSON API。LexPrime 提供跳转查询 + 收藏工作流。",
    },
    "gsxt": {
        "name": "国家企业信用信息公示系统",
        "search_url": "https://www.gsxt.gov.cn/corp-query-entprise-info-xxgg-{kw}.html",
        "detail_url": "https://www.gsxt.gov.cn/corp-query-entprise-info-{id}.html",
        "fallback_msg": "Cloudflare 521 强保护 + 无公开 API。LexPrime 推荐跳转查询或用户自录入。",
    },
}


class SmartSource(BaseSource):
    """智能适配器: 尝试爬 → 失败 fallback 跳转"""
    source_name = "smart"

    def __init__(self, source_key: str):
        super().__init__()
        self.source_key = source_key
        self.jump_info = JUMP_URLS.get(source_key, {})

    async def crawl(self, **kwargs) -> List[Dict[str, Any]]:
        """尝试爬取, 失败返回带跳转链接的元数据"""
        logger.info(f"[{self.source_name}] 尝试爬取 {self.jump_info.get('name', self.source_key)}...")

        # 尝试 1: 调用真实 API
        items = await self._try_real_api(**kwargs)

        if items:
            return items

        # 失败: 联邦模式 - 返回跳转元数据
        logger.warning(f"[{self.source_name}] 爬取失败, fallback 到联邦模式")
        return self._fallback_metadata(**kwargs)

    async def _try_real_api(self, **kwargs) -> List[Dict[str, Any]]:
        """尝试真实 API 调用"""
        try:
            # 只试 1 次, timeout 5s (快速失败, 走 fallback)
            base_url = JUMP_URLS.get(self.source_key, {}).get("search_url", "").split("?")[0].rstrip("/")
            if not base_url:
                return []

            resp = await self.fetch(base_url, timeout=5)
            if not resp:
                return []

            # 如果返回 HTML (反爬重定向页或 SPA), 不解析
            if "html" in resp.headers.get("content-type", "").lower():
                logger.info(f"[{self.source_name}] 返 HTML, 跳过解析")
                return []

            return []
        except Exception as e:
            logger.debug(f"[{self.source_name}] API 尝试失败: {e}")
            return []

    def _fallback_metadata(self, **kwargs) -> List[Dict[str, Any]]:
        """返回带跳转链接的元数据 (1 条, 表示该源已 fallback)"""
        kw = kwargs.get("query", "")
        search_url = self.jump_info.get("search_url", "").format(kw=kw or "")

        return [{
            "_type": "fallback_metadata",
            "source": self.source_key,
            "source_name": self.jump_info.get("name", self.source_key),
            "fallback_msg": self.jump_info.get("fallback_msg", ""),
            "search_url": search_url,
            "query": kw,
            "recommendation": self._get_recommendation(),
        }]

    def _get_recommendation(self) -> str:
        """推荐策略"""
        recs = {
            "npc_laws": "1. 跳转 flk.npc.gov.cn 查询\n2. 复制法规摘要到 LexPrime 收藏\n3. 或下载 cncases 102GB (含法规)",
            "court_cases": "1. 跳转 rmfyalk.court.gov.cn 查询\n2. 或下载 cncases 102GB (含 8500 万判例)\n3. 律所内部案件 → 直接录入 lawyer_added_cases",
            "zhixing": "1. 跳转 zxgk.court.gov.cn 查询失信被执行人\n2. 录入到 companies.is_zxgk\n3. 配合裁判文书网做尽调",
            "gsxt": "1. 跳转 gsxt.gov.cn 查询工商信息\n2. 录入到 companies 表 (含股权穿透)\n3. 或用 LexPrime 自建库 (10 公司已 seed)",
        }
        return recs.get(self.source_key, "")


# ===== 4 个适配器实例 =====

class NpcLawsSmart(SmartSource):
    source_name = "npc_laws_smart"
    def __init__(self): super().__init__("npc_laws")

class CourtCasesSmart(SmartSource):
    source_name = "court_cases_smart"
    def __init__(self): super().__init__("court_cases")

class ZhixingSmart(SmartSource):
    source_name = "zhixing_smart"
    def __init__(self): super().__init__("zhixing")

class GsxtSmart(SmartSource):
    source_name = "gsxt_smart"
    def __init__(self): super().__init__("gsxt")


async def main():
    """测试 4 个源"""
    sources = [
        ("npc_laws", NpcLawsSmart()),
        ("court_cases", CourtCasesSmart()),
        ("zhixing", ZhixingSmart()),
        ("gsxt", GsxtSmart()),
    ]
    for key, src in sources:
        logger.info(f"\n--- {JUMP_URLS[key]['name']} ---")
        results = await src.crawl(query="合同")
        if results and results[0].get("_type") == "fallback_metadata":
            meta = results[0]
            logger.info(f"  联邦模式: {meta['fallback_msg']}")
            logger.info(f"  跳转 URL: {meta['search_url']}")
            logger.info(f"  推荐:\n    {meta['recommendation'].replace(chr(10), chr(10) + '    ')}")
        else:
            logger.info(f"  真数据: {len(results)} 条")
        await src.close()


if __name__ == "__main__":
    asyncio.run(main())
