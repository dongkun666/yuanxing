# LexPrime API 文档

## 概述

LexPrime API 是面向律师和律所的法律智能服务平台的核心接口层，提供判例检索、合同审查、文书生成、律师协作等全流程法律业务支持。

**服务地址**: `http://127.0.0.1:3847`  
**文档地址**: `/docs` (Swagger UI) | `/redoc` (ReDoc)  
**API 版本**: 0.1.0

---

## 认证

### Bearer Token

所有 API 接口需要在请求头中携带 Bearer Token：

```bash
curl -H "Authorization: Bearer <your_token>" http://localhost:3847/api/cases
```

### Token 获取

通过登录接口获取 token：

```bash
curl -X POST http://localhost:3847/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your_password"}'
```

---

## 错误码

| 状态码 | 说明 | 示例 |
|--------|------|------|
| 200 | 请求成功 | 正常响应 |
| 400 | 请求参数错误 | 参数校验失败、格式错误 |
| 401 | 未授权 | Token 无效或过期 |
| 403 | 无权限 | 权限不足 |
| 404 | 资源不存在 | 找不到指定的判例、法规等 |
| 409 | 冲突 | 资源已存在 |
| 413 | 请求体过大 | 文件上传超过限制 |
| 415 | 不支持的媒体类型 | 文件格式不支持 |
| 500 | 服务器内部错误 | 服务端异常 |
| 503 | 服务不可用 | 后端服务未启动 |

---

## 核心接口

### 1. 健康检查

```bash
GET /api/health
```

**响应示例**:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "timestamp": "2026-03-15T10:30:00",
  "databases": {
    "main": {"connected": true, "latency_ms": 12},
    "elasticsearch": {"connected": true, "latency_ms": 5},
    "neo4j": {"available": true, "latency_ms": 8}
  },
  "environment": "development"
}
```

### 2. 判例检索

#### 获取判例列表

```bash
GET /api/cases?cause=借款&year=2026&limit=20
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| cause | string | 案由关键词 |
| cause_category | string | 案由分类 |
| year | int | 判决年份 |
| court | string | 法院名称 |
| limit | int | 每页数量 (最大500) |
| offset | int | 偏移量 |
| full | bool | 是否返回完整字段 |

**响应示例**:

```json
[
  {
    "id": 12345,
    "doc_id": "case-abc123",
    "case_id": "(2026)京01民初123号",
    "case_name": "张三诉李四借款合同纠纷案",
    "court": "北京市第一中级人民法院",
    "cause": "借款合同纠纷",
    "cause_category": "合同纠纷",
    "judgment_date": "2026-03-15",
    "year": 2026,
    "lex_score": 85,
    "view_count": 156,
    "favorite_count": 12
  }
]
```

#### 获取判例详情

```bash
GET /api/cases/{doc_id}
```

#### 全文搜索

```bash
POST /api/search
Content-Type: application/json

{
  "query": "借款合同 违约",
  "index": "cases",
  "page": 1,
  "size": 20,
  "filters": {"cause_category": "合同纠纷"}
}
```

**响应示例**:

```json
{
  "total": 156,
  "page": 1,
  "size": 20,
  "items": [...]
}
```

### 3. 法规查询

```bash
GET /api/laws?law_type=法律&status=现行有效&limit=50
```

**响应示例**:

```json
[
  {
    "id": 1001,
    "law_id": "民法典",
    "title": "中华人民共和国民法典",
    "law_type": "法律",
    "status": "现行有效",
    "issue_date": "2020-05-28",
    "effective_date": "2021-01-01",
    "level": 1
  }
]
```

### 4. 企业查询

```bash
GET /api/companies?name=示例科技&region=北京市&limit=20
```

**响应示例**:

```json
[
  {
    "id": 2001,
    "unified_id": "91110101MA01ABCDEF",
    "company_name": "北京示例科技有限公司",
    "legal_rep": "王五",
    "business_status": "存续",
    "industry": "软件和信息技术服务业",
    "region": "北京市",
    "is_zxgk": false
  }
]
```

### 5. 合同审查

#### 上传合同文本

```bash
POST /api/contract-review/upload
Content-Type: application/json

{
  "contract_type": "借款合同",
  "contract_text": "甲方（出借人）：张三...",
  "stance": "审查方",
  "industry": "金融",
  "amount": 500000.00,
  "focus_areas": ["利息条款", "违约责任"]
}
```

**响应示例**:

```json
{
  "review_id": "cr-abc123def456",
  "status": "completed",
  "latency_ms": 1500,
  "demo_mode": false,
  "next": "GET /api/contract-review/result/cr-abc123def456"
}
```

#### 获取审查结果

```bash
GET /api/contract-review/result/{review_id}
```

#### 获取谈判策略

```bash
POST /api/contract-review/negotiation
Content-Type: application/json

{
  "review_id": "cr-abc123def456",
  "stance": "甲方",
  "additional_priorities": ["clause_001", "clause_003"]
}
```

#### 导出报告

```bash
POST /api/contract-review/export
Content-Type: application/json

{
  "review_id": "cr-abc123def456",
  "format": "markdown",
  "include_strategy": true
}
```

### 6. Marketplace

#### 获取律师列表

```bash
GET /api/marketplace/lawyers?region=上海&min_experience_years=5
```

#### 创建律师画像

```bash
POST /api/marketplace/lawyers
Content-Type: application/json

{
  "lawyer_id": "L001",
  "name": "吴律师",
  "firm_id": "firm-001",
  "specialties": ["contract_dispute", "tort"],
  "jurisdictions": ["CN", "HK"],
  "languages": ["zh-CN", "en-US"],
  "region": "上海",
  "experience_years": 8,
  "rating": 4.7,
  "cross_border_capable": true
}
```

#### 创建协同办案案件

```bash
POST /api/marketplace/cases
Content-Type: application/json

{
  "lawyer_a_id": "L001",
  "case_type": "contract_dispute",
  "case_description": "被告逾期支付货款 50 万元",
  "fee": 50000.0,
  "required_specialties": ["contract_dispute"],
  "split_ratio": 0.6
}
```

#### 创建转介绍

```bash
POST /api/marketplace/referrals
Content-Type: application/json

{
  "referrer_id": "L001",
  "target_lawyer_id": "L002",
  "case_type": "intellectual_property",
  "case_description": "客户商标侵权案",
  "expected_fee": 30000.0,
  "match_score": 0.85
}
```

#### 创建跨境文件订单

```bash
POST /api/marketplace/cross-border
Content-Type: application/json

{
  "lawyer_id": "L001",
  "client_id": "client-002",
  "doc_type": "letter",
  "language": "en-US",
  "jurisdiction": "US",
  "fields": {"recipient": "ABC Corp", "amount_usd": 50000}
}
```

#### 获取 Marketplace 统计

```bash
GET /api/marketplace/metrics?period_days=30
```

### 7. AI 服务

#### AI 对话

```bash
POST /api/ai/chat
Content-Type: application/json

{
  "message": "帮我起草一份起诉状",
  "conversation_id": "conv-001",
  "stream": false
}
```

**响应示例**:

```json
{
  "reply": "好的！我来帮您起草起诉状...",
  "conversation_id": "conv-001",
  "disclaimer": "AI 输出仅供参考，不构成法律意见。"
}
```

#### 案件摘要

```bash
POST /api/ai/case-summary
Content-Type: application/json

{
  "case_name": "张三诉李四借款合同纠纷案",
  "case_number": "(2026)京01民初123号",
  "case_type": "借款合同纠纷",
  "plaintiff": "张三",
  "defendant": "李四",
  "amount": "50万元",
  "court": "北京市第一中级人民法院",
  "claims": "判令被告返还借款本金50万元",
  "facts": "原被告于2025年3月签订借款合同..."
}
```

#### 文书润色

```bash
POST /api/ai/polish
Content-Type: application/json

{
  "content": "借钱不还，打官司告他",
  "options": {
    "legalTerms": true,
    "logic": true,
    "typos": true,
    "format": true,
    "tone": false
  }
}
```

#### 智能填空

```bash
POST /api/ai/auto-fill
Content-Type: application/json

{
  "template_id": "complaint-001",
  "case_info": {
    "plaintiff": "张三",
    "defendant": "李四",
    "cause": "借款合同纠纷",
    "amount": "50万元",
    "court": "北京市海淀区人民法院"
  }
}
```

### 8. 日程管理

```bash
# 获取日程列表
GET /api/schedule?date_from=2026-03-01&date_to=2026-03-31

# 创建日程
POST /api/schedule
Content-Type: application/json

{
  "title": "案件开庭",
  "date": "2026-03-20",
  "time": "09:00",
  "duration": 180,
  "type": "court",
  "case_id": 12345
}

# 更新日程
PUT /api/schedule/{id}

# 删除日程
DELETE /api/schedule/{id}

# 检查时间冲突
GET /api/schedule/conflicts?date=2026-03-20&time=09:00

# 获取今日日程
GET /api/schedule/today
```

### 9. 客户管理

```bash
# 获取客户列表
GET /api/clients?page=1&page_size=20&search=张三

# 获取客户详情
GET /api/clients/{client_id}

# 创建客户
POST /api/clients
Content-Type: application/json

{
  "name": "张三",
  "client_type": "individual",
  "phone": "13800138000",
  "email": "zhangsan@example.com",
  "grade": "VIP"
}

# 更新客户
PUT /api/clients/{client_id}

# 删除客户
DELETE /api/clients/{client_id}

# 利益冲突检查
POST /api/clients/{client_id}/conflict-check

# 客户统计
GET /api/clients/stats?firm_id=firm-001
```

### 10. 律所管理

```bash
# 获取律所律师列表
GET /api/firm/lawyers?firm_id=firm-001&role=partner

# 创建工时记录
POST /api/firm/time-entries?firm_id=firm-001
Content-Type: application/json

{
  "lawyer_id": "L001",
  "case_id": 12345,
  "entry_date": "2026-03-15",
  "hours": 4.5,
  "description": "起草起诉状",
  "billable": true,
  "rate": 800.0
}

# 获取律所统计
GET /api/firm/stats?firm_id=firm-001
```

---

## JavaScript 使用示例

### 基础请求

```javascript
// 配置
const API_BASE = 'http://localhost:3847';
const token = 'your_token';

// 获取判例列表
async function getCases() {
  const response = await fetch(`${API_BASE}/api/cases?limit=20`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
}

// 搜索判例
async function searchCases(query) {
  const response = await fetch(`${API_BASE}/api/search`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query: query,
      index: 'cases',
      page: 1,
      size: 20
    })
  });
  return await response.json();
}

// 合同审查
async function reviewContract(contractText) {
  const response = await fetch(`${API_BASE}/api/contract-review/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      contract_type: '借款合同',
      contract_text: contractText,
      stance: '审查方'
    })
  });
  const result = await response.json();
  
  // 获取审查结果
  const detailResponse = await fetch(
    `${API_BASE}/api/contract-review/result/${result.review_id}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  return await detailResponse.json();
}

// AI 对话
async function chatWithAI(message) {
  const response = await fetch(`${API_BASE}/api/ai/chat`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: message,
      stream: false
    })
  });
  return await response.json();
}
```

---

## 最佳实践

### 分页策略

- 使用 `limit` 和 `offset` 参数实现分页
- 单次请求 `limit` 建议不超过 100
- 前端应实现滚动加载或分页控件

### 搜索优化

- 搜索关键词建议 2-10 个字符
- 使用 `filters` 参数缩小搜索范围
- 优先使用分类筛选再进行全文搜索

### 错误处理

```javascript
async function safeApiCall(url, options) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || error.message || '请求失败');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    
    if (error.message.includes('401')) {
      // Token 过期，重新登录
      window.location.href = '/login';
    }
    
    throw error;
  }
}
```

### 性能优化

- 列表接口默认返回精简数据，详情页再请求完整数据
- 使用 `?full=false` 减少数据传输
- 对频繁请求的接口使用缓存

---

## 变更日志

### v0.1.0 (2026-07-03)

- 初始版本
- 支持判例检索、法规查询、企业查询
- 支持合同审查、文书生成
- 支持 Marketplace 律师协作
- 支持 AI 服务（对话、摘要、润色、填空）
- 支持日程管理、客户管理
