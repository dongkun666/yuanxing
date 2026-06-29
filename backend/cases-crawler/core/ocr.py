"""
LexPrime OCR 引擎 — 统一抽象 (W5 Track B + W7 升级)

设计:
- PaddleOcrEngine: 真实 PaddleOCR (PP-OCRv6 中文专精, 兼容 v2.7+)
- MockOcrEngine:   开发/测试用 mock, 不依赖 paddlepaddle
- 自动按环境变量 LEX_OCR_ENGINE 切换 (auto | paddle | mock, 默认 auto)

W5 范围 (W3 license.py 的 OCR mock 迁移):
- W3: auth/license.py 的 _run_ocr_mock 只处理图片
- W5: 本模块支持图片 (PNG/JPG/JPEG) + PDF (含扫描件)
- W5: 返回 OcrResult 含 raw_text + 平均 confidence + 段位 lines (供 reviewer 用)

W7 升级 (plan-07-w7-yaml § 1):
- 创建 backend/venv312/ (Python 3.12.7 embeddable) — paddlepaddle wheel 不支持 3.14
- 装 paddlepaddle==3.3.1 + paddleocr==3.7.0 + numpy 2.x (3.x API 兼容)
- PaddleOcrEngine 兼容 PaddleOCR 2.7 (legacy) + 3.7 (current) 双 API:
    * 2.7: PaddleOCR(use_angle_cls=True, lang='ch').ocr(arr) → [[(bbox, (text, conf)), ...]]
    * 3.7: PaddleOCR(use_doc_orientation_classify=False, ..., lang='ch').predict(arr) → [dict{rec_texts, rec_scores, rec_polys, ...}]
- 自动 detect API 版本, 兼容两种 output 格式
- onednn 在 Paddle 3.x 默认开, 但 PP-OCRv6 有 dtype bug, 自动 FLAGS_use_mkldnn=0

生产部署 (W7 venv312):
    # 1. 创建 Python 3.12 隔离 venv (embeddable 已就位)
    #    backend/venv312/python.exe 已存在 (Python 3.12.7)
    # 2. pip 引导:
    #    backend/venv312/python.exe backend/venv312/get-pip.py
    # 3. 装 paddle 套件:
    #    backend/venv312/python.exe -m pip install paddlepaddle==3.3.1 paddleocr==3.7.0
    # 4. 模型自动下载到 ~/.paddlex/official_models/ (第一次推理时)
    # 5. 启动 backend 时:
    #    set LEX_OCR_ENGINE=paddle
    #    set PYTHONPATH=backend/venv312/Lib/site-packages  # 让 3.14 主进程找到 paddle 套件
    #    或: 在 .env 写 LEX_OCR_ENGINE=paddle + 用 venv312 直接启 uvicorn

参考:
- PRD §5.4 Skill Hub + Track B (B-ocr.md) PaddleOCR
- PaddleOCR 3.0+ 文档: https://github.com/PaddlePaddle/PaddleOCR
- T-REF-15/16 借鉴: 用统一 Tool 抽象层 (本模块即 OCR Tool)
"""
from __future__ import annotations

import io
import os
import re
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Protocol, runtime_checkable, Tuple, Dict, Any


# 抑制 Paddle 3.x onednn 在 PP-OCRv6 上的 dtype bug (ValueError ... DoubleAttribute)
# 必须在 import paddle 之前设置
os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("FLAGS_use_onednn", "0")


# ===== 数据结构 =====

@dataclass
class OcrLine:
    """单行 OCR 识别结果 (含 bounding box + 置信度)"""

    text: str
    confidence: float
    bbox: Optional[List[List[float]]] = None  # 4 点坐标 (PaddleOCR 标准)


@dataclass
class OcrResult:
    """OCR 识别结果 (整个文件维度)"""

    raw_text: str
    confidence: float  # 平均置信度 (0-1)
    lines: List[OcrLine] = field(default_factory=list)
    page_count: int = 1
    source_engine: str = "unknown"  # "paddle" | "mock" | "tesseract"
    detected_mime: str = ""  # "image/png" | "application/pdf" | ...

    def to_dict(self) -> dict:
        return {
            "raw_text": self.raw_text,
            "confidence": round(self.confidence, 4),
            "page_count": self.page_count,
            "source_engine": self.source_engine,
            "detected_mime": self.detected_mime,
            "line_count": len(self.lines),
        }


# ===== 异常 =====

class OcrError(Exception):
    """OCR 引擎执行失败 (底层)"""

    code = "ocr_error"


class OcrUnsupportedFormatError(OcrError):
    code = "ocr_unsupported_format"


class OcrEngineUnavailableError(OcrError):
    """指定的 engine (如 paddle) 不可用 (缺依赖)"""

    code = "ocr_engine_unavailable"


# ===== 引擎接口 =====

@runtime_checkable
class OcrEngine(Protocol):
    """OCR 引擎抽象 (T-REF-15 Tool 抽象层思想)"""

    name: str

    def is_available(self) -> bool:
        """检查依赖是否就位 (用于 auto 模式)"""

    def run(
        self,
        file_bytes: bytes,
        filename: str = "",
        mime_type: str = "",
    ) -> OcrResult:
        """执行 OCR

        Args:
            file_bytes: 文件二进制 (PNG/JPG/PDF 等)
            filename:   文件名 (用于 mime 推断 + mock 启发)
            mime_type:  显式 MIME (可选, 缺则从 filename 推断)

        Returns:
            OcrResult
        """


# ===== 工具函数 =====

_IMAGE_MAGIC = {
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"BM": "image/bmp",
    b"RIFF": "image/webp",  # RIFF + WEBP
}
_PDF_MAGIC = b"%PDF-"


def detect_mime(file_bytes: bytes, filename: str = "") -> str:
    """推断文件 MIME (基于 magic bytes, 优先于扩展名)"""
    if not file_bytes:
        return "application/octet-stream"
    head = file_bytes[:16]
    for magic, mime in _IMAGE_MAGIC.items():
        if head.startswith(magic):
            return mime
    if head.startswith(_PDF_MAGIC):
        return "application/pdf"
    # fallback: 扩展名
    ext = Path(filename).suffix.lower() if filename else ""
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
    }.get(ext, "application/octet-stream")


def is_pdf(data: bytes) -> bool:
    return data.startswith(_PDF_MAGIC)


def is_image(data: bytes) -> bool:
    return any(data.startswith(m) for m in _IMAGE_MAGIC)


# ===== PaddleOCR 引擎 (生产) =====

def _detect_paddle_api_version() -> Tuple[int, str]:
    """探测 PaddleOCR 主版本 + API 风格

    Returns:
        (major, api_style) — api_style ∈ {"v2", "v3"}
        - v2: PaddleOCR 2.x, 使用 .ocr(arr, cls=...) 返回 [[(bbox, (text, conf)), ...]]
        - v3: PaddleOCR 3.x, 使用 .predict(arr) 返回 [dict{rec_texts, rec_scores, rec_polys}]
    """
    try:
        import paddleocr  # noqa: F401
    except ImportError:
        return (0, "none")
    try:
        ver = getattr(paddleocr, "__version__", "0.0.0")
        major = int(ver.split(".")[0]) if ver and ver[0].isdigit() else 0
    except Exception:
        major = 0
    if major >= 3:
        return (major, "v3")
    if major == 2:
        return (major, "v2")
    return (major, "unknown")


class PaddleOcrEngine:
    """真实 PaddleOCR 引擎 (懒加载)

    依赖 (W7 venv312):
        paddlepaddle==3.3.1
        paddleocr==3.7.0  (PP-OCRv6 中文模型, 自动下载到 ~/.paddlex/)
        numpy 2.x (Paddle 3.x 兼容)
        PyMuPDF (fitz) for PDF
        Pillow for image

    兼容:
        PaddleOCR 2.7 (legacy, paddlepaddle 2.6.x) — 仍可工作
        PaddleOCR 3.x (current, paddlepaddle 3.x) — 主推
        自动 detect API 版本, 内部二选一

    第一次调用时下载模型到 ~/.paddlex/official_models/
    """

    name = "paddle"

    def __init__(self, lang: str = "ch", use_angle_cls: bool = True):
        self._lang = lang
        self._use_angle_cls = use_angle_cls
        self._engine = None
        self._init_error: Optional[str] = None
        self._api_version: int = 0
        self._api_style: str = "unknown"

    def is_available(self) -> bool:
        try:
            import paddleocr  # noqa: F401
            self._api_version, self._api_style = _detect_paddle_api_version()
            return True
        except ImportError as e:
            self._init_error = f"paddleocr not installed: {e}"
            return False

    def _get_engine(self):
        """懒加载 PaddleOCR 实例 (兼容 v2 / v3 API)"""
        if self._engine is not None:
            return self._engine
        if self._init_error:
            raise OcrEngineUnavailableError(self._init_error)
        try:
            from paddleocr import PaddleOCR
        except ImportError as e:
            self._init_error = f"paddleocr not installed: {e}"
            raise OcrEngineUnavailableError(self._init_error) from e
        try:
            self._api_version, self._api_style = _detect_paddle_api_version()
            if self._api_style == "v3":
                # PaddleOCR 3.x API
                self._engine = PaddleOCR(
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=self._use_angle_cls,
                    lang=self._lang,
                    device="cpu",
                    enable_mkldnn=False,  # W7: 避免 PP-OCRv6 dtype bug
                    show_log=False,
                )
            else:
                # PaddleOCR 2.x API (legacy)
                self._engine = PaddleOCR(
                    use_angle_cls=self._use_angle_cls,
                    lang=self._lang,
                    show_log=False,
                )
        except Exception as e:
            self._init_error = f"PaddleOCR init failed: {e}"
            raise OcrEngineUnavailableError(self._init_error) from e
        return self._engine

    def run(
        self,
        file_bytes: bytes,
        filename: str = "",
        mime_type: str = "",
    ) -> OcrResult:
        if not file_bytes:
            raise OcrUnsupportedFormatError("empty file_bytes")

        mime = mime_type or detect_mime(file_bytes, filename)
        engine = self._get_engine()

        if is_pdf(file_bytes):
            return self._run_pdf(engine, file_bytes, mime)
        if is_image(file_bytes):
            return self._run_image(engine, file_bytes, mime)

        raise OcrUnsupportedFormatError(
            f"unsupported mime for PaddleOCR: {mime}"
        )

    def _run_image(self, engine, file_bytes: bytes, mime: str) -> OcrResult:
        try:
            import numpy as np
            from PIL import Image
        except ImportError as e:
            raise OcrEngineUnavailableError(
                f"numpy/Pillow required for image OCR: {e}"
            ) from e

        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        arr = np.array(img)
        if self._api_style == "v3":
            raw = engine.predict(arr)
        else:
            raw = engine.ocr(arr, cls=self._use_angle_cls)
        return self._parse_paddle_result(raw, mime=mime, page_count=1)

    def _run_pdf(self, engine, file_bytes: bytes, mime: str) -> OcrResult:
        """PDF → 多页图像 → 逐页 OCR"""
        try:
            import numpy as np
            from PIL import Image
            import fitz  # PyMuPDF
        except ImportError as e:
            raise OcrEngineUnavailableError(
                f"PyMuPDF required for PDF OCR: {e}"
            ) from e

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        all_lines: List[OcrLine] = []
        all_text_parts: List[str] = []
        page_count = len(doc)
        for page_idx in range(page_count):
            page = doc[page_idx]
            mat = fitz.Matrix(2.0, 2.0)  # 2x 缩放提高识别率
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            arr = np.array(img)
            if self._api_style == "v3":
                raw = engine.predict(arr)
            else:
                raw = engine.ocr(arr, cls=self._use_angle_cls)
            page_result = self._parse_paddle_result(
                raw, mime=mime, page_count=1
            )
            all_lines.extend(page_result.lines)
            if page_result.raw_text:
                all_text_parts.append(page_result.raw_text)
        doc.close()
        if not all_lines:
            return OcrResult(
                raw_text="",
                confidence=0.0,
                lines=[],
                page_count=page_count,
                source_engine=self.name,
                detected_mime=mime,
            )
        avg_conf = sum(line.confidence for line in all_lines) / len(all_lines)
        return OcrResult(
            raw_text="\n\n".join(all_text_parts),
            confidence=avg_conf,
            lines=all_lines,
            page_count=page_count,
            source_engine=self.name,
            detected_mime=mime,
        )

    def _parse_paddle_result(
        self, raw, mime: str, page_count: int
    ) -> OcrResult:
        """PaddleOCR 输出格式兼容:
        - v2: [[(bbox, (text, conf)), ...]] (嵌套 list, 每页一段)
        - v3: [dict{rec_texts: [str], rec_scores: [float], rec_polys: [arr], ...}]
        """
        if self._api_style == "v3":
            return self._parse_paddle_v3(raw, mime, page_count)
        return self._parse_paddle_v2(raw, mime, page_count)

    @staticmethod
    def _parse_paddle_v2(
        raw, mime: str, page_count: int
    ) -> OcrResult:
        """PaddleOCR 2.7 输出格式: [[(bbox, (text, conf)), ...]]"""
        lines: List[OcrLine] = []
        text_parts: List[str] = []
        for page_result in raw or []:
            if not page_result:
                continue
            for item in page_result:
                if not item or len(item) < 2:
                    continue
                bbox, (text, conf) = item[0], item[1]
                if not text:
                    continue
                lines.append(OcrLine(
                    text=str(text),
                    confidence=float(conf) if conf else 0.0,
                    bbox=[[float(p[0]), float(p[1])] for p in bbox]
                    if bbox else None,
                ))
                text_parts.append(str(text))
        if not lines:
            return OcrResult(
                raw_text="",
                confidence=0.0,
                lines=[],
                page_count=page_count,
                source_engine="paddle",
                detected_mime=mime,
            )
        avg_conf = sum(line.confidence for line in lines) / len(lines)
        return OcrResult(
            raw_text="\n".join(text_parts),
            confidence=avg_conf,
            lines=lines,
            page_count=page_count,
            source_engine="paddle",
            detected_mime=mime,
        )

    @staticmethod
    def _parse_paddle_v3(
        raw, mime: str, page_count: int
    ) -> OcrResult:
        """PaddleOCR 3.x 输出格式: [dict{rec_texts, rec_scores, rec_polys}]"""
        lines: List[OcrLine] = []
        text_parts: List[str] = []
        for page_result in raw or []:
            if not isinstance(page_result, dict):
                continue
            rec_texts = page_result.get("rec_texts") or []
            rec_scores = page_result.get("rec_scores") or []
            rec_polys = page_result.get("rec_polys") or []
            for idx, text in enumerate(rec_texts):
                if not text:
                    continue
                conf = float(rec_scores[idx]) if idx < len(rec_scores) else 0.0
                bbox = None
                if idx < len(rec_polys):
                    try:
                        poly = rec_polys[idx]
                        bbox = [[float(p[0]), float(p[1])] for p in poly]
                    except Exception:
                        bbox = None
                lines.append(OcrLine(
                    text=str(text),
                    confidence=conf,
                    bbox=bbox,
                ))
                text_parts.append(str(text))
        if not lines:
            return OcrResult(
                raw_text="",
                confidence=0.0,
                lines=[],
                page_count=page_count,
                source_engine="paddle",
                detected_mime=mime,
            )
        avg_conf = sum(line.confidence for line in lines) / len(lines)
        return OcrResult(
            raw_text="\n".join(text_parts),
            confidence=avg_conf,
            lines=lines,
            page_count=page_count,
            source_engine="paddle",
            detected_mime=mime,
        )


# ===== Mock 引擎 (开发/测试) =====

class MockOcrEngine:
    """Mock OCR 引擎 (W3 license.py 启发式规则复用 + 扩展)

    规则:
    - 文件名包含 "test_ocr" + 编号 → 返回 fixture 文本
    - 否则按文件大小生成 1 段假合同文本 (保证可测试)
    - 不依赖任何外部库 (numpy/paddle)
    """

    name = "mock"

    # 5 张测试样张 (W5 验收要求)
    FIXTURES = {
        "test_ocr_1": (
            "房屋租赁合同\n\n"
            "第一条 租赁标的\n甲方将位于北京市朝阳区建国路 88 号的房屋出租给乙方使用。\n\n"
            "第二条 租赁期限\n租赁期限为 12 个月, 自 2026 年 1 月 1 日起至 2026 年 12 月 31 日止。\n\n"
            "第三条 租金及支付\n月租金为人民币 8000 元整, 乙方应于每月 5 日前支付当月租金。\n\n"
            "第四条 违约责任\n乙方逾期支付租金的, 每逾期一日按月租金 5% 加收违约金。\n"
            "甲方不得单方解除合同, 违反本条无效。\n",
            0.92,
        ),
        "test_ocr_2": (
            "借款合同\n\n"
            "出借人: 张三 (身份证号 110101199003078811)\n借款人: 李四 (手机 13812345678)\n\n"
            "借款金额: 人民币 500000 元整\n借款期限: 2026 年 3 月 1 日至 2027 年 3 月 1 日\n年利率: 24%\n\n"
            "争议管辖: 出借人住所地人民法院",
            0.88,
        ),
        "test_ocr_3": (
            "服务合同\n\n"
            "甲方 (委托方): 北京某科技公司\n乙方 (受托方): 上海某咨询公司\n\n"
            "服务内容: 战略咨询服务\n服务期限: 6 个月\n服务费用: 人民币 200000 元\n\n"
            "排他义务: 乙方在服务期内不得为甲方竞争对手提供同类服务。\n"
            "配合义务: 甲方应配合乙方提供必要资料。",
            0.85,
        ),
        "test_ocr_4": (
            "劳动合同\n\n"
            "甲方 (用人单位): 深圳某科技公司\n乙方 (劳动者): 王五\n\n"
            "工作岗位: 高级工程师\n合同期限: 3 年 (2026 年 6 月 1 日至 2029 年 5 月 31 日)\n"
            "月薪: 30000 元\n\n"
            "甲方可单方解除本合同, 提前 30 日通知即可。",
            0.90,
        ),
        "test_ocr_5": (
            "销售合同\n\n"
            "卖方: 广州某制造公司\n买方: 北京某贸易公司\n\n"
            "标的物: 工业设备 100 台\n单价: 5000 元/台\n总金额: 500000 元\n\n"
            "交付时间: 2026 年 7 月 15 日前\n"
            "争议管辖: 卖方所在地法院",
            0.87,
        ),
    }

    def is_available(self) -> bool:
        return True

    def run(
        self,
        file_bytes: bytes,
        filename: str = "",
        mime_type: str = "",
    ) -> OcrResult:
        if not file_bytes:
            raise OcrUnsupportedFormatError("empty file_bytes")

        mime = mime_type or detect_mime(file_bytes, filename)

        # 1) fixture 命中 (test_ocr_1 ~ test_ocr_5)
        for key, (text, conf) in self.FIXTURES.items():
            if key in filename:
                return OcrResult(
                    raw_text=text,
                    confidence=conf,
                    lines=[
                        OcrLine(text=line, confidence=conf)
                        for line in text.splitlines() if line
                    ],
                    page_count=1,
                    source_engine=self.name,
                    detected_mime=mime,
                )

        # 2) 通用启发 (兼容 W3 license.py 的 _run_ocr_mock 行为)
        # 文件名启发 license_no / 关键词
        license_match = re.search(
            r"((?:[A-Z0-9]{2,6}[-/]?\d{4}[-/]?[A-Z]?\d{3,8}))",
            filename.upper(),
        )
        size_kb = len(file_bytes) / 1024
        confidence = min(0.95, max(0.50, size_kb / 1024))

        if license_match:
            raw_text = (
                f"律师执业证\n姓名: 王律师\n执业证号: {license_match.group(1)}\n"
                f"执业机构: 北京市某律师事务所\n"
            )
        else:
            # 通用合同: 基于文件 size 哈希生成稳定文本
            digest = hashlib.md5(file_bytes).hexdigest()[:8].upper()
            raw_text = (
                f"合同草案 #{digest}\n\n"
                "第一条 合作内容\n甲乙双方就本合同标的进行合作。\n\n"
                "第二条 双方权利义务\n"
                "甲方应按约定支付合作费用。\n乙方应按约定提供产品/服务。\n\n"
                "第三条 违约责任\n任何一方违约的, 应承担违约责任。\n\n"
                "第四条 争议解决\n因本合同发生的争议, 由双方协商解决。\n"
            )

        return OcrResult(
            raw_text=raw_text,
            confidence=confidence,
            lines=[
                OcrLine(text=line, confidence=confidence)
                for line in raw_text.splitlines() if line
            ],
            page_count=1,
            source_engine=self.name,
            detected_mime=mime,
        )


# ===== Engine factory =====

_ENGINE_INSTANCE: Optional[OcrEngine] = None
_ENGINE_NAME: Optional[str] = None


def _select_engine() -> OcrEngine:
    """按 env 选引擎

    LEX_OCR_ENGINE:
        auto (默认): paddle 可用 → paddle, 否则 mock
        paddle:      强制 paddle, 不可用 raise
        mock:        强制 mock
    """
    requested = os.getenv("LEX_OCR_ENGINE", "auto").lower().strip()
    if requested == "mock":
        return MockOcrEngine()
    if requested == "paddle":
        paddle = PaddleOcrEngine()
        if not paddle.is_available():
            raise OcrEngineUnavailableError(
                "LEX_OCR_ENGINE=paddle 但 paddleocr 未安装。"
                "请 pip install paddleocr paddlepaddle (Python 3.11/3.12 venv)"
            )
        return paddle
    # auto
    paddle = PaddleOcrEngine()
    if paddle.is_available():
        return paddle
    return MockOcrEngine()


def get_ocr_engine() -> OcrEngine:
    """获取 OCR 引擎 (单例 + 懒加载)"""
    global _ENGINE_INSTANCE, _ENGINE_NAME
    requested = os.getenv("LEX_OCR_ENGINE", "auto").lower().strip()
    if _ENGINE_INSTANCE is None or _ENGINE_NAME != requested:
        _ENGINE_NAME = requested
        _ENGINE_INSTANCE = _select_engine()
    return _ENGINE_INSTANCE


def reset_ocr_engine() -> None:
    """重置引擎单例 (测试用)"""
    global _ENGINE_INSTANCE, _ENGINE_NAME
    _ENGINE_INSTANCE = None
    _ENGINE_NAME = None


def is_paddle_available() -> bool:
    """PaddleOCR 是否可用 (供 health check)"""
    return PaddleOcrEngine().is_available()


def current_engine_name() -> str:
    """当前生效的引擎名 (供 health check)"""
    try:
        return get_ocr_engine().name
    except Exception as e:
        return f"unavailable: {e}"


# ===== 单元自测 =====

if __name__ == "__main__":
    # 5 张样张自测
    engine = get_ocr_engine()
    print(f"[ocr] engine = {engine.name}")
    for i in range(1, 6):
        result = engine.run(
            file_bytes=b"fake-image-bytes-for-test",
            filename=f"test_ocr_{i}.png",
        )
        print(f"\n[ocr] test_ocr_{i}: {result.confidence:.2f} conf, "
              f"{len(result.lines)} lines")
        print(f"  first line: {result.lines[0].text if result.lines else '(empty)'}")


# ===== W7 升级: Paddle 3.x onednn 抑制 =====
# (在 _detect_paddle_api_version() 已 import paddleocr 之前 os.environ.setdefault 设置)
# 这里再次显式设置 (防止 import 顺序问题)
os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("FLAGS_use_onednn", "0")

