"""
LexPrime 多模态处理模块
========================

提供 OCR 增强、文档理解、语音交互等多模态能力。

支持 Mock 模式：当真实多模态服务不可用时，返回模拟数据。
"""
from __future__ import annotations

import re
import time
import uuid
import base64
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger


class OCRMode(str, Enum):
    """OCR 模式"""
    GENERAL = "general"
    TABLE = "table"
    SEAL = "seal"
    HANDWRITING = "handwriting"
    LAYOUT = "layout"


class DocumentType(str, Enum):
    """文档类型"""
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    IMAGE = "image"
    SCANNED_PDF = "scanned_pdf"


class VoiceCommandType(str, Enum):
    """语音指令类型"""
    CASE_SEARCH = "case_search"
    DICTATION = "dictation"
    NAVIGATION = "navigation"
    REMINDER = "reminder"
    QUERY = "query"


@dataclass
class OCRResult:
    """OCR 识别结果"""
    text: str
    confidence: float
    page_count: int = 0
    tables: List[Dict[str, Any]] = field(default_factory=list)
    seals: List[Dict[str, Any]] = field(default_factory=list)
    handwriting_texts: List[Dict[str, Any]] = field(default_factory=list)
    layout_blocks: List[Dict[str, Any]] = field(default_factory=list)
    processing_time_ms: int = 0


@dataclass
class TableStructure:
    """表格结构"""
    table_id: str
    row_count: int
    col_count: int
    headers: List[str]
    rows: List[List[str]]
    confidence: float


@dataclass
class SealInfo:
    """印章信息"""
    seal_id: str
    seal_type: str
    seal_name: str
    position: Dict[str, int]
    confidence: float
    is_valid: bool


@dataclass
class DocumentStructure:
    """文档结构"""
    doc_id: str
    title: str
    doc_type: str
    page_count: int
    total_chars: int
    sections: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VoiceTranscription:
    """语音转文字结果"""
    text: str
    confidence: float
    duration_ms: int
    language: str
    segments: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class VoiceCommand:
    """语音指令解析结果"""
    command_type: str
    intent: str
    entities: Dict[str, Any]
    confidence: float
    raw_text: str


@dataclass
class TTSResult:
    """文字转语音结果"""
    audio_base64: str
    duration_ms: int
    text: str
    voice_name: str
    sample_rate: int


class MultimodalEngine:
    """多模态处理引擎

    提供完整的多模态处理能力：
    - OCR 增强（表格识别、印章识别、手写识别、版面分析）
    - 文档理解（PDF 结构提取、Word 解析、图片文字提取、图表理解）
    - 语音交互（ASR、TTS、语音指令识别）
    """

    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self._ocr_cache: Dict[str, OCRResult] = {}
        self._doc_cache: Dict[str, DocumentStructure] = {}
        self._processing_stats: Dict[str, int] = {
            "ocr_total": 0,
            "doc_parse_total": 0,
            "asr_total": 0,
            "tts_total": 0,
        }

    def ocr_recognize(self, image_data: str,
                      mode: OCRMode = OCRMode.GENERAL,
                      options: Optional[Dict[str, Any]] = None) -> OCRResult:
        """OCR 文字识别

        Args:
            image_data: 图片数据 (base64 或文件路径)
            mode: OCR 模式
            options: 额外选项

        Returns:
            OCR 识别结果
        """
        t0 = time.time()

        if self.mock_mode:
            result = self._mock_ocr(mode, options)
        else:
            result = OCRResult(
                text="",
                confidence=0.0,
                processing_time_ms=0,
            )

        result.processing_time_ms = int((time.time() - t0) * 1000)
        self._processing_stats["ocr_total"] += 1

        logger.info(
            f"OCR recognition: mode={mode.value}, "
            f"confidence={result.confidence}, "
            f"time={result.processing_time_ms}ms"
        )

        return result

    def _mock_ocr(self, mode: OCRMode,
                  options: Optional[Dict[str, Any]]) -> OCRResult:
        """Mock OCR 识别"""
        base_text = (
            "民事起诉状\n\n"
            "原告：张三，男，1985年1月15日出生，汉族，住北京市朝阳区XX路XX号。\n"
            "被告：李四，男，1982年3月20日出生，汉族，住北京市海淀区XX路XX号。\n\n"
            "诉讼请求：\n"
            "1. 判令被告返还借款本金人民币50万元；\n"
            "2. 判令被告支付借款利息（按年利率13.8%计算，自2025年1月1日起至实际给付之日止）；\n"
            "3. 本案诉讼费用由被告承担。\n\n"
            "事实与理由：\n"
            "原被告系朋友关系。2025年1月1日，被告因经营需要向原告借款人民币50万元，"
            "双方签订了借款合同，约定借款期限一年，年利率15%。借款到期后，"
            "原告多次催要，被告至今未还。为维护原告合法权益，特向贵院提起诉讼，"
            "请求依法判决。\n\n"
            "此致\n"
            "北京市朝阳区人民法院\n\n"
            "具状人：张三\n"
            "2026年1月15日"
        )

        tables = []
        seals = []
        handwriting_texts = []
        layout_blocks = []

        if mode == OCRMode.TABLE or mode == OCRMode.GENERAL:
            tables = [
                {
                    "table_id": "tbl-001",
                    "row_count": 4,
                    "col_count": 3,
                    "headers": ["序号", "项目", "金额（元）"],
                    "rows": [
                        ["1", "借款本金", "500,000.00"],
                        ["2", "利息", "69,000.00"],
                        ["3", "合计", "569,000.00"],
                    ],
                    "confidence": 0.92,
                },
            ]

        if mode == OCRMode.SEAL or mode == OCRMode.GENERAL:
            seals = [
                {
                    "seal_id": "seal-001",
                    "seal_type": "company_seal",
                    "seal_name": "北京某某科技有限公司",
                    "position": {"x": 450, "y": 1200, "width": 100, "height": 100},
                    "confidence": 0.95,
                    "is_valid": True,
                },
            ]

        if mode == OCRMode.HANDWRITING:
            handwriting_texts = [
                {
                    "text": "以上笔录我看过，与我说的一致",
                    "position": {"x": 100, "y": 800},
                    "confidence": 0.78,
                },
                {
                    "text": "张三",
                    "position": {"x": 400, "y": 850},
                    "confidence": 0.85,
                },
            ]

        if mode == OCRMode.LAYOUT or mode == OCRMode.GENERAL:
            layout_blocks = [
                {"type": "title", "content": "民事起诉状", "position": [150, 50, 350, 80]},
                {"type": "paragraph", "content": "原告基本信息", "position": [50, 100, 450, 140]},
                {"type": "paragraph", "content": "被告基本信息", "position": [50, 150, 450, 190]},
                {"type": "heading", "content": "诉讼请求", "position": [50, 210, 150, 230]},
                {"type": "list", "content": "诉讼请求列表", "position": [70, 240, 450, 320]},
                {"type": "heading", "content": "事实与理由", "position": [50, 340, 180, 360]},
                {"type": "paragraph", "content": "事实理由段落", "position": [50, 370, 450, 500]},
                {"type": "signature", "content": "签名区", "position": [350, 550, 450, 620]},
            ]

        confidence = 0.95
        if mode == OCRMode.HANDWRITING:
            confidence = 0.78
        elif mode == OCRMode.TABLE:
            confidence = 0.90
        elif mode == OCRMode.SEAL:
            confidence = 0.93

        return OCRResult(
            text=base_text,
            confidence=confidence,
            page_count=1,
            tables=tables,
            seals=seals,
            handwriting_texts=handwriting_texts,
            layout_blocks=layout_blocks,
        )

    def parse_document(self, file_path: str,
                       doc_type: Optional[DocumentType] = None,
                       options: Optional[Dict[str, Any]] = None) -> DocumentStructure:
        """解析文档结构

        Args:
            file_path: 文件路径
            doc_type: 文档类型
            options: 额外选项

        Returns:
            文档结构
        """
        t0 = time.time()

        if self.mock_mode:
            result = self._mock_document_parse(doc_type, options)
        else:
            result = DocumentStructure(
                doc_id="",
                title="",
                doc_type="",
                page_count=0,
                total_chars=0,
                sections=[],
                tables=[],
                images=[],
            )

        self._processing_stats["doc_parse_total"] += 1
        logger.info(f"Document parse: type={doc_type}, pages={result.page_count}")

        return result

    def _mock_document_parse(self, doc_type: Optional[DocumentType],
                             options: Optional[Dict[str, Any]]) -> DocumentStructure:
        """Mock 文档解析"""
        dt = doc_type.value if doc_type else DocumentType.PDF.value

        sections = [
            {
                "level": 1,
                "title": "第一条 合同双方",
                "content": "甲方：北京某某科技有限公司\n乙方：张三",
                "page": 1,
            },
            {
                "level": 1,
                "title": "第二条 服务内容",
                "content": "1. 服务项目：法律咨询服务\n2. 服务期限：一年",
                "page": 1,
            },
            {
                "level": 1,
                "title": "第三条 服务费用",
                "content": "服务费用：人民币50,000元整",
                "page": 2,
            },
            {
                "level": 1,
                "title": "第四条 违约责任",
                "content": "任何一方违约，应承担违约责任。",
                "page": 2,
            },
        ]

        tables = [
            {
                "table_id": "tbl-001",
                "title": "服务费用明细",
                "page": 2,
                "row_count": 4,
                "col_count": 3,
            },
        ]

        images = [
            {
                "image_id": "img-001",
                "type": "signature",
                "page": 3,
                "position": {"x": 350, "y": 500},
            },
        ]

        total_chars = 3000
        page_count = 3
        if dt == DocumentType.PDF.value:
            page_count = 5
            total_chars = 5000
        elif dt == DocumentType.WORD.value:
            page_count = 3
            total_chars = 3500
        elif dt == DocumentType.SCANNED_PDF.value:
            page_count = 8
            total_chars = 8000

        return DocumentStructure(
            doc_id=f"doc-{uuid.uuid4().hex[:8]}",
            title="法律服务合同",
            doc_type=dt,
            page_count=page_count,
            total_chars=total_chars,
            sections=sections,
            tables=tables,
            images=images,
            metadata={
                "author": "LexPrime",
                "created_at": "2026-01-01",
                "modified_at": "2026-06-01",
                "file_size": 1024000,
            },
        )

    def speech_to_text(self, audio_data: str,
                       language: str = "zh-CN",
                       options: Optional[Dict[str, Any]] = None) -> VoiceTranscription:
        """语音转文字 (ASR)

        Args:
            audio_data: 音频数据 (base64 或文件路径)
            language: 语言
            options: 额外选项

        Returns:
            语音转文字结果
        """
        t0 = time.time()

        if self.mock_mode:
            result = self._mock_asr(language, options)
        else:
            result = VoiceTranscription(
                text="",
                confidence=0.0,
                duration_ms=0,
                language=language,
            )

        self._processing_stats["asr_total"] += 1
        logger.info(f"ASR: language={language}, confidence={result.confidence}")

        return result

    def _mock_asr(self, language: str,
                  options: Optional[Dict[str, Any]]) -> VoiceTranscription:
        """Mock 语音转文字"""
        mock_texts = [
            "帮我检索一下最近的民间借贷案例",
            "我要审查这份合同有没有风险",
            "帮我写一份起诉状",
            "明天下午三点有个开庭提醒",
            "计算一下50万借款一年的利息",
        ]

        import random
        text = random.choice(mock_texts)

        segments = [
            {
                "start_ms": 0,
                "end_ms": 2000,
                "text": text,
                "confidence": 0.92,
            },
        ]

        return VoiceTranscription(
            text=text,
            confidence=0.92,
            duration_ms=2000,
            language=language,
            segments=segments,
        )

    def text_to_speech(self, text: str,
                       voice_name: str = "zh-CN-XiaoxiaoNeural",
                       speed: float = 1.0) -> TTSResult:
        """文字转语音 (TTS)

        Args:
            text: 要转换的文本
            voice_name: 音色名称
            speed: 语速

        Returns:
            TTS 结果
        """
        t0 = time.time()

        if self.mock_mode:
            result = TTSResult(
                audio_base64="",
                duration_ms=int(len(text) * 100 / speed),
                text=text,
                voice_name=voice_name,
                sample_rate=16000,
            )
        else:
            result = TTSResult(
                audio_base64="",
                duration_ms=0,
                text=text,
                voice_name=voice_name,
                sample_rate=16000,
            )

        self._processing_stats["tts_total"] += 1
        logger.info(f"TTS: voice={voice_name}, text_len={len(text)}")

        return result

    def parse_voice_command(self, text: str) -> VoiceCommand:
        """解析语音指令

        Args:
            text: 语音识别后的文本

        Returns:
            指令解析结果
        """
        text_lower = text.lower()

        command_type = "query"
        intent = "general_query"
        entities: Dict[str, Any] = {}
        confidence = 0.5

        if any(kw in text for kw in ["检索", "查找", "案例", "判例"]):
            command_type = VoiceCommandType.CASE_SEARCH.value
            intent = "search_cases"
            confidence = 0.85

            cause_match = re.search(r'(民间借贷|借款合同|买卖合同|劳动合同|离婚|继承)', text)
            if cause_match:
                entities["cause"] = cause_match.group(1)

        elif any(kw in text for kw in ["写", "起草", "生成", "起诉状", "答辩状", "合同"]):
            command_type = VoiceCommandType.DICTATION.value
            intent = "generate_document"
            confidence = 0.80

            if "起诉状" in text:
                entities["doc_type"] = "complaint"
            elif "答辩状" in text:
                entities["doc_type"] = "defense"
            elif "合同" in text:
                entities["doc_type"] = "contract"

        elif any(kw in text for kw in ["打开", "进入", "跳转到", "去"]):
            command_type = VoiceCommandType.NAVIGATION.value
            intent = "navigate"
            confidence = 0.75

            if "案例" in text:
                entities["target"] = "cases"
            elif "合同" in text:
                entities["target"] = "contracts"
            elif "日程" in text:
                entities["target"] = "schedule"

        elif any(kw in text for kw in ["提醒", "闹钟", "备忘", "记住"]):
            command_type = VoiceCommandType.REMINDER.value
            intent = "set_reminder"
            confidence = 0.80

            time_match = re.search(r'(\d+)点(\d*)分', text)
            if time_match:
                entities["hour"] = int(time_match.group(1))
                entities["minute"] = int(time_match.group(2) or 0)

        elif any(kw in text for kw in ["查询", "查一下", "搜索", "找"]):
            command_type = VoiceCommandType.QUERY.value
            intent = "search_query"
            confidence = 0.70

        return VoiceCommand(
            command_type=command_type,
            intent=intent,
            entities=entities,
            confidence=confidence,
            raw_text=text,
        )

    def extract_table_from_image(self, image_data: str) -> List[TableStructure]:
        """从图片中提取表格

        Args:
            image_data: 图片数据

        Returns:
            表格结构列表
        """
        ocr_result = self.ocr_recognize(image_data, mode=OCRMode.TABLE)

        tables = []
        for t in ocr_result.tables:
            tables.append(TableStructure(
                table_id=t.get("table_id", ""),
                row_count=t.get("row_count", 0),
                col_count=t.get("col_count", 0),
                headers=t.get("headers", []),
                rows=t.get("rows", []),
                confidence=t.get("confidence", 0.0),
            ))

        return tables

    def detect_seals(self, image_data: str) -> List[SealInfo]:
        """检测印章

        Args:
            image_data: 图片数据

        Returns:
            印章信息列表
        """
        ocr_result = self.ocr_recognize(image_data, mode=OCRMode.SEAL)

        seals = []
        for s in ocr_result.seals:
            seals.append(SealInfo(
                seal_id=s.get("seal_id", ""),
                seal_type=s.get("seal_type", ""),
                seal_name=s.get("seal_name", ""),
                position=s.get("position", {}),
                confidence=s.get("confidence", 0.0),
                is_valid=s.get("is_valid", True),
            ))

        return seals

    def analyze_layout(self, image_data: str) -> List[Dict[str, Any]]:
        """版面分析

        Args:
            image_data: 图片数据

        Returns:
            版面块列表
        """
        ocr_result = self.ocr_recognize(image_data, mode=OCRMode.LAYOUT)
        return ocr_result.layout_blocks

    def get_stats(self) -> Dict[str, Any]:
        """获取处理统计"""
        return {
            "ocr_total": self._processing_stats["ocr_total"],
            "doc_parse_total": self._processing_stats["doc_parse_total"],
            "asr_total": self._processing_stats["asr_total"],
            "tts_total": self._processing_stats["tts_total"],
            "supported_modes": [m.value for m in OCRMode],
            "supported_doc_types": [d.value for d in DocumentType],
            "supported_voices": [
                {"name": "zh-CN-XiaoxiaoNeural", "language": "zh-CN", "gender": "female"},
                {"name": "zh-CN-YunxiNeural", "language": "zh-CN", "gender": "male"},
            ],
        }


_multimodal_instance: Optional[MultimodalEngine] = None


def get_multimodal_engine() -> MultimodalEngine:
    """获取多模态引擎单例"""
    global _multimodal_instance
    if _multimodal_instance is None:
        _multimodal_instance = MultimodalEngine(mock_mode=True)
    return _multimodal_instance
