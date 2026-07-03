"""
LexPrime RAG 引擎优化模块
==========================

提供向量检索优化、知识库质量优化和上下文压缩功能。

支持 Mock 模式：当真实 RAG 服务不可用时，返回模拟数据。
"""
from __future__ import annotations

import re
import time
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger


class RetrievalMode(str, Enum):
    """检索模式"""
    VECTOR_ONLY = "vector_only"
    KEYWORD_ONLY = "keyword_only"
    HYBRID = "hybrid"


class ChunkStrategy(str, Enum):
    """分块策略"""
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SEMANTIC = "semantic"
    RECURSIVE = "recursive"


class RerankingModel(str, Enum):
    """重排序模型"""
    BGE_RERANKER = "bge-reranker"
    CROSS_ENCODER = "cross-encoder"
    LLMRERANK = "llm-rerank"


@dataclass
class RAGConfig:
    """RAG 配置"""
    retrieval_mode: RetrievalMode = RetrievalMode.HYBRID
    top_k: int = 10
    hybrid_weight: float = 0.7
    enable_reranking: bool = True
    reranking_model: RerankingModel = RerankingModel.BGE_RERANKER
    rerank_top_k: int = 5
    chunk_strategy: ChunkStrategy = ChunkStrategy.RECURSIVE
    chunk_size: int = 512
    chunk_overlap: int = 50
    enable_context_compression: bool = True
    max_context_tokens: int = 4000
    enable_kg_enhancement: bool = False
    enable_metadata_filter: bool = True
    embedding_model: str = "lexprime-embedding-v1"


@dataclass
class RetrievedChunk:
    """检索到的文本块"""
    chunk_id: str
    doc_id: str
    doc_title: str
    doc_type: str
    content: str
    score: float
    vector_score: float = 0.0
    keyword_score: float = 0.0
    rerank_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_page: Optional[int] = None


@dataclass
class CompressedContext:
    """压缩后的上下文"""
    original_chunks: int
    compressed_tokens: int
    original_tokens: int
    compression_ratio: float
    relevant_snippets: List[Dict[str, Any]]
    summary: str


@dataclass
class KnowledgeBaseStats:
    """知识库统计信息"""
    total_docs: int
    total_chunks: int
    total_tokens: int
    doc_types: Dict[str, int]
    avg_chunk_size: float
    last_updated: str
    embedding_status: str


@dataclass
class RetrievalEvaluation:
    """检索效果评估"""
    query: str
    retrieved_count: int
    relevant_count: int
    precision: float
    recall: float
    f1_score: float
    mrr: float
    ndcg: float
    avg_latency_ms: float


class RAGEngine:
    """RAG 引擎

    提供完整的 RAG 优化能力：
    - 混合检索（向量 + 关键词）
    - 重排序
    - 多种分块策略
    - 文档解析增强
    - 元数据提取
    - 知识图谱增强
    - 上下文压缩
    - 相关片段提取
    - 摘要压缩
    """

    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self._config = RAGConfig()
        self._knowledge_bases: Dict[str, Dict[str, Any]] = {}
        self._retrieval_history: List[Dict[str, Any]] = []
        self._init_mock_data()

    def _init_mock_data(self):
        """初始化 Mock 数据"""
        self._knowledge_bases = {
            "default": {
                "name": "默认知识库",
                "description": "LexPrime 默认法律知识库",
                "total_docs": 50000,
                "total_chunks": 200000,
                "total_tokens": 100000000,
                "doc_types": {
                    "cases": 30000,
                    "laws": 15000,
                    "contracts": 5000,
                },
                "avg_chunk_size": 480,
                "last_updated": "2026-07-01T10:00:00",
                "embedding_status": "ready",
                "chunk_strategy": "recursive",
                "chunk_size": 512,
            },
            "contract_review": {
                "name": "合同审查知识库",
                "description": "专门用于合同审查的知识库",
                "total_docs": 10000,
                "total_chunks": 50000,
                "total_tokens": 25000000,
                "doc_types": {
                    "contracts": 5000,
                    "contract_templates": 3000,
                    "risk_cases": 2000,
                },
                "avg_chunk_size": 500,
                "last_updated": "2026-06-25T14:30:00",
                "embedding_status": "ready",
                "chunk_strategy": "semantic",
                "chunk_size": 600,
            },
        }

    def get_config(self) -> RAGConfig:
        """获取当前 RAG 配置"""
        return self._config

    def update_config(self, config: Dict[str, Any]) -> RAGConfig:
        """更新 RAG 配置

        Args:
            config: 配置更新字典

        Returns:
            更新后的配置
        """
        for key, value in config.items():
            if hasattr(self._config, key):
                if key in ('retrieval_mode',) and isinstance(value, str):
                    try:
                        setattr(self._config, key, RetrievalMode(value))
                    except ValueError:
                        pass
                elif key in ('reranking_model',) and isinstance(value, str):
                    try:
                        setattr(self._config, key, RerankingModel(value))
                    except ValueError:
                        pass
                elif key in ('chunk_strategy',) and isinstance(value, str):
                    try:
                        setattr(self._config, key, ChunkStrategy(value))
                    except ValueError:
                        pass
                else:
                    setattr(self._config, key, value)

        logger.info(f"RAG config updated")
        return self._config

    def hybrid_search(self, query: str,
                      knowledge_base: str = "default",
                      top_k: Optional[int] = None,
                      filters: Optional[Dict[str, Any]] = None) -> List[RetrievedChunk]:
        """混合检索

        结合向量检索和关键词检索，返回综合排序结果。

        Args:
            query: 查询文本
            knowledge_base: 知识库名称
            top_k: 返回数量
            filters: 过滤条件

        Returns:
            检索到的文本块列表
        """
        t0 = time.time()

        k = top_k or self._config.top_k

        vector_results = self._vector_search(query, knowledge_base, k * 2, filters)
        keyword_results = self._keyword_search(query, knowledge_base, k * 2, filters)

        if self._config.retrieval_mode == RetrievalMode.VECTOR_ONLY:
            results = vector_results[:k]
        elif self._config.retrieval_mode == RetrievalMode.KEYWORD_ONLY:
            results = keyword_results[:k]
        else:
            results = self._merge_hybrid_results(vector_results, keyword_results, k)

        if self._config.enable_reranking and len(results) > 0:
            results = self._rerank(query, results)

        results = results[:k]

        latency_ms = int((time.time() - t0) * 1000)
        self._retrieval_history.append({
            "query": query,
            "results_count": len(results),
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat(),
        })

        logger.info(
            f"Hybrid search: query='{query[:50]}...', "
            f"results={len(results)}, latency={latency_ms}ms"
        )

        return results

    def _vector_search(self, query: str, knowledge_base: str,
                       top_k: int, filters: Optional[Dict[str, Any]]) -> List[RetrievedChunk]:
        """向量检索（Mock）"""
        if self.mock_mode:
            return self._mock_vector_results(query, top_k, knowledge_base)
        return []

    def _keyword_search(self, query: str, knowledge_base: str,
                        top_k: int, filters: Optional[Dict[str, Any]]) -> List[RetrievedChunk]:
        """关键词检索（Mock）"""
        if self.mock_mode:
            return self._mock_keyword_results(query, top_k, knowledge_base)
        return []

    def _mock_vector_results(self, query: str, top_k: int,
                             knowledge_base: str) -> List[RetrievedChunk]:
        """生成 Mock 向量检索结果"""
        results = []
        query_hash = hash(query)

        mock_docs = [
            {
                "title": "中华人民共和国民法典",
                "type": "law",
                "content_prefix": "第五百七十七条 当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
            },
            {
                "title": "张三诉李四借款合同纠纷案",
                "type": "case",
                "content_prefix": "本院认为，合法的借贷关系受法律保护。被告李四向原告张三借款的事实，有借条、转账记录等证据予以证实，本院予以确认。",
            },
            {
                "title": "买卖合同司法解释",
                "type": "law",
                "content_prefix": "第一条 当事人之间没有书面合同，一方以送货单、收货单、结算单、发票等主张存在买卖合同关系的，人民法院应当结合当事人之间的交易方式、交易习惯以及其他相关证据，对买卖合同是否成立作出认定。",
            },
            {
                "title": "房屋租赁合同纠纷案例",
                "type": "case",
                "content_prefix": "关于房屋租赁合同的解除问题，根据《民法典》第七百二十二条规定，承租人无正当理由未支付或者迟延支付租金的，出租人可以请求承租人在合理期限内支付。",
            },
            {
                "title": "劳动合同法实施条例",
                "type": "law",
                "content_prefix": "第十九条 有下列情形之一的，依照劳动合同法规定的条件、程序，用人单位可以与劳动者解除固定期限劳动合同、无固定期限劳动合同或者以完成一定工作任务为期限的劳动合同。",
            },
        ]

        for i in range(min(top_k, len(mock_docs))):
            idx = (query_hash + i) % len(mock_docs)
            doc = mock_docs[idx]
            score = 0.95 - i * 0.08 + (query_hash % 100) / 1000

            results.append(RetrievedChunk(
                chunk_id=f"vec-{uuid.uuid4().hex[:8]}",
                doc_id=f"doc-{idx:04d}",
                doc_title=doc["title"],
                doc_type=doc["type"],
                content=doc["content_prefix"],
                score=score,
                vector_score=score,
                keyword_score=0.0,
                metadata={"source": "vector_search", "position": i},
            ))

        return sorted(results, key=lambda x: x.vector_score, reverse=True)

    def _mock_keyword_results(self, query: str, top_k: int,
                              knowledge_base: str) -> List[RetrievedChunk]:
        """生成 Mock 关键词检索结果"""
        results = []
        query_hash = hash(query + "_kw")

        mock_docs = [
            {
                "title": "合同违约赔偿标准",
                "type": "legal_opinion",
                "content_prefix": "合同违约赔偿的范围包括直接损失和可得利益损失。根据《民法典》第五百八十四条规定，当事人一方不履行合同义务或者履行合同义务不符合约定，造成对方损失的，损失赔偿额应当相当于因违约所造成的损失。",
            },
            {
                "title": "民间借贷利息计算",
                "type": "legal_opinion",
                "content_prefix": "民间借贷的利率可以适当高于银行的利率，但最高不得超过银行同类贷款利率的四倍（包含利率本数）。超出此限度的，超出部分的利息不予保护。",
            },
            {
                "title": "诉讼时效规定",
                "type": "law",
                "content_prefix": "向人民法院请求保护民事权利的诉讼时效期间为三年。法律另有规定的，依照其规定。诉讼时效期间自权利人知道或者应当知道权利受到损害以及义务人之日起计算。",
            },
        ]

        for i in range(min(top_k, len(mock_docs))):
            idx = (query_hash + i) % len(mock_docs)
            doc = mock_docs[idx]
            score = 0.90 - i * 0.10 + (query_hash % 80) / 1000

            results.append(RetrievedChunk(
                chunk_id=f"kw-{uuid.uuid4().hex[:8]}",
                doc_id=f"doc-kw-{idx:04d}",
                doc_title=doc["title"],
                doc_type=doc["type"],
                content=doc["content_prefix"],
                score=score,
                vector_score=0.0,
                keyword_score=score,
                metadata={"source": "keyword_search", "position": i},
            ))

        return sorted(results, key=lambda x: x.keyword_score, reverse=True)

    def _merge_hybrid_results(self, vector_results: List[RetrievedChunk],
                              keyword_results: List[RetrievedChunk],
                              top_k: int) -> List[RetrievedChunk]:
        """合并混合检索结果"""
        weight = self._config.hybrid_weight
        merged: Dict[str, RetrievedChunk] = {}

        for chunk in vector_results:
            merged[chunk.doc_id] = RetrievedChunk(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                doc_title=chunk.doc_title,
                doc_type=chunk.doc_type,
                content=chunk.content,
                score=chunk.vector_score * weight,
                vector_score=chunk.vector_score,
                keyword_score=0.0,
                metadata=chunk.metadata,
            )

        for chunk in keyword_results:
            if chunk.doc_id in merged:
                existing = merged[chunk.doc_id]
                existing.keyword_score = chunk.keyword_score
                existing.score = existing.vector_score * weight + chunk.keyword_score * (1 - weight)
            else:
                merged[chunk.doc_id] = RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    doc_title=chunk.doc_title,
                    doc_type=chunk.doc_type,
                    content=chunk.content,
                    score=chunk.keyword_score * (1 - weight),
                    vector_score=0.0,
                    keyword_score=chunk.keyword_score,
                    metadata=chunk.metadata,
                )

        results = sorted(merged.values(), key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _rerank(self, query: str, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """重排序（Mock）"""
        if not chunks:
            return chunks

        for i, chunk in enumerate(chunks):
            base_score = chunk.score
            query_terms = set(re.findall(r'[\u4e00-\u9fa5]+', query))
            content_terms = set(re.findall(r'[\u4e00-\u9fa5]+', chunk.content))

            overlap = len(query_terms & content_terms)
            overlap_ratio = overlap / max(len(query_terms), 1)

            rerank_score = base_score * 0.6 + overlap_ratio * 0.4
            chunk.rerank_score = rerank_score
            chunk.score = rerank_score

        reranked = sorted(chunks, key=lambda x: x.rerank_score, reverse=True)
        return reranked[:self._config.rerank_top_k]

    def chunk_document(self, content: str,
                       strategy: Optional[ChunkStrategy] = None,
                       chunk_size: Optional[int] = None,
                       chunk_overlap: Optional[int] = None) -> List[Dict[str, Any]]:
        """文档分块

        Args:
            content: 文档内容
            strategy: 分块策略
            chunk_size: 块大小
            chunk_overlap: 重叠大小

        Returns:
            分块结果列表
        """
        strat = strategy or self._config.chunk_strategy
        size = chunk_size or self._config.chunk_size
        overlap = chunk_overlap or self._config.chunk_overlap

        if strat == ChunkStrategy.FIXED_SIZE:
            chunks = self._chunk_fixed_size(content, size, overlap)
        elif strat == ChunkStrategy.SENTENCE:
            chunks = self._chunk_by_sentence(content, size, overlap)
        elif strat == ChunkStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraph(content, size, overlap)
        elif strat == ChunkStrategy.SEMANTIC:
            chunks = self._chunk_semantic(content, size, overlap)
        elif strat == ChunkStrategy.RECURSIVE:
            chunks = self._chunk_recursive(content, size, overlap)
        else:
            chunks = self._chunk_fixed_size(content, size, overlap)

        return [
            {
                "chunk_index": i,
                "content": chunk,
                "char_count": len(chunk),
                "token_count": len(chunk) // 2,
            }
            for i, chunk in enumerate(chunks)
        ]

    def _chunk_fixed_size(self, content: str, size: int, overlap: int) -> List[str]:
        """固定大小分块"""
        if not content:
            return []

        chunks = []
        start = 0

        while start < len(content):
            end = start + size
            if end >= len(content):
                chunks.append(content[start:])
                break
            chunks.append(content[start:end])
            start = end - overlap

        return chunks

    def _chunk_by_sentence(self, content: str, size: int, overlap: int) -> List[str]:
        """按句子分块"""
        if not content:
            return []

        sentences = re.split(r'(?<=[。！？])', content)
        sentences = [s for s in sentences if s.strip()]

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sent_len = len(sentence)

            if current_length + sent_len > size and current_chunk:
                chunks.append(''.join(current_chunk))
                overlap_text = ''.join(current_chunk[-2:]) if len(current_chunk) >= 2 else ''
                current_chunk = [overlap_text] if overlap_text else []
                current_length = len(overlap_text)

            current_chunk.append(sentence)
            current_length += sent_len

        if current_chunk:
            chunks.append(''.join(current_chunk))

        return chunks

    def _chunk_by_paragraph(self, content: str, size: int, overlap: int) -> List[str]:
        """按段落分块"""
        if not content:
            return []

        paragraphs = re.split(r'\n\s*\n', content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para_len = len(para)

            if current_length + para_len > size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_length = para_len
            else:
                current_chunk.append(para)
                current_length += para_len

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def _chunk_semantic(self, content: str, size: int, overlap: int) -> List[str]:
        """语义分块（Mock）"""
        return self._chunk_by_sentence(content, size, overlap)

    def _chunk_recursive(self, content: str, size: int, overlap: int) -> List[str]:
        """递归分块"""
        chunks = self._chunk_by_paragraph(content, size, overlap)

        result = []
        for chunk in chunks:
            if len(chunk) <= size:
                result.append(chunk)
            else:
                sub_chunks = self._chunk_by_sentence(chunk, size, overlap)
                result.extend(sub_chunks)

        return result

    def compress_context(self, query: str, chunks: List[RetrievedChunk],
                         max_tokens: Optional[int] = None) -> CompressedContext:
        """上下文压缩

        Args:
            query: 查询文本
            chunks: 检索到的文本块
            max_tokens: 最大 token 数

        Returns:
            压缩后的上下文
        """
        max_tok = max_tokens or self._config.max_context_tokens

        if not chunks:
            return CompressedContext(
                original_chunks=0,
                compressed_tokens=0,
                original_tokens=0,
                compression_ratio=0.0,
                relevant_snippets=[],
                summary="",
            )

        original_tokens = sum(len(c.content) // 2 for c in chunks)
        relevant_snippets = []

        for chunk in chunks:
            snippet = self._extract_relevant_snippet(query, chunk.content)
            if snippet:
                relevant_snippets.append({
                    "doc_id": chunk.doc_id,
                    "doc_title": chunk.doc_title,
                    "snippet": snippet,
                    "relevance_score": chunk.score,
                })

        compressed_text = '\n\n'.join([s["snippet"] for s in relevant_snippets])
        compressed_tokens = len(compressed_text) // 2

        while compressed_tokens > max_tok and len(relevant_snippets) > 1:
            relevant_snippets.pop()
            compressed_text = '\n\n'.join([s["snippet"] for s in relevant_snippets])
            compressed_tokens = len(compressed_text) // 2

        summary = self._generate_summary(query, relevant_snippets)

        compression_ratio = 1.0 - (compressed_tokens / max(original_tokens, 1))

        return CompressedContext(
            original_chunks=len(chunks),
            compressed_tokens=compressed_tokens,
            original_tokens=original_tokens,
            compression_ratio=round(compression_ratio, 4),
            relevant_snippets=relevant_snippets,
            summary=summary,
        )

    def _extract_relevant_snippet(self, query: str, content: str,
                                  window_size: int = 200) -> str:
        """提取相关片段"""
        if not content:
            return ""

        query_terms = re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', query)
        if not query_terms:
            return content[:window_size * 2]

        best_pos = 0
        best_score = 0

        for i in range(0, len(content) - window_size, window_size // 2):
            window = content[i:i + window_size]
            score = sum(1 for term in query_terms if term in window)
            if score > best_score:
                best_score = score
                best_pos = i

        start = max(0, best_pos - 50)
        end = min(len(content), best_pos + window_size + 50)
        snippet = content[start:end]

        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def _generate_summary(self, query: str, snippets: List[Dict[str, Any]]) -> str:
        """生成摘要（Mock）"""
        if not snippets:
            return ""

        doc_titles = list(set(s["doc_title"] for s in snippets[:5]))
        snippet_count = len(snippets)

        summary = (
            f"针对「{query[:30]}」的查询，"
            f"从 {snippet_count} 个相关片段中提取了关键信息，"
            f"涉及 {len(doc_titles)} 份文档。"
            f"主要来源包括：{', '.join(doc_titles[:3])} 等。"
        )

        return summary

    def extract_metadata(self, content: str, doc_type: str = "general") -> Dict[str, Any]:
        """提取文档元数据

        Args:
            content: 文档内容
            doc_type: 文档类型

        Returns:
            元数据字典
        """
        metadata = {
            "char_count": len(content),
            "word_count": len(re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', content)),
            "paragraph_count": len([p for p in re.split(r'\n\s*\n', content) if p.strip()]),
            "language": "zh-CN",
        }

        date_pattern = r'(\d{4})[年\-\.](\d{1,2})[月\-\.](\d{1,2})[日]?'
        dates = re.findall(date_pattern, content)
        if dates:
            metadata["dates"] = [f"{d[0]}-{d[1]}-{d[2]}" for d in dates[:10]]
            metadata["date_count"] = len(dates)

        legal_ref_pattern = r'《([^》]+)》'
        legal_refs = re.findall(legal_ref_pattern, content)
        if legal_refs:
            metadata["legal_references"] = list(set(legal_refs))[:20]
            metadata["legal_ref_count"] = len(set(legal_refs))

        case_id_pattern = r'[〔\(（](\d{4})[〕\)）][^案号]{0,20}(?:民初|民终|刑初|刑终|行初|行终).{0,10}号'
        case_ids = re.findall(case_id_pattern, content)
        if case_ids:
            metadata["case_id_count"] = len(case_ids)

        court_pattern = r'([^，。；\n]*?(?:人民法院|中级人民法院|高级人民法院|最高人民法院))'
        courts = re.findall(court_pattern, content)
        if courts:
            metadata["courts"] = list(set(courts))[:10]

        party_pattern = r'(原告|被告|上诉人|被上诉人|申请人|被申请人)[：:]\s*([^\n，。；]+)'
        parties = re.findall(party_pattern, content)
        if parties:
            metadata["parties"] = [{"role": p[0], "name": p[1].strip()} for p in parties[:10]]

        return metadata

    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """获取知识库列表"""
        return list(self._knowledge_bases.values())

    def get_knowledge_base(self, name: str) -> Optional[Dict[str, Any]]:
        """获取知识库详情"""
        return self._knowledge_bases.get(name)

    def get_kb_stats(self, name: str = "default") -> Optional[KnowledgeBaseStats]:
        """获取知识库统计"""
        kb = self._knowledge_bases.get(name)
        if not kb:
            return None

        return KnowledgeBaseStats(
            total_docs=kb["total_docs"],
            total_chunks=kb["total_chunks"],
            total_tokens=kb["total_tokens"],
            doc_types=kb["doc_types"],
            avg_chunk_size=kb["avg_chunk_size"],
            last_updated=kb["last_updated"],
            embedding_status=kb["embedding_status"],
        )

    def evaluate_retrieval(self, queries: List[Dict[str, Any]],
                           knowledge_base: str = "default") -> List[RetrievalEvaluation]:
        """评估检索效果

        Args:
            queries: 测试查询列表，每个包含 query 和 expected_doc_ids
            knowledge_base: 知识库名称

        Returns:
            评估结果列表
        """
        results = []

        for test_case in queries:
            query = test_case.get("query", "")
            expected = set(test_case.get("expected_doc_ids", []))

            t0 = time.time()
            retrieved = self.hybrid_search(query, knowledge_base=knowledge_base)
            latency_ms = int((time.time() - t0) * 1000)

            retrieved_ids = set(r.doc_id for r in retrieved)

            if expected:
                relevant = len(retrieved_ids & expected)
                precision = relevant / max(len(retrieved_ids), 1)
                recall = relevant / max(len(expected), 1)
                f1 = 2 * precision * recall / max(precision + recall, 1e-9)
            else:
                relevant = 0
                precision = 0.0
                recall = 0.0
                f1 = 0.0

            mrr = 0.0
            for rank, chunk in enumerate(retrieved, 1):
                if chunk.doc_id in expected:
                    mrr = 1.0 / rank
                    break

            dcg = 0.0
            for rank, chunk in enumerate(retrieved, 1):
                if chunk.doc_id in expected:
                    dcg += 1.0 / (rank.bit_length())

            idcg = sum(1.0 / (i.bit_length()) for i in range(1, min(len(expected), len(retrieved)) + 1))
            ndcg = dcg / max(idcg, 1e-9)

            results.append(RetrievalEvaluation(
                query=query,
                retrieved_count=len(retrieved),
                relevant_count=relevant,
                precision=round(precision, 4),
                recall=round(recall, 4),
                f1_score=round(f1, 4),
                mrr=round(mrr, 4),
                ndcg=round(ndcg, 4),
                avg_latency_ms=latency_ms,
            ))

        return results


_rag_instance: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """获取 RAG 引擎单例"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGEngine(mock_mode=True)
    return _rag_instance
