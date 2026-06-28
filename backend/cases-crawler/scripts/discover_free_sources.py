"""
4 个免费数据源 API 端点探测
2026-06-28 · B 任务

探测:
1. 国家法律法规数据库 (flk.npc.gov.cn)
2. 人民法院案例库 (rmfyalk.court.gov.cn)
3. 中国执行信息公开网 (zxgk.court.gov.cn)
4. 国家企业信用信息公示系统 (gsxt.gov.cn)

策略:
- 主页 → 找 API 调用 (前端 JS / Network 抓包)
- 试常见 API 路径 (/api/, /search, /list)
- 试 GraphQL / JSONP / POST 表单
- 不行就 fallback: 跳转到公开查询页 (用户手动查)
"""
import asyncio
import httpx
import json
from loguru import logger
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def probe_source(client, name, base_url, paths):
    """探测单个源的多个 API 端点"""
    logger.info(f"\n{'=' * 60}\n{name}\nBase: {base_url}\n{'=' * 60}")

    found = []
    for path_info in paths:
        if isinstance(path_info, tuple):
            path, method = path_info
        else:
            path, method = path_info, "GET"
        url = base_url + path

        try:
            if method == "GET":
                resp = await client.get(url, timeout=10)
            else:
                resp = await client.post(url, timeout=10)

            text_len = len(resp.text)
            content_type = resp.headers.get("content-type", "")

            if resp.status_code == 200:
                logger.info(f"  ✓ HTTP 200 | {method:4s} {path[:50]:50s} | size={text_len} | ct={content_type[:30]}")
                # 试 JSON 解析
                if "json" in content_type:
                    try:
                        data = resp.json()
                        logger.info(f"    JSON keys: {list(data.keys())[:5]}")
                        found.append((path, method, "json", data))
                    except:
                        logger.info(f"    JSON parse fail")
                else:
                    # HTML, 找搜索表单
                    if "搜索" in resp.text or "search" in resp.text.lower():
                        logger.info(f"    HTML 页面 (有搜索)")
                        found.append((path, method, "html", resp.text[:500]))
            else:
                logger.info(f"  ✗ HTTP {resp.status_code} | {method:4s} {path[:50]}")
        except Exception as e:
            logger.info(f"  ✗ Exception: {str(e)[:80]} | {method:4s} {path[:50]}")

    return found


async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html, */*",
    }

    async with httpx.AsyncClient(headers=headers, http2=True, follow_redirects=True) as client:
        # 1. 国家法律法规数据库
        npc_paths = [
            ("/api/", "GET"),
            ("/api/lawList", "GET"),
            ("/api/laws", "GET"),
            ("/api/search", "GET"),
            ("/api/detail", "GET"),
            ("/", "GET"),
        ]
        npc_found = await probe_source(client, "1. 国家法律法规数据库 (flk.npc.gov.cn)",
                                       "https://flk.npc.gov.cn", npc_paths)

        # 2. 人民法院案例库
        court_paths = [
            ("/api/caseList", "GET"),
            ("/api/cases", "GET"),
            ("/api/search", "GET"),
            ("/", "GET"),
        ]
        court_found = await probe_source(client, "2. 人民法院案例库 (rmfyalk.court.gov.cn)",
                                          "https://rmfyalk.court.gov.cn", court_paths)

        # 3. 中国执行信息公开网
        zhixing_paths = [
            ("/shixin/search", "GET"),
            ("/zhixing/search", "GET"),
            ("/api/search", "GET"),
            ("/", "GET"),
        ]
        zhixing_found = await probe_source(client, "3. 中国执行信息公开网 (zxgk.court.gov.cn)",
                                            "https://zxgk.court.gov.cn", zhixing_paths)

        # 4. 国家企业信用信息公示系统
        gsxt_paths = [
            ("/api/search", "GET"),
            ("/api/company", "GET"),
            ("/search", "GET"),
            ("/", "GET"),
        ]
        gsxt_found = await probe_source(client, "4. 国家企业信用 (gsxt.gov.cn)",
                                        "https://www.gsxt.gov.cn", gsxt_paths)

        # 5. 备选: caseopen.org (cncases demo)
        caseopen_paths = [
            ("/api/search", "GET"),
            ("/api/cases", "GET"),
            ("/", "GET"),
        ]
        caseopen_found = await probe_source(client, "5. caseopen.org (cncases demo)",
                                            "https://caseopen.org", caseopen_paths)

    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("探测结果总结")
    logger.info("=" * 60)
    for name, found in [
        ("国家法律法规数据库", npc_found),
        ("人民法院案例库", court_found),
        ("中国执行信息公开网", zhixing_found),
        ("国家企业信用", gsxt_found),
        ("caseopen.org", caseopen_found),
    ]:
        logger.info(f"\n{name}: {len(found)} 个可用端点")
        for path, method, kind, _ in found:
            logger.info(f"  - {method} {path} ({kind})")


if __name__ == "__main__":
    asyncio.run(main())
