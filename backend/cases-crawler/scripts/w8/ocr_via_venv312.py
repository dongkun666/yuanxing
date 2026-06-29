"""
W8 D4: venv312 OCR 子进程脚本 (lex-ai)

W8 D4 升级: W5 时代 Python 3.14 paddlepaddle wheel 装不上 (W5 final report §3),
主进程 (Python 3.14) 跑 OCR 必须走 fallback。本脚本作为 venv312 (Python 3.12)
子进程, 把 PaddleEngine OCR 结果通过 stdout JSON 返回给主进程。

协议:
- argv[1]: PNG/PDF 文件路径 (主进程先把 bytes 写文件, 避免 base64 编码损耗)
- stdout: JSON { ok, engine, raw_text, confidence, lines, page_count, detected_mime, error? }

依赖: backend/venv312/python.exe + paddlepaddle 3.3.1 + paddleocr 3.7.0

用法:
    venv312/python.exe scripts/w8/ocr_via_venv312.py <png_or_pdf_path>
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Paddle 3.x onednn 抑制 (PP-OCRv6 dtype bug)
os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("FLAGS_use_onednn", "0")


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "missing file path"}))
        return 1
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(json.dumps({"ok": False, "error": f"file not found: {file_path}"}))
        return 1

    # 把 cases-crawler 加到 sys.path, 让 core.ocr 可 import
    cases_crawler = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(cases_crawler))

    try:
        from core.ocr import get_ocr_engine, OcrError  # noqa: E402
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"import core.ocr failed: {e}"}))
        return 1

    try:
        engine = get_ocr_engine()
        file_bytes = file_path.read_bytes()
        result = engine.run(file_bytes, filename=file_path.name)
        out = {
            "ok": True,
            "engine": result.source_engine,
            "raw_text": result.raw_text,
            "confidence": round(result.confidence, 4),
            "lines": [
                {"text": ln.text, "confidence": round(ln.confidence, 4)}
                for ln in result.lines
            ],
            "line_count": len(result.lines),
            "page_count": result.page_count,
            "detected_mime": result.detected_mime,
        }
        print(json.dumps(out, ensure_ascii=False))
        return 0
    except OcrError as e:
        print(json.dumps({"ok": False, "error": f"OcrError: {e}"}))
        return 2
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(json.dumps({"ok": False, "error": f"unexpected: {e!r}"}))
        return 3


if __name__ == "__main__":
    sys.exit(main())