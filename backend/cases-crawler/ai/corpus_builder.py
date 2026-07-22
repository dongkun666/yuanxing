"""
LexPrime 法律语料库构建模块
============================

提供法律文本清洗、数据增强和标注工具集成功能。

支持 Mock 模式：当真实语料处理不可用时，返回模拟数据。
"""
from __future__ import annotations

import re
import uuid
import random
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

from loguru import logger


class CorpusType(str):
    """语料类型"""
    LEGAL_CASE = "legal_case"
    REGULATION = "regulation"
    CONTRACT = "contract"
    LEGAL_OPINION = "legal_opinion"
    ACADEMIC_PAPER = "academic_paper"


class DataAugmentationType(str):
    """数据增强类型"""
    SYNONYM_REPLACEMENT = "synonym_replacement"
    BACK_TRANSLATION = "back_translation"
    TEXT_NOISE = "text_noise"
    RANDOM_DELETION = "random_deletion"
    RANDOM_SWAP = "random_swap"
    CONTEXTUAL_INSERTION = "contextual_insertion"


@dataclass
class CorpusConfig:
    """语料库配置"""
    corpus_name: str = "legal_corpus_v1"
    corpus_type: str = "mixed"
    min_length: int = 50
    max_length: int = 10000
    language: str = "zh-CN"
    deduplicate: bool = True
    deduplicate_threshold: float = 0.95
    quality_filter: bool = True
    min_quality_score: float = 0.6
    enable_augmentation: bool = False
    augmentation_types: List[str] = field(default_factory=list)
    augmentation_ratio: float = 1.0
    chunk_size: int = 512
    chunk_overlap: int = 50
    split_by_sentence: bool = True


@dataclass
class CorpusDocument:
    """语料文档"""
    doc_id: str
    title: str
    content: str
    doc_type: str
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    token_count: int = 0
    created_at: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class CorpusDataset:
    """语料数据集"""
    dataset_id: str
    name: str
    description: str
    doc_count: int
    total_tokens: int
    doc_types: Dict[str, int]
    created_at: str
    updated_at: str
    status: str = "ready"
    split_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnnotationTask:
    """标注任务"""
    task_id: str
    dataset_id: str
    task_type: str
    total_items: int
    completed_items: int
    status: str
    assignees: List[str] = field(default_factory=list)
    created_at: str = ""
    deadline: str = ""


class CorpusBuilder:
    """法律语料库构建器

    提供完整的语料库构建流程：
    - 文本清洗和标准化
    - 质量评估和过滤
    - 去重处理
    - 数据增强
    - 分块和分片
    - 标注任务管理
    """

    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self._datasets: Dict[str, CorpusDataset] = {}
        self._documents: Dict[str, List[CorpusDocument]] = {}
        self._annotation_tasks: Dict[str, AnnotationTask] = {}
        self._init_mock_data()

    def _init_mock_data(self):
        """初始化 Mock 数据"""
        now = datetime.now().isoformat()

        self._datasets = {
            "ds-001": CorpusDataset(
                dataset_id="ds-001",
                name="法律案例语料库 v1.0",
                description="包含各类民商事、刑事、行政案例的裁判文书语料",
                doc_count=30000,
                total_tokens=150000000,
                doc_types={
                    "civil": 15000,
                    "criminal": 8000,
                    "administrative": 4000,
                    "commercial": 3000,
                },
                created_at="2026-05-01T10:00:00",
                updated_at="2026-06-15T14:30:00",
                status="ready",
                split_info={
                    "train": 27000,
                    "val": 2000,
                    "test": 1000,
                },
            ),
            "ds-002": CorpusDataset(
                dataset_id="ds-002",
                name="法律法规语料库 v1.0",
                description="国家法律法规、司法解释、部门规章等规范性文件",
                doc_count=15000,
                total_tokens=80000000,
                doc_types={
                    "law": 3000,
                    "regulation": 5000,
                    "judicial_interpretation": 2000,
                    "department_rule": 5000,
                },
                created_at="2026-05-10T09:00:00",
                updated_at="2026-06-20T11:00:00",
                status="ready",
                split_info={
                    "train": 13500,
                    "val": 1000,
                    "test": 500,
                },
            ),
            "ds-003": CorpusDataset(
                dataset_id="ds-003",
                name="合同模板语料库 v1.0",
                description="各类合同模板和范本，包含常用条款和风险点标注",
                doc_count=5000,
                total_tokens=25000000,
                doc_types={
                    "sales": 1000,
                    "labor": 800,
                    "lease": 700,
                    "service": 600,
                    "loan": 500,
                    "other": 1400,
                },
                created_at="2026-06-01T14:00:00",
                updated_at="2026-06-25T16:00:00",
                status="processing",
                split_info={},
            ),
        }

        self._annotation_tasks = {
            "at-001": AnnotationTask(
                task_id="at-001",
                dataset_id="ds-001",
                task_type="entity_linking",
                total_items=5000,
                completed_items=3200,
                status="in_progress",
                assignees=["lawyer_01", "lawyer_02", "lawyer_03"],
                created_at="2026-06-10T10:00:00",
                deadline="2026-07-10T23:59:59",
            ),
            "at-002": AnnotationTask(
                task_id="at-002",
                dataset_id="ds-003",
                task_type="risk_labeling",
                total_items=2000,
                completed_items=2000,
                status="completed",
                assignees=["lawyer_04", "lawyer_05"],
                created_at="2026-05-20T09:00:00",
                deadline="2026-06-20T23:59:59",
            ),
        }

    def list_datasets(self, status: Optional[str] = None) -> List[CorpusDataset]:
        """获取语料数据集列表

        Args:
            status: 按状态筛选

        Returns:
            数据集列表
        """
        datasets = list(self._datasets.values())

        if status:
            datasets = [d for d in datasets if d.status == status]

        datasets.sort(key=lambda x: x.updated_at, reverse=True)
        return datasets

    def get_dataset(self, dataset_id: str) -> Optional[CorpusDataset]:
        """获取数据集详情

        Args:
            dataset_id: 数据集 ID

        Returns:
            数据集信息，不存在则返回 None
        """
        return self._datasets.get(dataset_id)

    def create_dataset(self, name: str, description: str = "",
                       config: Optional[CorpusConfig] = None) -> CorpusDataset:
        """创建新的语料数据集

        Args:
            name: 数据集名称
            description: 数据集描述
            config: 语料配置

        Returns:
            创建的数据集
        """
        dataset_id = f"ds-{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        dataset = CorpusDataset(
            dataset_id=dataset_id,
            name=name,
            description=description,
            doc_count=0,
            total_tokens=0,
            doc_types={},
            created_at=now,
            updated_at=now,
            status="empty",
            split_info={},
        )

        self._datasets[dataset_id] = dataset
        self._documents[dataset_id] = []

        logger.info(f"Corpus dataset created: {dataset_id}, name={name}")
        return dataset

    def clean_text(self, text: str) -> str:
        """清洗法律文本

        Args:
            text: 原始文本

        Returns:
            清洗后的文本
        """
        if not text:
            return ""

        cleaned = text

        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned)
        cleaned = re.sub(r'\r\n?', '\n', cleaned)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = re.sub(r'[ \t]*\n[ \t]*', '\n', cleaned)

        cleaned = cleaned.strip()

        return cleaned

    def normalize_legal_text(self, text: str) -> str:
        """标准化法律文本

        Args:
            text: 原始文本

        Returns:
            标准化后的文本
        """
        if not text:
            return ""

        normalized = text

        normalized = re.sub(r'[〔［\[]', '〔', normalized)
        normalized = re.sub(r'[〕］\]]', '〕', normalized)
        normalized = re.sub(r'[（(]', '（', normalized)
        normalized = re.sub(r'[)）]', '）', normalized)

        normalized = re.sub(
            r'(\d{4})[年\-\.](\d{1,2})[月\-\.](\d{1,2})[日]?',
            r'\1年\2月\3日',
            normalized
        )

        normalized = re.sub(r'人民币\s*([\d,\.]+)\s*元', r'人民币\1元', normalized)

        return normalized

    def calculate_quality_score(self, text: str, doc_type: str = "general") -> float:
        """计算文本质量分数

        Args:
            text: 文本内容
            doc_type: 文档类型

        Returns:
            质量分数 (0-1)
        """
        if not text:
            return 0.0

        score = 0.0
        length = len(text)

        if length < 50:
            return 0.1
        elif length < 200:
            score += 0.15
        elif length < 1000:
            score += 0.25
        elif length < 5000:
            score += 0.3
        else:
            score += 0.25

        legal_keywords = [
            '原告', '被告', '法院', '判决', '合同', '法律', '规定', '条款',
            '证据', '诉讼', '权利', '义务', '责任', '赔偿', '违约', '效力',
        ]
        keyword_count = sum(1 for kw in legal_keywords if kw in text)
        score += min(0.3, keyword_count * 0.03)

        paragraph_count = text.count('\n\n') + 1
        if paragraph_count >= 3:
            score += 0.15
        elif paragraph_count >= 2:
            score += 0.1
        else:
            score += 0.05

        sentence_endings = text.count('。') + text.count('！') + text.count('？')
        if sentence_endings >= 10:
            score += 0.15
        elif sentence_endings >= 5:
            score += 0.1
        else:
            score += 0.05

        gibberish_patterns = [
            r'[a-zA-Z]{20,}',
            r'\d{20,}',
            r'(.)\1{10,}',
        ]
        for pattern in gibberish_patterns:
            if re.search(pattern, text):
                score -= 0.3
                break

        return max(0.0, min(1.0, score))

    def deduplicate_texts(self, texts: List[str],
                          threshold: float = 0.95) -> Tuple[List[str], List[int]]:
        """文本去重

        Args:
            texts: 文本列表
            threshold: 相似度阈值

        Returns:
            (去重后的文本列表, 保留的索引列表)
        """
        if not texts:
            return [], []

        if self.mock_mode:
            seen = set()
            unique_texts = []
            keep_indices = []

            for i, text in enumerate(texts):
                normalized = self._normalize_for_dedup(text)
                if normalized not in seen:
                    seen.add(normalized)
                    unique_texts.append(text)
                    keep_indices.append(i)

            return unique_texts, keep_indices

        return texts, list(range(len(texts)))

    def _normalize_for_dedup(self, text: str) -> str:
        """去重用的文本标准化"""
        normalized = re.sub(r'\s+', '', text)
        normalized = re.sub(r'[，。！？、；：""''（）《》【】]', '', normalized)
        return normalized.lower()

    def augment_text(self, text: str,
                     augmentation_types: Optional[List[str]] = None) -> List[str]:
        """数据增强 - 生成文本变体

        Args:
            text: 原始文本
            augmentation_types: 增强类型列表

        Returns:
            增强后的文本列表
        """
        if not text:
            return []

        aug_types = augmentation_types or [DataAugmentationType.SYNONYM_REPLACEMENT]
        augmented = []

        if DataAugmentationType.SYNONYM_REPLACEMENT in aug_types:
            aug_text = self._synonym_replacement(text)
            if aug_text != text:
                augmented.append(aug_text)

        if DataAugmentationType.RANDOM_DELETION in aug_types:
            aug_text = self._random_deletion(text)
            if aug_text != text:
                augmented.append(aug_text)

        if DataAugmentationType.RANDOM_SWAP in aug_types:
            aug_text = self._random_swap(text)
            if aug_text != text:
                augmented.append(aug_text)

        return augmented

    def _synonym_replacement(self, text: str) -> str:
        """同义词替换增强"""
        synonym_map = {
            "原告": "起诉方",
            "被告": "被诉方",
            "法院": "人民法院",
            "判决": "裁判",
            "合同": "协议",
            "规定": "约定",
            "赔偿": "补偿",
            "违约": "不履行约定义务",
            "证据": "证明材料",
            "诉讼": "起诉",
        }

        result = text
        for original, synonym in synonym_map.items():
            if random.random() < 0.3:
                result = result.replace(original, synonym)

        return result

    def _random_deletion(self, text: str, p: float = 0.05) -> str:
        """随机删除增强"""
        chars = list(text)
        chars = [c for c in chars if not (c.strip() and random.random() < p)]
        return ''.join(chars)

    def _random_swap(self, text: str, n: int = 2) -> str:
        """随机交换词增强"""
        words = re.split(r'(?<=[，。！？、；：])', text)
        if len(words) < 3:
            return text

        words = [w for w in words if w.strip()]
        if len(words) < 3:
            return text

        for _ in range(n):
            i, j = random.sample(range(len(words)), 2)
            words[i], words[j] = words[j], words[i]

        return ''.join(words)

    def chunk_text(self, text: str, chunk_size: int = 512,
                   chunk_overlap: int = 50) -> List[str]:
        """文本分块

        Args:
            text: 原始文本
            chunk_size: 每块大小（字符数）
            chunk_overlap: 块之间的重叠大小

        Returns:
            文本块列表
        """
        if not text:
            return []

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            if end >= len(text):
                chunks.append(text[start:])
                break

            chunk = text[start:end]

            last_sentence_end = max(
                chunk.rfind('。'),
                chunk.rfind('！'),
                chunk.rfind('？'),
                chunk.rfind('\n\n'),
            )

            if last_sentence_end > chunk_size * 0.5:
                end = start + last_sentence_end + 1
                chunk = text[start:end]

            chunks.append(chunk)
            start = end - chunk_overlap
            if start < 0:
                start = 0

        return chunks

    def extract_metadata(self, text: str, doc_type: str = "general") -> Dict[str, Any]:
        """提取文档元数据

        Args:
            text: 文档内容
            doc_type: 文档类型

        Returns:
            元数据字典
        """
        metadata = {
            "char_count": len(text),
            "line_count": text.count('\n') + 1,
            "paragraph_count": len([p for p in text.split('\n\n') if p.strip()]),
        }

        date_pattern = r'(\d{4})[年\-\.](\d{1,2})[月\-\.](\d{1,2})[日]?'
        dates = re.findall(date_pattern, text)
        if dates:
            metadata["dates"] = [f"{d[0]}-{d[1]}-{d[2]}" for d in dates[:5]]
            metadata["date_count"] = len(dates)

        court_pattern = r'([^，。；\n]*?(?:人民法院|中级人民法院|高级人民法院|最高人民法院))'
        courts = re.findall(court_pattern, text)
        if courts:
            metadata["courts"] = list(set(courts))[:5]
            metadata["court_count"] = len(set(courts))

        case_id_pattern = r'[〔\(（](\d{4})[〕\)）].{0,10}民初.{0,5}号'
        case_ids = re.findall(case_id_pattern, text)
        if case_ids:
            metadata["case_id_count"] = len(case_ids)

        legal_basis_pattern = r'《([^》]+)》'
        legal_bases = re.findall(legal_basis_pattern, text)
        if legal_bases:
            metadata["legal_references"] = list(set(legal_bases))[:10]
            metadata["legal_ref_count"] = len(set(legal_bases))

        party_pattern = r'(原告|被告|上诉人|被上诉人|申请人|被申请人)[：:]\s*([^\n，。；]+)'
        parties = re.findall(party_pattern, text)
        if parties:
            metadata["parties"] = [
                {"role": p[0], "name": p[1].strip()}
                for p in parties[:10]
            ]

        return metadata

    def add_documents(self, dataset_id: str,
                      documents: List[Dict[str, Any]],
                      config: Optional[CorpusConfig] = None) -> Dict[str, Any]:
        """批量添加文档到数据集

        Args:
            dataset_id: 数据集 ID
            documents: 文档列表
            config: 语料配置

        Returns:
            处理结果统计
        """
        if dataset_id not in self._datasets:
            raise ValueError(f"Dataset not found: {dataset_id}")

        cfg = config or CorpusConfig()
        processed = []
        skipped = 0

        for doc_data in documents:
            content = doc_data.get("content", "")
            cleaned = self.clean_text(content)

            if len(cleaned) < cfg.min_length:
                skipped += 1
                continue

            if cfg.quality_filter:
                quality_score = self.calculate_quality_score(
                    cleaned, doc_data.get("doc_type", "general")
                )
                if quality_score < cfg.min_quality_score:
                    skipped += 1
                    continue
            else:
                quality_score = 0.5

            normalized = self.normalize_legal_text(cleaned)
            metadata = self.extract_metadata(normalized, doc_data.get("doc_type", "general"))
            metadata.update(doc_data.get("metadata", {}))

            doc = CorpusDocument(
                doc_id=doc_data.get("doc_id") or f"doc-{uuid.uuid4().hex[:12]}",
                title=doc_data.get("title", "")[:200],
                content=normalized,
                doc_type=doc_data.get("doc_type", "general"),
                source=doc_data.get("source", ""),
                metadata=metadata,
                quality_score=quality_score,
                token_count=len(normalized) // 2,
                created_at=datetime.now().isoformat(),
                tags=doc_data.get("tags", []),
            )

            processed.append(doc)

        if cfg.deduplicate and processed:
            contents = [d.content for d in processed]
            _, keep_indices = self.deduplicate_texts(contents, cfg.deduplicate_threshold)
            processed = [processed[i] for i in keep_indices]

        if dataset_id not in self._documents:
            self._documents[dataset_id] = []

        self._documents[dataset_id].extend(processed)

        dataset = self._datasets[dataset_id]
        dataset.doc_count += len(processed)
        dataset.total_tokens += sum(d.token_count for d in processed)
        dataset.updated_at = datetime.now().isoformat()

        for doc in processed:
            doc_type = doc.doc_type
            dataset.doc_types[doc_type] = dataset.doc_types.get(doc_type, 0) + 1

        if dataset.status == "empty":
            dataset.status = "ready"

        logger.info(
            f"Added {len(processed)} documents to dataset {dataset_id}, "
            f"skipped {skipped}"
        )

        return {
            "added": len(processed),
            "skipped": skipped,
            "total_in_dataset": dataset.doc_count,
        }

    def list_annotation_tasks(self, status: Optional[str] = None) -> List[AnnotationTask]:
        """获取标注任务列表

        Args:
            status: 按状态筛选

        Returns:
            标注任务列表
        """
        tasks = list(self._annotation_tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks

    def get_annotation_task(self, task_id: str) -> Optional[AnnotationTask]:
        """获取标注任务详情

        Args:
            task_id: 任务 ID

        Returns:
            标注任务信息
        """
        return self._annotation_tasks.get(task_id)

    def create_annotation_task(self, dataset_id: str, task_type: str,
                               assignees: Optional[List[str]] = None,
                               deadline: str = "") -> AnnotationTask:
        """创建标注任务

        Args:
            dataset_id: 数据集 ID
            task_type: 任务类型
            assignees: 分配的标注人员
            deadline: 截止时间

        Returns:
            创建的标注任务
        """
        task_id = f"at-{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        dataset = self._datasets.get(dataset_id)
        total_items = dataset.doc_count // 10 if dataset else 1000

        task = AnnotationTask(
            task_id=task_id,
            dataset_id=dataset_id,
            task_type=task_type,
            total_items=total_items,
            completed_items=0,
            status="pending",
            assignees=assignees or [],
            created_at=now,
            deadline=deadline,
        )

        self._annotation_tasks[task_id] = task
        logger.info(f"Annotation task created: {task_id}, type={task_type}")
        return task


_builder_instance: Optional[CorpusBuilder] = None


def get_corpus_builder() -> CorpusBuilder:
    """获取语料库构建器单例"""
    global _builder_instance
    if _builder_instance is None:
        _builder_instance = CorpusBuilder(mock_mode=True)
    return _builder_instance
