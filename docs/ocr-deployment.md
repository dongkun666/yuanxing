# PaddleOCR 部署指引 (LexPrime W5 Track B)

> 适用版本: LexPrime v0.7.0+ (2026-06-29 起) · Track B (B-ocr.md)
> 默认配置: **Mock 模式** (开发/测试, 零依赖)
> 生产配置: **PaddleOCR 模式** (中文专精, 离线)

## 1. 为什么需要 PaddleOCR

LexPrime 是律师工作台, 合同扫描件 / 拍照上传是高频场景。通用云 OCR (百度/腾讯) 既贵又涉及数据合规。PaddleOCR 是百度开源的中文 OCR 专精模型, 离线部署, 数据不出本机。

| 方案 | 中文准确率 | 离线 | 部署成本 | 合规 |
|---|---|---|---|---|
| **PaddleOCR 2.7 (本项目用)** | ★★★★★ | ✓ | 中 (1GB venv) | ✓ (本地推理) |
| 百度云 OCR | ★★★★★ | ✗ | 低 (API) | △ (数据上云) |
| Tesseract OCR | ★★★ | ✓ | 低 | ✓ |
| 通用视觉 LLM (Qwen-VL) | ★★★★ | ✗ | 高 (GPU) | △ |

参考: PRD § 5.4 Skill Hub + docs/prd/tracks/B-ocr.md + docs/prd/14-references-from-products.md § 14.4.2

## 2. 引擎切换

LexPrime 的 `core/ocr.py` 抽象了 2 个引擎, 通过环境变量切换:

```python
# core/ocr.py
LEX_OCR_ENGINE=auto   # 默认: paddle 可用 → paddle, 否则 mock
LEX_OCR_ENGINE=paddle # 强制 paddle, 不可用 raise
LEX_OCR_ENGINE=mock   # 强制 mock (开发/测试)
```

健康检查端点: `GET /api/contract-review/ocr-health`
返回:
```json
{
  "ocr_engine": "paddle",          // 当前生效引擎
  "ocr_engine_paddle_available": true,  // paddleocr 是否可 import
  "supported_mimes": [...],
  "max_upload_bytes": 20971520
}
```

## 3. 生产部署 (PaddleOCR 真模型)

### 3.1 环境要求

- **Python 3.11 / 3.12** (paddlepaddle 官方 wheel 不支持 3.14)
- **内存**: 4GB+ (模型 + 推理)
- **磁盘**: 1GB+ (模型自动下载到 `~/.paddlex/official_models/`)
- **可选 GPU**: paddlepaddle-gpu 2.6.x + CUDA 11.2+ (推理加速 5-10x)

### 3.2 独立 venv 安装 (避免污染主项目)

```bash
# 1. 创建独立 venv (Python 3.11)
python3.11 -m venv venv-ocr
source venv-ocr/bin/activate  # Windows: venv-ocr\Scripts\activate

# 2. 装 paddlepaddle (CPU 版)
pip install paddlepaddle==2.6.1

# 3. 装 paddleocr (中文 PP-OCRv3 模型 ~12MB, 首次推理自动下载)
pip install paddleocr==2.7.3
# 装 Pillow + PyMuPDF (PDF 扫描件用)
pip install Pillow PyMuPDF

# 4. 验证
python -c "from paddleocr import PaddleOCR; o = PaddleOCR(lang='ch'); print('OK')"
# 首次会下载模型到 ~/.paddlex/official_models/ (5-10s)
```

### 3.3 集成到 LexPrime backend

LexPrime 默认装在 Python 3.14 (paddlepaddle 不支持), 因此**生产部署需要双 venv 策略**:

#### 方案 A: 独立 OCR 微服务 (推荐)

```bash
# venv-ocr 跑 OCR 微服务 (FastAPI)
# 暴露 /ocr POST 端点, 接 image/PDF bytes → 返回 {text, confidence}
# LexPrime 主服务 (Python 3.14) 通过 HTTP 调 OCR 微服务
# 在 core/ocr.py 增加 HttpOcrEngine (T-REF-15 借鉴)
```

#### 方案 B: 同 venv (需要降级 Python)

```bash
# LexPrime 主服务降级到 Python 3.11
# 装 paddlepaddle 2.6.1 + paddleocr 2.7.3 进同一 venv
# 启动时 export LEX_OCR_ENGINE=paddle
```

### 3.4 模型下载 (离线场景)

```bash
# 第一次推理会下载模型到 ~/.paddlex/official_models/
# 离线环境需预先下载:
pip install huggingface-hub
python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='PaddlePaddle/PaddleOCR',
    repo_type='model',
    local_dir='./paddleocr-models'
)
"
# 然后在 .env 指定模型路径:
# PADDLE_OCR_MODEL_DIR=./paddleocr-models
```

## 4. 测试模式 (开发/默认)

LexPrime 默认走 **Mock 模式**, 5 张样张 fixture + 启发式:

```bash
# 默认 (auto: paddle 可用→paddle, 否则 mock)
unset LEX_OCR_ENGINE

# 强制 mock (开发)
export LEX_OCR_ENGINE=mock

# 跑测试
cd backend/cases-crawler
LEX_OCR_ENGINE=mock python -m pytest tests/test_ocr_engine.py tests/test_pii.py -v
```

测试覆盖 (W5):
- `test_ocr_engine.py` 24 tests: 5 张样张 + MIME 推断 + 引擎工厂
- `test_pii.py` 19 tests: 10 case PII 脱敏 (身份证/手机/银行卡/邮箱/地址/人名/混合/无 PII/边界/OCR 模拟)
- `test_contract_review_ocr_endpoint.py` 9 tests: E2E (multipart upload → 风险列表)

## 5. 排错

### paddlepaddle 装不上
- **症状**: `pip install paddlepaddle` 报 "Could not find a version that satisfies the requirement"
- **原因**: 当前 Python 版本 (3.13/3.14) 没有官方 wheel
- **解**: 切到 Python 3.11/3.12 venv

### 模型下载失败
- **症状**: `PaddleOCR` 初始化卡在下载, 报 "Download failed"
- **原因**: 网络限制 (GFW)
- **解**: 配 `HF_ENDPOINT=https://hf-mirror.com` 或手动下载

### paddlepaddle 启动 crash
- **症状**: `paddleocr` 报 "DLL load failed" / "libpaddle not found"
- **解**: 装 Microsoft Visual C++ Redistributable (Windows)

## 6. 相关文档

- `docs/prd/tracks/B-ocr.md` Track B PRD
- `docs/prd/14-references-from-products.md` § 14.4.2 (PaddleOCR 借鉴)
- `docs/prd/05-knowledge-base.md` (含 OCR 在证据处理)
- `core/ocr.py` (引擎抽象)
- `core/pii.py` (PII 脱敏)
- `api/contract_review_router.py` (/ocr-upload + /ocr-health)

---

**W5 状态**: 抽象层 + Mock 模式 + 5 张样张 + 10 case PII + E2E 全部 PASS (43 tests, 100%)
**生产部署**: 配独立 venv-ocr + PaddleOcrEngine, 详见本文件 § 3
