"""
W10 A1 OCR 缓存两步拆分测试 (lex-ai · 2026-06-29)

D4 producer blocker #1 修复验证:
1. OcrCache 缓存 hit/miss/TTL/purge 4 个状态
2. Step 1 (run_ocr_with_cache) 缓存命中 vs 实际 OCR
3. Step 2 (postprocess_ocr_text) PII 脱敏 + 段落解析
4. Skill 2 接管 (postprocess_for_skill2_review) ReviewerInput-ready dict
5. venv312 桥接协议 (smoke test - 不真启子进程)

策略:
- 纯单元测试为主, 不依赖 OCR 引擎实际加载
- 用 tempfile.mkdtemp 隔离每个 test 的缓存 db
"""
from pathlib import Path

import pytest


# ===== Fixtures =====

@pytest.fixture
def tmp_cache_db(tmp_path):
    """每个测试用独立 tmp 缓存 db"""
    db_path = tmp_path / "ocr_cache.db"
    return db_path


@pytest.fixture
def reset_singleton():
    """每个测试前清缓存单例"""
    from core.ocr_cache import reset_ocr_cache
    reset_ocr_cache()
    yield
    reset_ocr_cache()


# ===== Step 1: OcrCache 单元测试 =====

class TestOcrCache:
    def test_cache_init_creates_schema(self, tmp_cache_db, reset_singleton):
        """初始化应该建表 + 索引"""
        from core.ocr_cache import OcrCache
        cache = OcrCache(db_path=tmp_cache_db, ttl_seconds=60)
        try:
            stats = cache.stats()
            assert stats["entry_count"] == 0
            assert stats["ttl_seconds"] == 60
        finally:
            cache.close()

    def test_cache_set_and_get(self, tmp_cache_db, reset_singleton):
        """set + get 命中"""
        from core.ocr_cache import OcrCache
        cache = OcrCache(db_path=tmp_cache_db, ttl_seconds=60)
        try:
            file_hash = "abc123def456"
            result_dict = {"raw_text": "测试", "confidence": 0.9, "page_count": 1,
                           "source_engine": "mock", "detected_mime": "image/png",
                           "line_count": 1}
            cache.set(file_hash, "test.png", "image/png", 1024, "mock", result_dict)
            hit = cache.get(file_hash)
            assert hit is not None
            out, age = hit
            assert out["raw_text"] == "测试"
            assert out["confidence"] == 0.9
            assert age < 1.0
        finally:
            cache.close()

    def test_cache_get_miss_returns_none(self, tmp_cache_db, reset_singleton):
        """miss → None"""
        from core.ocr_cache import OcrCache
        cache = OcrCache(db_path=tmp_cache_db, ttl_seconds=60)
        try:
            hit = cache.get("nonexistent_hash")
            assert hit is None
        finally:
            cache.close()

    def test_cache_ttl_expiry(self, tmp_cache_db, reset_singleton):
        """TTL 过期 → 返回 None (即使 set 了)"""
        from core.ocr_cache import OcrCache
        cache = OcrCache(db_path=tmp_cache_db, ttl_seconds=0)  # 0s TTL 立即过期
        try:
            file_hash = "ttl_test"
            result_dict = {"raw_text": "expired", "confidence": 0.5, "page_count": 1,
                           "source_engine": "mock", "detected_mime": "image/png",
                           "line_count": 0}
            cache.set(file_hash, "x.png", "image/png", 100, "mock", result_dict)
            # 0s TTL 应该立即过期
            hit = cache.get(file_hash)
            assert hit is None
        finally:
            cache.close()

    def test_cache_purge_expired(self, tmp_cache_db, reset_singleton):
        """purge_expired 删除过期条目"""
        import time as time_mod
        from core.ocr_cache import OcrCache
        cache = OcrCache(db_path=tmp_cache_db, ttl_seconds=1)
        try:
            file_hash = "to_be_purged"
            cache.set(file_hash, "x.png", "image/png", 100, "mock",
                      {"raw_text": "x", "confidence": 0.5, "page_count": 1,
                       "source_engine": "mock", "detected_mime": "image/png", "line_count": 0})
            # 等待过期
            time_mod.sleep(1.5)
            purged = cache.purge_expired()
            assert purged >= 1
            # 再次 get 应该 None
            hit = cache.get(file_hash)
            assert hit is None
        finally:
            cache.close()

    def test_hash_file_bytes_deterministic(self):
        """相同 bytes → 相同 hash"""
        from core.ocr_cache import OcrCache
        h1 = OcrCache.hash_file_bytes(b"hello world")
        h2 = OcrCache.hash_file_bytes(b"hello world")
        h3 = OcrCache.hash_file_bytes(b"hello world!")
        assert h1 == h2
        assert h1 != h3
        assert len(h1) == 32  # sha256 hex 前 32 字符


# ===== Step 1: run_ocr_with_cache =====

class TestRunOcrWithCache:
    def test_first_run_miss_then_ocr(self, tmp_cache_db, reset_singleton, monkeypatch):
        """首次 miss → 实际 OCR → 缓存入库"""
        from core.ocr_cache import OcrCache, run_ocr_with_cache

        cache = OcrCache(db_path=tmp_cache_db, ttl_seconds=300)
        try:
            fake_bytes = b"fake-image-bytes-for-test" * 100
            # 强制使用 mock engine (避免 paddle 依赖)
            monkeypatch.setenv("LEX_OCR_ENGINE", "mock")

            r1 = run_ocr_with_cache(fake_bytes, filename="test_ocr_1.png", cache=cache)
            assert r1.cache_hit is False
            assert r1.engine == "mock"
            assert r1.file_size == len(fake_bytes)
            assert r1.mime == "image/png"
            assert r1.source in ("primary", "bridge_subprocess")
            assert r1.ocr_result.raw_text  # 非空
        finally:
            cache.close()

    def test_second_run_hit_returns_cached(self, tmp_cache_db, reset_singleton, monkeypatch):
        """第二次同文件 → 缓存命中"""
        from core.ocr_cache import OcrCache, run_ocr_with_cache

        cache = OcrCache(db_path=tmp_cache_db, ttl_seconds=300)
        try:
            fake_bytes = b"fake-image-bytes-for-test" * 100
            monkeypatch.setenv("LEX_OCR_ENGINE", "mock")

            r1 = run_ocr_with_cache(fake_bytes, filename="test_ocr_1.png", cache=cache)
            assert r1.cache_hit is False

            r2 = run_ocr_with_cache(fake_bytes, filename="test_ocr_1.png", cache=cache)
            assert r2.cache_hit is True
            assert r2.cache_age_seconds >= 0
            assert r2.source == "cache"
            # 缓存命中内容应一致
            assert r2.ocr_result.raw_text == r1.ocr_result.raw_text
        finally:
            cache.close()

    def test_use_cache_false_skips_cache(self, tmp_cache_db, reset_singleton, monkeypatch):
        """use_cache=False 不读缓存 (每次都跑 OCR)"""
        from core.ocr_cache import OcrCache, run_ocr_with_cache

        cache = OcrCache(db_path=tmp_cache_db, ttl_seconds=300)
        try:
            fake_bytes = b"force-no-cache" * 50
            monkeypatch.setenv("LEX_OCR_ENGINE", "mock")

            r1 = run_ocr_with_cache(fake_bytes, filename="test_ocr_2.png",
                                     use_cache=False, cache=cache)
            r2 = run_ocr_with_cache(fake_bytes, filename="test_ocr_2.png",
                                     use_cache=False, cache=cache)
            # 都不应命中 (因为 use_cache=False)
            assert r1.cache_hit is False
            assert r2.cache_hit is False
        finally:
            cache.close()

    def test_different_files_different_hashes(self, tmp_cache_db, reset_singleton, monkeypatch):
        """不同文件 hash 不同 → 缓存不串"""
        from core.ocr_cache import OcrCache, run_ocr_with_cache

        cache = OcrCache(db_path=tmp_cache_db, ttl_seconds=300)
        try:
            monkeypatch.setenv("LEX_OCR_ENGINE", "mock")
            r1 = run_ocr_with_cache(b"file-A" * 100, filename="test_ocr_1.png", cache=cache)
            r2 = run_ocr_with_cache(b"file-B" * 100, filename="test_ocr_2.png", cache=cache)
            assert r1.file_hash != r2.file_hash
        finally:
            cache.close()


# ===== Step 2: postprocess_ocr_text =====

class TestPostprocessOcrText:
    def test_empty_text_returns_empty(self):
        """空文本 → 空结果"""
        from core.ocr_cache import postprocess_ocr_text
        pp = postprocess_ocr_text("")
        assert pp.sanitized_text == ""
        assert pp.paragraphs == []

    def test_skip_pii_keeps_text(self):
        """skip_pii=True 保留原文"""
        from core.ocr_cache import postprocess_ocr_text
        text = "甲方: 张三, 身份证 110101199003078811"
        pp = postprocess_ocr_text(text, skip_pii=True)
        assert "110101199003078811" in pp.sanitized_text  # 未脱敏
        assert pp.pii_report.get("skipped") is True

    def test_pii_desensitize_id_card(self):
        """身份证号被脱敏"""
        from core.ocr_cache import postprocess_ocr_text
        text = "甲方: 张三, 身份证 110101199003078811"
        pp = postprocess_ocr_text(text)
        assert "110101199003078811" not in pp.sanitized_text
        assert pp.pii_report.get("id_card_count", 0) >= 1

    def test_pii_desensitize_mobile(self):
        """手机号被脱敏"""
        from core.ocr_cache import postprocess_ocr_text
        text = "联系电话: 13812345678"
        pp = postprocess_ocr_text(text)
        assert "13812345678" not in pp.sanitized_text
        assert pp.pii_report.get("mobile_count", 0) >= 1

    def test_paragraph_splitting(self):
        """段落按 \\n\\n 切"""
        from core.ocr_cache import postprocess_ocr_text
        text = "第一段内容\n\n第二段内容\n\n第三段内容"
        pp = postprocess_ocr_text(text, skip_pii=True, paragraph_min_length=2)
        assert len(pp.paragraphs) == 3
        assert pp.paragraphs[0]["idx"] == 1
        assert pp.paragraphs[0]["text"] == "第一段内容"

    def test_short_paragraphs_merge(self):
        """短段 (paragraph_min_length 以下) 累积合并"""
        from core.ocr_cache import postprocess_ocr_text
        text = "短\n\n第二段长一些内容"
        pp = postprocess_ocr_text(text, skip_pii=True, paragraph_min_length=10)
        # "短" (< 10 字符) 累积到第二段前面
        assert len(pp.paragraphs) == 1
        assert "短" in pp.paragraphs[0]["text"]
        assert "第二段长一些内容" in pp.paragraphs[0]["text"]


# ===== Step 2 (Skill 2 接管): postprocess_for_skill2_review =====

class TestPostprocessForSkill2Review:
    def test_skill2_input_ready_for_short_text(self):
        """文本 < 50 字 → ready_for_review=False"""
        from core.ocr_cache import postprocess_for_skill2_review
        pp = postprocess_for_skill2_review("短", contract_type="房屋租赁")
        assert pp.skill2_input is not None
        assert pp.skill2_input["contract_type"] == "房屋租赁"
        assert pp.skill2_input["ready_for_review"] is False
        assert pp.skill2_input["stance"] == "审查方"

    def test_skill2_input_ready_for_long_text(self):
        """文本 >= 50 字 → ready_for_review=True"""
        from core.ocr_cache import postprocess_for_skill2_review
        long_text = "第一条 租赁标的\n" + "甲方将位于上海市浦东新区某某路 123 号房屋出租给乙方使用。" * 2
        pp = postprocess_for_skill2_review(long_text, contract_type="房屋租赁")
        assert pp.skill2_input["ready_for_review"] is True
        assert pp.skill2_input["contract_type"] == "房屋租赁"

    def test_skill2_invalid_contract_type_fallback(self):
        """contract_type 非法 → fallback 到 "其他" """
        from core.ocr_cache import postprocess_for_skill2_review
        pp = postprocess_for_skill2_review("text " * 20, contract_type="不是有效的合同类型")
        assert pp.skill2_input["contract_type"] == "其他"


# ===== Bridge 子进程 (smoke test, 不真启 venv312) =====

class TestBridgeSmoke:
    def test_bridge_script_path_returns_path(self):
        """桥接脚本路径解析 (绝对)"""
        from core.ocr_cache import _bridge_script_path
        p = _bridge_script_path()
        assert isinstance(p, Path)
        # 跨平台: 路径用 PosixPath parts 比较, 避免 Windows \\ 误判
        assert p.is_absolute()
        assert p.name == "ocr_via_venv312.py"
        assert p.parent.name == "w8"
        assert p.parent.parent.name == "scripts"

    def test_bridge_python_path_returns_path(self):
        """venv312 python 路径解析"""
        from core.ocr_cache import _bridge_python_path
        p = _bridge_python_path()
        assert isinstance(p, Path)
        assert "venv312" in str(p)
        assert p.is_absolute()

    def test_run_ocr_via_bridge_returns_none_when_no_python(self, tmp_path):
        """venv312 不存在时, 桥接返回 None (graceful fallback)"""
        # 指向一个不存在的 venv312 (临时 dir)
        from core import ocr_cache as ocr_cache_mod
        import core.ocr_cache

        # monkey-patch 桥接路径到不存在的目录
        orig_bridge_py = ocr_cache_mod._bridge_python_path
        orig_bridge_script = ocr_cache_mod._bridge_script_path
        try:
            core.ocr_cache._bridge_python_path = lambda: tmp_path / "nonexistent_python.exe"
            core.ocr_cache._bridge_script_path = lambda: tmp_path / "nonexistent_script.py"
            result = core.ocr_cache.run_ocr_via_bridge(b"fake", filename="x.png")
            assert result is None
        finally:
            core.ocr_cache._bridge_python_path = orig_bridge_py
            core.ocr_cache._bridge_script_path = orig_bridge_script


# ===== 集成: Step 1 + Step 2 串联 =====

class TestIntegrationStep1Step2:
    def test_end_to_end_cache_then_postprocess(self, tmp_cache_db, reset_singleton, monkeypatch):
        """完整链路: OCR (缓存) → 后处理 → Skill 2 接管"""
        from core.ocr_cache import (
            OcrCache, run_ocr_with_cache, postprocess_for_skill2_review,
        )

        cache = OcrCache(db_path=tmp_cache_db, ttl_seconds=300)
        try:
            monkeypatch.setenv("LEX_OCR_ENGINE", "mock")
            fake_bytes = b"fake-png-bytes" * 200

            # Step 1: OCR (含缓存)
            r = run_ocr_with_cache(fake_bytes, filename="test_ocr_1.png", cache=cache)
            assert r.ocr_result.raw_text
            assert r.cache_hit is False

            # Step 2: 后处理
            pp = postprocess_for_skill2_review(
                r.ocr_result.raw_text,
                contract_type="房屋租赁",
                skip_pii=False,
            )
            assert pp.sanitized_text
            assert pp.skill2_input is not None
            assert pp.skill2_input["contract_type"] == "房屋租赁"
            assert isinstance(pp.skill2_input["ready_for_review"], bool)

            # 再跑一次, 这次缓存命中
            r2 = run_ocr_with_cache(fake_bytes, filename="test_ocr_1.png", cache=cache)
            assert r2.cache_hit is True
            assert r2.source == "cache"
        finally:
            cache.close()