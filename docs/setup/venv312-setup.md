# LexPrime venv312 PaddleEngine 装包指引

> 适用: LexPrime W8 D1 (2026-06-29) · Track B OCR 生产部署
> 目标: 在 `backend/venv312/` 里装 paddlepaddle 3.3.1 + paddleocr 3.7.0 (PP-OCRv6 中文专精)
> 评审现场 (W7 #1 #2) Tesseract + Mock 兜底仍可用, 这套 venv 是 W8 D4 E2E 切真 PaddleEngine 的前置

## 1. 背景: 为什么需要独立 venv312

LexPrime 主 backend 默认跑 Python 3.14 (C:\Python314\python.exe), **paddlepaddle 3.3.1 官方 wheel 不兼容 3.14**:

| 方案 | paddlepaddle 兼容 | 数据合规 | 离线 |
|---|---|---|---|
| **PaddleOCR 3.7 (本项目用)** | Python 3.8-3.12 | 本地推理 | 是 |
| 百度云 OCR | 无要求 | 数据上云 ❌ | 否 |
| Tesseract OCR (W5 兜底) | 任意 | 本地推理 | 是 |
| 通用视觉 LLM (Qwen-VL) | 任意 | API 调用 | 否 |

→ 引入**独立 Python 3.12.7 embeddable venv** 隔离 OCR 推理, 主进程 3.14 通过进程隔离调用。

## 2. 当前状态 (2026-06-29)

| 文件 / 目录 | 大小 | 状态 |
|---|---|---|
| `backend/python-3.12.7-embed-amd64.zip` | 10.5 MB | 官方分发包 (Python embeddable 3.12.7 win64) |
| `backend/venv312/` | ~1.28 GB | 已解包 + 装好 paddle 套件 (Python 3.12.7) |

`backend/venv312/` 由本机直接解包 zip 而非 `py -3.12 -m venv` 标准 venv, 但功能等价 (Scripts/ + Lib/site-packages/ + get-pip.py + python.exe 在根目录)。

## 3. 全新搭建步骤 (从零)

### 3.1 下载 Python 3.12.7 embeddable

```powershell
# 下载 (官方分发, win64 zip ~10.5MB)
# 源: https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip
# 本机缓存: backend/python-3.12.7-embed-amd64.zip
```

### 3.2 解包到 backend/venv312/

```powershell
cd E:\元枢法智前端\yuanxing\backend
Expand-Archive -Path python-3.12.7-embed-amd64.zip -DestinationPath venv312 -Force
```

### 3.3 装 pip (embed 分发不含 pip)

```powershell
# 1) 启用 site-packages (默认 python312._pth 禁用了)
# 编辑 venv312/python312._pth, 取消 #import site 注释
$pth = "E:\元枢法智前端\yuanxing\backend\venv312\python312._pth"
(Get-Content $pth) -replace '^#import site', 'import site' | Set-Content $pth

# 2) 下载并运行 get-pip.py
Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile "venv312\get-pip.py"
& "E:\元枢法智前端\yuanxing\backend\venv312\python.exe" "E:\元枢法智前端\yuanxing\backend\venv312\get-pip.py"
```

### 3.4 装 paddlepaddle + paddleocr (清华镜像)

```powershell
& "E:\元枢法智前端\yuanxing\backend\venv312\python.exe" -m pip install --upgrade pip
& "E:\元枢法智前端\yuanxing\backend\venv312\python.exe" -m pip install paddlepaddle==3.3.1 -i https://pypi.tuna.tsinghua.edu.cn/simple
& "E:\元枢法智前端\yuanxing\backend\venv312\python.exe" -m pip install paddleocr==3.7.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
& "E:\元枢法智前端\yuanxing\backend\venv312\python.exe" -m pip install Pillow PyMuPDF -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3.5 import 验证

```powershell
& "E:\元枢法智前端\yuanxing\backend\venv312\python.exe" -c "import paddle, paddleocr; print('paddle:', paddle.__version__, '/ paddleocr:', paddleocr.__version__)"
```

**期望输出**:
```
paddle: 3.3.1 / paddleocr: 3.7.0
```

(可能有 `UserWarning: No ccache found` 警告, 无害, 不影响推理)

## 4. 与主 backend 集成 (W8 D4 计划)

> **重要发现 (2026-06-29)**: paddlepaddle 3.3.1 wheel 编译时绑定 **Python 3.12 ABI** (PEP 425), 主 backend Python 3.14 进程**无法**通过 PYTHONPATH 跨版本 import (libpaddle.pyd 报 `DLL load failed`)。
> → **方案 A 不可行**。推荐 **方案 B (双进程)** 或 **方案 C (venv312 直启 uvicorn)**。

### 方案 A: PYTHONPATH 注入 (理论可行, 实测 ❌)

```powershell
$env:PYTHONPATH = "E:\元枢法智前端\yuanxing\backend\venv312\Lib\site-packages"
C:\Python314\python.exe -c "import paddle"
# → ImportError: DLL load failed (libpaddle.pyd 是 3.12 ABI)
```

### 方案 B: 双进程隔离 (推荐, T-REF-15 借鉴)

```python
# venv312 跑独立 FastAPI OCR 微服务 (端口 8089), 主 backend (3.14) 通过 HTTP 调用
# POST /ocr {file_bytes, filename} → {raw_text, confidence, lines[]}
# 此方案需要 W5 HttpOcrEngine (W5 留口子, W8 D4 实施)
```

启动命令:

```powershell
# OCR 微服务 (Python 3.12 venv312)
& "E:\元枢法智前端\yuanxing\backend\venv312\python.exe" -m uvicorn ocr_service.main:app --port 8089

# 主 backend (Python 3.14)
$env:LEX_OCR_ENGINE = "paddle"
$env:LEX_OCR_SERVICE_URL = "http://localhost:8089"
uvicorn cases_crawler.main:app --port 3847
```

### 方案 C: 直接用 venv312 启 uvicorn (W5 工程化倾向)

```powershell
& "E:\元枢法智前端\yuanxing\backend\venv312\python.exe" -m uvicorn cases_crawler.main:app --port 3847
```

主进程是 Python 3.12, paddle 原生支持。但 FastAPI / SQLAlchemy / 其他 wheel 要重装到 venv312 (本 venv312 不带, 完整一份 backend 套件 ~3GB)。

## 5. 模型管理

PaddleOCR 3.7 + paddlex 3.7.2 自动管理模型到:

- 默认路径: `C:\Users\<你>\.paddlex\official_models\`
- 模型: PP-OCRv6 (detection + recognition + cls, ~12MB)
- 自定义路径: 环境变量 `PADDLEX_HOME` (写到 .env)

**首次推理**才会下载, ~10s 等待, 后续秒级启动。

## 6. 常见问题

| 现象 | 原因 | 修复 |
|---|---|---|
| `ModuleNotFoundError: No module named 'paddle'` | PYTHONPATH 没设 / venv 没用对 | 见 § 4 方案 A |
| `ValueError: ... DoubleAttribute` (PP-OCRv6 报 onednn dtype) | Paddle 3.x onednn 默认开启不兼容 PP-OCRv6 | ocr.py 顶部已自动设置 `FLAGS_use_mkldnn=0`, 检查是否正常 import |
| `UserWarning: No ccache found` | 没装 ccache (C 编译缓存) | 无害, 仅源码编译时才会慢, wheel 安装不受影响 |
| `ImportError: DLL load failed` | Python 3.14 装 paddlepaddle 失败 | **不要在 3.14 装**, 必须 3.12 venv |
| PaddleOcrEngine 返回 dict vs list (API 不一致) | PaddleOCR 2.7 返回 list, 3.7 返回 dict | ocr.py _detect_paddle_api_version() 自动兼容 (W7 commit 0815a2e) |

## 7. 参考

- W7 PaddleEngine 代码: `backend/cases-crawler/core/ocr.py` (commit `0815a2e`)
- W5 OCR 兜底 (Tesseract + Mock): commit `3b48ce8`
- 主部署文档: `docs/ocr-deployment.md`
- PRD: `docs/prd/05-knowledge-base.md` § 5.4 Skill Hub + `docs/prd/tracks/B-ocr.md`
- PaddleOCR 3.7 文档: https://github.com/PaddlePaddle/PaddleOCR

## 8. 检查清单 (D1 验收)

- [x] `backend/venv312/python.exe --version` → `Python 3.12.7`
- [x] `import paddle; print(paddle.__version__)` → `3.3.1`
- [x] `import paddleocr; print(paddleocr.__version__)` → `3.7.0`
- [x] `backend/requirements-ocr.txt` 落档
- [x] `docs/setup/venv312-setup.md` 落档 (本文档)
- [x] `.gitignore` 排除 `backend/venv312/` + `backend/python-3.12.7-embed-amd64.zip`
- [x] git commit push (1 commit D1)
- [ ] (D4) PaddleEngine 推理 e2e + `LEX_OCR_ENGINE=paddle` 端到端
- [ ] (后续) 模型自动下载到 `~/.paddlex/` 验证
