# LexPrime 开发文档

## 开发环境搭建

### 1. 安装 Python

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3.11 python3.11-dev python3.11-venv

# macOS (使用 Homebrew)
brew install python@3.11

# 验证安装
python3.11 --version
```

### 2. 创建虚拟环境

```bash
cd backend/cases-crawler
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
```

### 3. 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 4. 配置开发环境

```bash
# 创建 .env 文件
cp .env.example .env

# 编辑 .env 文件，设置开发环境配置
# 将 API_DEBUG 设置为 true
```

### 5. 启动开发服务器

```bash
# 启动后端服务（带自动重载）
uvicorn api.main:app --host 0.0.0.0 --port 3847 --reload

# 启动数据库（使用 Docker）
docker-compose up -d postgresql elasticsearch neo4j redis minio

# 访问文档
open http://localhost:3847/docs
```

---

## 代码规范

### Python 代码规范

#### 1. 代码风格

- 使用 **Black** 进行代码格式化
- 使用 **Ruff** 进行代码检查
- 遵循 PEP 8 规范

#### 2. 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块名 | 小写，下划线分隔 | `database.py` |
| 类名 | 大驼峰 | `Database` |
| 函数名 | 小写，下划线分隔 | `get_case_detail` |
| 变量名 | 小写，下划线分隔 | `case_id` |
| 常量 | 全大写，下划线分隔 | `MAX_LIMIT` |
| 私有成员 | 单下划线开头 | `_private_method` |

#### 3. 类型注解

所有函数参数和返回值必须添加类型注解：

```python
def get_case(doc_id: str) -> CaseDetail:
    pass
```

#### 4. 文档字符串

使用 Google 风格的文档字符串：

```python
def get_case(doc_id: str) -> CaseDetail:
    """获取判例详情

    根据文档ID获取判例完整信息，包含判决书全文、法律依据等。

    Args:
        doc_id: 文档唯一标识

    Returns:
        CaseDetail: 判例详情对象

    Raises:
        HTTPException: 判例不存在时抛出 404 错误
    """
    pass
```

#### 5. 导入顺序

按照以下顺序导入：

1. 标准库
2. 第三方库
3. 项目内部模块

```python
import os
from typing import Optional, List

from fastapi import APIRouter, Query, HTTPException

from api.models import CaseOut, CaseDetail
```

### JavaScript 代码规范

#### 1. 代码风格

- 使用 **ESLint** 进行代码检查
- 使用 **Prettier** 进行代码格式化

#### 2. 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 变量名 | 小驼峰 | `caseId` |
| 函数名 | 小驼峰 | `getCaseDetail` |
| 常量 | 全大写，下划线分隔 | `MAX_LIMIT` |
| 类名 | 大驼峰 | `ApiClient` |
| 组件名 | 大驼峰 | `CaseList` |

#### 3. 代码结构

- 使用 ES6+ 语法
- 使用 `async/await` 处理异步操作
- 使用 `const/let` 代替 `var`

#### 4. 错误处理

```javascript
async function fetchData(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
}
```

### CSS 代码规范

- 使用 Bootstrap 5 作为基础框架
- 使用类名命名，避免使用 ID
- 使用语义化的类名

---

## 提交规范

### Commit Message 格式

使用 Conventional Commits 规范：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Type 类型

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 Bug |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响逻辑） |
| `refactor` | 重构（不新增功能也不修复 Bug） |
| `test` | 测试相关 |
| `chore` | 构建/工具相关 |
| `perf` | 性能优化 |

### 示例

```bash
# 新功能
feat(api): 添加合同审查接口

# 修复 Bug
fix(search): 修复全文搜索结果排序问题

# 文档更新
docs(api): 更新 API 文档示例

# 代码格式
style(main): 格式化代码

# 重构
refactor(database): 重构数据库连接管理

# 测试
test(cases): 添加判例检索单元测试

# 构建
chore(deps): 更新依赖版本
```

### 分支管理

```
main                    # 主分支（生产环境）
├── develop             # 开发分支（集成测试）
│   ├── feature/xxx     # 功能分支
│   ├── fix/xxx         # Bug 修复分支
│   └── refactor/xxx    # 重构分支
```

### 开发流程

1. 从 `develop` 分支创建新分支
2. 在新分支上开发
3. 提交代码（遵循 Commit 规范）
4. 推送到远程仓库
5. 创建 Pull Request
6. 代码审查通过后合并到 `develop`
7. 定期从 `develop` 合并到 `main`

---

## 测试流程

### 测试类型

| 类型 | 说明 |
|------|------|
| 单元测试 | 测试单个函数或方法 |
| 集成测试 | 测试模块间的交互 |
| API 测试 | 测试 API 接口 |
| 端到端测试 | 测试完整业务流程 |

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行指定测试文件
pytest tests/test_api.py -v

# 运行指定测试函数
pytest tests/test_api.py::test_health -v

# 生成测试报告
pytest tests/ --cov=api --cov-report=html

# 生成覆盖率报告
pytest tests/ --cov=api --cov-report=xml
```

### 测试文件结构

```
tests/
├── conftest.py          # 测试配置和夹具
├── test_api.py          # API 测试
├── test_database.py     # 数据库测试
├── test_search.py       # 搜索测试
└── test_contract.py     # 合同审查测试
```

### 测试示例

```python
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_cases():
    response = client.get("/api/cases?limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_search_cases():
    response = client.post("/api/search", json={
        "query": "借款合同",
        "index": "cases",
        "page": 1,
        "size": 10
    })
    assert response.status_code == 200
    assert "total" in response.json()
```

---

## 开发工具

### 代码编辑器

推荐使用 VS Code，并安装以下插件：

- **Python**：Python 开发支持
- **Pylance**：Python 类型检查
- **Black**：代码格式化
- **Ruff**：代码检查
- **ESLint**：JavaScript 代码检查
- **Prettier**：代码格式化
- **Docker**：Docker 支持
- **GitLens**：Git 增强

### 配置文件

#### VS Code 配置

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": true
  }
}
```

#### Ruff 配置

```toml
[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I", "B", "C4", "UP"]
ignore = ["E501"]

[tool.ruff.flake8-quotes]
inline-quotes = "double"

[tool.ruff.isort]
known-first-party = ["api", "core", "models", "config"]
```

---

## 代码审查

### 审查流程

1. 创建 Pull Request
2. 指派代码审查人员
3. 审查人员提出修改意见
4. 开发者修改代码
5. 审查通过后合并

### 审查要点

- **代码质量**：是否符合代码规范
- **功能正确性**：是否实现了预期功能
- **安全性**：是否存在安全漏洞
- **性能**：是否存在性能问题
- **可维护性**：代码是否易于维护
- **测试覆盖率**：是否有足够的测试用例

---

## 部署流程

### 开发环境

```bash
# 启动开发服务器
uvicorn api.main:app --host 0.0.0.0 --port 3847 --reload

# 启动数据库
docker-compose up -d
```

### 测试环境

```bash
# 构建镜像
docker build -t lexprime:test .

# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 运行测试
pytest tests/ -v
```

### 生产环境

```bash
# 构建生产镜像
docker build -t lexprime:latest .

# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d
```

---

## 常见问题

### Q1：如何调试代码？

A：使用 VS Code 的调试功能：

1. 创建 `.vscode/launch.json` 文件
2. 配置调试器
3. 设置断点
4. 启动调试

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["api.main:app", "--host", "0.0.0.0", "--port", "3847"],
      "justMyCode": false
    }
  ]
}
```

### Q2：如何查看 API 文档？

A：启动服务后访问：

- Swagger UI：`http://localhost:3847/docs`
- ReDoc：`http://localhost:3847/redoc`

### Q3：如何添加新的 API 路由？

A：按照以下步骤：

1. 在 `api/` 目录下创建新的路由文件
2. 定义路由和 Pydantic 模型
3. 在 `api/main.py` 中注册路由

### Q4：如何添加新的数据库模型？

A：按照以下步骤：

1. 在 `models/` 目录下创建新的模型文件
2. 定义 SQLAlchemy 模型
3. 创建数据库迁移

```bash
alembic revision --autogenerate -m "Add new model"
alembic upgrade head
```

### Q5：如何处理 API 错误？

A：使用 FastAPI 的异常处理机制：

```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="Resource not found")
```

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v0.1.0 | 2026-07-03 | 初始版本，完成开发文档 |
