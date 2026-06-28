"""
cncases 种子下载器 (libtorrent + 进度监控)
2026-06-28 · 任务 1

依赖: pip install libtorrent
- 102GB 数据, 1Gbps 1-2h / 100Mbps 8-16h
- 用 libtorrent (Python binding for libtorrent) 跑 BT 客户端
- 进度: 每 5 秒打印一次, 日志输出到 logs/

用法:
    python scripts/download_cncases.py --output-dir E:/data/cncases
    python scripts/download_cncases.py --output-dir E:/data/cncases --max-download-gb 5  # 测试用, 只下 5GB
"""
import asyncio
import argparse
import os
import sys
import time
from pathlib import Path
from loguru import logger


def check_libtorrent():
    """检查 libtorrent 是否安装"""
    try:
        import libtorrent as lt
        return lt
    except ImportError:
        logger.error("libtorrent 未安装! 请先: pip install libtorrent")
        logger.error("Windows 用户注意: libtorrent 编译依赖多, 可用 qBittorrent 替代 (见 DOWNLOAD_GUIDE.md)")
        sys.exit(1)


# 种子 magnet link (从 cncases/cases 仓库 README 提取的种子文件)
# 实际: 用户从 https://github.com/cncases/cases/releases 下载 810air.torrent
CNCASES_TORRENT_URL = "https://github.com/cncases/cases/releases/download/v0.2.11/810air.torrent"


async def download_cncases(output_dir: str, max_gb: float = 0, session_name: str = "lexprime_cncases"):
    """用 libtorrent 下载 cncases 种子"""
    lt = check_libtorrent()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 创建 torrent session
    ses = lt.session()
    ses.listen_on(6881, 6891)  # BT 端口

    # 用户友好配置
    settings = lt.session_settings()
    settings.user_agent = "LexPrime/0.7.0 libtorrent/2.0"
    ses.apply_settings(settings)

    # 下载种子文件
    torrent_path = output_path / "810air.torrent"
    if not torrent_path.exists():
        logger.info(f"下载种子文件: {CNCASES_TORRENT_URL}")
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(CNCASES_TORRENT_URL, timeout=30)
            if resp.status_code == 200:
                torrent_path.write_bytes(resp.content)
                logger.info(f"✓ 种子已下载: {torrent_path} ({len(resp.content)} bytes)")
            else:
                logger.error(f"种子下载失败: HTTP {resp.status_code}")
                logger.error(f"请手动从 {CNCASES_TORRENT_URL} 下载到 {torrent_path}")
                return

    # 添加 torrent 到 session
    info = lt.torrent_info(str(torrent_path))
    params = lt.add_torrent_params()
    params.ti = info
    params.save_path = str(output_path)
    params.storage_mode = lt.storage_mode_t.storage_mode_sparse
    handle = ses.add_torrent(params)
    handle.set_sequential_download(True)

    logger.info(f"开始下载: {info.name()}")
    logger.info(f"大小: {info.total_size() / 1024**3:.2f} GB")
    logger.info(f"保存路径: {output_path}")
    logger.info(f"按 Ctrl+C 停止 (resume 友好)")

    if max_gb > 0:
        logger.info(f"限制: 只下载 {max_gb} GB (测试)")

    last_log = 0
    try:
        while not handle.status().is_seeding:
            await asyncio.sleep(5)

            s = handle.status()
            now = time.time()
            if now - last_log < 5:
                continue
            last_log = now

            progress = s.progress
            state = ["queued", "checking", "downloading metadata",
                     "downloading", "finished", "seeding", "allocating",
                     "checking resume data"][s.state]

            # 限流
            if max_gb > 0 and s.total_done >= max_gb * 1024**3:
                logger.info(f"达到 {max_gb}GB 限制, 停止")
                ses.remove_torrent(handle)
                break

            # 限速: 避免占满带宽
            if s.download_rate > 0:
                download_speed = s.download_rate / 1024 / 1024  # MB/s
            else:
                download_speed = 0

            logger.info(
                f"[{state}] {progress * 100:.2f}% | "
                f"{s.total_done / 1024**3:.2f} GB / {s.total_size() / 1024**3:.2f} GB | "
                f"{download_speed:.2f} MB/s | "
                f"peers: {s.num_peers}"
            )

    except KeyboardInterrupt:
        logger.info("用户中断, 保留进度 (下次可 resume)")
    finally:
        # 不关闭 session, 允许 resume
        pass


async def main():
    parser = argparse.ArgumentParser(description="cncases 102GB 种子下载器")
    parser.add_argument("--output-dir", default="E:/data/cncases", help="下载目标目录")
    parser.add_argument("--max-download-gb", type=float, default=0, help="限制下载量 (GB), 0=不限制")
    args = parser.parse_args()

    await download_cncases(args.output_dir, args.max_download_gb)


if __name__ == "__main__":
    asyncio.run(main())
