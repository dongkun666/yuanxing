# LexPrime 域名配置指南

## 1. 域名注册

### 1.1 推荐注册商
- **阿里云/万网**：国内首选，支持工信部备案
- **腾讯云**：国内主流，备案流程便捷
- **GoDaddy**：国际知名，适合海外部署
- **Namecheap**：性价比高，支持隐私保护

### 1.2 域名注册步骤

1. **查询域名可用性**
   ```bash
   # 使用 whois 查询
   whois lexprime.com
   ```

2. **注册主域名**
   - `lexprime.com` - 主域名
   - `lexprime.cn` - 国内备用域名（如需要）

3. **注册子域名规划**
   - `api.lexprime.com` - API 服务
   - `www.lexprime.com` - 主站
   - `cdn.lexprime.com` - CDN 加速
   - `admin.lexprime.com` - 管理后台
   - `monitor.lexprime.com` - 监控面板

### 1.3 域名安全设置

- **开启 WHOIS 隐私保护**
- **设置域名锁定（Domain Lock）**
- **配置注册商 2FA（双因素认证）**
- **添加域名联系人邮箱验证**

---

## 2. DNS 配置

### 2.1 记录类型说明

| 记录类型 | 名称 | 值 | 说明 |
|---------|------|-----|------|
| A | @ | 服务器公网 IP | 主域名指向服务器 |
| A | www | 服务器公网 IP | www 子域名 |
| A | api | 服务器公网 IP | API 服务 |
| A | monitor | 服务器公网 IP | 监控面板 |
| CNAME | cdn | CDN 服务商域名 | CDN 加速 |
| MX | @ | 邮件服务商地址 | 邮件服务 |
| TXT | @ | v=spf1 include:_spf.mailgun.org ~all | SPF 记录 |
| TXT | _dmarc | v=DMARC1; p=none; sp=none; fo=1 | DMARC 记录 |
| CNAME | _acme-challenge | Let's Encrypt 验证 | HTTPS 自动续期 |

### 2.2 阿里云 DNS 配置示例

```json
{
  "records": [
    {
      "type": "A",
      "name": "@",
      "value": "123.45.67.89",
      "ttl": 600
    },
    {
      "type": "A",
      "name": "www",
      "value": "123.45.67.89",
      "ttl": 600
    },
    {
      "type": "A",
      "name": "api",
      "value": "123.45.67.89",
      "ttl": 600
    },
    {
      "type": "CNAME",
      "name": "cdn",
      "value": "lexprime.com.cdn.dnsv1.com",
      "ttl": 600
    }
  ]
}
```

### 2.3 DNS 验证

```bash
# 验证 A 记录
dig A lexprime.com +short

# 验证 API 子域名
dig A api.lexprime.com +short

# 验证所有记录
dig lexprime.com ANY
```

---

## 3. HTTPS 配置

### 3.1 使用 Let's Encrypt（推荐）

#### 3.1.1 安装 Certbot

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

#### 3.1.2 生成证书

```bash
# 生成单域名证书
sudo certbot certonly --nginx -d lexprime.com -d www.lexprime.com -d api.lexprime.com

# 生成通配符证书（推荐）
sudo certbot certonly --manual --preferred-challenges=dns -d '*.lexprime.com' -d lexprime.com
```

#### 3.1.3 证书自动续期

```bash
# 测试续期
sudo certbot renew --dry-run

# 添加 cron 任务（每天凌晨 3 点执行）
echo "0 3 * * * root certbot renew --quiet --deploy-hook 'docker-compose restart frontend'" | sudo tee -a /etc/crontab
```

#### 3.1.4 证书文件位置

```
/etc/letsencrypt/live/lexprime.com/
├── cert.pem          # 证书文件
├── chain.pem         # 证书链
├── fullchain.pem     # 完整证书链（Nginx 使用这个）
└── privkey.pem       # 私钥文件
```

### 3.2 SSL 证书配置到 Docker

将证书挂载到 Nginx 容器：

```bash
# 创建 SSL 目录
mkdir -p /workspace/ssl

# 复制证书文件
sudo cp /etc/letsencrypt/live/lexprime.com/fullchain.pem /workspace/ssl/
sudo cp /etc/letsencrypt/live/lexprime.com/privkey.pem /workspace/ssl/

# 设置权限
sudo chown -R www-data:www-data /workspace/ssl
sudo chmod 600 /workspace/ssl/*.pem
```

### 3.3 SSL 安全配置建议

- 使用 TLS 1.2+
- 禁用弱加密算法
- 启用 HSTS（HTTP Strict Transport Security）
- 配置 OCSP Stapling

---

## 4. CDN 配置

### 4.1 CDN 服务商选择

| 服务商 | 优势 | 适用场景 |
|-------|------|---------|
| 阿里云 CDN | 国内节点多，速度快 | 国内用户为主 |
| 腾讯云 CDN | 价格优惠，配置简单 | 中小规模站点 |
| Cloudflare | 免费版可用，全球节点 | 海外用户为主 |
| AWS CloudFront | 企业级，功能强 | 复杂场景 |

### 4.2 Cloudflare 配置指南

#### 4.2.1 添加站点

1. 登录 Cloudflare 控制台
2. 添加站点 `lexprime.com`
3. 更新域名 NS 记录为 Cloudflare 提供的 NS 服务器

#### 4.2.2 配置 DNS 记录

| 类型 | 名称 | 目标 | 状态 |
|-----|------|-----|------|
| A | @ | 服务器 IP | 橙色（已代理） |
| A | www | 服务器 IP | 橙色（已代理） |
| A | api | 服务器 IP | 橙色（已代理） |
| CNAME | cdn | lexprime.com | 橙色（已代理） |

#### 4.2.3 SSL/TLS 设置

- **SSL/TLS 加密模式**：完全（Strict）
- **自动 HTTPS 重定向**：开启
- **HSTS**：开启（max-age=31536000）
- **TLS 1.3**：开启

#### 4.2.4 缓存规则

```javascript
// 静态资源缓存 1 年
*.js, *.css, *.png, *.jpg, *.svg -> Cache Level: Cache Everything, Edge TTL: 1 year

// API 请求不缓存
/api/* -> Cache Level: Bypass

// HTML 文件缓存 1 小时
*.html -> Cache Level: Standard, Edge TTL: 1 hour
```

#### 4.2.5 页面规则示例

| 规则 | 设置 |
|-----|------|
| `api.lexprime.com/*` | 缓存级别：绕过缓存，浏览器缓存 TTL：30 分钟 |
| `lexprime.com/assets/*` | 缓存级别：缓存一切，边缘 TTL：1 年 |
| `lexprime.com/*` | 始终使用 HTTPS |

### 4.3 CDN 验证

```bash
# 验证 CDN 是否生效
curl -I https://lexprime.com | grep -i "cf-ray"

# 查看缓存状态
curl -I https://lexprime.com/assets/app.js | grep -i "cf-cache-status"
```

---

## 5. 域名备案（国内服务器）

### 5.1 备案材料

- 域名证书
- 服务器购买凭证
- 企业营业执照（企业备案）
- 负责人身份证
- 备案真实性核验单

### 5.2 备案流程

1. **准备材料** → 2. **填写备案信息** → 3. **提交审核** → 4. **短信验证** → 5. **管局审核** → 6. **备案通过**

### 5.3 备案注意事项

- 备案期间域名无法访问（约 10-20 个工作日）
- 建议提前准备备案，不要等到上线前才开始
- 备案成功后如需变更域名/服务器，需重新备案或做变更备案

---

## 6. 配置检查清单

- [ ] 域名已注册并完成实名认证
- [ ] DNS 记录已正确配置（A/CNAME/MX/TXT）
- [ ] DNS 记录已生效（TTL 时间内）
- [ ] SSL 证书已安装并配置
- [ ] HTTPS 重定向已配置
- [ ] HSTS 已启用
- [ ] CDN 已配置并生效
- [ ] 域名已完成备案（国内服务器）
- [ ] 证书自动续期已配置
- [ ] 安全设置已完成（域名锁定、2FA）