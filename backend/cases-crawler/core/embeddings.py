"""
LexPrime Embedding 服务 (v0.1.0-draft)

W4: 合同/类案/法规 BGE 中文 embedding 统一封装 (T-REF-22)

设计原则:
1. **离线优先**: 默认走本地 BGE 模型, 不依赖外部 API
2. **统一接口**: BaseEmbedder 抽象, 业务侧不感知底层实现
3. **降级兼容**: 模型加载失败时自动回退到 MockEmbedder (hashing, deterministic 512-dim)
4. **性能**: 单条 CPU 推理 < 100ms (BGE small-zh 实际 6-10ms)

依赖 (见 requirements.txt):
- sentence-transformers>=2.7
- numpy>=1.26

用法:
    from core.embeddings import get_embedder

    embedder = get_embedder()  # 自动选 BGE 或 Mock
    vecs = embedder.encode(["合同条款", "法条引用"])  # shape (2, 512)
    single = embedder.encode_one("单条文本")  # shape (512,)
"""
from __future__ import annotations

import hashlib
import os
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Sequence

import numpy as np


# ===== 常量 =====

# LexPrime 统一 embedding 维度 (BGE-small-zh 默认 512)
EMBEDDING_DIM = 512

# 默认模型 (PRD § 5.4 Skill Hub: 中文优先, 模型小 ~93MB)
DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"

# 模型缓存目录 (用户已下载到 E:/falvxiangmu/cache/sentence-transformers)
DEFAULT_CACHE_DIR = os.environ.get(
    "LEXPRIME_ST_CACHE",
    "E:/falvxiangmu/cache/sentence-transformers",
)


# ===== 抽象接口 =====


class BaseEmbedder(ABC):
    """Embedder 抽象接口。"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...

    @property
    @abstractmethod
    def dim(self) -> int:
        ...

    @abstractmethod
    def encode(self, texts: Sequence[str], batch_size: int = 32) -> np.ndarray:
        """批量编码, 返回 shape (N, dim) 的 float32 ndarray。"""
        ...

    def encode_one(self, text: str) -> np.ndarray:
        """单条编码, 返回 shape (dim,) 的 float32 ndarray。"""
        arr = self.encode([text])
        return arr[0] if len(arr) else np.zeros(self.dim, dtype=np.float32)


# ===== BGE 真实实现 =====


class BGEEmbedder(BaseEmbedder):
    """BAAI/bge-small-zh-v1.5 真实 embedding (sentence-transformers 加载)。

    性能参考 (本地 CPU 推理, 2026-06-29 测试):
    - 单条 encode: 6-10ms (P95 9.1ms)
    - 批 8: mean 10.7ms
    - 模型大小: ~93MB (cache 一次后秒加载)
    """

    def __init__(self, model_name: str = DEFAULT_MODEL,
                 cache_dir: Optional[str] = DEFAULT_CACHE_DIR,
                 device: str = "cpu"):
        # 离线: 关掉代理, 用 hf-mirror (国内可达)
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            os.environ.pop(k, None)
        os.environ.setdefault("NO_PROXY", "*")
        os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        self._model_name = model_name
        self._cache_dir = cache_dir
        self._device = device
        self._model = SentenceTransformer(model_name, cache_folder=cache_dir, device=device)
        # 锁定输出维度 (sentence-transformers 5.x 改名)
        dim_fn = getattr(self._model, "get_embedding_dimension", None) \
            or self._model.get_sentence_embedding_dimension
        self._dim: int = int(dim_fn())
        # Warm-up (首次 encode 略慢, 提前跑一次)
        _ = self._model.encode(["warmup"], normalize_embeddings=True)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dim(self) -> int:
        return self._dim

    def encode(self, texts: Sequence[str], batch_size: int = 32) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)
        # BGE 推荐 normalize_embeddings=True (cosine 相似度 = dot product)
        arr = self._model.encode(
            list(texts),
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return arr.astype(np.float32)


# ===== Mock 降级实现 =====


class MockEmbedder(BaseEmbedder):
    """Hashing-based mock embedder (无 ML 依赖, deterministic 512-dim)。

    算法: SHA-256(text) → 多次切片 → 4-gram 哈希 → 桶累加 → L2 归一化。
    目的: 测试 / 离线兜底 (模型加载失败时仍能跑向量索引)。

    注意: 语义质量极差 (相同文本 → 完全相同向量, 相似文本可能完全无关),
    仅保证**确定性**和**维度一致**, **不能用于生产检索**。
    """

    def __init__(self, dim: int = EMBEDDING_DIM, model_name: str = "mock-hash-v1"):
        self._dim = dim
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dim(self) -> int:
        return self._dim

    def encode(self, texts: Sequence[str], batch_size: int = 32) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)
        out = np.zeros((len(texts), self._dim), dtype=np.float32)
        for i, text in enumerate(texts):
            out[i] = self._hash_to_vec(text)
        return out

    def _hash_to_vec(self, text: str) -> np.ndarray:
        if not text:
            return np.zeros(self._dim, dtype=np.float32)
        # 中文 + 英文 4-gram 特征
        text = text.strip()
        grams: List[str] = []
        # 单字 + 双字 + 3-gram + 词级 (空格分隔)
        for ch in text:
            grams.append(ch)
        for j in range(len(text) - 1):
            grams.append(text[j : j + 2])
        for j in range(len(text) - 2):
            grams.append(text[j : j + 3])
        for word in text.split():
            grams.append(word)

        vec = np.zeros(self._dim, dtype=np.float32)
        for g in grams:
            h = hashlib.md5(g.encode("utf-8")).digest()
            # 取前 8 字节作 64-bit int, mod dim → 桶位置
            bucket = int.from_bytes(h[:8], "little") % self._dim
            # 用 hash 的 bit 决定 +/- (sign hashing)
            sign = 1.0 if (h[8] & 1) else -1.0
            vec[bucket] += sign
        # L2 归一化
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec


# ===== 工厂 =====


_EMBEDDER_SINGLETON: Optional[BaseEmbedder] = None
_EMBEDDER_KIND: str = "unset"


def get_embedder(prefer: str = "bge",
                  cache_dir: Optional[str] = DEFAULT_CACHE_DIR,
                  force_mock: bool = False) -> BaseEmbedder:
    """获取 embedder 单例。

    Args:
        prefer: 'bge' (默认) / 'mock' / 'auto'
        cache_dir: sentence-transformers 缓存目录
        force_mock: True 时强制用 Mock (测试用)

    Returns:
        BaseEmbedder 实例 (BGEEmbedder 或 MockEmbedder)
    """
    global _EMBEDDER_SINGLETON, _EMBEDDER_KIND

    if _EMBEDDER_SINGLETON is not None and _EMBEDDER_KIND == prefer and not force_mock:
        return _EMBEDDER_SINGLETON

    if force_mock or prefer == "mock":
        _EMBEDDER_SINGLETON = MockEmbedder()
        _EMBEDDER_KIND = "mock"
        return _EMBEDDER_SINGLETON

    if prefer == "bge":
        try:
            _EMBEDDER_SINGLETON = BGEEmbedder(cache_dir=cache_dir)
            _EMBEDDER_KIND = "bge"
            return _EMBEDDER_SINGLETON
        except Exception as e:  # noqa: BLE001
            import logging
            logging.warning(
                "BGE 模型加载失败, 自动降级到 MockEmbedder (semantic quality 差, 仅供测试): %s",
                e,
            )
            _EMBEDDER_SINGLETON = MockEmbedder()
            _EMBEDDER_KIND = "mock"
            return _EMBEDDER_SINGLETON

    raise ValueError(f"Unknown prefer={prefer!r}, use 'bge' / 'mock' / 'auto'")


def reset_embedder() -> None:
    """重置单例 (测试用)。"""
    global _EMBEDDER_SINGLETON, _EMBEDDER_KIND
    _EMBEDDER_SINGLETON = None
    _EMBEDDER_KIND = "unset"


# ===== 性能工具 =====


def benchmark(embedder: BaseEmbedder, n: int = 50, text: Optional[str] = None) -> dict:
    """基准测试: 测单条 encode 延迟 (P50 / P95 / P99 / max)。

    Returns:
        dict {n, min_ms, median_ms, p95_ms, p99_ms, max_ms, dim}
    """
    if text is None:
        text = "月租金为人民币 5000 元整, 逾期支付的, 每逾期一天, 按月租金的 5% 加收违约金"
    # warmup
    _ = embedder.encode([text])

    times: List[float] = []
    for _ in range(n):
        t0 = time.time()
        _ = embedder.encode([text])
        times.append((time.time() - t0) * 1000)
    times.sort()
    p50 = times[len(times) // 2]
    p95 = times[int(len(times) * 0.95)]
    p99 = times[int(len(times) * 0.99)] if n >= 100 else p95
    return {
        "n": n,
        "min_ms": round(times[0], 2),
        "median_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "max_ms": round(times[-1], 2),
        "dim": embedder.dim,
        "model": embedder.model_name,
    }


# ===== CLI =====


if __name__ == "__main__":
    print("=== LexPrime Embedding 服务自检 ===\n")

    # 1) BGE
    print("[1/3] 加载 BGE 模型 ...")
    bge = get_embedder(prefer="bge")
    print(f"  model: {bge.model_name}, dim: {bge.dim}")

    # 2) Mock
    print("\n[2/3] 加载 Mock (deterministic hashing) ...")
    mock = get_embedder(prefer="mock")
    print(f"  model: {mock.model_name}, dim: {mock.dim}")

    # 3) 性能
    print("\n[3/3] 性能压测 (BGE CPU 推理) ...")
    stats = benchmark(bge, n=50)
    print(f"  single encode: P50={stats['median_ms']}ms, P95={stats['p95_ms']}ms, "
          f"max={stats['max_ms']}ms (target: < 100ms)")

    # 4) 一致性
    v1 = bge.encode_one("违约金过高, 司法实践中通常被调减")
    v2 = bge.encode_one("违约金过高, 司法实践中通常被调减")
    cos = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-12))
    print(f"\n  same text cosine similarity: {cos:.4f} (应 ≈ 1.0)")

    v3 = bge.encode_one("房屋租赁合同")
    cos2 = float(np.dot(v1, v3) / (np.linalg.norm(v1) * np.linalg.norm(v3) + 1e-12))
    print(f"  different text cosine: {cos2:.4f} (应 < 0.9)")
