<!--
  LexPrime 起诉状模板 v1 (lex-coder · 2026-06-29)
  Skill 3 文书生成 / 4 模板之一 (评审 #1 #2 律师最常问 Top 3)
  PRD § 5.4 Skill Hub + § 5.6 当事人服务类文书

  占位符 (后端替换):
  - {{case_id}}         案号 (案号格式: (YYYY)X民初NNNN号)
  - {{lawyer_id}}      代理律师编号 / 律所
  - {{plaintiff_name}}  原告姓名/名称
  - {{plaintiff_id}}    原告身份证号 / 统一社会信用代码
  - {{plaintiff_addr}}  原告住所地
  - {{defendant_name}}  被告姓名/名称
  - {{defendant_id}}    被告身份证号 / 统一社会信用代码
  - {{defendant_addr}}  被告住所地
  - {{court}}           受诉法院 (e.g. 北京市朝阳区人民法院)
  - {{cause}}           案由 (e.g. 民间借贷纠纷)
  - {{facts}}           事实与理由 (多段, 律师原稿)
  - {{evidence}}        证据清单 (多行, 一项一行)
  - {{claims}}          诉讼请求 (多行, 一项一行)
  - {{date}}            起诉日期
  - {{amount}}          涉案金额 (CNY, 仅做参考)

  渲染: 后端 doc_gen_router.py render_template() 用 str.replace()
-->
# 民 事 起 诉 状

**案号:** {{case_id}}

---

## 当事人信息

### 原告

- **姓名/名称:** {{plaintiff_name}}
- **身份证号/统一社会信用代码:** {{plaintiff_id}}
- **住所地:** {{plaintiff_addr}}
- **联系电话:** {{plaintiff_phone}}
- **委托诉讼代理人:** {{lawyer_id}}

### 被告

- **姓名/名称:** {{defendant_name}}
- **身份证号/统一社会信用代码:** {{defendant_id}}
- **住所地:** {{defendant_addr}}
- **联系电话:** {{defendant_phone}}

---

## 诉讼请求

{{claims}}

---

## 事实与理由

{{facts}}

---

## 证据清单

{{evidence}}

---

## 此致

**{{court}}**

---

具状人: {{plaintiff_name}} （签章）

{{lawyer_id}}

{{date}}

---

> **AI 辅助声明:** 本文书由 LexPrime 元枢法智 (Skill 3 文书生成 v0.1.0-w9) 自动生成, 内容基于律师提供的事实与证据整理。本文书仅供参考与辅助律师起草使用, 不构成正式法律意见, 律师应根据案件实际情况进行审核、修改和完善。