"""
cncases 导入监控 (文件到达 → 自动触发导入)
2026-06-28 · 任务 1 配套

功能:
- 监控下载目录, ZIP 文件到达自动触发 cncases_importer
- 进度: 总大小 / 已下载 / 预计剩余时间
- 完成后自动启动导入

用法:
    python scripts/monitor_cncases.py --watch-dir E:/data/cncases
"""
import asyncio
import argparse
import os
import sys
import time
from pathlib import Path
from loguru import logger


def get_zip_stats(watch_dir: Path):
    """统计 ZIP 文件状态"""
    if not watch_dir.exists():
        return None

    zips = sorted(watch_dir.glob("**/*.zip"))
    if not zips:
        return None

    total_size = 0
    complete = []
    partial = []
    for z in zips:
        size = z.stat().st_size
        total_size += size
        if size > 0:
            complete.append(z)
        else:
            partial.append(z)

    return {
        "total_zips": len(zips),
        "complete_zips": len(complete),
        "partial_zips": len(partial),
        "total_size_gb": total_size / 1024**3,
        "complete": complete,
        "partial": partial,
    }


async def monitor(watch_dir: str, threshold_complete: int = 5, check_interval: int = 60):
    """监控下载目录"""
    watch_path = Path(watch_dir)
    watch_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"监控目录: {watch_path}")
    logger.info(f"完成阈值: {threshold_complete} 个 ZIP 触发导入")
    logger.info(f"检查间隔: {check_interval}s")
    logger.info(f"按 Ctrl+C 停止")

    last_total = 0
    last_time = 0
    imported = False

    try:
        while True:
            stats = get_zip_stats(watch_path)
            now = time.time()

            if stats is None:
                logger.info(f"[{now:.0f}] 等待 ZIP 文件...")
            else:
                # 速度估算
                if last_time > 0:
                    delta_size = stats["total_size_gb"] - last_total
                    delta_time = now - last_time
                    speed_mb = (delta_size * 1024) / delta_time if delta_time > 0 else 0
                else:
                    speed_mb = 0
                last_total = stats["total_size_gb"]
                last_time = now

                logger.info(
                    f"[{now:.0f}] "
                    f"ZIP: {stats['complete_zips']}/{stats['total_zips']} | "
                    f"大小: {stats['total_size_gb']:.2f} GB | "
                    f"速度: {speed_mb:.1f} MB/s"
                )

                # 完成阈值触发
                if not imported and stats["complete_zips"] >= threshold_complete:
                    logger.info(f"✓ 达到 {threshold_complete} 个 ZIP, 触发自动导入...")
                    await trigger_import(watch_path)
                    imported = True

            await asyncio.sleep(check_interval)

    except KeyboardInterrupt:
        logger.info("停止监控")


async def trigger_import(watch_path: Path):
    """触发 cncases 导入"""
    import subprocess
    project_root = Path(__file__).parent.parent
    cmd = [
        sys.executable, "-m", "importers.cncases_importer",
        "--raw-path", str(watch_path),
        "--batch-size", "5000"
    ]
    logger.info(f"执行: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=86400)
        logger.info(f"导入完成: returncode={result.returncode}")
        if result.returncode != 0:
            logger.error(f"stderr: {result.stderr[:500]}")
    except subprocess.TimeoutExpired:
        logger.error("导入超时 (>24h)")
    except Exception as e:
        logger.error(f"导入失败: {e}")


async def main():
    parser = argparse.ArgumentParser(description="cncases 导入监控器")
    parser.add_argument("--watch-dir", default="E:/data/cncases", help="下载目录")
    parser.add_argument("--threshold-complete", type=int, default=5, help="完成 ZIP 阈值, 触发导入")
    parser.add_argument("--interval", type=int, default=60, help="检查间隔 (秒)")
    args = parser.parse_args()

    await monitor(args.watch_dir, args.threshold_complete, args.interval)


if __name__ == "__main__":
    asyncio.run(main())
