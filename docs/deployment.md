# LexPrime 部署文档

## 环境要求

### 硬件要求

| 环境 | CPU | 内存 | 存储 |
|------|-----|------|------|
| 开发环境 | 4核+ | 8GB+ | 100GB+ |
| 测试环境 | 8核+ | 16GB+ | 200GB+ |
| 生产环境 | 16核+ | 32GB+ | 500GB+ |

### 软件要求

| 软件 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 后端运行环境 |
| PostgreSQL | 16+ | 主数据库 |
| Elasticsearch | 8.x | 全文搜索 |
| Neo4j | 5.x | 知识图谱 |
| Redis | 7.x | 缓存 |
| MinIO | - | 文件存储 |
| Docker | 24+ | 容器化部署 |
| Docker Compose | 2.20+ | 多容器编排 |

---

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository_url>
cd lexprime
```

### 2. 安装依赖

```bash
cd backend/cases-crawler
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下内容：

```env
# API 配置
API_HOST=0.0.0.0
API_PORT=3847
API_DEBUG=false
SECRET_KEY=your-secret-key

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=lexprime
DB_USER=lexprime
DB_PASSWORD=your-db-password

# Elasticsearch 配置
ES_HOST=http://localhost:9200
ES_INDEX_CASES=cases
ES_INDEX_LAWS=laws
ES_INDEX_COMPANIES=companies

# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# MinIO 配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=lexprime

# AI 服务配置
OPENAI_API_KEY=your-openai-api-key
CLAUDE_API_KEY=your-claude-api-key

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=app.log
```

### 4. 初始化数据库

```bash
# 创建数据库表
alembic upgrade head

# 初始化 Elasticsearch 索引
python -m scripts.init_es_indexes
```

### 5. 启动服务

#### 方式一：直接启动

```bash
# 启动后端服务
uvicorn api.main:app --host 0.0.0.0 --port 3847

# 启动前端服务（如果有）
cd frontend
npm install
npm run dev
```

#### 方式二：使用 Docker Compose

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 方式三：使用系统服务

创建 `/etc/systemd/system/lexprime.service` 文件：

```ini
[Unit]
Description=LexPrime API Service
After=network.target postgresql.service elasticsearch.service

[Service]
Type=simple
User=lexprime
WorkingDirectory=/opt/lexprime/backend/cases-crawler
ExecStart=/opt/lexprime/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 3847
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
systemctl daemon-reload
systemctl start lexprime
systemctl enable lexprime

# 查看状态
systemctl status lexprime

# 查看日志
journalctl -u lexprime -f
```

---

## 配置说明

### 数据库配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| DB_HOST | 数据库主机 | localhost |
| DB_PORT | 数据库端口 | 5432 |
| DB_NAME | 数据库名称 | lexprime |
| DB_USER | 数据库用户名 | lexprime |
| DB_PASSWORD | 数据库密码 | - |

### Elasticsearch 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| ES_HOST | ES 服务地址 | http://localhost:9200 |
| ES_INDEX_CASES | 判例索引名 | cases |
| ES_INDEX_LAWS | 法规索引名 | laws |
| ES_INDEX_COMPANIES | 企业索引名 | companies |

### API 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| API_HOST | 监听地址 | 0.0.0.0 |
| API_PORT | 监听端口 | 3847 |
| API_DEBUG | 调试模式 | false |
| SECRET_KEY | 密钥 | - |

### 日志配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| LOG_LEVEL | 日志级别 | INFO |
| LOG_FILE | 日志文件路径 | app.log |

---

## 启动命令

### 开发环境

```bash
# 启动后端（带自动重载）
uvicorn api.main:app --host 0.0.0.0 --port 3847 --reload

# 启动数据库（使用 Docker）
docker-compose up -d postgresql elasticsearch neo4j redis minio
```

### 测试环境

```bash
# 启动所有服务
docker-compose -f docker-compose.test.yml up -d

# 运行测试
pytest tests/ -v

# 生成测试报告
pytest tests/ --cov=api --cov-report=html
```

### 生产环境

```bash
# 构建 Docker 镜像
docker build -t lexprime:latest .

# 使用 Docker Compose 启动
docker-compose -f docker-compose.prod.yml up -d

# 或使用系统服务
systemctl start lexprime
```

---

## 服务管理

### 查看服务状态

```bash
# 查看 API 服务
curl http://localhost:3847/api/health

# 查看数据库连接
psql -h localhost -U lexprime -d lexprime -c "SELECT 1"

# 查看 Elasticsearch
curl http://localhost:9200/_cluster/health

# 查看 Redis
redis-cli ping

# 查看 Neo4j
curl -u neo4j:password http://localhost:7474/db/data/
```

### 停止服务

```bash
# Docker Compose
docker-compose down

# 系统服务
systemctl stop lexprime
```

### 重启服务

```bash
# Docker Compose
docker-compose restart

# 系统服务
systemctl restart lexprime
```

---

## 数据库迁移

### 创建迁移

```bash
alembic revision --autogenerate -m "Add new field"
```

### 执行迁移

```bash
alembic upgrade head
```

### 回滚迁移

```bash
alembic downgrade -1
```

---

## 数据备份与恢复

### 备份数据库

```bash
# PostgreSQL
pg_dump -h localhost -U lexprime lexprime > backup.sql

# Elasticsearch
curl -X POST http://localhost:9200/_snapshot/backup/all -H 'Content-Type: application/json' -d '{"indices": "*"}'

# Neo4j
neo4j-admin database dump neo4j --to-path=/backup

# Redis
redis-cli SAVE
```

### 恢复数据库

```bash
# PostgreSQL
psql -h localhost -U lexprime lexprime < backup.sql

# Elasticsearch
curl -X POST http://localhost:9200/_snapshot/backup/all/_restore

# Neo4j
neo4j-admin database load neo4j --from-path=/backup

# Redis
cp /var/lib/redis/dump.rdb /path/to/restore
```

---

## 常见问题

### Q1：服务启动失败

A：检查以下内容：

```bash
# 检查端口是否被占用
netstat -tlnp | grep 3847

# 检查数据库连接
psql -h localhost -U lexprime -d lexprime

# 检查日志
cat app.log
```

### Q2：Elasticsearch 连接失败

A：确保 ES 服务已启动：

```bash
# 启动 ES
systemctl start elasticsearch

# 检查状态
curl http://localhost:9200/

# 检查防火墙
ufw allow 9200/tcp
```

### Q3：数据库迁移失败

A：检查迁移文件和数据库连接：

```bash
# 检查数据库连接
alembic current

# 手动执行迁移
alembic upgrade head --sql
```

### Q4：API 返回 500 错误

A：查看日志定位问题：

```bash
cat app.log | grep ERROR
```

### Q5：前端无法访问 API

A：检查 CORS 配置和网络：

```bash
# 检查 CORS 中间件配置
# 检查防火墙
ufw allow 3847/tcp

# 检查 Nginx 配置
cat /etc/nginx/sites-available/lexprime
```

---

## 监控与日志

### 日志配置

日志文件默认保存在 `app.log`，包含以下级别：

- DEBUG：调试信息
- INFO：一般信息
- WARNING：警告信息
- ERROR：错误信息
- CRITICAL：严重错误

### 健康检查

访问 `/api/health` 端点检查服务状态：

```bash
curl http://localhost:3847/api/health
```

响应示例：

```json
{
  "status": "ok",
  "version": "0.1.0",
  "timestamp": "2026-03-15T10:30:00",
  "databases": {
    "main": {"connected": true, "latency_ms": 12},
    "elasticsearch": {"connected": true, "latency_ms": 5},
    "neo4j": {"available": true, "latency_ms": 8}
  }
}
```

### 性能监控

建议配置以下监控工具：

- Prometheus + Grafana：性能监控
- ELK Stack：日志分析
- New Relic / Datadog：应用性能监控

---

## 安全建议

### 生产环境配置

1. **禁用 DEBUG 模式**：设置 `API_DEBUG=false`
2. **使用强密码**：数据库、Redis、Neo4j 使用复杂密码
3. **配置防火墙**：只允许必要端口访问
4. **使用 HTTPS**：配置 SSL 证书
5. **定期备份**：设置定时备份任务

### SSL 配置

使用 Let's Encrypt 配置 SSL：

```bash
# 安装 Certbot
apt install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com

# 自动更新
certbot renew --dry-run
```

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v0.1.0 | 2026-07-03 | 初始版本，完成部署文档 |
