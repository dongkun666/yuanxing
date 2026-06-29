<!--
  LexPrime 合同模板 v1 (lex-coder · 2026-06-29)
  Skill 3 文书生成 / 4 模板之三 (评审 #1 #2 律师最常问 Top 3)
  PRD § 5.4 Skill Hub + § 5.6 当事人服务类文书

  适用合同类型 (复用 Skill 2 8 大类):
  - 房屋租赁 / 借款 / 劳动 / 服务 / 销售 / 承揽 / 委托 / 其他

  占位符 (后端替换):
  - {{contract_id}}     合同编号
  - {{contract_type}}   合同类型 (房屋租赁合同 / 借款合同 / ...)
  - {{party_a}}         甲方 (名称/姓名)
  - {{party_a_id}}      甲方身份证号 / 统一社会信用代码
  - {{party_a_addr}}    甲方住所地
  - {{party_b}}         乙方
  - {{party_b_id}}      乙方身份证号 / 统一社会信用代码
  - {{party_b_addr}}    乙方住所地
  - {{subject}}         标的 (合同标的物/服务)
  - {{amount}}          合同金额 (CNY)
  - {{amount_cn}}       合同金额 (大写)
  - {{term}}            履行期限
  - {{start_date}}      生效日期
  - {{end_date}}        终止日期
  - {{facts}}           其他合同条款 (多段)
  - {{lawyer_id}}       起草律师
  - {{date}}            签订日期
-->
# {{contract_type}}

**合同编号:** {{contract_id}}

---

## 合同主体

### 甲方

- **名称/姓名:** {{party_a}}
- **身份证号/统一社会信用代码:** {{party_a_id}}
- **住所地:** {{party_a_addr}}
- **联系电话:** {{party_a_phone}}
- **法定代表人:** {{party_a_rep}}

### 乙方

- **名称/姓名:** {{party_b}}
- **身份证号/统一社会信用代码:** {{party_b_id}}
- **住所地:** {{party_b_addr}}
- **联系电话:** {{party_b_phone}}
- **法定代表人:** {{party_b_rep}}

---

## 第一条 合同标的

{{subject}}

---

## 第二条 合同金额与支付方式

- **合同金额:** 人民币 {{amount}} 元 (大写: {{amount_cn}})
- **支付方式:** {{payment_method}}
- **付款时间:** {{payment_schedule}}

---

## 第三条 履行期限与方式

- **履行期限:** 自 {{start_date}} 起至 {{end_date}} 止
- **履行地点:** {{perform_location}}
- **履行方式:** {{perform_method}}

---

## 第四条 双方权利义务

{{facts}}

---

## 第五条 违约责任

{{breach_terms}}

---

## 第六条 争议解决

- **管辖:** 本合同履行过程中发生的争议, 由双方协商解决; 协商不成的, 提交 {{jurisdiction}} 仲裁委员会仲裁 / 向 {{jurisdiction}} 人民法院起诉。

---

## 第七条 合同生效

本合同自双方签字盖章之日起生效, 一式两份, 甲方乙方各执一份, 具有同等法律效力。

---

## 第八条 其他约定

{{misc_terms}}

---

甲方 (签章): {{party_a}}

乙方 (签章): {{party_b}}

---

**起草律师:** {{lawyer_id}}

**签订日期:** {{date}}

---

> **AI 辅助声明:** 本合同由 LexPrime 元枢法智 (Skill 3 文书生成 v0.1.0-w9) 自动生成, 内容基于律师提供的合同要素整理。本合同仅供参考与辅助律师起草使用, 律师应根据交易实际情况、相关法律法规和行业惯例进行审核、修改和完善, 并经双方充分协商后签署。