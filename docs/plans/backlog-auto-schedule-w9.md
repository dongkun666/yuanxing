# Backlog Auto-Schedule W9 (DRY-RUN (no mavis plan queued))

> 自动生成于 2026-06-29T13:49:22Z, 来自 PRD backlog open P0+P1 ticket → mavis team plan YAML

## 状态

- **Status**: DRY-RUN (no mavis plan queued)
- **调度命令**: `mavis team plan run --no-wait /mnt/e/元枢法智前端/yuanxing/docs/plans/plan-auto-w10-from-backlog.yaml`
- **Plan YAML**: [plan-auto-w10-from-backlog.yaml](./plan-auto-w10-from-backlog.yaml) (full path: `/mnt/e/元枢法智前端/yuanxing/docs/plans/plan-auto-w10-from-backlog.yaml`)
- **触发**: scripts/auto_schedule_backlog.py (W9 A2)

## 数据源

- **Database**: `prd_backlog` (SQLite)
- **过滤条件**: `status='open' AND priority IN ('P0', 'P1') AND created_at >= NOW() - 24h`
- **Ticket 总数**: 245

## Ticket 分布 (按 category)

| Category | Count | Owner 集合 | Priority 分布 |
| --- | ---: | --- | --- |
| 产品 | 105 | lex-ai, lex-coder, lex-design | P0=56, P1=49 |
| 技术 | 49 | lex-ai, lex-coder | P0=21, P1=28 |
| 法务 | 70 | lex-ai | P0=35, P1=35 |
| 其他 | 21 | lex-pm | P0=7, P1=14 |

## Ticket 明细 (按 priority, P0 → P3, ID 升序)

| ID | Category | Priority | Owner | Title |
| ---: | --- | --- | --- | --- |
| 1 | 产品 | P0 | lex-coder | UI 团队协同 (主任派单 + 授薪审查 + 主任审核) |
| 2 | 产品 | P0 | lex-coder | UI 客户友好版 (隐藏法条 + 突出风险 + 客户白话解释) |
| 3 | 产品 | P0 | lex-coder | 批量审查 UI (批量上传 + 批量审查 + 风险汇总 + 仪表盘) |
| 4 | 产品 | P0 | lex-design | 私有化部署 UI (公司 Logo + 主题色 + 审计日志 + SSO + 数据导出 + 私有模型微调) |
| 5 | 产品 | P0 | lex-ai | 跨 Skill 引用 (Skill 1+2 联动: 合同审查 → 类案检索) |
| 6 | 产品 | P0 | lex-ai | 红黄绿灯规则详细定义 (yellow = 存在 major 无 fatal, 边界清晰化) |
| 7 | 产品 | P0 | lex-ai | 风险分级按行业上下文动态调整 (婚姻家事产权归属 = major, IT 产权归属 = advisory) |
| 8 | 产品 | P0 | lex-ai | '建议争取' 改 '建议明确约定' (避免客户误解) |
| 43 | 产品 | P0 | lex-coder | UI 团队协同 (主任派单 + 授薪审查 + 主任审核) |
| 44 | 产品 | P0 | lex-coder | UI 客户友好版 (隐藏法条 + 突出风险 + 客户白话解释) |
| 45 | 产品 | P0 | lex-coder | 批量审查 UI (批量上传 + 批量审查 + 风险汇总 + 仪表盘) |
| 46 | 产品 | P0 | lex-design | 私有化部署 UI (公司 Logo + 主题色 + 审计日志 + SSO + 数据导出 + 私有模型微调) |
| 47 | 产品 | P0 | lex-ai | 跨 Skill 引用 (Skill 1+2 联动: 合同审查 → 类案检索) |
| 48 | 产品 | P0 | lex-ai | 红黄绿灯规则详细定义 (yellow = 存在 major 无 fatal, 边界清晰化) |
| 49 | 产品 | P0 | lex-ai | 风险分级按行业上下文动态调整 (婚姻家事产权归属 = major, IT 产权归属 = advisory) |
| 50 | 产品 | P0 | lex-ai | '建议争取' 改 '建议明确约定' (避免客户误解) |
| 85 | 产品 | P0 | lex-coder | UI 团队协同 (主任派单 + 授薪审查 + 主任审核) |
| 86 | 产品 | P0 | lex-coder | UI 客户友好版 (隐藏法条 + 突出风险 + 客户白话解释) |
| 87 | 产品 | P0 | lex-coder | 批量审查 UI (批量上传 + 批量审查 + 风险汇总 + 仪表盘) |
| 88 | 产品 | P0 | lex-design | 私有化部署 UI (公司 Logo + 主题色 + 审计日志 + SSO + 数据导出 + 私有模型微调) |
| 89 | 产品 | P0 | lex-ai | 跨 Skill 引用 (Skill 1+2 联动: 合同审查 → 类案检索) |
| 90 | 产品 | P0 | lex-ai | 红黄绿灯规则详细定义 (yellow = 存在 major 无 fatal, 边界清晰化) |
| 91 | 产品 | P0 | lex-ai | 风险分级按行业上下文动态调整 (婚姻家事产权归属 = major, IT 产权归属 = advisory) |
| 92 | 产品 | P0 | lex-ai | '建议争取' 改 '建议明确约定' (避免客户误解) |
| 127 | 产品 | P0 | lex-coder | UI 团队协同 (主任派单 + 授薪审查 + 主任审核) |
| 128 | 产品 | P0 | lex-coder | UI 客户友好版 (隐藏法条 + 突出风险 + 客户白话解释) |
| 129 | 产品 | P0 | lex-coder | 批量审查 UI (批量上传 + 批量审查 + 风险汇总 + 仪表盘) |
| 130 | 产品 | P0 | lex-design | 私有化部署 UI (公司 Logo + 主题色 + 审计日志 + SSO + 数据导出 + 私有模型微调) |
| 131 | 产品 | P0 | lex-ai | 跨 Skill 引用 (Skill 1+2 联动: 合同审查 → 类案检索) |
| 132 | 产品 | P0 | lex-ai | 红黄绿灯规则详细定义 (yellow = 存在 major 无 fatal, 边界清晰化) |
| 133 | 产品 | P0 | lex-ai | 风险分级按行业上下文动态调整 (婚姻家事产权归属 = major, IT 产权归属 = advisory) |
| 134 | 产品 | P0 | lex-ai | '建议争取' 改 '建议明确约定' (避免客户误解) |
| 169 | 产品 | P0 | lex-coder | UI 团队协同 (主任派单 + 授薪审查 + 主任审核) |
| 170 | 产品 | P0 | lex-coder | UI 客户友好版 (隐藏法条 + 突出风险 + 客户白话解释) |
| 171 | 产品 | P0 | lex-coder | 批量审查 UI (批量上传 + 批量审查 + 风险汇总 + 仪表盘) |
| 172 | 产品 | P0 | lex-design | 私有化部署 UI (公司 Logo + 主题色 + 审计日志 + SSO + 数据导出 + 私有模型微调) |
| 173 | 产品 | P0 | lex-ai | 跨 Skill 引用 (Skill 1+2 联动: 合同审查 → 类案检索) |
| 174 | 产品 | P0 | lex-ai | 红黄绿灯规则详细定义 (yellow = 存在 major 无 fatal, 边界清晰化) |
| 175 | 产品 | P0 | lex-ai | 风险分级按行业上下文动态调整 (婚姻家事产权归属 = major, IT 产权归属 = advisory) |
| 176 | 产品 | P0 | lex-ai | '建议争取' 改 '建议明确约定' (避免客户误解) |
| 211 | 产品 | P0 | lex-coder | UI 团队协同 (主任派单 + 授薪审查 + 主任审核) |
| 212 | 产品 | P0 | lex-coder | UI 客户友好版 (隐藏法条 + 突出风险 + 客户白话解释) |
| 213 | 产品 | P0 | lex-coder | 批量审查 UI (批量上传 + 批量审查 + 风险汇总 + 仪表盘) |
| 214 | 产品 | P0 | lex-design | 私有化部署 UI (公司 Logo + 主题色 + 审计日志 + SSO + 数据导出 + 私有模型微调) |
| 215 | 产品 | P0 | lex-ai | 跨 Skill 引用 (Skill 1+2 联动: 合同审查 → 类案检索) |
| 216 | 产品 | P0 | lex-ai | 红黄绿灯规则详细定义 (yellow = 存在 major 无 fatal, 边界清晰化) |
| 217 | 产品 | P0 | lex-ai | 风险分级按行业上下文动态调整 (婚姻家事产权归属 = major, IT 产权归属 = advisory) |
| 218 | 产品 | P0 | lex-ai | '建议争取' 改 '建议明确约定' (避免客户误解) |
| 253 | 产品 | P0 | lex-coder | UI 团队协同 (主任派单 + 授薪审查 + 主任审核) |
| 254 | 产品 | P0 | lex-coder | UI 客户友好版 (隐藏法条 + 突出风险 + 客户白话解释) |
| 255 | 产品 | P0 | lex-coder | 批量审查 UI (批量上传 + 批量审查 + 风险汇总 + 仪表盘) |
| 256 | 产品 | P0 | lex-design | 私有化部署 UI (公司 Logo + 主题色 + 审计日志 + SSO + 数据导出 + 私有模型微调) |
| 257 | 产品 | P0 | lex-ai | 跨 Skill 引用 (Skill 1+2 联动: 合同审查 → 类案检索) |
| 258 | 产品 | P0 | lex-ai | 红黄绿灯规则详细定义 (yellow = 存在 major 无 fatal, 边界清晰化) |
| 259 | 产品 | P0 | lex-ai | 风险分级按行业上下文动态调整 (婚姻家事产权归属 = major, IT 产权归属 = advisory) |
| 260 | 产品 | P0 | lex-ai | '建议争取' 改 '建议明确约定' (避免客户误解) |
| 39 | 其他 | P0 | lex-pm | 隐私脱敏 3 档原则 (公开/内部/私密) + git 提交 checklist |
| 81 | 其他 | P0 | lex-pm | 隐私脱敏 3 档原则 (公开/内部/私密) + git 提交 checklist |
| 123 | 其他 | P0 | lex-pm | 隐私脱敏 3 档原则 (公开/内部/私密) + git 提交 checklist |
| 165 | 其他 | P0 | lex-pm | 隐私脱敏 3 档原则 (公开/内部/私密) + git 提交 checklist |
| 207 | 其他 | P0 | lex-pm | 隐私脱敏 3 档原则 (公开/内部/私密) + git 提交 checklist |
| 249 | 其他 | P0 | lex-pm | 隐私脱敏 3 档原则 (公开/内部/私密) + git 提交 checklist |
| 291 | 其他 | P0 | lex-pm | 隐私脱敏 3 档原则 (公开/内部/私密) + git 提交 checklist |
| 19 | 技术 | P0 | lex-ai | OCR 引擎冷启动优化 (PaddleOcrEngine + Tesseract fallback, 冷启动 < 10s |
| 20 | 技术 | P0 | lex-ai | 批量审查支持 PDF/Word/扫描件混合上传 (OCR 集成) |
| 21 | 技术 | P0 | lex-coder | SSO 集成 LDAP/Active Directory (公司账号登录) |
| 61 | 技术 | P0 | lex-ai | OCR 引擎冷启动优化 (PaddleOcrEngine + Tesseract fallback, 冷启动 < 10s |
| 62 | 技术 | P0 | lex-ai | 批量审查支持 PDF/Word/扫描件混合上传 (OCR 集成) |
| 63 | 技术 | P0 | lex-coder | SSO 集成 LDAP/Active Directory (公司账号登录) |
| 103 | 技术 | P0 | lex-ai | OCR 引擎冷启动优化 (PaddleOcrEngine + Tesseract fallback, 冷启动 < 10s |
| 104 | 技术 | P0 | lex-ai | 批量审查支持 PDF/Word/扫描件混合上传 (OCR 集成) |
| 105 | 技术 | P0 | lex-coder | SSO 集成 LDAP/Active Directory (公司账号登录) |
| 145 | 技术 | P0 | lex-ai | OCR 引擎冷启动优化 (PaddleOcrEngine + Tesseract fallback, 冷启动 < 10s |
| 146 | 技术 | P0 | lex-ai | 批量审查支持 PDF/Word/扫描件混合上传 (OCR 集成) |
| 147 | 技术 | P0 | lex-coder | SSO 集成 LDAP/Active Directory (公司账号登录) |
| 187 | 技术 | P0 | lex-ai | OCR 引擎冷启动优化 (PaddleOcrEngine + Tesseract fallback, 冷启动 < 10s |
| 188 | 技术 | P0 | lex-ai | 批量审查支持 PDF/Word/扫描件混合上传 (OCR 集成) |
| 189 | 技术 | P0 | lex-coder | SSO 集成 LDAP/Active Directory (公司账号登录) |
| 229 | 技术 | P0 | lex-ai | OCR 引擎冷启动优化 (PaddleOcrEngine + Tesseract fallback, 冷启动 < 10s |
| 230 | 技术 | P0 | lex-ai | 批量审查支持 PDF/Word/扫描件混合上传 (OCR 集成) |
| 231 | 技术 | P0 | lex-coder | SSO 集成 LDAP/Active Directory (公司账号登录) |
| 271 | 技术 | P0 | lex-ai | OCR 引擎冷启动优化 (PaddleOcrEngine + Tesseract fallback, 冷启动 < 10s |
| 272 | 技术 | P0 | lex-ai | 批量审查支持 PDF/Word/扫描件混合上传 (OCR 集成) |
| 273 | 技术 | P0 | lex-coder | SSO 集成 LDAP/Active Directory (公司账号登录) |
| 27 | 法务 | P0 | lex-ai | 房屋租赁 clause 4 押金条款 baseline 升级 major |
| 28 | 法务 | P0 | lex-ai | 借款合同 clause 3 利息 24% 边界 baseline 升级 major |
| 29 | 法务 | P0 | lex-ai | 销售合同 clause 5 终身维修 baseline 升级 major |
| 30 | 法务 | P0 | lex-ai | 劳动合同 clause 7 永久保密 baseline 升级 major |
| 31 | 法务 | P0 | lex-ai | 服务合同 clause 4 知识产权 + clause 5 维护期 baseline 升级 major |
| 69 | 法务 | P0 | lex-ai | 房屋租赁 clause 4 押金条款 baseline 升级 major |
| 70 | 法务 | P0 | lex-ai | 借款合同 clause 3 利息 24% 边界 baseline 升级 major |
| 71 | 法务 | P0 | lex-ai | 销售合同 clause 5 终身维修 baseline 升级 major |
| 72 | 法务 | P0 | lex-ai | 劳动合同 clause 7 永久保密 baseline 升级 major |
| 73 | 法务 | P0 | lex-ai | 服务合同 clause 4 知识产权 + clause 5 维护期 baseline 升级 major |
| 111 | 法务 | P0 | lex-ai | 房屋租赁 clause 4 押金条款 baseline 升级 major |
| 112 | 法务 | P0 | lex-ai | 借款合同 clause 3 利息 24% 边界 baseline 升级 major |
| 113 | 法务 | P0 | lex-ai | 销售合同 clause 5 终身维修 baseline 升级 major |
| 114 | 法务 | P0 | lex-ai | 劳动合同 clause 7 永久保密 baseline 升级 major |
| 115 | 法务 | P0 | lex-ai | 服务合同 clause 4 知识产权 + clause 5 维护期 baseline 升级 major |
| 153 | 法务 | P0 | lex-ai | 房屋租赁 clause 4 押金条款 baseline 升级 major |
| 154 | 法务 | P0 | lex-ai | 借款合同 clause 3 利息 24% 边界 baseline 升级 major |
| 155 | 法务 | P0 | lex-ai | 销售合同 clause 5 终身维修 baseline 升级 major |
| 156 | 法务 | P0 | lex-ai | 劳动合同 clause 7 永久保密 baseline 升级 major |
| 157 | 法务 | P0 | lex-ai | 服务合同 clause 4 知识产权 + clause 5 维护期 baseline 升级 major |
| 195 | 法务 | P0 | lex-ai | 房屋租赁 clause 4 押金条款 baseline 升级 major |
| 196 | 法务 | P0 | lex-ai | 借款合同 clause 3 利息 24% 边界 baseline 升级 major |
| 197 | 法务 | P0 | lex-ai | 销售合同 clause 5 终身维修 baseline 升级 major |
| 198 | 法务 | P0 | lex-ai | 劳动合同 clause 7 永久保密 baseline 升级 major |
| 199 | 法务 | P0 | lex-ai | 服务合同 clause 4 知识产权 + clause 5 维护期 baseline 升级 major |
| 237 | 法务 | P0 | lex-ai | 房屋租赁 clause 4 押金条款 baseline 升级 major |
| 238 | 法务 | P0 | lex-ai | 借款合同 clause 3 利息 24% 边界 baseline 升级 major |
| 239 | 法务 | P0 | lex-ai | 销售合同 clause 5 终身维修 baseline 升级 major |
| 240 | 法务 | P0 | lex-ai | 劳动合同 clause 7 永久保密 baseline 升级 major |
| 241 | 法务 | P0 | lex-ai | 服务合同 clause 4 知识产权 + clause 5 维护期 baseline 升级 major |
| 279 | 法务 | P0 | lex-ai | 房屋租赁 clause 4 押金条款 baseline 升级 major |
| 280 | 法务 | P0 | lex-ai | 借款合同 clause 3 利息 24% 边界 baseline 升级 major |
| 281 | 法务 | P0 | lex-ai | 销售合同 clause 5 终身维修 baseline 升级 major |
| 282 | 法务 | P0 | lex-ai | 劳动合同 clause 7 永久保密 baseline 升级 major |
| 283 | 法务 | P0 | lex-ai | 服务合同 clause 4 知识产权 + clause 5 维护期 baseline 升级 major |
| 9 | 产品 | P1 | lex-coder | 立场切换 (甲方/乙方/丙方/审查方) |
| 10 | 产品 | P1 | lex-ai | 立场组合 (联合体 / 多方合同 / 担保链) |
| 11 | 产品 | P1 | lex-ai | 模板版本管理 (按行业/标的/复杂度) |
| 12 | 产品 | P1 | lex-coder | 风险驾驶舱自动告警 (邮件/微信) |
| 13 | 产品 | P1 | lex-coder | 跨部门权限管理 (业务部门只读, 法务部读写) |
| 14 | 产品 | P1 | lex-design | § 3.21.4 智能界面适配 (按律师执业画像) |
| 15 | 产品 | P1 | lex-ai | § 3.21.6 合同审查偏好记忆 (严苛度/行业侧重/风险阈值) |
| 51 | 产品 | P1 | lex-coder | 立场切换 (甲方/乙方/丙方/审查方) |
| 52 | 产品 | P1 | lex-ai | 立场组合 (联合体 / 多方合同 / 担保链) |
| 53 | 产品 | P1 | lex-ai | 模板版本管理 (按行业/标的/复杂度) |
| 54 | 产品 | P1 | lex-coder | 风险驾驶舱自动告警 (邮件/微信) |
| 55 | 产品 | P1 | lex-coder | 跨部门权限管理 (业务部门只读, 法务部读写) |
| 56 | 产品 | P1 | lex-design | § 3.21.4 智能界面适配 (按律师执业画像) |
| 57 | 产品 | P1 | lex-ai | § 3.21.6 合同审查偏好记忆 (严苛度/行业侧重/风险阈值) |
| 93 | 产品 | P1 | lex-coder | 立场切换 (甲方/乙方/丙方/审查方) |
| 94 | 产品 | P1 | lex-ai | 立场组合 (联合体 / 多方合同 / 担保链) |
| 95 | 产品 | P1 | lex-ai | 模板版本管理 (按行业/标的/复杂度) |
| 96 | 产品 | P1 | lex-coder | 风险驾驶舱自动告警 (邮件/微信) |
| 97 | 产品 | P1 | lex-coder | 跨部门权限管理 (业务部门只读, 法务部读写) |
| 98 | 产品 | P1 | lex-design | § 3.21.4 智能界面适配 (按律师执业画像) |
| 99 | 产品 | P1 | lex-ai | § 3.21.6 合同审查偏好记忆 (严苛度/行业侧重/风险阈值) |
| 135 | 产品 | P1 | lex-coder | 立场切换 (甲方/乙方/丙方/审查方) |
| 136 | 产品 | P1 | lex-ai | 立场组合 (联合体 / 多方合同 / 担保链) |
| 137 | 产品 | P1 | lex-ai | 模板版本管理 (按行业/标的/复杂度) |
| 138 | 产品 | P1 | lex-coder | 风险驾驶舱自动告警 (邮件/微信) |
| 139 | 产品 | P1 | lex-coder | 跨部门权限管理 (业务部门只读, 法务部读写) |
| 140 | 产品 | P1 | lex-design | § 3.21.4 智能界面适配 (按律师执业画像) |
| 141 | 产品 | P1 | lex-ai | § 3.21.6 合同审查偏好记忆 (严苛度/行业侧重/风险阈值) |
| 177 | 产品 | P1 | lex-coder | 立场切换 (甲方/乙方/丙方/审查方) |
| 178 | 产品 | P1 | lex-ai | 立场组合 (联合体 / 多方合同 / 担保链) |
| 179 | 产品 | P1 | lex-ai | 模板版本管理 (按行业/标的/复杂度) |
| 180 | 产品 | P1 | lex-coder | 风险驾驶舱自动告警 (邮件/微信) |
| 181 | 产品 | P1 | lex-coder | 跨部门权限管理 (业务部门只读, 法务部读写) |
| 182 | 产品 | P1 | lex-design | § 3.21.4 智能界面适配 (按律师执业画像) |
| 183 | 产品 | P1 | lex-ai | § 3.21.6 合同审查偏好记忆 (严苛度/行业侧重/风险阈值) |
| 219 | 产品 | P1 | lex-coder | 立场切换 (甲方/乙方/丙方/审查方) |
| 220 | 产品 | P1 | lex-ai | 立场组合 (联合体 / 多方合同 / 担保链) |
| 221 | 产品 | P1 | lex-ai | 模板版本管理 (按行业/标的/复杂度) |
| 222 | 产品 | P1 | lex-coder | 风险驾驶舱自动告警 (邮件/微信) |
| 223 | 产品 | P1 | lex-coder | 跨部门权限管理 (业务部门只读, 法务部读写) |
| 224 | 产品 | P1 | lex-design | § 3.21.4 智能界面适配 (按律师执业画像) |
| 225 | 产品 | P1 | lex-ai | § 3.21.6 合同审查偏好记忆 (严苛度/行业侧重/风险阈值) |
| 261 | 产品 | P1 | lex-coder | 立场切换 (甲方/乙方/丙方/审查方) |
| 262 | 产品 | P1 | lex-ai | 立场组合 (联合体 / 多方合同 / 担保链) |
| 263 | 产品 | P1 | lex-ai | 模板版本管理 (按行业/标的/复杂度) |
| 264 | 产品 | P1 | lex-coder | 风险驾驶舱自动告警 (邮件/微信) |
| 265 | 产品 | P1 | lex-coder | 跨部门权限管理 (业务部门只读, 法务部读写) |
| 266 | 产品 | P1 | lex-design | § 3.21.4 智能界面适配 (按律师执业画像) |
| 267 | 产品 | P1 | lex-ai | § 3.21.6 合同审查偏好记忆 (严苛度/行业侧重/风险阈值) |
| 40 | 其他 | P1 | lex-pm | 律师推荐语 (评审律师推荐同行, 推动付费转化) |
| 41 | 其他 | P1 | lex-pm | 引荐网络 #R3-#R6 (评审律师引荐同行) |
| 82 | 其他 | P1 | lex-pm | 律师推荐语 (评审律师推荐同行, 推动付费转化) |
| 83 | 其他 | P1 | lex-pm | 引荐网络 #R3-#R6 (评审律师引荐同行) |
| 124 | 其他 | P1 | lex-pm | 律师推荐语 (评审律师推荐同行, 推动付费转化) |
| 125 | 其他 | P1 | lex-pm | 引荐网络 #R3-#R6 (评审律师引荐同行) |
| 166 | 其他 | P1 | lex-pm | 律师推荐语 (评审律师推荐同行, 推动付费转化) |
| 167 | 其他 | P1 | lex-pm | 引荐网络 #R3-#R6 (评审律师引荐同行) |
| 208 | 其他 | P1 | lex-pm | 律师推荐语 (评审律师推荐同行, 推动付费转化) |
| 209 | 其他 | P1 | lex-pm | 引荐网络 #R3-#R6 (评审律师引荐同行) |
| 250 | 其他 | P1 | lex-pm | 律师推荐语 (评审律师推荐同行, 推动付费转化) |
| 251 | 其他 | P1 | lex-pm | 引荐网络 #R3-#R6 (评审律师引荐同行) |
| 292 | 其他 | P1 | lex-pm | 律师推荐语 (评审律师推荐同行, 推动付费转化) |
| 293 | 其他 | P1 | lex-pm | 引荐网络 #R3-#R6 (评审律师引荐同行) |
| 22 | 技术 | P1 | lex-coder | 审计日志 IP 地址 + 操作类型 (细化) |
| 23 | 技术 | P1 | lex-ai | 私有模型微调 (公司行业条款 + 历史合同) |
| 24 | 技术 | P1 | lex-ai | W7 PaddleEngine 接入 (兼容 PaddleOCR 2.7 + 3.7 API) |
| 25 | 技术 | P1 | lex-ai | W8 D1 venv312 paddlepaddle 装包 + D2 FTS5 jieba 索引重建 |
| 64 | 技术 | P1 | lex-coder | 审计日志 IP 地址 + 操作类型 (细化) |
| 65 | 技术 | P1 | lex-ai | 私有模型微调 (公司行业条款 + 历史合同) |
| 66 | 技术 | P1 | lex-ai | W7 PaddleEngine 接入 (兼容 PaddleOCR 2.7 + 3.7 API) |
| 67 | 技术 | P1 | lex-ai | W8 D1 venv312 paddlepaddle 装包 + D2 FTS5 jieba 索引重建 |
| 106 | 技术 | P1 | lex-coder | 审计日志 IP 地址 + 操作类型 (细化) |
| 107 | 技术 | P1 | lex-ai | 私有模型微调 (公司行业条款 + 历史合同) |
| 108 | 技术 | P1 | lex-ai | W7 PaddleEngine 接入 (兼容 PaddleOCR 2.7 + 3.7 API) |
| 109 | 技术 | P1 | lex-ai | W8 D1 venv312 paddlepaddle 装包 + D2 FTS5 jieba 索引重建 |
| 148 | 技术 | P1 | lex-coder | 审计日志 IP 地址 + 操作类型 (细化) |
| 149 | 技术 | P1 | lex-ai | 私有模型微调 (公司行业条款 + 历史合同) |
| 150 | 技术 | P1 | lex-ai | W7 PaddleEngine 接入 (兼容 PaddleOCR 2.7 + 3.7 API) |
| 151 | 技术 | P1 | lex-ai | W8 D1 venv312 paddlepaddle 装包 + D2 FTS5 jieba 索引重建 |
| 190 | 技术 | P1 | lex-coder | 审计日志 IP 地址 + 操作类型 (细化) |
| 191 | 技术 | P1 | lex-ai | 私有模型微调 (公司行业条款 + 历史合同) |
| 192 | 技术 | P1 | lex-ai | W7 PaddleEngine 接入 (兼容 PaddleOCR 2.7 + 3.7 API) |
| 193 | 技术 | P1 | lex-ai | W8 D1 venv312 paddlepaddle 装包 + D2 FTS5 jieba 索引重建 |
| 232 | 技术 | P1 | lex-coder | 审计日志 IP 地址 + 操作类型 (细化) |
| 233 | 技术 | P1 | lex-ai | 私有模型微调 (公司行业条款 + 历史合同) |
| 234 | 技术 | P1 | lex-ai | W7 PaddleEngine 接入 (兼容 PaddleOCR 2.7 + 3.7 API) |
| 235 | 技术 | P1 | lex-ai | W8 D1 venv312 paddlepaddle 装包 + D2 FTS5 jieba 索引重建 |
| 274 | 技术 | P1 | lex-coder | 审计日志 IP 地址 + 操作类型 (细化) |
| 275 | 技术 | P1 | lex-ai | 私有模型微调 (公司行业条款 + 历史合同) |
| 276 | 技术 | P1 | lex-ai | W7 PaddleEngine 接入 (兼容 PaddleOCR 2.7 + 3.7 API) |
| 277 | 技术 | P1 | lex-ai | W8 D1 venv312 paddlepaddle 装包 + D2 FTS5 jieba 索引重建 |
| 32 | 法务 | P1 | lex-ai | 法条 + 司法解释 + 地方高院裁判口径三级引用 |
| 33 | 法务 | P1 | lex-ai | '司法保护' 加 '非胜诉保证' 免责声明 (避免客户误解) |
| 34 | 法务 | P1 | lex-ai | 婚姻家事红线识别 (出轨/家暴/赌博/转移财产) |
| 35 | 法务 | P1 | lex-ai | 筹码具体性 (短期/长期 + 让步幅度) |
| 36 | 法务 | P1 | lex-ai | 维护期行业惯例 (IT ≥ 6-12 个月) |
| 74 | 法务 | P1 | lex-ai | 法条 + 司法解释 + 地方高院裁判口径三级引用 |
| 75 | 法务 | P1 | lex-ai | '司法保护' 加 '非胜诉保证' 免责声明 (避免客户误解) |
| 76 | 法务 | P1 | lex-ai | 婚姻家事红线识别 (出轨/家暴/赌博/转移财产) |
| 77 | 法务 | P1 | lex-ai | 筹码具体性 (短期/长期 + 让步幅度) |
| 78 | 法务 | P1 | lex-ai | 维护期行业惯例 (IT ≥ 6-12 个月) |
| 116 | 法务 | P1 | lex-ai | 法条 + 司法解释 + 地方高院裁判口径三级引用 |
| 117 | 法务 | P1 | lex-ai | '司法保护' 加 '非胜诉保证' 免责声明 (避免客户误解) |
| 118 | 法务 | P1 | lex-ai | 婚姻家事红线识别 (出轨/家暴/赌博/转移财产) |
| 119 | 法务 | P1 | lex-ai | 筹码具体性 (短期/长期 + 让步幅度) |
| 120 | 法务 | P1 | lex-ai | 维护期行业惯例 (IT ≥ 6-12 个月) |
| 158 | 法务 | P1 | lex-ai | 法条 + 司法解释 + 地方高院裁判口径三级引用 |
| 159 | 法务 | P1 | lex-ai | '司法保护' 加 '非胜诉保证' 免责声明 (避免客户误解) |
| 160 | 法务 | P1 | lex-ai | 婚姻家事红线识别 (出轨/家暴/赌博/转移财产) |
| 161 | 法务 | P1 | lex-ai | 筹码具体性 (短期/长期 + 让步幅度) |
| 162 | 法务 | P1 | lex-ai | 维护期行业惯例 (IT ≥ 6-12 个月) |
| 200 | 法务 | P1 | lex-ai | 法条 + 司法解释 + 地方高院裁判口径三级引用 |
| 201 | 法务 | P1 | lex-ai | '司法保护' 加 '非胜诉保证' 免责声明 (避免客户误解) |
| 202 | 法务 | P1 | lex-ai | 婚姻家事红线识别 (出轨/家暴/赌博/转移财产) |
| 203 | 法务 | P1 | lex-ai | 筹码具体性 (短期/长期 + 让步幅度) |
| 204 | 法务 | P1 | lex-ai | 维护期行业惯例 (IT ≥ 6-12 个月) |
| 242 | 法务 | P1 | lex-ai | 法条 + 司法解释 + 地方高院裁判口径三级引用 |
| 243 | 法务 | P1 | lex-ai | '司法保护' 加 '非胜诉保证' 免责声明 (避免客户误解) |
| 244 | 法务 | P1 | lex-ai | 婚姻家事红线识别 (出轨/家暴/赌博/转移财产) |
| 245 | 法务 | P1 | lex-ai | 筹码具体性 (短期/长期 + 让步幅度) |
| 246 | 法务 | P1 | lex-ai | 维护期行业惯例 (IT ≥ 6-12 个月) |
| 284 | 法务 | P1 | lex-ai | 法条 + 司法解释 + 地方高院裁判口径三级引用 |
| 285 | 法务 | P1 | lex-ai | '司法保护' 加 '非胜诉保证' 免责声明 (避免客户误解) |
| 286 | 法务 | P1 | lex-ai | 婚姻家事红线识别 (出轨/家暴/赌博/转移财产) |
| 287 | 法务 | P1 | lex-ai | 筹码具体性 (短期/长期 + 让步幅度) |
| 288 | 法务 | P1 | lex-ai | 维护期行业惯例 (IT ≥ 6-12 个月) |

## 生成的 Plan YAML 概要

```yaml
version: 1
plan:
  name: 'LexPrime Phase 4 Week 10 自动调度 (from PRD backlog open P0/P1, 245 ticket)'
  max_concurrency: 2
  max_consecutive_failures: 2
  max_cycles: 3
  auto_accept: true
  auto_reject_retries: 1
  verifier_config:
    default_verifiers: [verifier]
    audit_sample_rate: 0.0
  metadata:
    generated_by: 'scripts/backlog_to_plan_tasks.py'
    generated_at: '2026-06-29T13:49:22Z'
    source: 'prd_backlog WHERE status=open AND priority IN (P0,P1)'
    ticket_count: 245
    ticket_distribution:
      产品: 105
      其他: 21
      技术: 49
      法务: 70
tasks:

  # Task auto: 产品 backlog 调度 (105 ticket)
  - id: 'product-w10-auto'
    title: 'W10 产品 backlog 自动调度 (105 ticket: P0=56, P1=49)'
    prompt: |
      W10 A2 自动调度: 从 PRD backlog 拉取 产品 类 open P0/P1 ticket (105 个), assigned_to=lex-pm. 

      必读文档:
...(truncated, full plan YAML 见 plan-auto-w10-from-backlog.yaml)
```

## Schedule Invocation

```bash
mavis team plan run --no-wait /mnt/e/元枢法智前端/yuanxing/docs/plans/plan-auto-w10-from-backlog.yaml
```

### 执行结果

- **returncode**: `None` 
- **stdout**:
```
_(dry-run, no output)_
```
- **stderr**:
```
_(none)_
```

## 下一步

1. W9 A2 deliverable: 转 plan YAML + 调度日志 ✓
2. Owner (Mavis/lex-pm) 验收: 启动 `mavis team plan run /mnt/e/元枢法智前端/yuanxing/docs/plans/plan-auto-w10-from-backlog.yaml` 真启 plan (本期 A2 默认 dry-run, 不污染 owner 队列)
3. 真实运行后: worker agent 按 task 处理 ticket, 完成后写 deliverable.md
4. cron 集成: `scripts/cron/auto-schedule-backlog.sh` 每日 09:00 跑, 增量调度 (since 24h)

---
*本日志由 scripts/auto_schedule_backlog.py 自动生成 · W9 A2 自动调度*
