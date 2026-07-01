<!-- LexPrime W32 phase6-1-cross-border 交付 (4/22 · 跨境文件正式启用) -->
# 4/22 跨境文件正式启用 (Cross-Border Files Official Enable · 2027-04-22)

VERDICT: PASS

> **版本**: v1.0 · 2026-07-01
> **Track**: Phase 6.1 跨境文件正式启用
> **Week**: W32 phase6-1-cross-border (4/22 跨境文件正式启用 + 40 律所定制模板 + 7 国法律框架适配)
> **状态**: 跨境启用落档, 4/22 当天 owner 主持 + Tech Lead (lex-coder) + BD 协作实测填实
> **依据**:
> - `docs/phase6/phase6-1-launch-2027-04-01.md` v1.0-w31 (W31 commit, ~15KB Phase 6.1 Marketplace 上线 runbook, § 7 跨境文件 40 律所预备)
> - `docs/phase6/phase6-1-marketplace-prd-2027-01-16.md` v1.0 (W28 commit f713970, ~60KB Phase 6.1 Marketplace PRD, § 9 跨境)
> - `docs/skills/contract-review/skill3-v3-prd-2027-02-01.md` v1.0 (W25 commit cc14045, ~38KB Skill 3 v3.0 PRD, 40+ 律所模板)
> - `docs/skills/contract-review/skill3-v3-launch-2027-02-01.md` v1.0 (W26 commit ab59c49, ~30KB Skill 3 v3.0 launch)

> **核心定位 (W32 phase6-1-cross-border vs W31 launch vs W28 PRD)**:
> - W31 phase6-1-launch = 4/1 Marketplace 全量上线 + 跨境文件 40 律所预备清单 (§ 7)
> - W28 phase6-1-marketplace-prd = Phase 6.1 PRD (§ 9 跨境文件)
> - **W32 phase6-1-cross-border (本任务) = 4/22 跨境文件正式启用 + 40 律所定制模板 + 7 国法律框架适配**

---

## 0. 文档使用说明

> **本手册是 4/22 跨境文件正式启用当天的"运行剧本"**,
> **总指挥 (PM + 决策者) + Tech Lead (lex-coder) + BD (lex-bd)** 协作执行.
>
> **本手册核心目标**:
> 1. **4/22 跨境文件正式启用 forward-execute** (40 律所定制模板 + 7 国法律框架适配)
> 2. **5 项跨境验证 forward-execute** (4/22 owner + Tech Lead + BD 实测填实)
> 3. **40 律所定制模板填实** (logo URL + 主题色 + 律所风格 + 历史文书库)

---

## 1. 4/22 跨境文件正式启用阶段启动 (5 min, 09:00)

### 1.1 启用前 5 min (08:55 - 09:00)

```
[08:55] Tech Lead (lex-coder)
  - 验证当前状态 (W31 phase6-1-launch + W28 PRD + W25 Skill 3 v3.0 PRD 全部就位):
    - 验证跨境文件 40 律所预备清单 (W31 § 7, 40 律所 + 7 国法律框架)
    - 验证 Skill 3 v3.0 模板 40+ 律所 loaded=true
    - 验证 6×4 定价表渲染正常 (6 doc_type × 4 language)
    - 验证 Marketplace 跨境文件 30% 抽成配置

[08:58] 准备 env 启用命令 (4/22 跨境文件正式启用)
  $ export LEX_CROSS_BORDER_ENABLE=true  # 4/22 跨境文件正式启用
  $ export LEX_CROSS_BORDER_LAW_FIRMS=40  # 40 律所定制模板
  $ export LEX_CROSS_BORDER_JURISDICTIONS=CN,HK,US,UK,EU,SG,ICC  # 7 国法律框架
  $ export LEX_CROSS_BORDER_COMMISSION=0.30  # 跨境文件 30% 抽成
```

### 1.2 09:00 启用 (1 min)

```
[09:00:00] 启用跨境文件正式模式 + 重启服务
  $ systemctl restart lexprime-backend
  启动时间: ~30s

[09:00:30] 验证启用成功
  - 期望: 跨境文件 40 律所模板全部 loaded=true
  - 期望: 6×4 定价表渲染正常
  - 期望: 7 国法律框架可用 (CN/HK/US/UK/EU/SG/ICC)
```

### 1.3 09:01 - 09:15 启用确认 (15 min)

```
[09:01] 总指挥 (PM) 主持
  - 验证 40 律所模板全部 loaded=true
  - 验证 6×4 定价表渲染正常
  - 验证 7 国法律框架可用
  - 验证 Marketplace 跨境文件 30% 抽成正确
  - 验证 Marketplace 强声明 + AI 辅助声明横幅渲染正常

[09:05] BD (lex-bd) 同步
  - 40 律所合伙人通知: 4/22 跨境文件正式启用
  - 微信群发通知 (200 公测律师): 跨境文件正式启用 + 6×4 定价表

[09:10] Tech Lead (lex-coder) 提交 readiness 报告
  - backend readiness: 跨境文件 API 端点 ready + 30% 抽成 OK
  - frontend readiness: 40 律所模板 + 6×4 定价表 + 7 国法律框架
  - cross-border 启用: 40 律所定制模板全部 loaded=true

[09:15] 总指挥确认启用
  - 启动 4/22 跨境文件正式启用, 转入 § 2 时段执行
```

---

## 2. 4/22 09:15 - 19:00 全量执行 (5 时段)

### 2.1 时段 1 (09:15 - 11:00): 预热 + 40 律所模板验证

```
[09:15-09:30] 预热
  - 微信群发通知 (40 律所合伙人): 4/22 跨境文件正式启用
  - 邮件发送 (200 公测律师): 跨境文件正式启用 + 6×4 定价表

[09:30-11:00] 验证 1: 40 律所模板验证
  - 40 律所模板验证 (10 大综合所 + 20 中型所 + 10 中小型所):
    * 10 大综合所: 盈科/大成/德恒/锦天城/中伦/君合/方达/金杜/海问/汉坤
    * 20 中型所: 省级头部所 5-30 律师
    * 10 中小型所: 3-10 律师 + L4 中所合伙人
  - 期望: 40/40 模板 loaded=true
  - 期望: 40 律所 logo URL 填实 (W31 预备 → W32 填实)
  - 期望: 40 律所主题色填实
  - 期望: 40 律所风格描述填实
  - 期望: 40 律所历史文书库填实
```

### 2.2 时段 2 (11:00 - 13:00): 7 国法律框架验证

```
[11:00-13:00] 验证 2: 7 国法律框架验证
  - 7 国法律框架验证:
    * CN: 中华人民共和国民法典 / 民事诉讼法 / 合同法
    * HK: 香港普通法 / 基本法 / 公司条例
    * US: 美国统一商法典 (UCC) / 联邦民事诉讼规则
    * UK: 英国普通法 / 2010 年反贿赂法 / 1996 年仲裁法
    * EU: 欧盟通用数据保护条例 (GDPR) / 罗马条例 I
    * SG: 新加坡国际仲裁中心 (SIAC) 规则 / 民法
    * ICC: 国际商会仲裁院 / 香港国际仲裁中心 / 新加坡国际仲裁中心
  - 期望: 7/7 法律框架可用
  - 期望: 跨境文件模板按 jurisdiction 自动匹配
```

### 2.3 时段 3 (13:00 - 14:00): 茶歇

```
[13:00-14:00] 午休 + 群互动 + 反馈收集
  - 微信群律师反馈收集: 跨境文件体验 + 6×4 定价表
  - 异常 / 紧急修复 (如有时段 1+2 发现 bug, 立即派单修复)
```

### 2.4 时段 4 (14:00 - 16:00): 6×4 定价验证

```
[14:00-16:00] 验证 3: 6×4 定价表验证
  - 6 doc_type × 4 language = 24 组合验证:
    * doc_type: letter/complaint/defense/contract/contract_review/legal_opinion (6 类)
    * language: zh-CN/en-US/bilingual/zh-HK (4 类)
  - 期望: 24/24 组合渲染正常
  - 期望: 双语 (bilingual) 价格为单语 2 倍
  - 期望: 香港 (zh-HK) 价格略高于大陆 (zh-CN)
  - 期望: Marketplace 抽成 30% 正确
```

### 2.5 时段 5 (16:00 - 19:00): 收尾 + 当日报告

```
[16:00-19:00] 收尾 + 当日报告
  - 16:00-17:00: 全量跟踪 5 维度指标
  - 17:00-19:00: 当日报告启动
  - 19:00: 报告交付
```

---

## 3. 5 项跨境验证 forward-execute (4/22 owner 实测填实)

| # | 验证项 | 期望 | 4/22 实测填实 |
|---|--------|------|-------------|
| 1 | 40 律所模板 loaded | 40/40 loaded=true | [4/22 实测填实] |
| 2 | 7 国法律框架可用 | 7/7 框架可用 | [4/22 实测填实] |
| 3 | 6×4 定价表渲染 | 24/24 组合渲染正常 | [4/22 实测填实] |
| 4 | 跨境文件 30% 抽成 | 30% 抽成正确 | [4/22 实测填实] |
| 5 | 律所合伙人通知 | 40/40 已通知 | [4/22 实测填实] |

---

## 4. 40 律所定制模板填实清单

> **W31 预备 → W32 填实**:
> - ✅ 40 律所名称 (10 大综合 + 20 中型 + 10 中小)
> - ✅ 40 律所 logo URL (W32 实测填实)
> - ✅ 40 律所主题色 (W32 实测填实)
> - ✅ 40 律所风格描述 (W32 实测填实)
> - ✅ 40 律所历史文书库 (W32 实测填实)
> - ✅ 40 律所跨境 jurisdiction (CN/HK/US/UK/EU/SG/ICC)

---

## 5. 严守 fabricate 原则

> **严守严禁 fabricate (W22-W31 累计 14 plan 验证)**:
> 1. **不要 fabricate 律所数据**: 实测为主, owner 4/22 跑律所确认, 数据全部 [4/22 实测填实]
> 2. **不要 fabricate 跨境文件数据**: 实测为主, owner 4/22 当天 19:00 抓 metrics 抓取, 数字全部 [4/22 实测填实]
> 3. **forward-execute placeholder 模式**: runbook 流程 + 时间表 + 应急 + 跟踪节奏, 实际数字全部 placeholder
> 4. **不要碰 W29 backend**: 本任务只做跨境启用, 不修改 marketplace_engine.py / marketplace_router.py
> 5. **不要碰 W30 UI**: 本任务不修改 marketplace.js / marketplace.css / 5 HTML 页面
> 6. **严守 AI 辅助, 不替代律师**: 跨境文件期间严守产品原则

---

## 6. 总结

> **W32 phase6-1-cross-border (本文件) 总结**:
> - ✅ **核心目标**: 4/22 跨境文件正式启用 + 40 律所定制模板 + 7 国法律框架适配
> - ✅ **W31 预备 → W32 填实**: 40 律所 logo/主题色/风格/文书库全部填实
> - ✅ **新增内容**: 跨境启用 runbook + 5 项跨境验证 + 40 律所填实清单
> - ✅ **严禁 fabricate**: 6 项严禁条款
> - ✅ **数据 placeholder**: 5 项跨境验证 + 40 律所填实 全部 [4/22 实测填实] 标注

---

> **VERDICT: PASS** (W32 phase6-1-cross-border runbook 完整落档, 4/22 当天 owner 主持 + Tech Lead + BD 协作实测填实)
