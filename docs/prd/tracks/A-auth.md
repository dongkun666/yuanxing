<!-- Auto-split from PRD.md v0.7.0 on 2026-06-28 -->
> 本文档为 LexPrime 全面 PRD 的分章节版本, 供各 agent 独立阅读
> 主文档: `PRD.md` · 完整 15 章节 42KB · 各章节交叉引用见 `00-index.md`

# Track A: Auth 后端 (Rust + JWT)

> 来源: PRD § 9.2 Phase 4 计划 · 12 周 Phase 4 第 1-4 周
> 负责人: 全栈 · 优先级: P0 · 工时: 4 周

---

## 1. 目标

实现律师用户注册 / 登录 / Token 刷新 / 律师执业证认证, 为后续所有功能 (OCR/Skill/数据) 提供用户体系基础。

## 2. 范围 (In Scope)

- Rust Actix-web 框架
- JWT (Access 15min + Refresh 7d)
- 律师执业证 OCR + 人工审核
- RBAC (个人版 / 企业版 / 管理员)
- 密码 bcrypt + 多因素认证 (TOTP)
- 邮箱验证 + 短信验证
- 全链路审计日志

## 3. 不在范围 (Out of Scope)

- 律所多人协作 (企业版 Phase 5)
- 第三方登录 (微信/支付宝) Phase 5
- 实名认证接口 (司法部接口对接) Phase 5

## 4. 任务分解

- W1: 选型 + 项目脚手架 + 数据库 schema
- W2: 注册 / 登录 / Token 刷新 + bcrypt + TOTP
- W3: 律师执业证 OCR (对接 PaddleOCR) + 审核工作流
- W4: 邮箱验证 + 短信验证 + 审计日志 + E2E 测试

## 5. 验收标准 (Acceptance Criteria)

- [ ] 律师可注册 + 邮箱验证 + 执业证上传
- [ ] JWT 签发 + 刷新机制正常
- [ ] TOTP 可绑定 + 验证
- [ ] 律师执业证审核工作流 (AI 初审 + 人工复审)
- [ ] 审计日志全链路可追溯
- [ ] E2E 测试覆盖 100% 核心流程
- [ ] 0 严重安全漏洞

## 6. 依赖

**前置 Track**: 无 (Phase 4 第一个启动)
**技术依赖**: Rust 1.75+ / Actix-web 4 / SQLAlchemy (Python 端复用) / Redis (Token 存储)
**资源依赖**: 短信网关 (阿里云) / 邮件服务 (SendGrid) / TOTP 算法库

## 7. 风险

- 律师执业证审核: AI 误判 → 人工复审兜底
- TOTP 密钥泄露 → 强制重置流程
- Token 刷新竞态 → 单一 refresh_token 设计

## 8. 相关 PRD 章节

- § 7.5 后端架构
- § 8 数据安全策略
- § 12.1 数据安全风险

---
**Track 任务已就绪, 等候启动。**
