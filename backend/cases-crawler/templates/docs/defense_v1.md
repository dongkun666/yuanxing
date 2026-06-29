<!--
  LexPrime 答辩状模板 v1 (lex-coder · 2026-06-29)
  Skill 3 文书生成 / 4 模板之二 (评审 #1 #2 律师最常问 Top 3)
  PRD § 5.4 Skill Hub + § 5.6 当事人服务类文书

  占位符 (后端替换):
  - {{case_id}}         案号
  - {{lawyer_id}}      代理律师编号 / 律所
  - {{plaintiff_name}}  原告姓名/名称
  - {{defendant_name}}  被告姓名/名称 (答辩人)
  - {{defendant_id}}    被告身份证号 / 统一社会信用代码
  - {{defendant_addr}}  被告住所地
  - {{court}}           受诉法院
  - {{cause}}           案由
  - {{facts}}           答辩事实与理由 (多段)
  - {{evidence}}        反证 / 证据清单 (多行)
  - {{claims_response}} 对原告诉讼请求的答辩 (多行)
  - {{date}}            答辩日期
-->
# 民 事 答 辩 状

**案号:** {{case_id}}

---

## 答辩人

- **姓名/名称:** {{defendant_name}}
- **身份证号/统一社会信用代码:** {{defendant_id}}
- **住所地:** {{defendant_addr}}
- **联系电话:** {{defendant_phone}}
- **委托诉讼代理人:** {{lawyer_id}}

**被答辩人(原告):** {{plaintiff_name}}

---

## 案由

答辩人就 {{plaintiff_name}} 诉 {{defendant_name}} {{cause}} 一案, 现提出答辩如下:

---

## 对原告诉讼请求的答辩

{{claims_response}}

---

## 事实与理由

{{facts}}

---

## 证据清单 (反证 / 答辩证据)

{{evidence}}

---

## 此致

**{{court}}**

---

答辩人: {{defendant_name}} （签章）

{{lawyer_id}}

{{date}}

---

> **AI 辅助声明:** 本文书由 LexPrime 元枢法智 (Skill 3 文书生成 v0.1.0-w9) 自动生成, 内容基于律师提供的事实与证据整理。本文书仅供参考与辅助律师起草使用, 不构成正式法律意见, 律师应根据案件实际情况进行审核、修改和完善。