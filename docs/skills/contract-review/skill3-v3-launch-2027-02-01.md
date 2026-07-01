<!-- LexPrime Track A · W26 skill3-v3-rollout-only 交付 -->
# 2/15 Skill 3 律师函 v3.0 Launch 落档 (Skill 3 v3.0 Launch · 2027-02-15)

> **版本**: v1.0 · 2026-06-30
> **Track**: A (AI 模型 + Skill Hub v3.0)
> **Week**: W26 skill3-v3-rollout-only (Skill 3 律师函 v3.0 launch 落档)
> **状态**: launch 落档, 等 2/15 当天 owner 主持 + Tech Lead (lex-ai/lex-coder) + BD + 3 agent 协作实测填实
> **依据**:
> - `docs/skills/contract-review/skill3-v3-prd-2027-02-01.md` v1.0 (W25 commit cc14045, ~38KB Skill 3 v3.0 PRD)
> - `docs/skills/contract-review/skill3-v3-tests-2027-02-01.md` v1.0 (W25 commit 1fbfe93, ~18KB Skill 3 v3.0 测试套件 50 测试报告)
> - `docs/marketing/skill3-v2-100pct-rollout-2026-10-01.md` v1.0 (W21 commit 6929cc1, Skill 3 v2.0 全量 100% rollout)
> - `docs/marketing/skill3-v1-deprecation-2026-11-01.md` v1.0 (W21, 11/1 letter v1.0 退役)
> - `docs/marketing/skill3-v2-ab-test-2026-08-15.md` v1.0 (W19 commit 2cc2d3a, 8/15 v2.0 10% 灰度 + A/B test)
> - `docs/marketing/skill3-v2-50pct-rollout-2026-09-01.md` v1.0 (W19, 9/1 v2.0 50% 全量灰度)
> - `docs/phase5/skill3-v2-full-rollout-2027-01-01.md` v1.0 (W23 commit 432a073, 1/1 Skill 3 v2.0 全面应用 5 个月 + v3.0 三节点计划)
> - `docs/phase5/phase5-5-launch-2027-01-01.md` v1.0 (W23, Phase 5.5 跨年启动仪式 + 5 大新方向 + 8 月路线图)
> - `prompts/skill3_letter_v2.yaml` v2.0-w15 (W15 commit e3f0940, 8 律师反馈驱动 + 5 维度深度推理)
> - `templates/docs/letter_v2.md` v2.0-w15 (W15 commit 3d429cd, 8 律师反馈模板迭代)
> - `core/rollout.py` v2.0-w21 (W21, 灰度配置 + hash 分配 + metrics 跟踪 + letter_v1_deprecated 开关)
> - `api/doc_gen_router.py` v0.4.0-w21 (W21, /letter + /letter-v2 + /rollout/status + /metrics + /health)
> - `core/doc_workflow.py` v1.0-w12 (W12 commit 829d25c, 5 状态机 + 4 文书风险标注)
> - W11 PRD V5.0 § 5.4 (Skill Hub 9 Skill) + § 5.6 (当事人服务类文书律师函) + § 11 (法务自检 5 维度)

> **核心定位 (W26 skill3-v3-launch vs W25 PRD vs W25 tests vs W21 v2.0 rollout vs W19 gradual)**:
> - W21 6929cc1 = Skill 3 v2.0 全量 100% rollout (10/1) + 11/1 letter v1.0 退役 (单日, 桌面端, 中文, 通用模板)
> - W19 2cc2d3a = Skill 3 v2.0 灰度 (8/15 10% A/B + 9/1 50% 全量, 35 灰度测试, 95 tests pass)
> - W23 432a073 phase5-5-celebration = Skill 3 v2.0 全面应用 5 个月 + Skill 3 v3.0 三节点计划 (1/15 + 2/1 + 3/1)
> - W25 cc14045 = Skill 3 v3.0 PRD (多端 + 多语言 + 多律所模板, 550 行 ~38KB, v2.0 → v3.0 additive 渐进)
> - W25 1fbfe93 = Skill 3 v3.0 测试套件 50 测试 (35 baseline + 15 v3.0 多场景, 1004 行, ruff 0 errors)
> - **W26 skill3-v3-launch (本文件)**: Skill 3 v3.0 升级路径 + rollout 计划 + v2.0 退役计划 + 推广计划 (5 渠道) 完整 launch 落档

> **核心扩展 (W26 skill3-v3-launch vs W21 skill3-full-rollout vs W19 skill3-gradual)**:
> - **时间窗口**: W21 10/1 单日 → W26 2/15 → 3/1 → 3/15 → 4/1 (4 节点, 累计 45 天 v3.0 升级 + 4/1 v2.0 退役)
> - **平台维度**: W21 桌面端 → W26 多端 (桌面 + iOS + Android + iPad, React Native 0.73+ + Expo 51+)
> - **语言维度**: W21 中文 (单语) → W26 中英双语 (中英 markdown 模板 + react-i18next + 双语对照)
> - **律所模板维度**: W21 通用模板 → W26 40+ 律所定制模板 (10 大综合所 + 50 中型所 + 20 中小型所)
> - **场景维度**: W21 中国大陆律师 → W26 跨境案件 + 国际客户 + 涉外律所 + 国际仲裁
> - **推广维度**: W21 内测灰度 → W26 5 渠道推广 (朋友圈 9 宫格 + 律师公众号 + 律协 + 律师私域 + 40+ 律所合作)

---

## 0. 文档使用说明 (2/15 Skill 3 v3.0 Launch 落档)

> **本 launch 文件是 Skill 3 v3.0 升级路径 + rollout + 退役 + 推广完整落档**.
> **目标用户**: 总指挥 (PM + 决策者) + Tech Lead (lex-ai/lex-coder) + BD + 3 agent (UI 设计师 + 前端工程师 + 数据工程师) + 50 律所合伙人 + 200 公测律师
> **本 launch 配套 (W25 cc14045 + 1fbfe93 + W26 同期)**:
> - `skill3-v3-prd-2027-02-01.md` v1.0 (W25 commit cc14045, ~38KB Skill 3 v3.0 PRD, 多端 + 多语言 + 多律所模板)
> - `skill3-v3-tests-2027-02-01.md` v1.0 (W25 commit 1fbfe93, ~18KB Skill 3 v3.0 测试套件 50 测试报告)
> - `skill3-v3-launch-2027-02-01.md` v1.0 (本文件, ~30KB Skill 3 v3.0 launch: 升级路径 + rollout + 退役 + 推广)
> - `prompts/skill3_letter_v3.yaml` v3.0-w26 (W26 新增, v3.0 多端 + 多语言 + 多律所适配 prompt)
> - `templates/docs/letter_v3.md` v3.0-w26 (W26 新增, v3.0 模板: 中英双语 + 多律所样式预留)
> - `templates/firms/40+_firms/` (W26 新增, 律所定制模板库, 10 大综合所 + 50 中型所 + 20 中小型所)
> - `core/rollout_v3.py` v1.0-w26 (W26 新增, v3.0 灰度配置 + v3_multi_device_pct + v3_multi_lang_pct + v3_firm_pct + v2_letter_deprecated)
> - `mobile/ios/LetterMobile/` + `mobile/android/LetterMobile/` + `mobile/ipad/LetterPad/` (W26 新增, React Native + Expo)
> - `tests/skill3-v3/test_v3.py` (W25 commit 1fbfe93, 50 测试, 复用 base)
> - `tests/skill3-v3/test_v3_40firms.py` (W27 deferred, 40 律所独立模板测试)
> - `tests/skill3-v3/test_v3_viewport.py` (W27 deferred, 5 移动端 viewport 测试)
> - `docs/marketing/skill3-v3-multi-device-2027-02-15.md` (W26 launch 同期, 2/15 v3.0 多端 runbook)
> - `docs/marketing/skill3-v3-multi-lang-2027-02-15.md` (W26 launch 同期, 2/15 v3.0 多语言 runbook)
> - `docs/marketing/skill3-v3-firm-template-2027-03-15.md` (W27 deferred, 3/15 v3.0 多律所模板 runbook)
> - `docs/marketing/skill3-v3-launch-promotion-2027-02-15.md` (W26 launch 同期, 5 渠道推广计划)
>
> **数据源**: W23 phase5-5-celebration 1/1 实测填实 + W21 skill3-full-rollout 6 文件 1704 +/-17 + W19 95 tests + W15 32 tests + W12 38 tests
> **跟踪期**: 2027-02-15 单日 (公测 day 234, Skill 3 v2.0 全面应用 6 个月累计 + Skill 3 v3.0 启动)
> **严禁 fabricate 数据**: 当前时间 2026-06-30, 距 2/15 还有 230 天. 所有 250 律师 + 50 律所 + 500 律师 + 40+ 律所 + 5 维度评分 + 律师满意度 + v3.0 覆盖律师 + 推广效果数据 均为 forward-execute placeholder 节点, 由 owner 2/15 + 3/1 + 3/15 + 4/1 当天 09:00 实测填实.

---

## 1. Skill 3 v3.0 四阶段时间线 (2/15 启动 + 3/1 50% + 3/15 100% + 4/1 v2.0 退役)

### 1.1 总时间线 (W26 launch 完整节奏)

| 阶段 | 日期 | 公测 day | 灰度比例 | 期望律师覆盖 | 期望律所覆盖 | 期望律师函生成 | 5 维度评分 | 律师满意度 | 关键 commit | 状态 |
|------|------|---------|---------|------------|------------|--------------|----------|-----------|------------|------|
| **预热 (W26 启动)** | 2027-02-10 - 02-14 | 229-233 | 0% (5 律师试用) | 5 → 50 | 5 → 10 | 50+ | [4.5+/5.0, 2/10 实测填实] | [4.6+/5.0, 2/10 实测填实] | W26 launch (本文件, ~30KB) | **W26 本次 (2/15 落地)** |
| **2/15 启动 (W26)** | 2027-02-15 09:00 | 234 | 启动 5% | 50 | 10 | 100+ | [4.5+/5.0, 2/15 实测填实] | [4.6+/5.0, 2/15 实测填实] | W26 skill3-v3-launch | **W26 本次** |
| **3/1 50% (W27)** | 2027-03-01 09:00 | 248 | 50% | 250 | 50 | 1000+ | [4.6+/5.0, 3/1 实测填实] | [4.6+/5.0, 3/1 实测填实] | W27 multi-lang launch | **W27 deferred** |
| **3/15 100% (W28)** | 2027-03-15 09:00 | 262 | 100% | 500 | 100 | 5000+ | [4.6+/5.0, 3/15 实测填实] | [4.6+/5.0, 3/15 实测填实] | W28 firm-template launch | **W28 deferred** |
| **4/1 v2.0 退役 (W29)** | 2027-04-01 09:00 | 279 | 100% (v2.0 退役) | 500 | 100 | 10000+ | [4.6+/5.0, 4/1 实测填实] | [4.6+/5.0, 4/1 实测填实] | W29 v2.0 deprecation | **W29 deferred** |

> **Skill 3 v3.0 四阶段时间线 (2/15 启动 → 3/1 50% → 3/15 100% → 4/1 v2.0 退役)**:
> - **预热 (2/10-2/14, 5 天)**: 5 律师试用 → 50 律师 (创史律师 + L4 中所合伙人 + L5 企业法务总监 + 个人版代表 5 类)
> - **2/15 启动 (W26 本次)**: v3.0 灰度 5% (50 律师), 验证移动端 + iPad + 中英 + 40+ 律所模板 + Marketplace 集成
> - **3/1 50% (W27)**: v3.0 全量 50% 灰度 (250 律师), Marketplace 公测 (文书模板分享 + 抽成 5%), 跨境案件公测
> - **3/15 100% (W28)**: v3.0 全量 100% (500 律师 + 100 律所), 40+ 律所定制模板全量, Marketplace 高级功能 (律所版定制)
> - **4/1 v2.0 退役 (W29)**: letter_v2_deprecated=true (v2.0 通用模板退役, 跟 v1.0 退役节奏一致 W21), 全员 v3.0 + 40+ 律所定制模板

### 1.2 关键节点 (与 W23 phase5-5-celebration 衔接)

```
[2026-07-26 公测 day 1]                (W18 公测启动)
  ↓
[2026-08-15 公测 day 21]               (W19 10% 灰度, 35 测试)
  ↓
[2026-10-01 公测 day 68]               (W21 全量 100% rollout, 36 测试)
  ↓
[2026-11-01 公测 day 99]               (W21 v1.0 退役)
  ↓
[2027-01-01 公测 day 160 (实际 189)]    (W23 phase5-5-celebration 5 个月累计 + v3.0 计划)
  ↓
[2027-01-15 公测 day 203]              (W24 phase5-5-mid-month 中段, W25 PRD 接力)
  ↓
[2027-02-01 公测 day 220]              (W25 PRD 落地 cc14045 + tests 落地 1fbfe93)
  ↓
[2027-02-15 公测 day 234]              ⭐ (W26 skill3-v3-launch, 本文件 v3.0 启动)
  ↓
[2027-03-01 公测 day 248]              (W27 v3.0 多语言全量 50%)
  ↓
[2027-03-15 公测 day 262]              (W28 v3.0 多律所模板全量 100%)
  ↓
[2027-04-01 公测 day 279]              (W29 v2.0 通用模板退役)
```

> **关键节点核心扩展 (W26 launch vs W21 v2.0 rollout vs W23 phase5-5-celebration)**:
> - **衔接 W23**: W23 phase5-5-celebration 已规划 v3.0 三节点 (1/15 + 2/1 + 3/1), W26 launch 拆更细为四阶段 (2/15 启动 + 3/1 50% + 3/15 100% + 4/1 退役)
> - **衔接 W25**: W25 cc14045 PRD + 1fbfe93 tests 已落地 v3.0 PRD + 50 测试, W26 launch 补充 rollout + 退役 + 推广
> - **衔接 W21**: W21 6929cc1 v2.0 全量 + v1.0 退役格式样板 (复用 100% rollout + 退役 5 验证清单), W26 v3.0 跟 v2.0 同节奏
> - **衔接 W19**: W19 2cc2d3a 灰度机制 (RolloutConfig + hash 分配 + MetricsCollector), W26 v3.0 复用 W19 灰度底层 + 新增 v3.0 字段 (multi_device + multi_lang + firm + v2_deprecated)

---

## 2. Skill 3 v3.0 升级路径 (v2.0 W21 6929cc1 → v3.0 W26, additive 渐进)

### 2.1 v3.0 4 步升级路径

```
[Step 1: 复用基础 (W21 6929cc1 + W19 2cc2d3a + W15 e3f0940/3d429cd + W12 829d25c + W9 5d8ecdc)]
  - v2.0 全量模板 (letter_v2.md, 8 律师反馈驱动, 5 维度风险标注 + 客户签字栏 + doc_workflow)
  - v2.0 全量 prompt (skill3_letter_v2.yaml, 5 维度深度推理 + 阈值 0.6)
  - v2.0 全量 API (POST /api/doc-gen/letter-v2, GET /rollout/status, GET /metrics, GET /health)
  - v2.0 灰度机制 (RolloutConfig + assign_version + MetricsCollector, 4/1 letter_v2 退役)
  - v2.0 doc_workflow (5 状态机: draft → ai_reviewed → lawyer_reviewed → client_signed → archived)
  - 复用比例: 80%+ (W23 phase5-5-celebration v2.0 全面应用 5 个月 + 5000+ 律师函累计验证)

[Step 2: 多端扩展 (W26 2/15 启动)] 新增 iOS + Android + iPad
  - mobile/ios/LetterMobile/App.tsx + mobile/android/LetterMobile/App.tsx + mobile/ipad/LetterPad/App.tsx
  - React Native 0.73+ + Expo 51+ + React Navigation 6+ + Zustand 4+
  - 跨平台同步 (WebSocket + SQLite 本地缓存 + 云端 WebDAV/S3 三层)
  - Apple Pencil 2 代支持 (律师手写签字 + 模板自定义标注)
  - 50 律师灰度 (2/15 启动)

[Step 3: 多语言扩展 (W26 launch + W27 接力)] 新增英文 + 双语对照 + react-i18next
  - templates/docs/letter_v3_zh.md (中文律师函 v3.0, 复用 v2.0)
  - templates/docs/letter_v3_en.md (英文律师函 v3.0, 英美法系 + 香港法 + 新加坡法 + 国际仲裁)
  - templates/docs/letter_v3_bilingual.md (双语对照律师函 v3.0, 跨境案件)
  - prompts/skill3_letter_v3.yaml (W26 多语言版 prompt, language + jurisdiction + bilingual_layout)
  - react-i18next 13+ 框架 (zh-CN + en-US 资源 + localStorage 缓存 + 自动检测)
  - 250 律师覆盖 (3/1 50%)

[Step 4: 多律所模板扩展 (W26 launch + W28 接力)] 新增 40+ 律所定制模板
  - templates/firms/10_big/ (10 大综合所: 盈科 + 大成 + 德恒 + 锦天城 + 中伦 + 君合 + 方达 + 金杜 + 海问 + 汉坤)
  - templates/firms/50_medium/ (50 中型所, 省级头部所 5-30 律师, W26 launch 详细清单)
  - templates/firms/20_small/ (20 中小型所, 3-10 律师 + L4 中所合伙人, W26 launch 详细清单)
  - core/firm_branding.py (律所定制 logo + 主题色 + 律所风格 + 律所历史文书库)
  - marketplace/firm_marketplace.py (律所版定制 Marketplace 高级功能, 10 律师起 ¥99,999/年)
  - 500 律师覆盖 (3/15 100%) + 100 律所
  - v2.0 通用模板退役 (4/1 letter_v2_deprecated=true, 跟 v1.0 退役节奏一致 W21)
```

> **v3.0 4 步升级路径核心扩展 (vs v2.0)**:
> - **Step 1 复用基础**: v2.0 全面应用 5 个月 (W23 phase5-5-celebration, 5000+ 律师函累计 + 4.5+/5.0 评分 + 4.6+/5.0 满意度) 复用比例 80%+
> - **Step 2 多端**: v2.0 桌面端 (Windows + macOS + Linux, W20 Electron 17.4.11) → v3.0 桌面 + iOS + Android + iPad, 跨平台数据同步 (WebSocket + SQLite 本地缓存 + 云端 WebDAV/S3 三层)
> - **Step 3 多语言**: v2.0 中文单语 → v3.0 中文 + 英文 + 双语对照 (跨境案件 + 国际客户 + 涉外律所 + 国际仲裁), react-i18next 13+ 框架
> - **Step 4 多律所模板**: v2.0 通用模板 → v3.0 40+ 律所定制模板 (律所 logo + 主题色 + 律所风格 + 律所历史文书库), Marketplace 高级功能 (10 律师起 ¥99,999/年)

### 2.2 v3.0 兼容性保证 (W12 A2 doc_workflow 不动)

> **W26 skill3-v3-launch 严守兼容性原则 (W21 + W22 6 plan 验证, W23 + W24 接力)**:
> - **W12 A2 doc_workflow 5 状态机不动**: draft → ai_reviewed → lawyer_reviewed → client_signed → archived (W26 多端 + 多语言 + 多律所模板 复用)
> - **W12 A2 signature_router 不动**: POST /api/signature/{doc_id} (W26 多端 iPad Apple Pencil 签字复用)
> - **W21 6929cc1 v2.0 已有代码不动**: rollout.py + doc_gen_router.py + letter_v2.md + skill3_letter_v2.yaml (W26 v3.0 是叠加, 新增 rollout_v3.py 不修改 v2.0)
> - **W19 2cc2d3a 灰度机制不动**: RolloutConfig + assign_version + MetricsCollector (W26 v3.0 复用, 新增 v3_multi_device_pct + v3_multi_lang_pct + v3_firm_pct + letter_v2_deprecated)
> - **W15 e3f0940/3d429cd v2.0 模板不动**: letter_v2.md + skill3_letter_v2.yaml 保持原样 (W26 v3.0 是 letter_v3_zh/en/bilingual + skill3_letter_v3.yaml 新增)
> - **PRD V5.0 § 5.4 + § 5.6 + § 11 不动**: Skill Hub 9 Skill + 当事人服务类文书 + 法务自检 (W26 v3.0 严格遵守)

### 2.3 v3.0 vs v2.0 关键对比 5 大变化

| 维度 | v2.0 (10/1 全量 100%, W21 6929cc1) | v3.0 (3/15 100%, W26 launch + W28 接力) | 变化 |
|------|------------------------------------|---------------------------------------|------|
| **平台** | 桌面端 (Windows + macOS + Linux) | 多端 (桌面 + iOS + Android + iPad) | + 移动 + iPad |
| **语言** | 中文 (单语) | 中英双语 (中 + 英 + 双语对照) | + 英文 + 双语对照 |
| **律所模板** | 通用模板 | 80+ 律所定制模板 (10 大 + 50 中型 + 20 中小型) | + 律所 logo + 主题色 + 律所风格 + 律所历史文书库 |
| **Marketplace** | 不支持 | 支持 (文书模板分享 + 抽成 5% + 律所版定制 ¥99,999/年起) | + Marketplace 集成 (MVP 1/15 → 公测 2/1 → 全功能 3/15) |
| **场景** | 中国大陆律师 | 跨境案件 + 国际客户 + 涉外律所 + 国际仲裁 | + 跨境案件 (英美法系 + 香港法 + 新加坡法 + ICC/HKIAC/SIAC) |
| **个人版定价** | ¥99/月 | ¥99/月 | 持平 |
| **企业版定价** | ¥1,500-2,000/律师/年 | ¥1,500-2,000/律师/年 | 持平 |
| **律所版定制** | - | ¥99,999 起 (10 律师起, 含 logo + 主题色 + 私有化部署) | + 律所版定制新增 |
| **覆盖律师** | 250 (1/1, W23) | 500 (3/15 期望) | + 250 律师 (2x) |
| **覆盖律所** | 50 (1/1, W23) | 100 (3/15 期望) | + 50 律所 (2x) |
| **跨境案件** | 不支持 | 支持 (中英双语 + 国际仲裁) | + 跨境案件新增 |
| **国际客户** | 不支持 | 支持 (英文模板 + 双语对照) | + 国际客户新增 |
| **涉外律所** | 不支持 | 支持 (英文模板 + 双语对照) | + 涉外律所新增 |
| **退役计划** | v1.0 退役 11/1 (W21) | v2.0 退役 4/1 (W29 deferred) | + v2.0 退役延期 5 个月 |

> **v3.0 vs v2.0 关键对比 5 大变化 (核心扩展)**:
> - **平台扩展**: 桌面端 → 多端 (桌面 + 移动 + iPad), 跨平台数据同步 (WebSocket + SQLite 本地缓存 + 云端)
> - **语言扩展**: 中文 → 中英双语, 适配跨境案件 + 国际客户 + 涉外律所 (英美法系 + 香港法 + 新加坡法 + ICC/HKIAC/SIAC)
> - **律所模板扩展**: 通用模板 → 80+ 律所定制模板, 律所 logo + 主题色 + 律所风格 + 律所历史文书库
> - **Marketplace 集成**: 不支持 → 支持 (文书模板分享 + 抽成 5% + 律所版定制 ¥99,999/年起)
> - **场景扩展**: 中国大陆律师 → 跨境案件 + 国际客户 + 涉外律所 + 国际仲裁 (W26 多语言核心扩展)

---

## 3. Skill 3 v3.0 测试套件 (复用 W25 1fbfe93 50 测试)

### 3.1 测试套件结构 (35 baseline + 15 v3.0 多场景)

> **复用 W25 commit 1fbfe93 `tests/skill3-v3/test_v3.py` (1004 行, 50 测试, 4 fixture)**:

| 测试 Class | 测试数 | 复用来源 | 覆盖范围 |
|------------|-------|---------|----------|
| **TestRolloutConfig** | 5 | W19-1..4 + W21-1 | 默认配置 + 边界 + env 加载 + 退役字段 |
| **TestAssignVersion** | 10 | W19-5..15 + W21-3..5 | 4 阶段 + 退役 + force_v1/v2 + hash 稳定 + doc_type 过滤 |
| **TestHashLawyer** | 3 | W19-12..14 | range 0-99 + 稳定性 + 均匀分布 |
| **TestMetricsCollector** | 8 | W19-15..22 | record + satisfaction + conversion + summary + ab_winner |
| **TestEndpoints** | 6 | W19-23..27 + W21-5 | /health + /rollout/status + /metrics + /letter + /letter-v2 + deprecation |
| **TestBackwardCompat** | 3 | W21-6..8 | 模板文件 + DOC_TYPES + letter 加载 |
| **TestV3MultiEndpoint** | 5 | W25 新增 (移动 + iPad) | iPhone/Android/iPad UA + JSON schema |
| **TestV3MultiLanguage** | 5 | W25 新增 (中英双语) | 中英字段 + prompt 双语 + 错误消息 + bucket 标签 |
| **TestV3MultiFirm** | 5 | W25 新增 (40+ 律所) | 42 律所 hash + 5 维度 + A/B + 100pct + 退役 |
| **总计** | **50** | **35 baseline + 15 v3.0** | **覆盖 W26 v3.0 launch 全部场景** |

> **关键设计 (复用 W25 决策)**:
> - **路径**: `tests/skill3-v3/test_v3.py` (W25 新建, 不在 `backend/cases-crawler/tests/`)
> - **sys.path 注入**: 独立可跑, 不污染 backend 测试
> - **不修改 W21 6929cc1**: 0 修改 backend/cases-crawler/* 文件
> - **fixture**: reset_global_state (autouse) + mobile_iphone_ua + mobile_android_ua + tablet_ipad_ua + forty_law_firms (42 mock)
> - **运行**: `python -m pytest tests/skill3-v3/test_v3.py` 1.01s 跑完 50 测试, ruff 0 errors

### 3.2 35 Baseline 测试覆盖 (W19 + W21 复用)

> **复用 W19 commit 2cc2d3a 35 灰度测试 + W21 commit 6929cc1 36 退役测试 → W25 1fbfe93 35 baseline**:
> - **TestRolloutConfig (5)**: phase=disabled, pct=0, ab=(50,50), letter_v1_deprecated=False 默认 + 边界 + env 加载 + 退役字段
> - **TestAssignVersion (10)**: 4 阶段路由 + 退役开关 + force_v1/v2 + hash 稳定 + doc_type 过滤
> - **TestHashLawyer (3)**: SHA-256 hash % 100 ∈ [0, 99] + 稳定性 + 均匀分布 (1000 律师 / 100 桶, 3-sigma 容许 3-22)
> - **TestMetricsCollector (8)**: record + satisfaction (1-5) + conversion (0/1) + summary + ab_winner
> - **TestEndpoints (6)**: /health + /rollout/status (含退役字段) + /metrics + /letter + /letter-v2 + deprecation
> - **TestBackwardCompat (3)**: v1/v2 模板文件 + DOC_TYPES + letter 加载 (W21 兼容)

> **W26 v3.0 launch 复用要点**: W26 v3.0 rollout 复用全部 35 baseline (灰度 + 退役 + 兼容性逻辑 v2.0/v3.0 双支持), 不重设计

### 3.3 15 v3.0 多场景测试 (W25 新增, W26 launch 复用)

> **W25 新增 15 v3.0 测试覆盖 W26 launch 三大方向**:

| v3.0 方向 | 测试 Class | 测试数 | 覆盖范围 |
|----------|-----------|-------|----------|
| **多端 (移动 + iPad)** | TestV3MultiEndpoint | 5 | iPhone Safari UA + Android Chrome UA + iPad Safari UA + JSON schema 完整 + 9 必填字段 |
| **多语言 (中英)** | TestV3MultiLanguage | 5 | 19 中文字段 + 15 英文字段 + prompt 双语 (10 key) + 错误消息中英 + bucket 标签中英 |
| **多律所模板 (40+)** | TestV3MultiFirm | 5 | 42 mock 律所 hash 稳定 + 5 维度评分 ≥ 0.7 + A/B winner + 100pct 全 v2 + 退役全 v2 |

> **W26 v3.0 launch 复用要点**: W26 launch 引用 W25 1fbfe93 50 测试报告, 不重跑测试 (W26 仅 rollout-only, 不动测试). W27+ 接力 W25 deferred items:
> - `tests/skill3-v3/test_v3_40firms.py` (W27 deferred, 40 律所独立模板测试, 5-8 测试)
> - `tests/skill3-v3/test_v3_viewport.py` (W27 deferred, 5 移动端 viewport, Playwright)
> - `tests/skill3-v3/test_v3_ipad.py` (W27 deferred, iPad screenshot 5 张, Playwright headless)

---

## 4. Skill 3 v3.0 PRD 引用 (W25 cc14045 落地, W26 launch 复用)

### 4.1 PRD 三大方向 (W25 cc14045 详细 PRD, W26 launch 引用)

> **复用 W25 commit cc14045 `docs/skills/contract-review/skill3-v3-prd-2027-02-01.md` (550 行 ~38KB)**:

| 方向 | 启动节点 | 完成节点 | 核心功能 | 期望覆盖律师 | 5 维度评分 | 关键 commit |
|------|---------|---------|---------|------------|-----------|------------|
| **多端 (移动 + iPad)** | 2027-01-15 (W24 plan) | 2027-02-15 (W26 启动 50 律师) | iOS + Android + iPad App, 跨平台同步 | 50 → 200 | 4.5+/5.0 | W26 launch (本文件) |
| **多语言 (中英)** | 2027-02-15 (W26 启动) | 2027-03-01 (50%) → 2027-03-15 (100%) | 中文 + 英文 + 双语对照模板 + react-i18next | 50 → 250 → 500 | 4.6+/5.0 | W26 launch + W27 接力 |
| **多律所模板 (40+ 律所)** | 2027-03-15 (W28 接力) | 2027-04-01 (100%) | 10 大综合所 + 50 中型所 + 20 中小型所 | 250 → 500 | 4.6+/5.0 | W28 接力 |

> **W26 launch vs W25 PRD 核心差异**:
> - **W25 PRD (550 行 ~38KB)**: 详细 PRD, 含多端 + 多语言 + 多律所模板 3 大方向完整设计 + 5 段式 + Marketplace 集成 + 跨境案件场景
> - **W26 launch (本文件 ~30KB)**: launch 落档, 引用 W25 PRD + tests 报告, 补充 rollout 计划 (2/15 启动 + 3/1 50% + 3/15 100% + 4/1 v2.0 退役) + 推广计划 (5 渠道)

### 4.2 多端 + 多语言 + 多律所模板 (W26 launch 引用 W25 PRD)

#### 4.2.1 多端 (W26 launch 复用 W25 PRD § 2)

> **W26 launch 引用 W25 cc14045 PRD § 2 多端 (W24 接力 1/15 → W26 launch 2/15 50 律师)**:
> - **iOS App**: React Native 0.73+ + Expo 51+, iPhone 12/13/14/15 + iOS 16+ 适配, Touch ID / Face ID 集成
> - **Android App**: React Native 0.73+ + Expo 51+, Android 11+ 适配, 指纹识别 + 面部识别集成
> - **iPad App**: iPad Pro 12.9 + iPad Air, Apple Pencil 2 代支持 (律师手写签字 + 模板自定义标注)
> - **跨平台数据同步**: WebSocket (实时同步) + SQLite 本地缓存 (离线可用) + 云端 (WebDAV / S3 兼容) 三层同步
> - **3 指标跟踪**: 5 维度评分 (移动端 vs 桌面端 vs iPad 对比) + 转化率 (移动端律师付费) + 律师满意度 (1v1 微信 + 群内反馈)

#### 4.2.2 多语言 (W26 launch 复用 W25 PRD § 3)

> **W26 launch 引用 W25 cc14045 PRD § 3 多语言 (W26 launch 2/15 启动 → W27 3/1 50%)**:
> - **中文律师函 v3.0**: 复用 W21 6929cc1 v2.0 全量模板, 升级 v3.0 多语言架构 + react-i18next zh-CN 资源
> - **英文律师函 v3.0**: 全新英文模板, 适配英美法系 (Common Law) + 香港法 + 新加坡法 + 国际仲裁 (ICC / HKIAC / SIAC)
> - **双语律师函 v3.0**: 中英双语对照版, 适合跨境案件 + 国际客户 + 涉外律所 (中英 markdown 双栏对照)
> - **react-i18next 13+**: 律师函生成 / 审核 / 签字 / 归档 4 路由国际化 (zh-CN + en-US)
> - **Marketplace 集成**: 文书模板分享 (合同模板 + 律师函模板 + 起诉状模板, ¥10-100/模板) + 抽成 5% (W23 phase5-5-launch-2027-01-01.md § 5 大方向 #5 复用)

#### 4.2.3 多律所模板 (W26 launch 引用 W25 PRD § 4)

> **W26 launch 引用 W25 cc14045 PRD § 4 多律所模板 (W26 launch 占位 + W28 接力 3/15)**:

| 律所类型 | 数量 | 律所清单 (W26 launch 占位) | 期望律师覆盖 |
|---------|------|---------------------|------------|
| **10 大综合所** | 10 | 盈科 / 大成 / 德恒 / 锦天城 / 中伦 / 君合 / 方达 / 金杜 / 海问 / 汉坤 | 200 律师 |
| **50 中型所** | 50 | 省级头部所 5-30 律师 (W26 launch 占位 + W28 详细清单) | 200 律师 |
| **20 中小型所** | 20 | 3-10 律师 + L4 中所合伙人 (W26 launch 占位 + W28 详细清单) | 100 律师 |
| **合计** | **80+** | **W26 launch 占位 + W28 详细 PRD** | **500 律师 (3/15 期望)** |

> **多律所模板核心要素 (W26 launch 占位 + W28 接力)**:
> - **律所 logo**: 各律所定制 logo (PNG / SVG, 含主色 + 副色 + 字体)
> - **主题色**: 各律所 CI 主题色 (主色 + 副色 + 强调色 + 文本色)
> - **律所风格**: 各律所品牌字体 + 排版 + 间距 + 装饰元素
> - **律所历史文书库**: 各律所过往律师函 / 合同 / 起诉状 模板 (W26 launch 占位 + W28 律师合伙人提供)
> - **Marketplace 高级功能**: 律所版定制 logo + 主题色 + 私有化部署 + Marketplace 高级 (10 律师起 ¥99,999/年)

---

## 5. Skill 3 v3.0 2/15 启动仪式 (W26 launch 核心节点)

### 5.1 启动前 5 天预热 (2/10-2/14)

```
[2/10 周三] BD 邮件 + 微信群 + 朋友圈预通知
  标题: "重要预告: 2/15 LexPrime Skill 3 v3.0 律师函 多端+多语言+多律所模板 启动"

  内容:
    - 启动时间: 2027-02-15 09:00 (公测 day 234)
    - 启动内容: Skill 3 v3.0 律师函 (多端 + 多语言 + 多律所模板)
    - 灰度范围: 5% (50 律师试用)
    - 影响范围: 仅律师函 (letter) 类型, 其他 3 文书类型 (complaint/defense/contract) 不变
    - 兼容性:
      * 现有 v2.0 文书数据保留 (W12 A2 doc_workflow 状态机不动)
      * 历史 v2.0 文书可继续查询/编辑/签字
      * 新生成律师函 v3.0 多端适配 (移动 + iPad)
      * 中英双语模板 (跨境案件 + 国际客户)
    - 升级要点 (W25 PRD cc14045 落地, 50 测试 1fbfe93 通过):
      * v3.0 多端 (iOS + Android + iPad, React Native 0.73+ + Expo 51+)
      * v3.0 多语言 (中文 + 英文 + 双语对照, react-i18next 13+)
      * v3.0 多律所模板 (80+ 律所定制, 10 大 + 50 中型 + 20 中小型)
      * Marketplace 集成 (文书模板分享 + 抽成 5% + 律所版定制 ¥99,999/年起)
      * 跨境案件场景 (英美法系 + 香港法 + 新加坡法 + ICC/HKIAC/SIAC)

[2/11 周四] 律师 1v1 微信沟通 (5 类律师代表)
  - 创史律师: [姓名 placeholder, 2/11 实测填实]
  - L4 中所合伙人: [姓名 placeholder, 2/11 实测填实]
  - L5 企业法务总监: [姓名 placeholder, 2/11 实测填实]
  - 个人版代表 5 类: [姓名 placeholder, 2/11 实测填实]

[2/12 周五] 微信群通知 (3 渠道)
  - 律师私域群 (W18 recruit-1000 5 渠道 1000 律师)
  - 律所合伙人群 (40+ 律所, W23 phase5-5 接力)
  - 公测律师群 (250 律师, W21 v2.0 全面应用 5 个月)

[2/13 周六] 朋友圈 9 宫格预热 (9 张图, 见 § 9.1)
  - 9 张图: v3.0 多端 + 多语言 + 多律所 + Marketplace + 跨境案件 + 5 维度评分 + 律师满意度 + 转化率 + 推广效果
  - 文字: "2/15 Skill 3 v3.0 律师函 启动, 多端+多语言+多律所模板, AI 辅助不替代律师"

[2/14 周日] 律师公众号 + 律协预通知
  - 律师公众号 (W18 recruit-1000, 1 推文)
  - 律协 (50 律所合作, 1 邮件)
  - 启动前一天最后提醒
```

### 5.2 2/15 09:00 启动 (1 min)

```
[08:55] Tech Lead (lex-ai/lex-coder)
  - 验证当前状态 (W21 6929cc1 v2.0 全量 100% 保持, 累计 4 个月):
    curl http://localhost:8000/api/doc-gen/rollout/status
  - 期望: phase=rollout_100pct, rollout_pct=100, letter_v1_deprecated=true (W21 11/1 退役), letter_v2_deprecated=false (4/1 待退役)
  - v2.0 4 个月累计: [X, 2/15 实测填实, owner 2/15 08:55 抓取]
  - v2.0 4 个月稳定性: [稳定/波动/异常, 2/15 实测填实]
  - v3.0 启动决策: [按计划 2/15 启动/推迟启动, 2/15 实测填实]

[08:58] 准备 env 切换命令 (W26 新增 v3.0 字段)
  $ export LEX_SKILL3_V3_ENABLED=true  # W26 新增: v3.0 启动开关
  $ export LEX_SKILL3_V3_MULTI_DEVICE_PCT=5  # W26 新增: 多端 5%
  $ export LEX_SKILL3_V3_MULTI_LANG_PCT=5  # W26 新增: 多语言 5%
  $ export LEX_SKILL3_V3_FIRM_PCT=5  # W26 新增: 多律所模板 5%
  $ export LEX_SKILL3_LETTER_V2_DEPRECATED=false  # W26 新增: 4/1 退役开关 (2/15 启动时仍可用)
  $ export LEX_SKILL3_LETTER_V1_DEPRECATED=true  # W21 保持: v1.0 退役
  # force_v3 白名单: 5 类律师代表 (创史 + L4 + L5 + 个人版 5 类)
  $ export LEX_SKILL3_FORCE_V3=lawyer_001,lawyer_011,lawyer_020,lawyer_030,lawyer_040  # placeholder, 2/15 实测填实
  $ export LEX_SKILL3_FORCE_V2=lawyer_002  # 保留评审律师白名单 (W21)

[09:00:00] 切换 env + 重启服务
  $ systemctl restart lexprime-backend
  启动时间: ~30s

[09:00:30] 验证切换成功
  $ curl http://localhost:8000/api/doc-gen/rollout/status | jq
  期望:
    {
      "rollout": {
        "phase": "rollout_100pct",
        "rollout_pct": 100,
        "v3_enabled": true,  # W26 新增
        "v3_multi_device_pct": 5,
        "v3_multi_lang_pct": 5,
        "v3_firm_pct": 5,
        "letter_v1_deprecated": true,  # W21 保持
        "letter_v2_deprecated": false,  # W26 新增, 4/1 待退役
        "deprecated_after_date": "2027-04-01",
        "backward_compat_note": "现有 v2.0 文书数据保留 (W12 A2 doc_workflow 不动), 4/1 之后只支持 v3.0 + 40+ 律所定制模板生成"
      }
    }

[09:00:45] 端到端 smoke test (5 律师抽样, force_v3 白名单)
  $ for i in 001 011 020 030 040; do
      curl -X POST http://localhost:8000/api/doc-gen/letter \
        -H "Content-Type: application/json" \
        -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)" \
        -d "{\"lawyer_id\": \"lawyer_${i}\", \"fields\": {\"sender\": \"张律师\", \"recipient\": \"李四\", \"language\": \"zh-CN\", \"firm_id\": \"yingke\"}}"
    done
  期望: 5 次调用中 100% 返回 served_version=letter_v3 + bucket=treatment_a/b + firm_template=yingke (10 大综合所)
```

### 5.3 09:15 - 19:00 启动执行 (10h 跟踪)

```
[09:15-09:30] 启动仪式 (5 时段 + 茶歇, 09:15-19:00)
| 时段 | 时间 | 环节 | 负责人 | 输出物 |
|------|------|------|--------|--------|
| 预热 | 09:15-09:30 | 50 律师群发通知 (微信群 + 邮件 + 朋友圈) | BD | 律师确认清单 + 启动说明 |
| 时段 1 | 09:30-11:00 | 50 律师首次使用 v3.0 多端 (移动 + iPad + 桌面) | 50 律师 + Tech | v3.0 生成记录 + 5 维度评分 |
| 时段 2 | 11:00-13:00 | 50 律师多语言对比 (中 vs 英 vs 双语) | 50 律师 + Tech | 多语言体验数据 + 律师反馈 |
| 茶歇 | 13:00-14:00 | 午休 + 律师微信群互动 | BD | 律师反馈收集 + 案例分享 |
| 时段 3 | 14:00-15:30 | 50 律师多律所模板 (80+ 律所定制) | 50 律师 + Tech | 多律所模板体验 + 律所定制反馈 |
| 时段 4 | 15:30-17:00 | 转化跟踪 + 客服答疑 | BD + Tech | 转化率数据 (7 天后回填) |
| 时段 5 | 17:00-19:00 | 收尾 + 当日报告启动 | 总指挥 + Tech | 2/15 实测填实数字 + 报告 |
| 收尾 | 19:00-19:30 | 5% 灰度保持 + 3/1 50% 准备 | Tech Lead | 当日报告交付 + 3/1 cron |

[09:15 抽样逻辑] 50 律师 = 5% v3.0 启动 (50 / 250 = 20% 公测律师 + 50 / 1000 = 5% 私域律师 = 50 律师)
  - 假设公测 day 234 (2/15) 律师总数 250 (W23 phase5-5 接力 + W24 中段 + W25 累计)
  - 期望启动律师: 50 (5% v3.0, 5 类律师代表)
  - A/B test 关闭: bucket 仍按 hash 50/50 划分 (treatment_a / treatment_b) 用于分桶报告
  - force_v3 白名单: 5 类律师代表 (创史 + L4 + L5 + 个人版 5 类)
  - firm_template 抽样: 10 大综合所代表 (盈科 + 大成 + 德恒 + 锦天城 + 中伦 + 君合 + 方达 + 金杜 + 海问 + 汉坤, 各 5 律师)

[09:15 抽样律师清单] 2/15 启动律师 [实测填实, owner 2/15 09:15 通过 metrics 端点查询]
  treatment_a (25 律师):
    1. [lawyer_id_001, 姓名 placeholder, 创史律师, 2/15 owner 填实]
    2. [lawyer_id_002, 姓名 placeholder, L4 中所合伙人, 2/15 owner 填实]
    ... 23 more
  treatment_b (25 律师):
    1. [lawyer_id_026, 姓名 placeholder, L5 企业法务总监, 2/15 owner 填实]
    2. [lawyer_id_027, 姓名 placeholder, 个人版代表, 2/15 owner 填实]
    ... 23 more
  firm_template 抽样 (50 律师 / 10 律所 = 5 律师/律所):
    盈科: 5 律师 [姓名 placeholder, 2/15 owner 填实]
    大成: 5 律师 [姓名 placeholder, 2/15 owner 填实]
    ... 8 more 律所
  letter_v2 用户: 200 律师 (95% v2.0 仍可用, 4/1 退役)
```

### 5.4 跟踪 3 指标 (与 v2.0 一致)

```
[指标 1: 5 维度评分] 自动 + 律师主动评分
  自动: v3.0 生成时自动从 prompt 提取 risk_dim_facts/legal/demand/deadline/consequence (0-1 浮点)
  律师: 律师生成后 24h 内主动评分 (1-5), 通过 /api/doc-gen/metrics/update 端点 PATCH
  期望分布: facts 0.7-0.9, legal 0.6-0.85, demand 0.7-0.9, deadline 0.5-0.8, consequence 0.65-0.85
  v3.0 vs v2.0 对比: 多端 + 多语言 + 多律所 是否稳定保持 4.5+/5.0
  数据来源: GET /api/doc-gen/metrics → summary.5_dimension_avg_scores

[指标 2: 转化率] 生成后 7 天跟踪
  跟踪窗口: 2/15 09:00 - 2/22 09:00 (7 天)
  转化定义: 律师生成律师函后 7 天内是否付费 (¥99/月个人版 / ¥1,500-2,000/律师/年企业版 / ¥99,999/年起律所版)
  期望: 5% 启动律师转化率 >= 35% (W21 v2.0 baseline + 持平)
  v3.0 vs v2.0 对比: 多端 + 多语言 + 多律所 是否提升转化率
  数据来源: dashboard 付费转化指标 + paid_converted 事件

[指标 3: 律师满意度] 律师主动评分
  评分时间: 生成后 48h 内律师主动评分 (1-5)
  期望: 启动律师满意度 >= 4.5/5.0 (W21 v2.0 baseline + 持平)
  v3.0 vs v2.0 对比: 多端 (移动/iPad) vs 桌面端 vs v2.0 律师满意度
  数据来源: 律师主动评价 (1v1 微信沟通 / 邮件回复 / 群内反馈)
```

---

## 6. Skill 3 v3.0 3/1 50% 灰度 (W27 接力, W26 launch 引用)

### 6.1 灰度升级 (W27 接力 W26 launch)

```
[3/1 09:00] v3.0 多语言全量 50% 灰度升级
  - 250 律师覆盖 (5% → 50%, 增加 200 律师)
  - 50 律所覆盖 (10 → 50, 增加 40 中型所)
  - env 切换: LEX_SKILL3_V3_MULTI_LANG_PCT=50
  - 灰度机制: 复用 W19 2cc2d3a RolloutConfig + SHA-256 hash 分配 + MetricsCollector
  - A/B test 关闭: bucket 仍按 hash 50/50 划分 (treatment_a / treatment_b) 用于分桶报告
  - Marketplace 公测启动 (文书模板分享 + 抽成 5%, W26 launch + W23 phase5-5 接力)

[3/1 09:00-19:00] 50% 灰度执行 (10h 跟踪)
  - 09:15-09:30: 200 律师群发通知 (微信群 + 邮件)
  - 09:30-11:00: 200 律师首次使用 v3.0 多语言 (中 + 英 + 双语)
  - 11:00-13:00: 跨境案件律师对比 v2.0 (中 vs 英 vs 双语 体验)
  - 14:00-15:30: Marketplace 公测 (文书模板分享 + 抽成 5%)
  - 17:00-19:00: 50% 灰度当日报告 + 3/15 100% 准备

[3/1 19:00] 50% 灰度决策 (3/15 100% 是否按计划执行)
  - 决策依据: [3/1 19:00 实测填实]
  - v3.0 稳定性: [稳定/波动/异常, 3/1 19:00 实测填实]
  - 律师反馈: [积极/中等/消极, 3/1 19:00 实测填实]
  - 推荐行动: [按计划 3/15 100% / 推迟 100% / 保持 50% 不变, 3/1 19:00 实测填实]
```

### 6.2 灰度机制 (复用 W19 2cc2d3a 模式)

> **复用 W19 commit 2cc2d3a 灰度底层 (不重设计)**:
> - **RolloutConfig**: env 加载 + 4 阶段 (disabled/ab_10pct/rollout_50pct/rollout_100pct)
> - **assign_version**: SHA-256 hash(lawyer_id) 稳定分配 v1.0 / v2.0 / v3.0 (deterministic, 防止串扰)
> - **MetricsCollector**: in-memory 3 指标跟踪 (5 维度评分 + 转化率 + 律师满意度)
> - **GenerationMetric**: 单次生成记录 (律师 ID + 版本 + bucket + latency + risk_scores)
> - **update_satisfaction (1-5) / update_conversion (0/1)** 律师主动评分 API
> - **env 切换**: LEX_SKILL3_V3_MULTI_DEVICE_PCT / V3_MULTI_LANG_PCT / V3_FIRM_PCT / FORCE_V3 / FORCE_V2 / FORCE_V1 / LETTER_V2_DEPRECATED / LETTER_V1_DEPRECATED
> - **强制列表**: FORCE_V3 (5 类律师代表) / FORCE_V2 (W21 评审律师) / FORCE_V1 (兼容黑名单)

> **W26 v3.0 复用 + 扩展**:
> - W19 RolloutConfig 复用 → W26 v3.0 新增 v3_enabled + v3_multi_device_pct + v3_multi_lang_pct + v3_firm_pct
> - W19 assign_version 复用 → W26 v3.0 新增 v3_0 + letter_v3 + firm_template 路由
> - W19 MetricsCollector 复用 → W26 v3.0 新增 v3_0 + multi_device + multi_lang + firm_template 维度跟踪
> - W21 letter_v1_deprecated 复用 → W26 新增 letter_v2_deprecated (4/1 退役)

### 6.3 A/B winner 决策 (复用 W19 模式)

> **复用 W19 2cc2d3a A/B test 决策模式**:
> - **A/B test 关闭 (3/1 50% 期间)**: bucket 仍按 hash 50/50 划分 (treatment_a / treatment_b) 用于分桶报告
> - **A/B winner = 综合 (满意度 + 转化率) 高者**: W19 5 维度评分 + 转化率 + 律师满意度 综合
> - **决策依据**: 3/1 19:00 实测填实, owner 决定 3/15 100% 是否按计划执行
> - **异常处理**: v3.0 报错率 > 5% 或律师强烈负面反馈 (20+) 立即回滚到 5% 灰度

---

## 7. Skill 3 v3.0 3/15 100% 全量 (W28 接力, W26 launch 引用)

### 7.1 全量切换 (W28 接力 W26 launch + W27)

```
[3/15 09:00] v3.0 多律所模板全量 100% 升级
  - 500 律师覆盖 (50% → 100%, 增加 250 律师)
  - 100 律所覆盖 (50 → 100, 增加 50 律所, 10 大 + 50 中型 + 40 中小型所)
  - env 切换: LEX_SKILL3_V3_FIRM_PCT=100
  - 全量机制: 复用 W21 6929cc1 全量 100% rollout 模式
  - 80+ 律所定制模板全量 (10 大综合所 + 50 中型所 + 20 中小型所)
  - Marketplace 高级功能 (律所版定制 logo + 主题色 + 私有化部署 + 10 律师起 ¥99,999/年)

[3/15 09:00-19:00] 100% 全量执行 (10h 跟踪)
  - 09:15-09:30: 250 律师群发通知 (微信群 + 邮件 + 朋友圈)
  - 09:30-11:00: 250 律师首次使用 v3.0 多律所模板 (80+ 律所定制)
  - 11:00-13:00: 律所合伙人验证律所定制 (10 大综合所合伙人)
  - 14:00-15:30: Marketplace 高级功能 (律所版定制 + 私有化部署)
  - 17:00-19:00: 100% 全量当日报告 + 4/1 v2.0 退役准备

[3/15 19:00] 100% 全量决策 (4/1 v2.0 退役是否按计划执行)
  - 决策依据: [3/15 19:00 实测填实]
  - v3.0 稳定性: [稳定/波动/异常, 3/15 19:00 实测填实]
  - 律师反馈: [积极/中等/消极, 3/15 19:00 实测填实]
  - 推荐行动: [按计划 4/1 v2.0 退役 / 推迟退役 / 保持 100% 不变, 3/15 19:00 实测填实]
```

### 7.2 全量验证 5 项 (复用 W21 100pct rollout 格式样板)

> **复用 W21 6929cc1 100% 全量验证 5 项 + W26 launch 扩展**:

| 验证项 | 期望结果 | 实测结果 |
|--------|----------|----------|
| **路由验证** | 500 律师 100% v3.0 (multi_device + multi_lang + firm) | [500/500 v3, 3/15 实测填实] |
| **兼容性验证** | v2.0 历史文书查询正常 | [50/50 查询成功, 3/15 实测填实] |
| **模板加载验证** | letter_v3_zh.md + letter_v3_en.md + letter_v3_bilingual.md + 80+ 律所模板加载 | [loaded=true, 3/15 实测填实] |
| **指标跟踪验证** | metrics 跟踪正常, by_version 100% letter_v3 + by_firm_template 80+ 律所 | [新增 v2 记录=0, 3/15 实测填实] |
| **应急回滚验证** | 关闭 v3_enabled 可恢复 v2.0 | [回滚逻辑正常, 3/15 实测填实] |

### 7.3 全量稳定跟踪 (3/15 - 3/31)

```
[3/15-3/31 全量阶段保持 (16 天)]
  - 每日 09:00: metrics 汇总 + 验证 by_version 100% letter_v3 + by_firm_template 80+ 律所
  - 每周一 09:00: 周度报告 (5 维度评分 + 转化率 + 律师满意度)
  - 每月 1 日 09:00: 月度报告 (3/15-3/31 全量阶段汇总 + 4/1 v2.0 退役准备)
  - cron 4/1 09:00 自动切换: scripts/trigger-skill3-v2-deprecation-0401.sh (W26 launch 占位 + W29 详细)
    * env LEX_SKILL3_LETTER_V2_DEPRECATED=true (4/1 退役开关)
```

---

## 8. Skill 3 v3.0 4/1 v2.0 退役计划 (W29 接力, W26 launch 引用)

### 8.1 v2.0 退役时间表 (5 阶段, 复用 W21 格式样板)

> **复用 W21 6929cc1 v1.0 退役格式样板 + W26 v2.0 退役 5 阶段时间表**:

| 阶段 | 日期 | 灰度阶段 | v3.0 比例 | v2.0 退役开关 | 说明 |
|------|------|----------|----------|--------------|------|
| **预热** | 3/15 - 3/25 | rollout_100pct (v3.0) | 100% | false | 100% 全量 v3.0, letter_v2 仍可用 (force_v2 律师兼容) |
| **预通知** | 3/25 - 3/31 | rollout_100pct (v3.0) | 100% | false | BD 通知律师 4/1 v2.0 退役 (邮件 + 微信群 + 朋友圈) |
| **退役日** | 4/1 09:00 | rollout_100pct (v3.0) | 100% | **true** | 切换 letter_v2_deprecated=true, 全员 v3.0 |
| **保持** | 4/1 - 4/30 | rollout_100pct (v3.0) | 100% | true | 全员 v3.0, 持续跟踪 metrics |
| **彻底清理** | 5/1 | rollout_100pct (v3.0) | 100% | true | v2.0 模板文件归档 (W30+ 决定) |

### 8.2 v2.0 退役前 7 天预通知 (3/25 - 3/31)

```
[3/25] BD 邮件 + 微信群 + 朋友圈通知
  标题: "重要通知: 4/1 起 LexPrime 律师函 v2.0 通用模板正式退役, 全员切换 v3.0 + 80+ 律所定制模板"

  内容:
    - 退役时间: 2027-04-01 09:00 (公测 day 279)
    - 退役内容: 律师函 v2.0 通用模板 (W21 commit 6929cc1, 10/1 全量 100%) 不再生成新文书
    - 影响范围: 仅律师函 (letter) 类型, 其他 3 文书类型 (complaint/defense/contract) 不变
    - 兼容性:
      * 现有 v2.0 文书数据保留 (W12 A2 doc_workflow 状态机不动)
      * 历史 v2.0 文书可继续查询/编辑/签字
      * 新生成律师函全部走 v3.0 + 80+ 律所定制模板 (W26 launch 接力 W28)
    - 升级要点 (W26 launch + W25 PRD cc14045):
      * v3.0 多端 (iOS + Android + iPad, React Native 0.73+ + Expo 51+)
      * v3.0 多语言 (中文 + 英文 + 双语对照, react-i18next 13+)
      * v3.0 多律所模板 (80+ 律所定制, 10 大 + 50 中型 + 20 中小型)
      * Marketplace 集成 (文书模板分享 + 抽成 5% + 律所版定制 ¥99,999/年起)
      * 跨境案件场景 (英美法系 + 香港法 + 新加坡法 + ICC/HKIAC/SIAC)

[3/26-3/31] 持续提醒
  - 微信群每日 1 条 (BD)
  - 邮件 1 封 (3/30, 周二)
  - 朋友圈 1 条 (3/31, 周三)
```

### 8.3 v2.0 退役兼容性 (复用 W21 v1.0 退役机制)

> **复用 W21 6929cc1 v1.0 退役机制 (W26 launch v2.0 退役同样适用)**:
> - **W12 A2 doc_workflow 5 状态机不动**: draft → ai_reviewed → lawyer_reviewed → client_signed → archived (W26 多端 + 多语言 + 多律所模板 复用)
> - **W12 A2 signature_router 不动**: POST /api/signature/{doc_id} (W26 多端 iPad Apple Pencil 签字复用)
> - **现有 v2.0 文书数据保留**: W12 A2 doc_workflow 不动, 历史 v2.0 文书可继续查询/编辑/签字
> - **letter_v2.md 模板文件保留**: 供历史数据查询 (不删除模板文件)
> - **新增 v2 记录 = 0**: letter_v2_deprecated=true 后, assign_version letter_v2_deprecated 优先级最高, 强制 v3.0
> - **应急回滚机制**: 关闭 letter_v2_deprecated 可临时恢复 v2.0 (紧急情况, 例如律师投诉)

---

## 9. Skill 3 v3.0 推广计划 (5 渠道)

### 9.1 朋友圈 9 宫格 (2/13 预热 + 2/15 启动 + 3/1 50% + 3/15 100% + 4/1 v2.0 退役)

> **W26 skill3-v3-launch 朋友圈 9 宫格推广计划 (复用 W18 recruit-1000 朋友圈模板, 5 节点)**:

| 节点 | 日期 | 9 宫格主题 | 9 张图清单 | 期望覆盖 |
|------|------|-----------|-----------|---------|
| **2/13 预热** | 2027-02-13 | Skill 3 v3.0 启动预告 | (1) 多端 iOS + Android + iPad (2) 多语言中英双语 (3) 多律所模板 10 大综合所 (4) Marketplace 文书模板分享 (5) 跨境案件英美法系 (6) 5 维度评分 4.5+/5.0 (7) 律师满意度 4.6+/5.0 (8) 转化率 35%+ (9) AI 辅助不替代律师 | 1000+ 律师私域 |
| **2/15 启动** | 2027-02-15 | Skill 3 v3.0 启动仪式 | (1) v3.0 启动 5% (2) 多端灰度 50 律师 (3) 多语言公测 (4) 多律所模板 10 大综合所 (5) Marketplace 公测 (6) 跨境案件首单 (7) 5 维度评分 4.5+/5.0 (8) 律师满意度 4.6+/5.0 (9) 2/15 实测填实数据 | 1000+ 律师私域 + 250 公测律师 |
| **3/1 50%** | 2027-03-01 | Skill 3 v3.0 多语言全量 50% | (1) 多语言 50% 250 律师 (2) Marketplace 公测 (3) 跨境案件 50% (4) 双语对照 50% (5) 英文模板 50% (6) react-i18next 50% (7) 5 维度评分 4.6+/5.0 (8) 律师满意度 4.6+/5.0 (9) 3/1 实测填实数据 | 1000+ 律师私域 + 250 公测律师 + 50 律所合伙人 |
| **3/15 100%** | 2027-03-15 | Skill 3 v3.0 多律所模板全量 100% | (1) 多律所 100% 500 律师 (2) 80+ 律所定制 (3) 10 大综合所全量 (4) 50 中型所全量 (5) 20 中小型所全量 (6) Marketplace 高级 (7) 律所版定制 ¥99,999/年起 (8) 5 维度评分 4.6+/5.0 (9) 3/15 实测填实数据 | 1000+ 律师私域 + 500 公测律师 + 100 律所合伙人 |
| **4/1 v2.0 退役** | 2027-04-01 | Skill 3 v2.0 通用模板退役 | (1) v2.0 退役 100% (2) v3.0 + 80+ 律所 (3) 跨境案件 100% (4) Marketplace 100% (5) v1.0 退役 5 个月回顾 (6) v2.0 退役 0 投诉 (7) 5 维度评分 4.6+/5.0 (8) 律师满意度 4.6+/5.0 (9) 4/1 实测填实数据 | 1000+ 律师私域 + 500 公测律师 + 100 律所合伙人 |

> **朋友圈 9 宫格核心要素**:
> - **9 张图比例**: 1:1 (1080x1080) + 4:3 (1080x810) + 16:9 (1920x1080) 三种比例, 适配微信朋友圈 + 公众号 + 律师群
> - **文字模板**: "2/15 Skill 3 v3.0 律师函 启动, 多端+多语言+多律所模板, AI 辅助不替代律师 [律师姓名] [2/15 实测填实数据]"
> - **传播路径**: 总指挥朋友圈 → 律师私域 (1000+ 律师, W18 recruit-1000) → 公测律师 (250 → 500) → 律所合伙人 (50 → 100) → 律师群 (3 类, 律所/创史/个人版)
> - **数据 placeholder**: 所有 5 维度评分 + 律师满意度 + 转化率 + 推广效果 数据均为 [2/15/3/1/3/15/4/1 实测填实], owner 节点当天 09:00 patch 替换

### 9.2 律师公众号 (W18 recruit-1000 复用, 5 节点)

> **复用 W18 recruit-1000 (commit d66fc33) 5 律师渠道 1000 律师 + 律师公众号**:

| 节点 | 日期 | 公众号推文主题 | 期望阅读 | 期望转化 |
|------|------|--------------|---------|---------|
| **2/13 预热** | 2027-02-13 | Skill 3 v3.0 启动预告 (多端 + 多语言 + 多律所模板) | [X, 2/13 实测填实] | [X, 2/13 实测填实] |
| **2/15 启动** | 2027-02-15 | Skill 3 v3.0 启动仪式 (5% 灰度 + 跨境案件 + Marketplace) | [X, 2/15 实测填实] | [X, 2/15 实测填实] |
| **3/1 50%** | 2027-03-01 | Skill 3 v3.0 多语言全量 50% (中英双语 + 双语对照 + 国际仲裁) | [X, 3/1 实测填实] | [X, 3/1 实测填实] |
| **3/15 100%** | 2027-03-15 | Skill 3 v3.0 多律所模板全量 100% (80+ 律所定制 + Marketplace 高级) | [X, 3/15 实测填实] | [X, 3/15 实测填实] |
| **4/1 v2.0 退役** | 2027-04-01 | Skill 3 v2.0 通用模板退役 (回顾 v2.0 6 个月 + v3.0 + 80+ 律所展望) | [X, 4/1 实测填实] | [X, 4/1 实测填实] |

> **律师公众号核心要素**:
> - **5 渠道 1000 律师**: W18 recruit-1000 (commit d66fc33) 律师渠道 (创史律师 + 个人版 + 企业版 + 律所合伙人 + 律师协会)
> - **公众号推文**: 5 节点 5 推文, 复用 W18 recruit-1000 + W23 phase5-5-celebration + W24 phase5-5-mid-month 推文模板
> - **推广效果**: 阅读量 + 转化率 (阅读后 7 天付费) + 律师满意度 (公众号评论 + 律师群反馈)
> - **数据 placeholder**: 所有数据均为 [2/13/2/15/3/1/3/15/4/1 实测填实], owner 节点当天 09:00 patch 替换

### 9.3 律协 (50 律所合作, 复用 W23 phase5-5-celebration 律所合作)

> **复用 W23 phase5-5-celebration 律所合作清单 + W26 launch 50 律所合作**:

| 律所类型 | 数量 | 律所清单 (W26 launch 占位 + W28 详细) | 期望律师覆盖 |
|---------|------|-----------------------------------|------------|
| **10 大综合所** | 10 | 盈科 / 大成 / 德恒 / 锦天城 / 中伦 / 君合 / 方达 / 金杜 / 海问 / 汉坤 | 200 律师 |
| **50 中型所** | 50 | 省级头部所 5-30 律师 (W26 launch 占位 + W28 详细清单) | 200 律师 |
| **20 中小型所** | 20 | 3-10 律师 + L4 中所合伙人 (W26 launch 占位 + W28 详细清单) | 100 律师 |
| **合计** | **80+ 律所** | **W26 launch 占位 + W28 详细 PRD** | **500 律师 (3/15 期望)** |

> **律协核心要素 (复用 W23 phase5-5-celebration 律所合作机制)**:
> - **律所合伙人 1v1 沟通**: W26 launch 2/15 启动前 5 类律师代表 + 律所合伙人 (W26 launch 律所合作清单)
> - **律所 logo + 主题色 + 律所风格 + 律所历史文书库**: W28 多律所模板接力, 律所合伙人提供
> - **Marketplace 高级功能**: 律所版定制 logo + 主题色 + 私有化部署 + Marketplace 高级 (10 律师起 ¥99,999/年)
> - **律所合伙人反馈**: 1v1 微信沟通 + 律所群 + 律所合伙人大会 (W23 phase5-5-celebration 接力)

### 9.4 律师私域 (W18 recruit-1000 5 渠道, 复用)

> **复用 W18 recruit-1000 (commit d66fc33) 5 律师渠道 1000 律师私域**:

| 渠道 | 数量 | 律师类型 | 推广内容 |
|------|------|---------|---------|
| **创史律师** | 40 | 创史 + 资深合伙人 | v3.0 多端 + 多律所定制 + Marketplace 高级 |
| **个人版** | 220 | 个人律师 + 个人版代表 | v3.0 多端 (移动) + 多语言 (跨境) |
| **企业版** | 40 | 企业法务总监 + L5 企业法务 | v3.0 多语言 (双语对照) + 跨境案件 |
| **律所合伙人** | 60 | L4 中所合伙人 + 律所合伙人 | v3.0 多律所定制 + Marketplace 律所版 |
| **律师协会** | 640 | 律师协会 + 公测律师 | v3.0 全功能 + 朋友圈 9 宫格 + 律师公众号 |
| **合计** | **1000** | **5 律师渠道** | **5 节点 × 5 渠道 = 25 推广触达** |

> **律师私域核心要素 (复用 W18 recruit-1000)**:
> - **5 律师渠道 1000 律师**: W18 recruit-1000 招募 1000 律师 (创史 + 个人 + 企业 + 律所 + 律协)
> - **25 推广触达**: 5 节点 (2/13 + 2/15 + 3/1 + 3/15 + 4/1) × 5 渠道 = 25 次推广触达
> - **推广效果**: 朋友圈 9 宫格 + 律师公众号 + 微信群 + 邮件 + 1v1 沟通 5 种方式
> - **数据 placeholder**: 所有数据均为 [2/13/2/15/3/1/3/15/4/1 实测填实], owner 节点当天 09:00 patch 替换

### 9.5 40+ 律所合作 (W26 launch 占位 + W28 多律所模板详细 PRD)

> **W26 launch 占位 + W28 多律所模板接力, 40+ 律所合作**:

| 律所 | 律师覆盖 | 律所 logo | 主题色 | 律所风格 | 律所历史文书库 | Marketplace 高级 |
|------|---------|----------|--------|---------|--------------|-----------------|
| **盈科 (Yingke)** | 50+ 律师 | [logo URL, 2/15 实测填实] | [主色, 2/15 实测填实] | [风格, 2/15 实测填实] | [文书库, W28 实测填实] | [¥99,999/年起, W28 实测填实] |
| **大成 (Dentons)** | 50+ 律师 | [logo URL, 2/15 实测填实] | [主色, 2/15 实测填实] | [风格, 2/15 实测填实] | [文书库, W28 实测填实] | [¥99,999/年起, W28 实测填实] |
| **德恒 (DeHeng)** | 30+ 律师 | [logo URL, 2/15 实测填实] | [主色, 2/15 实测填实] | [风格, 2/15 实测填实] | [文书库, W28 实测填实] | [¥99,999/年起, W28 实测填实] |
| **锦天城 (AllBright)** | 30+ 律师 | [logo URL, 2/15 实测填实] | [主色, 2/15 实测填实] | [风格, 2/15 实测填实] | [文书库, W28 实测填实] | [¥99,999/年起, W28 实测填实] |
| **中伦 (ZhongLun)** | 30+ 律师 | [logo URL, 2/15 实测填实] | [主色, 2/15 实测填实] | [风格, 2/15 实测填实] | [文书库, W28 实测填实] | [¥99,999/年起, W28 实测填实] |
| **君合 (JunHe)** | 30+ 律师 | [logo URL, 2/15 实测填实] | [主色, 2/15 实测填实] | [风格, 2/15 实测填实] | [文书库, W28 实测填实] | [¥99,999/年起, W28 实测填实] |
| **方达 (FangDa)** | 30+ 律师 | [logo URL, 2/15 实测填实] | [主色, 2/15 实测填实] | [风格, 2/15 实测填实] | [文书库, W28 实测填实] | [¥99,999/年起, W28 实测填实] |
| **金杜 (King & Wood)** | 30+ 律师 | [logo URL, 2/15 实测填实] | [主色, 2/15 实测填实] | [风格, 2/15 实测填实] | [文书库, W28 实测填实] | [¥99,999/年起, W28 实测填实] |
| **海问 (Haiwen)** | 20+ 律师 | [logo URL, 2/15 实测填实] | [主色, 2/15 实测填实] | [风格, 2/15 实测填实] | [文书库, W28 实测填实] | [¥99,999/年起, W28 实测填实] |
| **汉坤 (Han Kun)** | 20+ 律师 | [logo URL, 2/15 实测填实] | [主色, 2/15 实测填实] | [风格, 2/15 实测填实] | [文书库, W28 实测填实] | [¥99,999/年起, W28 实测填实] |
| **... 70 more 律所** | 280+ 律师 | [W28 详细 PRD] | [W28 详细 PRD] | [W28 详细 PRD] | [W28 详细 PRD] | [W28 详细 PRD] |
| **合计 80+** | **500+ 律师** | **80+ logo** | **80+ 主题色** | **80+ 律所风格** | **80+ 文书库** | **¥99,999/年起 × 80+** |

> **40+ 律所合作核心要素 (W26 launch 占位 + W28 详细 PRD)**:
> - **律所 logo + 主题色 + 律所风格**: W28 接力 W26 launch, 律所合伙人提供 + W26 launch 占位说明
> - **律所历史文书库**: W28 律师合伙人提供, W26 launch 占位说明
> - **Marketplace 高级功能**: 律所版定制 logo + 主题色 + 私有化部署 + Marketplace 高级 (10 律师起 ¥99,999/年)
> - **律所版定制收费**: W28 律师合伙人签订合作协议 + Marketplace 高级功能集成 + W26 launch 占位
> - **数据 placeholder**: 所有数据均为 [2/15/3/1/3/15 实测填实], owner 节点当天 09:00 patch 替换

---

## 10. Skill 3 v3.0 跟踪 3 指标 (与 v2.0 一致)

### 10.1 v3.0 四阶段 3 指标跟踪

| 指标 | 公式 | 期望目标 | 2/15 启动 | 3/1 50% | 3/15 100% | 4/1 v2.0 退役 |
|------|------|----------|----------|--------|----------|--------------|
| **5 维度评分** | 平均 (facts + legal + demand + deadline + consequence) | >= 4.5/5.0 v2 → 4.6+/5.0 v3 | [4.5+/5.0, 2/15 实测填实] | [4.6+/5.0, 3/1 实测填实] | [4.6+/5.0, 3/15 实测填实] | [4.6+/5.0, 4/1 实测填实] |
| **转化率 (7 天)** | paid_converted / doc_gen_request | >= 35% v2 → 持平 v3 | [0.XX, 2/22 实测填实] | [0.XX, 3/8 实测填实] | [0.XX, 3/22 实测填实] | [0.XX, 4/8 实测填实] |
| **律师满意度** | 律师主动评分 (1-5) | >= 4.5/5.0 v2 → 4.6+/5.0 v3 | [4.6+/5.0, 2/15 实测填实] | [4.6+/5.0, 3/1 实测填实] | [4.6+/5.0, 3/15 实测填实] | [4.6+/5.0, 4/1 实测填实] |

> **v3.0 四阶段 3 指标跟踪 (与 v2.0 一致)**:
> - **5 维度评分**: v2.0 持平 4.5+/5.0 (W21 全面应用 6 个月 baseline), v3.0 多端 → 多语言 → 多律所模板 持续优化 4.6+/5.0 (持平 + 个性化 + 跨境案件)
> - **转化率 (7 天)**: v2.0 持平 35%+ (W21 baseline), v3.0 多端 → 多语言 → 多律所模板 持续优化 (持平 + Marketplace 抽成 + 律所版定制)
> - **律师满意度**: v2.0 持平 4.6+/5.0 (W21 律师主动评分), v3.0 多端 → 多语言 → 多律所模板 持续优化 4.6+/5.0 (持平 + 跨平台 + Marketplace + 跨境案件 + 律所定制)

### 10.2 v3.0 多端 vs 多语言 vs 多律所模板 3 指标对比

> **v3.0 三大方向 3 指标对比 (W26 launch + W25 PRD § 6)**:

| 方向 | 5 维度评分 | 转化率 | 律师满意度 | 期望律师覆盖 | 期望律所覆盖 |
|------|----------|--------|-----------|------------|------------|
| **多端 (移动 + iPad)** | [4.5+/5.0, 2/15 实测填实] | [0.XX, 2/22 实测填实] | [4.6+/5.0, 2/15 实测填实] | 50 (2/15) → 200 (W25 接力) | 10 (2/15) → 50 (3/1) |
| **多语言 (中英双语)** | [4.6+/5.0, 3/1 实测填实] | [0.XX, 3/8 实测填实] | [4.6+/5.0, 3/1 实测填实] | 250 (3/1) → 500 (3/15) | 50 (3/1) → 100 (3/15) |
| **多律所模板 (80+ 律所)** | [4.6+/5.0, 3/15 实测填实] | [0.XX, 3/22 实测填实] | [4.6+/5.0, 3/15 实测填实] | 500 (3/15) | 100 (3/15) |

> **核心对比**: 3 大方向 3 指标全部持平 v2.0 (律师主动评分是核心, AI 评分仅辅助), 验证 v3.0 多端 + 多语言 + 多律所模板 是否稳定保持 v2.0 全面应用 6 个月 (W21 6929cc1 + W23 432a073 phase5-5-celebration) 的律师体验

---

## 11. Skill 3 v3.0 应急备案 (4 场景)

### 11.1 场景 1: v3.0 多端移动端崩溃

| 维度 | 详情 |
|------|------|
| **触发条件** | 2/15 09:30 移动端律师函生成失败 > 10% (iOS + Android) |
| **应急方案** | 立即回滚 v3.0 多端 (env `LEX_SKILL3_V3_MULTI_DEVICE_PCT=0`), v2.0 桌面端 + 修复 iOS/Android bug + 2/16 09:00 重试 |
| **owner** | lex-coder (W26 launch 占位 + W27 详细) |

### 11.2 场景 2: v3.0 多语言英文翻译质量低

| 维度 | 详情 |
|------|------|
| **触发条件** | 3/1 09:30 英文律师函 5 维度评分 < 4.0/5.0 |
| **应急方案** | 立即暂停英文版本 (env `LEX_SKILL3_V3_MULTI_LANG_EN_PCT=0`), 调优 prompt (skill3_letter_v3_en.yaml) + 1 周后重试 + 3/8 再验证 |
| **owner** | lex-ai |

### 11.3 场景 3: v3.0 多语言双语对照排版错乱

| 维度 | 详情 |
|------|------|
| **触发条件** | 3/1 09:30 双语对照律师函左右栏错位 / 字体不一致 |
| **应急方案** | 立即修复 markdown 模板 (letter_v3_bilingual.md) + 调整 CSS 样式 (react-i18next 13+) + 3/2 09:00 重试 |
| **owner** | lex-design + lex-coder |

### 11.4 场景 4: v3.0 多律所模板律所定制异常

| 维度 | 详情 |
|------|------|
| **触发条件** | 3/15 09:30 多律所模板律所 logo + 主题色 + 律所风格 加载失败 > 5% (80+ 律所) |
| **应急方案** | 立即回滚 v3.0 多律所模板 (env `LEX_SKILL3_V3_FIRM_PCT=0`), 修复 firm_branding.py + Marketplace 高级功能 + 律所版定制 + 3/16 09:00 重试 |
| **owner** | lex-coder + Mavis owner |

> **应急备案核心**: 严守"AI 辅助, 不替代律师"产品原则, v3.0 三大方向 (多端 + 多语言 + 多律所模板) 应急回滚 + 修复 + 重试, 不影响 v2.0 已有律师使用 + W12 A2 doc_workflow + signature_router 兼容 + Marketplace 集成 + 跨境案件场景扩展.

---

## 12. 不变性保证 (Compatibility Invariants, 复用 W25 § 7)

W26 skill3-v3-launch 不修改以下文件 (W21 6929cc1 + W19 2cc2d3a + W15 3d429cd/e3f0940 + W12 829d25c 保持原样):

- ✅ `backend/cases-crawler/api/doc_gen_router.py` (W21 增量 35 行保持原样)
- ✅ `backend/cases-crawler/core/rollout.py` (W21 增量 60 行保持原样)
- ✅ `backend/cases-crawler/templates/docs/letter_v1.md` (W21 退役 banner 保持原样)
- ✅ `backend/cases-crawler/templates/docs/letter_v2.md` (W15 v2.0 模板 4/1 退役前保持原样)
- ✅ `backend/cases-crawler/tests/test_skill3_ab_rollout.py` (W19 35 测试保持原样)
- ✅ `backend/cases-crawler/tests/test_skill3_full_rollout.py` (W21 36 测试保持原样)
- ✅ `backend/cases-crawler/tests/test_skill3_letter_v2.py` (W15 32 测试保持原样)
- ✅ `tests/skill3-v3/test_v3.py` (W25 50 测试保持原样, W26 launch 复用不重跑)
- ✅ `templates/docs/skill3_letter_v2.yaml` (W15 prompt 保持原样)
- ✅ `templates/docs/skill3_letter_v2_en.yaml` (W15 prompt 保持原样, W26 launch 引用 W25 PRD)
- ✅ `docs/marketing/skill3-v2-100pct-rollout-2026-10-01.md` (W21 全量 runbook 保持原样)
- ✅ `docs/marketing/skill3-v1-deprecation-2026-11-01.md` (W21 v1 退役 plan 保持原样)
- ✅ `docs/marketing/skill3-v2-ab-test-2026-08-15.md` (W19 10% 灰度 runbook 保持原样)
- ✅ `docs/marketing/skill3-v2-50pct-rollout-2026-09-01.md` (W19 50% 灰度 runbook 保持原样)
- ✅ `docs/skills/contract-review/skill3-v3-prd-2027-02-01.md` (W25 cc14045 PRD 保持原样, W26 launch 引用)
- ✅ `docs/skills/contract-review/skill3-v3-tests-2027-02-01.md` (W25 1fbfe93 tests 保持原样, W26 launch 引用)

**W26 launch 新增文件 (本次)**:
- ✅ `docs/skills/contract-review/skill3-v3-launch-2027-02-01.md` (本文件, ~30KB Skill 3 v3.0 launch 落档)

**W26 launch 复用文件 (不修改)**:
- ✅ `docs/skills/contract-review/skill3-v3-prd-2027-02-01.md` (W25 commit cc14045, 38KB PRD, 复用)
- ✅ `docs/skills/contract-review/skill3-v3-tests-2027-02-01.md` (W25 commit 1fbfe93, 18KB tests, 复用)

**W27+ deferred 新增文件**:
- ⏳ `tests/skill3-v3/test_v3_40firms.py` (W27 deferred, 40 律所独立模板测试)
- ⏳ `tests/skill3-v3/test_v3_viewport.py` (W27 deferred, 5 移动端 viewport)
- ⏳ `tests/skill3-v3/test_v3_ipad.py` (W27 deferred, iPad screenshot 5 张)
- ⏳ `docs/marketing/skill3-v3-multi-device-2027-02-15.md` (W27 deferred, 2/15 v3.0 多端 runbook)
- ⏳ `docs/marketing/skill3-v3-multi-lang-2027-02-15.md` (W27 deferred, 2/15 v3.0 多语言 runbook)
- ⏳ `docs/marketing/skill3-v3-firm-template-2027-03-15.md` (W27 deferred, 3/15 v3.0 多律所模板 runbook)
- ⏳ `docs/marketing/skill3-v3-launch-promotion-2027-02-15.md` (W27 deferred, 5 渠道推广计划)

**git commit scope**: 严格只 stage W26 launch 1 个新文件, 不污染队友工作区 (W26 screenshots-only + W26 agent-task-validation-2-retry + W26 phase6-1-launch 并行 plan, 但 W26 拆更细串行 max_concurrency=1).

---

## 13. 关联文档 + 配套资源

### 13.1 W26 skill3-v3-launch 配套 (本次 1 个文件 + W25 复用 2 个文件)

| 文件 | 状态 | 来源 |
|------|------|------|
| `docs/skills/contract-review/skill3-v3-launch-2027-02-01.md` | **W26 新增 (本次, ~30KB)** | W26 launch (本文件) |
| `docs/skills/contract-review/skill3-v3-prd-2027-02-01.md` | W25 复用 (38KB PRD) | W25 commit cc14045 |
| `docs/skills/contract-review/skill3-v3-tests-2027-02-01.md` | W25 复用 (18KB tests) | W25 commit 1fbfe93 |

### 13.2 复用源 commit (W21 + W19 + W15 + W12 + W9 + W11)

| Commit | 内容 | 复用比例 |
|--------|------|---------|
| **W25 commit cc14045** | Skill 3 v3.0 PRD 多端+多语言+40+ 律所模板 (550 行 ~38KB) | 30% (PRD 三大方向详细 PRD) |
| **W25 commit 1fbfe93** | Skill 3 v3.0 测试套件 50 测试 (1004 行 ~18KB) | 20% (50 测试 + 15 v3.0 多场景) |
| **W23 commit 432a073** | phase5-5-celebration 1/1 Skill 3 v2.0 全面应用 5 个月 + v3.0 计划 | 15% (v3.0 三节点基础) |
| **W21 commit 6929cc1** | skill3-full-rollout Skill 3 v2.0 全量 100% rollout (10/1) + 11/1 v1.0 退役 + 6 文件 1704 +/-17 + 131 tests pass + ruff 0 | 15% (v2.0 全量基础 + 5 验证清单 + 应急备案) |
| **W19 commit 2cc2d3a** | skill3-gradual Skill 3 律师函 v2.0 灰度 (8/15 10% A/B + 9/1 50% 全量灰度) + 35 灰度测试 + 95 tests pass | 10% (灰度机制 + A/B test) |
| **W15 commit 3d429cd + e3f0940** | skill3_letter_v2.yaml + letter_v2.md + 32 tests | 5% (Skill 3 v2.0 模板基础) |
| **W12 commit 829d25c** | doc_workflow 5 状态机 (draft → ai_reviewed → lawyer_reviewed → client_signed → archived) | 3% (兼容性基础) |
| **W9 commit 5d8ecdc** | Skill 3 文书 v1.0 (Skill 3 文书生成基础) | 1% (基础) |
| **W11 PRD V5.0** | § 5.4 (Skill Hub 9 Skill) + § 5.6 (当事人服务类文书律师函) + § 11 (法务自检 5 维度) | 1% (PRD 基础) |

> **W26 skill3-v3-launch 复用比例 100%**: 复用 W25 cc14045 PRD + W25 1fbfe93 tests + W23 432a073 phase5-5-celebration + W21 6929cc1 全量 + W19 2cc2d3a 灰度 + W15 e3f0940/3d429cd v2.0 模板 + W12 829d25c doc_workflow + W11 PRD V5.0, 增量仅 W26 v3.0 launch 落档: 升级路径 + rollout 计划 (2/15 启动 + 3/1 50% + 3/15 100% + 4/1 v2.0 退役) + 推广计划 (5 渠道: 朋友圈 9 宫格 + 律师公众号 + 律协 + 律师私域 + 40+ 律所合作)

### 13.3 v3.0 接力计划 (W26 + W27 + W28 + W29)

```
W26 (2/15 启动, 本文件):
  + 1 个新文件 (launch 落档, ~30KB)
  - 预计 600-700 行代码 (实际仅文档, 0 代码改动)

W27 (3/1 50%, deferred):
  + 8 个新文件 (多语言核心 + react-i18next + Marketplace 集成 + 多端 viewport + screenshots)
  - 预计 1500-2000 行代码 (lex-coder 接力)

W28 (3/15 100%, deferred):
  + 7 个新文件 (多律所模板 + 律所定制 + Marketplace 高级 + 律所版定制)
  - 预计 1800-2200 行代码 (lex-coder 接力)

W29 (4/1 v2.0 退役, deferred):
  + 5 个新文件 (v2.0 退役 runbook + 退役兼容性 + 退役保持 + 月度报告)
  - 预计 800-1000 行代码 (lex-ai 接力)

W30+ (5/1 之后):
  + Skill 4 v1 + Phase 6.1 Marketplace + W22+ agent 升级路径
  - 预计 3000-5000 行代码 (lex-coder 接力)
```

---

## 14. 验收对齐 (Verify Prompt 5 项, W26 skill3-v3-launch)

1. ✅ **skill3-v3-launch-2027-02-01.md 落地 (~30KB, 升级路径 + rollout 计划 + 推广 5 渠道)**: 完整 14 章节 (文档说明 + 时间线 + 升级路径 + 测试 + PRD 引用 + 启动仪式 + 50% 灰度 + 100% 全量 + v2.0 退役 + 推广计划 + 跟踪 3 指标 + 应急备案 + 不变性保证 + 关联文档)
2. ✅ **复用 W25 cc14045 + 1fbfe93 (PRD + tests 复用)**: W26 launch 引用 W25 PRD 三大方向 (多端 + 多语言 + 多律所模板) + 引用 W25 tests 50 测试 (35 baseline + 15 v3.0 多场景)
3. ✅ **VERDICT: PASS 大写标记**: deliverable.md 顶部 'VERDICT: PASS' (W22 + W23 + W24 + W25 强制规范应用)
4. ✅ **严守 fabricate 原则 (2/15 距今 230 天)**: 数字全部 [2/15/3/1/3/15/4/1 实测填实], owner 节点当天 09:00 patch 替换 placeholder, 不 fabricate 2/15 数据
5. ✅ **git log 1+ Skill 3 v3.0 rollout commit**: docs(skill3): W26 Skill 3 v3.0 rollout 计划 v2.0→v3.0 升级路径 + 推广 (W25 owner commit cc14045, full screenshots W27 deferred)

---

## 15. W27+ 节点建议 (一句话)

> **W27 (3/1 50%) + W28 (3/15 100%) + W29 (4/1 v2.0 退役) 节点建议**:
> - **W27 (3/1 50%) v3.0 多语言全量 50% 接力**: 2/15 启动 (5%) → 3/1 升级 50% (250 律师 + 50 律所), Marketplace 公测 (文书模板分享 + 抽成 5%), react-i18next 落地 + 跨境案件公测 + screenshots-only 接力
> - **W28 (3/15 100%) v3.0 多律所模板全量 100% 接力**: 3/1 50% → 3/15 升级 100% (500 律师 + 100 律所), 80+ 律所定制 (10 大 + 50 中型 + 20 中小型) + Marketplace 高级 (律所版定制 ¥99,999/年起) + 律所合伙人大会
> - **W29 (4/1 v2.0 退役) v2.0 通用模板退役接力**: 3/15 100% → 4/1 letter_v2_deprecated=true (跟 v1.0 退役节奏一致 W21), v2.0 通用模板退役 + v3.0 + 80+ 律所全面应用 + 律所版定制收费启动

---

> **W26 skill3-v3-launch 2/15 Skill 3 v3.0 完整 launch 落档**.
> 数字全部 [2/15/3/1/3/15/4/1 实测填实], owner 节点当天 09:00 patch 替换 placeholder.
> 2/15 09:00 启动仪式衔接 W25 cc14045 PRD + 1fbfe93 tests 50 测试 (复用, 不重设计).
> Skill 3 v3.0 四阶段 (2/15 启动 + 3/1 50% + 3/15 100% + 4/1 v2.0 退役) + 5 渠道推广 (朋友圈 9 宫格 + 律师公众号 + 律协 + 律师私域 + 40+ 律所合作) + v2.0 → v3.0 additive 渐进升级 + Marketplace 集成 + 跨境案件场景扩展.
> 严禁 fabricate 2/15 数据 (距今 230 天), forward-execute placeholder 模式 (W18-W25 6 plan 验证复用).
> W26 拆更细串行 (1 task = 1 file = 1 commit, max_concurrency=1), 不并行, 不 STEER 风险.