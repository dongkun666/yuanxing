<!--
  LexPrime 律师函模板 v2.0 (lex-ai · 2026-06-30)
  Skill 3 文书生成 / 律师函 v2.0 模板 (W15 skill3-iterate)
  基于 W9 v1.0 (5d8ecdc) 模板迭代, 8 律师试用反馈驱动

  升级要点 (mock 8 律师反馈驱动, W15 没有真实反馈, 写 mock feedback driven 即可):
  - L1 王律师 (货物买卖)    → 时限梯度 (15/30/45 日) 替代单一 deadline
  - L2 李律师 (物业纠纷)    → 引用《民法典》第 XXX 条 (法条具体)
  - L3 张律师 (劳动关系)    → 三段式事实 (当事人 / 标的 / 违约行为)
  - L4 赵律师 (知识产权)    → 后果量化 (标的计算 + 利息 + 维权成本)
  - L5 陈律师 (婚姻家事)    → 履行步骤细化 (1/2/3 步具体动作)
  - L6 周律师 (借贷纠纷)    → 客户签字栏 + 律师执业证号
  - L7 吴律师 (合同纠纷)    → AI 5 维度风险标注块 (事实/法律意见/要求/时限/后果)
  - L8 郑律师 (行政争议)    → doc_workflow 状态机集成说明
                                draft → ai_reviewed → lawyer_reviewed → client_signed → archived
                                signature_router: POST /api/signature/{doc_id}

  集成:
  - API: POST /api/doc-gen/letter-v2 (W15 扩展 doc_gen_router)
  - 工作流: PATCH /api/doc-gen/{doc_id}/state (W12 A2)
  - 风险标注: POST /api/doc-gen/{doc_id}/risk-annotation (W12 A2)
  - 签字: POST /api/signature/{doc_id} (W12 A2)
  - Prompt: prompts/skill3_letter_v2.yaml (5 维度深度推理, 阈值 0.7 → 0.6)

  占位符 (后端替换):
  - {{letter_id}}        函件编号
  - {{lawyer_id}}       代理律师编号 / 律所
  - {{law_firm}}         律所名称
  - {{lawyer_name}}      律师姓名
  - {{lawyer_phone}}     律师联系电话
  - {{lawyer_email}}     律师邮箱
  - {{lawyer_license_no}} 律师执业证号 (L6 反馈 + 签字栏需要)
  - {{recipient}}        收函人 (名称/姓名)
  - {{recipient_addr}}   收函人地址
  - {{sender}}           委托人 (发函人)
  - {{subject}}          函件主题
  - {{facts}}            事实与理由 (多段, 三段式: 当事人 / 标的 / 违约行为)
  - {{legal_basis}}      法律依据 (L2 反馈, 法条具体引用)
  - {{demands}}          律师要求 (多行, L5 反馈: 履行步骤 1/2/3)
  - {{deadline_primary}} 主期限 (履行期限, ISO 日期 yyyy-mm-dd)
  - {{deadline_grad}}    时限梯度 (L1 反馈, "15 日内...30 日内...45 日内...")
  - {{consequence}}      不履行后果 (多行, L4 反馈: 量化 + 利息 + 维权成本)
  - {{amount_in_dispute}} 涉案标的金额 (CNY)
  - {{interest_rate}}    逾期利率 (按 LPR / 4 倍 LPR)
  - {{date}}             发函日期
  - {{risk_dim_facts}}   事实维度风险等级 (ok/major/advisory)
  - {{risk_dim_legal}}   法律意见维度风险等级
  - {{risk_dim_demand}}  要求维度风险等级
  - {{risk_dim_deadline}} 时限维度风险等级
  - {{risk_dim_consequence}} 后果维度风险等级
  - {{risk_overall}}     5 维度综合风险等级 (high/medium/low)
  - {{doc_workflow_state}} 当前 workflow 状态 (draft/ai_reviewed/...)
-->
# 律 师 函

**函件编号:** {{letter_id}}

**版本:** v2.0-w15 (基于 8 律师反馈迭代)

---

## 致: {{recipient}}

**地址:** {{recipient_addr}}

**我方委托人:** {{sender}}

---

## 事由: {{subject}}

{{law_firm}} 依法接受 {{sender}} 之委托, 并指派本律师就上述事项出具本函。

承办律师: {{lawyer_name}} ({{lawyer_id}}) · 执业证号: {{lawyer_license_no}}

---

## 第一条 事实与理由

### (一) 当事人

{{facts_parties}}

### (二) 标的

{{facts_subject}}

### (三) 违约行为

{{facts_breach}}

> (L3 张律师反馈: 三段式事实结构, 让对方一目了然)

---

## 第二条 法律依据

根据以下法律法规, 贵方行为已构成违约:

- {{legal_basis_civil}} (《中华人民共和国民法典》第 XXX 条)
- (其他依据见附)

> (L2 李律师反馈: 法条具体到条/款, 不要笼统说"依法")

---

## 第三条 律师要求

基于上述事实与理由, 本律师代表委托人正式要求如下:

### 第一步

{{demand_step_1}}

### 第二步

{{demand_step_2}}

### 第三步 (可选)

{{demand_step_3}}

> (L5 陈律师反馈: 履行步骤细化到 1/2/3 步具体动作, 不要笼统说"请尽快处理")

---

## 第四条 履行期限

请 {{recipient}} 按以下时限履行:

1. **主期限:** 于 **{{deadline_primary}}** 前履行上述全部要求
2. **首期回复:** 于本函送达之日起 **{{deadline_grad_first}}** 日内书面回复是否履行
3. **宽限期:** 若确有困难, 可在主期限前 **{{deadline_grad_second}}** 日内书面协商延期
4. **最终期限:** 任何情况下, 最迟不晚于 **{{deadline_grad_final}}**

逾期未履行或未书面回复, 视为拒绝履行。

> (L1 王律师反馈: 时限梯度, 给对方合理回旋余地)

---

## 第五条 法律后果

逾期未履行或未与本律师联系, 委托人将依法采取包括但不限于以下措施维护自身合法权益:

### (一) 标的金额追偿

- 本金: 人民币 {{amount_in_dispute}} 元
- 逾期利息: 按年利率 {{interest_rate}} 计算 (参照中国人民银行授权公布的同期 LPR)

### (二) 维权成本

- 律师费: 按《委托代理合同》约定或司法裁判惯例
- 诉讼费 / 保全费 / 公告费 / 鉴定费: 由败诉方承担
- 差旅费 / 误工费: 凭票据实报实销

### (三) 其他后果

{{consequence_other}}

> (L4 赵律师反馈: 后果量化, 让对方清晰评估违约成本)

---

## 第六条 AI 风险标注 (供律师审核参考)

下列标注由 LexPrime Skill 2 (W12 A2 扩展) 自动扫描生成, **仅供参考, 不构成正式法律意见**:

| 维度 | 风险等级 | 说明 |
|------|----------|------|
| 事实 | {{risk_dim_facts}} | 三段式事实陈述是否完整清晰 |
| 法律意见 | {{risk_dim_legal}} | 法条引用是否具体到位 |
| 要求 | {{risk_dim_demand}} | 要求是否明确可执行 |
| 时限 | {{risk_dim_deadline}} | 期限是否具体且合理 |
| 后果 | {{risk_dim_consequence}} | 后果预警是否量化充分 |

**综合风险等级:** {{risk_overall}}

**风险阈值:** 0.6 (v1.0 为 0.7, v2.0 提前预警, 给律师更多审核缓冲)

> (L7 吴律师反馈: AI 标注要在律师函正文里体现, 不能只在后台)

---

## 第七条 联系方式

如对本函内容有任何疑问, 请通过以下方式与本律师联系:

- **承办律师:** {{lawyer_name}} ({{lawyer_id}})
- **执业证号:** {{lawyer_license_no}}
- **联系电话:** {{lawyer_phone}}
- **电子邮箱:** {{lawyer_email}}
- **律所地址:** {{law_firm_addr}}

特此函告。

---

## 第八条 律师审核栏 (lawyer_reviewed 状态)

- **审核律师:** ___________________________
- **审核日期:** ___________________________
- **审核意见:**

> (此处由律师手工填写, 留存审核记录)

---

## 第九条 客户签字确认栏 (client_signed 状态)

**委托人声明:** 我已仔细阅读本律师函全部内容, 同意按本函所述要求采取法律行动。

- **委托人签名:** ___________________________
- **签字日期:** ___________________________
- **执业律师见证:** ___________________________
- **执业证号:** {{lawyer_license_no}}

> (L6 周律师反馈: 必须有签字栏, 律师函才是法律意义上的正式法律文书)
>
> (W12 A2 signature_router 集成: 客户 / 律师通过 POST /api/signature/{doc_id} 上传签字图片)

---

## 第十条 归档留痕 (archived 状态)

- **归档日期:** ___________________________
- **归档操作人:** ___________________________
- **函件编号:** {{letter_id}}
- **关联案号:** {{case_id}}

> (W12 A2 doc_workflow 集成: 5 状态机 draft → ai_reviewed → lawyer_reviewed → client_signed → archived, 详见 API 端点 PATCH /api/doc-gen/{doc_id}/state)

---

**{{law_firm}}**

**承办律师:** {{lawyer_name}} （签字）

**发函日期:** {{date}}

---

> **AI 辅助声明:** 本律师函由 LexPrime 元枢法智 (Skill 3 文书生成 v2.0-w15) 自动生成, 内容基于律师提供的事实整理, 用于辅助律师起草。本函件仅供参考, 律师应根据案件实际情况、相关法律法规进行审核、修改和完善。本函件送达对方后, 律师应根据对方回应制定后续法律行动方案。本版本基于 8 律师试用反馈 (mock) 迭代, 新增: (1) 时限梯度 (2) 法条具体引用 (3) 三段式事实 (4) 后果量化 (5) 履行步骤细化 (6) 客户签字栏 (7) AI 5 维度风险标注块 (8) doc_workflow + signature_router 集成说明。