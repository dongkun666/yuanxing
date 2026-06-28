"""
cncases 判例数据导入器
2026-06-28 · 把 cncases/cases 仓库的 102GB ZIP 数据导入 LexPrime 数据库

数据格式 (cncases/lib.rs Case struct, CSV inside ZIP, GBK 编码, 中文列名):
    原始链接 / 案号 / 案件名称 / 法院 / 案件类型 / 审理程序 / 裁判日期 / 公开日期 /
    当事人 / 案由 / 法律依据 / 全文

使用:
    python -m importers.cncases_importer --raw-path /data/cncases --batch-size 5000
"""
import asyncio
import csv
import io
import os
import re
import zipfile
from pathlib import Path
from typing import Iterator, Optional
from datetime import date
from loguru import logger
from tqdm import tqdm

from core.db import Database, ESClient
from core.models import Case
from core.sanitize import (
    sanitize_full_text, html_to_plain,
    classify_cause, extract_year,
)
from core.config import settings


class CncasesImporter:
    """cncases 判例数据导入器"""

    def __init__(self, raw_path: str, batch_size: int = 5000):
        self.raw_path = Path(raw_path)
        self.batch_size = batch_size

        # 统计
        self.total = 0
        self.inserted = 0
        self.updated = 0
        self.failed = 0
        self.failed_docs = []

    def iter_zip_files(self) -> Iterator[Path]:
        """遍历 raw_data_path 下的所有 .zip 文件 (cncases 原始数据格式)"""
        if not self.raw_path.exists():
            logger.error(f"Path not found: {self.raw_path}")
            return

        for zip_path in sorted(self.raw_path.glob("**/*.zip")):
            logger.info(f"Found zip: {zip_path.name}")
            yield zip_path

    def iter_csv_in_zip(self, zip_path: Path) -> Iterator[dict]:
        """从 zip 中读取 CSV, 自动检测 GBK 编码"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for name in zf.namelist():
                    if not name.endswith('.csv'):
                        continue
                    with zf.open(name) as f:
                        # cncases 是 GBK 编码, 自动检测
                        try:
                            content = f.read()
                            text = content.decode('gbk', errors='replace')
                        except Exception as e:
                            logger.warning(f"GBK decode failed, trying UTF-8: {e}")
                            text = content.decode('utf-8', errors='replace')

                        reader = csv.DictReader(io.StringIO(text))
                        for row in reader:
                            yield row
        except Exception as e:
            logger.error(f"Failed to read zip {zip_path}: {e}")

    def parse_row(self, row: dict) -> Optional[dict]:
        """解析一行 CSV → Case dict, 字段对齐 cncases Case struct"""
        try:
            # 提取 doc_id (cncases docId 在 URL 末尾)
            doc_url = row.get("原始链接", "").strip()
            doc_id = doc_url.rsplit("=", 1)[-1] if "=" in doc_url else doc_url

            case_name = row.get("案件名称", "").strip()
            cause = row.get("案由", "").strip()
            cause_category, cause_color = classify_cause(cause)

            full_text = row.get("全文", "")
            full_text = sanitize_full_text(full_text)
            full_text_plain = html_to_plain(full_text)

            judgment_date_str = row.get("裁判日期", "").strip()
            judgment_date = None
            if judgment_date_str:
                try:
                    judgment_date = date.fromisoformat(judgment_date_str.replace("/", "-").replace(".", "-")[:10])
                except (ValueError, IndexError):
                    pass

            public_date_str = row.get("公开日期", "").strip()
            public_date = None
            if public_date_str:
                try:
                    public_date = date.fromisoformat(public_date_str.replace("/", "-").replace(".", "-")[:10])
                except (ValueError, IndexError):
                    pass

            return {
                "doc_id": doc_id,
                "case_id": row.get("案号", "").strip() or None,
                "case_name": case_name or None,
                "court": row.get("法院", "").strip() or None,
                "case_type": row.get("案件类型", "").strip() or None,
                "procedure": row.get("审理程序", "").strip() or None,
                "judgment_date": judgment_date,
                "public_date": public_date,
                "parties": row.get("当事人", "").strip() or None,
                "cause": cause or None,
                "cause_category": cause_category,
                "cause_color": cause_color,
                "legal_basis": row.get("法律依据", "").strip() or None,
                "full_text": full_text,
                "full_text_plain": full_text_plain,
                "source": "cncases",
                "source_url": doc_url,
                "year": extract_year(judgment_date_str),
            }
        except Exception as e:
            logger.warning(f"Parse row failed: {e}, doc={row.get('原始链接', 'unknown')[:50]}")
            self.failed += 1
            self.failed_docs.append(row.get("原始链接", "unknown")[:100])
            return None

    async def import_all(self):
        """导入所有 cncases 数据"""
        await Database.init()
        await ESClient.init()

        for zip_path in self.iter_zip_files():
            logger.info(f"Processing {zip_path.name}...")

            batch = []
            for row in tqdm(self.iter_csv_in_zip(zip_path), desc=f"Importing {zip_path.name[:20]}"):
                self.total += 1
                case_data = self.parse_row(row)
                if not case_data:
                    continue

                batch.append(case_data)
                if len(batch) >= self.batch_size:
                    await self._flush_batch(batch)
                    batch = []

            # 收尾
            if batch:
                await self._flush_batch(batch)

        await Database.close()
        await ESClient.close()

        # 报告
        logger.info(f"""
        ===== 导入完成 =====
        总行数: {self.total}
        新增: {self.inserted}
        更新: {self.updated}
        失败: {self.failed}
        """)

    async def _flush_batch(self, batch: list):
        """批量写入 PG + ES"""
        if not batch:
            return

        # 1. 写入 PostgreSQL
        try:
            async with Database.session() as session:
                for case_data in batch:
                    # 简单 upsert: 如果 doc_id 存在则更新, 不存在则插入
                    case = Case(**case_data)
                    session.add(case)
                await session.commit()
            self.inserted += len(batch)
        except Exception as e:
            logger.error(f"PG batch insert failed: {e}")
            self.failed += len(batch)

        # 2. 写入 Elasticsearch (异步, 失败不阻塞)
        try:
            es = ESClient.get()
            actions = []
            for case_data in batch:
                actions.append({"index": {"_index": settings.es_index_cases, "_id": case_data["doc_id"]}})
                # ES 文档 (去掉 full_text HTML, 只存 plain)
                es_doc = {**case_data, "full_text": case_data.get("full_text_plain", "")}
                es_doc.pop("full_text_plain", None)
                actions.append(es_doc)
            await es.bulk(operations=actions, refresh=False)
        except Exception as e:
            logger.warning(f"ES bulk failed (non-critical): {e}")


# CLI 入口
async def main():
    import argparse
    parser = argparse.ArgumentParser(description="LexPrime cncases 导入器")
    parser.add_argument("--raw-path", default=settings.cncases_raw_path, help="cncases 原始数据目录")
    parser.add_argument("--batch-size", type=int, default=settings.cncases_batch_size)
    parser.add_argument("--limit", type=int, default=0, help="限制导入条数 (测试用)")
    args = parser.parse_args()

    importer = CncasesImporter(args.raw_path, args.batch_size)
    await importer.import_all()


if __name__ == "__main__":
    asyncio.run(main())
