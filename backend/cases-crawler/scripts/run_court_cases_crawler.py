"""
人民法院案例库真实爬虫 runner
2026-06-28 · 任务 2

探测 API 端点 (rmfyalk.court.gov.cn), 真跑 + 写库
- 真实 caseopen.org API (cncases demo) 也可作为参考
- 反爬: 慢速 1 req/s + 真实 UA + Referer

用法:
    python scripts/run_court_cases_crawler.py --max 100
"""
import asyncio
import argparse
import sys
from pathlib import Path
from loguru import logger
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import Database
from crawlers.sources.court_cases import CourtCasesSource


async def discover_api():
    """探测 API 端点"""
    logger.info("=" * 60)
    logger.info("Step 1: 探测 API 端点")
    logger.info("=" * 60)

    src = CourtCasesSource()
    await src.init()

    test_endpoints = [
        # 人民法院案例库 (最高法 2024 重启)
        ("https://rmfyalk.court.gov.cn/api/caseList", {"page": 1, "size": 5, "type": "guide"}),
        ("https://rmfyalk.court.gov.cn/api/cases", {"page": 1, "size": 5}),
        ("https://rmfyalk.court.gov.cn/api/case/list", {"page": 1, "size": 5}),
        # cncases demo (caseopen.org)
        ("https://caseopen.org/api/search", {"q": "合同纠纷", "page": 1}),
        ("https://caseopen.org/api/cases", {"page": 1, "size": 5}),
        # 备选: 公开搜索
        ("https://www.court.gov.cn/api/search", {"q": "合同", "page": 1}),
    ]

    found = []
    for url, params in test_endpoints:
        logger.info(f"试: {url[:60]}...")
        try:
            resp = await src.fetch(url, params=params)
            if resp and resp.status_code == 200:
                logger.info(f"  ✓ HTTP 200, content-type: {resp.headers.get('content-type', 'unknown')[:40]}")
                try:
                    data = resp.json()
                    logger.info(f"  ✓ JSON OK, 顶层 keys: {list(data.keys())[:5]}")
                    found.append((url, data))
                except Exception as e:
                    logger.warning(f"  ✗ JSON parse failed: {e}, text[:100]: {resp.text[:100]}")
            else:
                logger.warning(f"  ✗ HTTP {resp.status_code if resp else 'None'}")
        except Exception as e:
            logger.warning(f"  ✗ Exception: {str(e)[:80]}")

    await src.close()
    return found


async def run_crawler(max_cases: int = 100):
    """真跑案例库爬虫"""
    logger.info("=" * 60)
    logger.info(f"Step 2: 真跑爬虫 (max={max_cases})")
    logger.info("=" * 60)

    await Database.init()
    src = CourtCasesSource()
    await src.init()

    try:
        # 抓取 guide (指导性案例) + typical (典型案例)
        results = await src.crawl(case_type="guide", max_pages=2)
        logger.info(f"✓ 抓取 guide: {len(results)} 条")
        for r in results[:3]:
            logger.info(f"  - {r.get('case_id', 'N/A')}: {(r.get('case_name') or '')[:60]}")
        return results
    except Exception as e:
        logger.error(f"爬取失败: {e}")
        return []
    finally:
        await src.close()
        await Database.close()


async def main():
    parser = argparse.ArgumentParser(description="人民法院案例库真实 runner")
    parser.add_argument("--max", type=int, default=100, help="最大条数")
    parser.add_argument("--skip-discover", action="store_true", help="跳过 API 探测")
    args = parser.parse_args()

    if not args.skip_discover:
        found = await discover_api()
        if not found:
            logger.warning("⚠️  未发现可用 API 端点")
            logger.warning("   - 最高人民法院案例库 (rmfyalk.court.gov.cn) 可能需要登录")
            logger.warning("   - 备选: 使用 cncases 8500万种子 (cncases_import.md)")
            logger.warning("   - 备选: 使用 mock 数据 (data-db.js)")

    results = await run_crawler(args.max)
    logger.info(f"\n总抓取: {len(results)} 条")


if __name__ == "__main__":
    asyncio.run(main())
