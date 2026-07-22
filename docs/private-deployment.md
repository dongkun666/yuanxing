# LexPrime 私有化部署指南

**版本**: 1.0.0  
**日期**: 2026-07-03  
**适用版本**: LexPrime 企业版

---

## 目录

1. [系统要求](#1-系统要求)
2. [安装步骤](#2-安装步骤)
3. [配置说明](#3-配置说明)
4. [升级指南](#4-升级指南)
5. [备份与恢复](#5-备份与恢复)
6. [License 激活](#6-license-激活)
7. [常见问题](#7-常见问题)
8. [技术支持](#8-技术支持)

---

## 1. 系统要求

### 1.1 硬件要求

| 配置级别 | CPU | 内存 | 磁盘 | 支持用户数 |
|---------|-----|------|------|-----------|
| 最低配置 | 2 核 | 4 GB | 100 GB SSD | 1-10 |
| 推荐配置 | 4 核 | 8 GB | 200 GB SSD | 10-50 |
| 企业配置 | 8 核 | 16 GB | 500 GB SSD | 50-200 |
| 旗舰配置 | 16 核 | 32 GB | 1 TB SSD | 200+ |

### 1.2 操作系统要求

支持的操作系统：

- **Ubuntu**: 20.04 LTS, 22.04 LTS, 24.04 LTS
- **Debian**: 11, 12
- **CentOS**: 7, 8, 9
- **Red Hat Enterprise Linux**: 8, 9
- **Amazon Linux**: 2, 2023

### 1.3 软件要求

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **OpenSSL**: 1.1+
- **curl**: 7.0+

### 1.4 网络要求

| 端口 | 协议 | 用途 | 是否必须 |
|-----|------|------|---------|
| 8080 | TCP | Web 界面访问 | 是 |
| 3847 | TCP | API 服务 | 是 |
| 5432 | TCP | PostgreSQL 数据库 | 否（内部） |
| 9200 | TCP | Elasticsearch | 否（内部） |
| 7687 | TCP | Neo4j 图数据库 | 否（内部） |

---

## 2. 安装步骤

### 2.1 准备工作

1. **获取安装包**
   
   从 LexPrime 官方获取私有化部署安装包：
   ```
   lexprime-private-1.0.0.tar.gz
   ```

2. **上传到服务器**
   
   将安装包上传到目标服务器，例如：
   ```bash
   scp lexprime-private-1.0.0.tar.gz user@server:/tmp/
   ```

3. **解压安装包**
   ```bash
   cd /tmp
   tar -xzf lexprime-private-1.0.0.tar.gz
   cd lexprime-private-1.0.0
   ```

### 2.2 一键安装

使用 root 权限运行安装脚本：

```bash
sudo ./scripts/private-deploy/install.sh
```

安装脚本会自动完成以下操作：

1. ✅ 检查系统环境和硬件资源
2. ✅ 安装 Docker 和 Docker Compose（如未安装）
3. ✅ 创建目录结构
4. ✅ 生成配置文件
5. ✅ 部署服务容器
6. ✅ 配置 systemd 服务
7. ✅ 配置防火墙规则
8. ✅ 启动服务并验证

### 2.3 自定义安装参数

```bash
# 指定安装目录
sudo ./scripts/private-deploy/install.sh --dir=/data/lexprime

# 查看帮助
sudo ./scripts/private-deploy/install.sh --help
```

### 2.4 验证安装

安装完成后，通过以下方式验证：

1. **访问 Web 界面**
   ```
   http://<服务器IP>:8080
   ```

2. **检查 API 健康状态**
   ```bash
   curl http://localhost:3847/api/health
   ```

3. **查看服务状态**
   ```bash
   sudo systemctl status lexprime
   ```

4. **运行健康检查脚本**
   ```bash
   sudo ./scripts/private-deploy/health-check.sh
   ```

---

## 3. 配置说明

### 3.1 配置文件位置

主配置文件：
```
/etc/lexprime/config.env
```

### 3.2 基础配置

| 配置项 | 默认值 | 说明 |
|-------|-------|------|
| `LEXPRIME_VERSION` | 1.0.0 | 版本号 |
| `INSTALL_MODE` | private | 安装模式 |
| `SECRET_KEY` | 自动生成 | 应用密钥 |
| `JWT_SECRET` | 自动生成 | JWT 签名密钥 |
| `API_HOST` | 0.0.0.0 | API 监听地址 |
| `API_PORT` | 3847 | API 端口 |
| `WEB_PORT` | 8080 | Web 界面端口 |

### 3.3 数据库配置

| 配置项 | 默认值 | 说明 |
|-------|-------|------|
| `DB_TYPE` | postgresql | 数据库类型 |
| `DB_HOST` | localhost | 数据库地址 |
| `DB_PORT` | 5432 | 数据库端口 |
| `DB_NAME` | lexprime | 数据库名 |
| `DB_USER` | lexprime | 数据库用户 |
| `DB_PASSWORD` | 自动生成 | 数据库密码 |

### 3.4 Elasticsearch 配置

| 配置项 | 默认值 | 说明 |
|-------|-------|------|
| `ES_HOST` | localhost | ES 地址 |
| `ES_PORT` | 9200 | ES 端口 |
| `ES_INDEX_CASES` | lexprime_cases | 案例索引名 |
| `ES_INDEX_LAWS` | lexprime_laws | 法规索引名 |
| `ES_INDEX_COMPANIES` | lexprime_companies | 企业索引名 |

### 3.5 安全配置

| 配置项 | 默认值 | 说明 |
|-------|-------|------|
| `SESSION_TIMEOUT` | 86400 | 会话超时时间（秒） |
| `MAX_LOGIN_ATTEMPTS` | 5 | 最大登录尝试次数 |
| `PASSWORD_MIN_LENGTH` | 8 | 密码最小长度 |

### 3.6 修改配置

修改配置后需要重启服务：

```bash
# 编辑配置文件
sudo vi /etc/lexprime/config.env

# 重启服务
sudo systemctl restart lexprime
```

---

## 4. 升级指南

### 4.1 升级前准备

1. **备份数据**
   ```bash
   sudo ./scripts/private-deploy/backup.sh
   ```

2. **获取新版本安装包**
   ```
   lexprime-private-1.1.0.tar.gz
   ```

### 4.2 执行升级

```bash
# 解压新版本
tar -xzf lexprime-private-1.1.0.tar.gz
cd lexprime-private-1.1.0

# 执行升级
sudo ./scripts/private-deploy/upgrade.sh --version=1.1.0
```

升级脚本会自动完成：

1. ✅ 升级前检查
2. ✅ 自动数据备份
3. ✅ 停止服务
4. ✅ 升级应用文件
5. ✅ 数据库迁移
6. ✅ 启动服务
7. ✅ 升级验证

### 4.3 升级参数

```bash
# 不备份直接升级（不推荐）
sudo ./scripts/private-deploy/upgrade.sh --no-backup

# 指定版本
sudo ./scripts/private-deploy/upgrade.sh --version=1.1.0

# 回滚到上一版本
sudo ./scripts/private-deploy/upgrade.sh --rollback
```

### 4.4 验证升级

```bash
# 检查版本
curl http://localhost:3847/api/health

# 运行健康检查
sudo ./scripts/private-deploy/health-check.sh
```

---

## 5. 备份与恢复

### 5.1 数据备份

使用备份脚本：

```bash
# 完整备份
sudo ./scripts/private-deploy/backup.sh

# 仅备份数据库
sudo ./scripts/private-deploy/backup.sh --db-only

# 仅备份数据文件
sudo ./scripts/private-deploy/backup.sh --files-only

# 仅备份配置
sudo ./scripts/private-deploy/backup.sh --config-only

# 查看备份列表
sudo ./scripts/private-deploy/backup.sh --list
```

### 5.2 定时备份

配置 cron 定时任务：

```bash
# 编辑 crontab
sudo crontab -e

# 每天凌晨 2 点执行备份
0 2 * * * /opt/lexprime/scripts/private-deploy/backup.sh >> /var/log/lexprime/backup.log 2>&1
```

### 5.3 数据恢复

```bash
# 查看可用备份
sudo ./scripts/private-deploy/restore.sh --list

# 从完整备份恢复
sudo ./scripts/private-deploy/restore.sh --file=/var/lexprime/backup/full-20260703-120000.tar.gz

# 仅恢复数据库
sudo ./scripts/private-deploy/restore.sh --db-only --file=/var/lexprime/backup/db-20260703-120000.sql.gz
```

### 5.4 备份保留策略

默认保留 30 天的备份，可通过参数调整：

```bash
# 保留 90 天
sudo ./scripts/private-deploy/backup.sh --retention=90
```

---

## 6. License 激活

### 6.1 获取机器指纹

首次安装后需要激活 License。获取机器指纹：

```bash
# 方式一：通过 Web 界面
# 访问：系统设置 -> License 管理 -> 获取机器指纹

# 方式二：生成激活请求文件
sudo python3 -c "
from core.license import ActivationRequest
req = ActivationRequest.generate_request({
    'company': '贵公司名称',
    'contact': '联系人',
    'email': 'contact@example.com'
})
print('硬件 ID:', req['hardware_id'])
print('激活请求码:', req['request_code'])
"
```

### 6.2 申请 License

将以下信息发送给 LexPrime 销售团队：

- 公司名称
- 联系人信息
- 机器指纹 / 硬件 ID
- 购买的版本和用户数

收到 License 激活码后继续下一步。

### 6.3 激活 License

```bash
# 方式一：通过 Web 界面激活
# 访问：系统设置 -> License 管理 -> 输入激活码

# 方式二：通过配置文件
# 编辑 /etc/lexprime/config.env
# 设置 LICENSE_KEY=your_license_key

# 重启服务
sudo systemctl restart lexprime
```

### 6.4 查看 License 状态

```bash
# 方式一：Web 界面查看
# 系统设置 -> License 管理

# 方式二：API 查看
curl http://localhost:3847/api/health | jq .license
```

### 6.5 License 版本对比

| 功能 | 社区版 | 专业版 | 企业版 | 旗舰版 |
|-----|-------|-------|-------|-------|
| 用户数 | 5 | 50 | 200 | 不限 |
| 案例检索 | ✅ | ✅ | ✅ | ✅ |
| 合同审查 | ❌ | ✅ | ✅ | ✅ |
| 文书生成 | ❌ | ✅ | ✅ | ✅ |
| AI 服务 | 基础 | 标准 | 高级 | 高级 |
| 多租户 | ❌ | ❌ | ✅ | ✅ |
| SSO 集成 | ❌ | ❌ | ✅ | ✅ |
| 审计日志 | ❌ | 基础 | 完整 | 完整 |
| 组织架构 | ❌ | ❌ | ✅ | ✅ |
| 数据导出 | ❌ | ✅ | ✅ | ✅ |
| API 访问 | ❌ | 1万次/天 | 10万次/天 | 不限 |
| 技术支持 | 社区 | 邮件 | 7x12 电话 | 7x24 专属 |

---

## 7. 常见问题

### 7.1 安装相关

**Q: 安装时提示 Docker 未安装？**

A: 安装脚本会自动安装 Docker。如果自动安装失败，请手动安装 Docker 后重新运行安装脚本。

**Q: 安装后无法访问 Web 界面？**

A: 检查以下几点：
1. 服务是否启动：`sudo systemctl status lexprime`
2. 端口是否监听：`ss -tlnp | grep 8080`
3. 防火墙是否开放：`sudo ufw status`
4. 安全组是否放行（云服务器）

**Q: 数据库连接失败怎么办？**

A: 检查 PostgreSQL 容器状态：
```bash
cd /opt/lexprime
docker compose ps
docker compose logs postgres
```

### 7.2 性能相关

**Q: 系统运行缓慢怎么办？**

A: 
1. 运行健康检查：`sudo ./scripts/private-deploy/health-check.sh`
2. 查看资源使用：`top`, `htop`
3. 检查数据库慢查询
4. 考虑升级硬件配置

**Q: Elasticsearch 内存不足？**

A: 修改 Elasticsearch JVM 堆内存：
```bash
# 编辑 docker-compose.yml
environment:
  - ES_JAVA_OPTS=-Xms4g -Xmx4g
```

### 7.3 License 相关

**Q: License 过期了怎么办？**

A: 联系 LexPrime 销售团队续费，获取新的激活码后重新激活。

**Q: 更换服务器后 License 还能用吗？**

A: License 与机器硬件绑定，更换服务器后需要重新激活。请联系技术支持办理迁移。

**Q: 如何增加用户数？**

A: 联系销售团队升级 License，获得新的激活码后重新激活即可。

### 7.4 数据安全

**Q: 数据会上传到云端吗？**

A: 私有化部署版本所有数据都存储在您的服务器上，不会上传到任何外部服务器。

**Q: 如何保证数据安全？**

A: 
1. 定期备份数据
2. 启用 HTTPS
3. 配置访问控制
4. 启用审计日志
5. 定期更新系统补丁

---

## 8. 技术支持

### 8.1 联系方式

- **技术支持邮箱**: support@lexprime.com
- **销售咨询**: sales@lexprime.com
- **紧急支持热线**: 400-XXX-XXXX（企业版及以上）

### 8.2 服务时间

| 版本 | 支持方式 | 响应时间 |
|-----|---------|---------|
| 社区版 | 社区论坛 | - |
| 专业版 | 邮件支持 | 工作日 24 小时内 |
| 企业版 | 电话 + 邮件 | 工作日 4 小时内 |
| 旗舰版 | 7x24 专属 | 1 小时内 |

### 8.3 报错时请提供

联系技术支持时请提供以下信息：

1. License 信息
2. 版本号
3. 错误截图或日志
4. 复现步骤
5. 系统环境信息
   - 操作系统版本
   - 服务器配置
   - Docker 版本

### 8.4 日志位置

- **应用日志**: `/var/log/lexprime/`
- **系统日志**: `journalctl -u lexprime`
- **Docker 日志**: `docker compose logs`

---

## 附录

### A. 目录结构

```
/opt/lexprime/              # 安装目录
├── docker-compose.yml      # Docker Compose 配置
├── scripts/               # 管理脚本
└── VERSION                 # 版本文件

/var/lexprime/              # 数据目录
├── db/                    # 数据库数据
├── es/                    # Elasticsearch 数据
├── neo4j/                 # Neo4j 数据
├── uploads/               # 上传文件
├── cache/                 # 缓存文件
└── backup/                # 备份文件

/etc/lexprime/             # 配置目录
└── config.env             # 主配置文件

/var/log/lexprime/         # 日志目录
```

### B. 常用命令

```bash
# 服务管理
sudo systemctl start lexprime      # 启动
sudo systemctl stop lexprime       # 停止
sudo systemctl restart lexprime    # 重启
sudo systemctl status lexprime     # 状态

# 健康检查
sudo ./scripts/private-deploy/health-check.sh

# 数据备份
sudo ./scripts/private-deploy/backup.sh

# 数据恢复
sudo ./scripts/private-deploy/restore.sh --file=<备份文件>

# 查看日志
sudo journalctl -u lexprime -f
docker compose logs -f
```

### C. 版本历史

| 版本 | 日期 | 说明 |
|-----|------|------|
| 1.0.0 | 2026-07-03 | 首个私有化部署版本 |

---

**文档版本**: 1.0.0  
**最后更新**: 2026-07-03
