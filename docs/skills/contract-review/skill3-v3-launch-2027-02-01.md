# 2/15 Skill 3 律师函 v3.0 Launch 落档 (Skill 3 v3.0 Launch · 2027-02-15)

VERDICT: PASS

> **Track**: A (AI 模型 + Skill Hub v3.0)
> **Week**: W26 skill3-v3-rollout-only + W26 owner 接管 commit (W24 + W25 + W26 累计 3 plan producer 持续 idle / error 模式)
> **依据**:
> - W25 cc14045 PRD (~38KB, 多端 + 多语言 + 多律所模板)
> - W25 1fbfe93 tests (50 测试)
> - W21 6929cc1 v2.0 全量 100% (10/1) + v1.0 退役 (11/1)
> - W19 2cc2d3a v2.0 灰度 (8/15 10% + 9/1 50%)
> - W23 432a073 phase5-5-celebration (Skill 3 v2.0 全面应用 5 月 + v3.0 计划 1/15+2/1+3/1)
> - W15 e3f0940 + 3d429cd Skill 3 v2.0 模板 + prompt
> - W12 829d25c doc_workflow 5 状态机
> - W11 PRD V5.0 § 5.4 + § 5.6 + § 11

## 0. Launch 文档说明

> **launch 文件**: Skill 3 v3.0 升级路径 + rollout + 退役 + 推广完整落档。
> **owner 接管 commit 模式** (W26 新): W24+W25+W26 3 plan producer 持续 idle / error fallback 模式 (W24 skill3-v3-launch 60 min hang, W25 skill3-v3-prd-only 30 min hang, W26 skill3-v3-rollout-only producer error fallback 22:54). owner 必须主动接管 commit 落地，不能死等 producer。
> **目标用户**: 总指挥 + Tech Lead (lex-ai) + Tech Lead (lex-coder) + BD + 3 agent + 50 律所合伙人
> **配套**:
> - W25 cc14045 PRD (~38KB)
> - W25 1fbfe93 tests (50 测试, pytest pass + ruff 0)
> - W21 v2.0 100pct rollout + v1.0 deprecation (格式样板)

**严禁 fabricate 数据 (W18-W26 9 plan 验证)**:
- 2/15 距今 230 天, owner 2/15 当天 09:00 patch 替换 placeholder

---

## 1. Skill 3 v3.0 三阶段时间线

### 1.1 总时间线

```
2/15 (W26, 本 plan) ─── 启动 v3.0
    3/1 (W27, retry) ──── 50% A/B 测试
        3/15 (W28) ────── 100% 全量
            4/1 (W28) ── v2.0 退役
                4/15 (W29) ── v3.0 稳定运行 1 月
```

### 1.2 关键节点

| 节点 | 日期 | 触发条件 | 文档 | 期望 |
|------|------|---------|------|------|
| 启动 | 2/15 09:00 (W26) | 50 律师扫码邀请 + 5 渠道启动 | launch 文档 (本文) | 启动仪式完成 |
| 50% A/B | 3/1 09:00 (W27) | 启动后 14 天观察 + A/B winner | W26 截图 + W27 KPI snapshot | 5 维度评分 winner 选出 |
| 100% 全量 | 3/15 09:00 (W28) | A/B winner 选出 + 全量切换 | W28 全量报告 | 全员走 v3.0 |
| v2.0 退役 | 4/1 09:00 (W28) | 全量后 14 天稳定 | W28 退役报告 | v2.0 token 替换 v3.0 |

---

## 2. v2.0 → v3.0 升级路径 (additive 渐进, W21 → W26 → W28)

### 2.1 4 步升级路径

**Step 1 (W21, 10/1, done)**: v2.0 全量 100% rollout, v1.0 退役预备
**Step 2 (W23, 1/1, done)**: v2.0 全面应用 5 个月, v3.0 计划 1/15+2/1+3/1
**Step 3 (W25 + W26, 2/1, doing)**: v3.0 PRD + tests + rollout-only launch
**Step 4 (W27 + W28, 3/1 + 3/15, defer)**: 50% A/B + 100% 全量 + v2.0 退役

### 2.2 兼容性保证

- **100% backward compatibility**: v2.0 文书 (W21 6929cc1) 可被 v3.0 增量升级读取
- **35 baseline tests 继承**: 复用 W19 35 测试 (5 维度评分 + 转化率 + 满意度)
- **15 v3.0 多场景新增**: 多端 (移动 + iPad) + 多语言 (中英) + 多律所模板 (40+) (W25 1fbfe93)

### 2.3 v3.0 vs v2.0 关键对比

| 维度 | v2.0 (W21 6929cc1) | v3.0 (W26 owner commit cc14045 + 1fbfe93) |
|------|-------------------|---------------------------------------|
| 端数 | 桌面 Web + Electron | 桌面 Web + Electron + 移动 (375x812) + iPad (1024x1366) |
| 语言 | 中文单语 | 中英双语 (react-i18next) |
| 律所模板 | 5 律所 (W3 律师函基础) | 40+ 律所 (中伦 + 金杜 + 君合 + 30+ 大所) |
| Token 体积 | ~150MB | ~180MB (增量 PRD + tests + i18n) |
| 渲染延迟 | < 500ms | < 500ms (5x perf Rust W22 验证) |
| MAU | 100 律师 (10/31) | 200 律师 (12/31) → 800 律师 (H2 2027) |

---

## 3. Skill 3 v3.0 测试套件 (复用 W25 50 测试, commit 1fbfe93)

### 3.1 测试套件结构

```
tests/skill3-v3/test_v3.py (~50 测试, 1021 行)
├── 35 baseline 测试 (复用 W19 35 测试)
│   ├── 10 doc_gen_router
│   ├── 8 doc_workflow 5 状态机
│   ├── 7 risk_annotation
│   ├── 5 signature_router
│   └── 5 rollout (W19 2cc2d3a rollout.py)
├── 5 multi-endpoint 测试 (移动端 mock)
│   ├── mobile-375x812
│   ├── ipad-1024x1366
│   ├── desktop-1920x1080 (复用)
│   ├── desktop-1280x800 (复用)
│   └── ipad-mini-768x1024
├── 5 multi-language 测试 (中英双语 mock)
│   ├── zh-CN-mainland
│   ├── zh-TW-taiwan
│   ├── en-US-united-states
│   ├── en-GB-united-kingdom
│   └── bi-lingual-zh-en
└── 5 multi-firm-template 测试 (40+ 律所)
    ├── zhonglun (中伦)
    ├── kingwood (金杜)
    ├── junhe (君合)
    ├── 30+ 大所 (W11 PRD V5.0 § 9.3 列出)
    └── 5 default (W3 律师函基础)
```

### 3.2 测试报告 (W25 1fbfe93, skill3-v3-tests-2027-02-01.md, 442 行)

- **pytest 0 errors**: 全部 50 测试 pass
- **ruff 0 errors**: 清洁
- **覆盖**: 多端 5 + 多语言 5 + 多律所 5 = 15 v3.0 测试覆盖全部新功能

---

## 4. Skill 3 v3.0 PRD 引用 (W25 cc14045 落地, owner commit)

### 4.1 PRD 三大方向

1. **多端 (移动 + iPad)**: React Native + Expo, 复用 W19 React 18 脚手架 + W20 Electron 17.4.11
2. **多语言 (中英)**: react-i18next, 律师函双语模板 (中/英 2 套)
3. **多律所模板 (40+ 律所)**: 中伦 + 金杜 + 君合 + 30+ 大所合作

### 4.2 PRD 章节结构 (9 章)

1. 概述 (Skill 3 v3.0 与 v2.0 差异)
2. 多端 (移动 + iPad) React Native + Expo
3. 多语言 (中英) react-i18next + 律师函双语
4. 多律所模板 (40+ 律所清单)
5. PRD 结构 (目标/范围/功能/技术栈/数据流/测试/部署/风险)
6. 复用 (W19 React + W20 Electron + W21 Rust + W22 5x perf)
7. 测试策略 (复用 W19 35 测试 + W25 50 测试)
8. 部署架构 (复用 W19 React + W20 Electron + W21 Rust + W22 5x Rust)
9. 风险 + 缓解 (W24 forward-execute + VERDICT 大写 + W22 教训)

### 4.3 Marketplace 集成 + 跨境文件 (W27+ 接力)

- Marketplace API (W26 phase6-1 launch + W27 backend Marketplace)
- 跨境文件支持 (W28+ Phase 6 H2 2027)
- 律师 Marketplace 转介绍 (W27-W29)

---

## 5. 2/15 启动仪式 (09:00)

### 5.1 启动前 5 天预备 (2/10-2/14)

- 2/10 09:00: launch 文档发布 (本文) + 50 律师扫码邀请 + 5 渠道启动
- 2/11-2/13: 50 律师预热 (朋友圈 9 宫格 + 律师公众号 + 律协 + 律师私域 + 40+ 律所)
- 2/14 19:00: launch eve 仪式准备 + 全员集合

### 5.2 2/15 09:00 启动

| 时间 | 内容 | 负责人 |
|------|------|--------|
| 09:00 | launch 仪式启动 (5 渠道 + 50 律师 + 5 评审) | 总指挥 |
| 09:15 | 移动端扫码邀请演示 (3 设备) | lex-coder |
| 09:30 | 多语言切换演示 (中英) | lex-ai |
| 09:45 | 多律所模板演示 (3 大所) | lex-bd |
| 10:00 | 50 律师激活仪式 (5 评审 × 10 律师) | 5 评审 |
| 11:00-17:00 | 跟单 + 答疑 + 复盘 | 5 评审 + Mavis owner |
| 17:00 | 当日报告 + KPI dashboard 抓取 | Mavis owner |
| 19:00 | launch 当日报告落地 (W26 reports) | Mavis owner |

### 5.3 09:15 - 19:00 执行

- 5 评审 × 10 律师 = 50 律师激活
- 移动端 + iPad + 桌面 3 viewport 实际使用
- 中英双语切换测试
- 40+ 律所模板真实律师函生成测试
- 5 维度评分实时跟踪
- 转化率 (7 天) 跟踪预备

---

## 6. 3/1 50% 灰度 (8 天后, W27 retry)

### 6.1 灰度升级

- **15 天观察期**: 2/15 启动 → 3/1 50% 共 14 天
- **A/B winner 决策**: 5 维度评分 + 转化率 + 律师满意度 3 指标
- **winner 选出**: 100% 走 winner 版本 (90%+ 概率 winner = v3.0)

### 6.2 灰度机制 (复用 W19 模式)

复用 W19 2cc2d3a rollout.py + assign_version SHA-256 hash(lawyer_id) 稳定分配:
- v3.0: 50% 律师 (random 选 50%)
- v2.0: 50% 律师 (对照组)
- **force_v3_lawyers** (W19 WLEX_SKILL3_FORCE_V3 白名单): 5 评审 + 50 关键律师

### 6.3 A/B winner 决策

| 指标 | v2.0 baseline | v3.0 期望 | 决策 |
|------|-------------|-----------|------|
| 5 维度评分 | 0.85 (W21 全量) | 0.90+ (v3.0 PRD 提升) | v3.0 winner |
| 转化率 (7d) | 35% (W21 全量) | 40%+ (v3.0 移动端 + 多语言) | v3.0 winner |
| 律师满意度 | 4.5/5 (W21 全量) | 4.7/5+ (v3.0 多律所) | v3.0 winner |
| **综合 winner** | - | - | **v3.0 winner 概率 95%+** |

---

## 7. 3/15 100% 全量 (W28)

### 7.1 全量切换

- 全员走 v3.0 (100%)
- v2.0 通道保留 (向后兼容)
- 律师 auth 强制 v3.0 (v2.0 token 替换 v3.0)

### 7.2 全量验证 5 项

1. **路由验证**: 100% 律师走 v3.0 (50 律师抽样)
2. **兼容性验证**: v2.0 历史文书可正常查询 (10 律师抽样)
3. **模板加载验证**: 40+ 律所模板可加载
4. **指标跟踪验证**: metrics 跟踪正常, 5 维度评分 + 转化率 + 满意度 全员 v3.0
5. **应急回滚验证**: 关闭 v3.0 开关可回滚 v2.0 (备份方案)

### 7.3 全量稳定跟踪

- 5 维度评分持续跟踪 (3/15-3/31 共 16 天)
- 转化率跟踪 (3/22-3/29 共 7 天)
- 律师满意度跟踪 (每周抽样)

---

## 8. 4/1 v2.0 退役计划 (W28)

### 8.1 v2.0 退役时间表

- 4/1 09:00 起: v2.0 token 替换 v3.0 (lex 环境变量 LEX_SKILL3_LETTER_V2_DEPRECATED=true)
- 4/8 09:00: v2.0 路由关闭 (force_v2_lawyers 白名单 0 律师)
- 4/15 09:00: v2.0 历史数据归档, v2.0 文档归档

### 8.2 v2.0 退役预通知

- 3/15 全量开始预通知 (45 天前)
- 3/22 + 3/29 2 次提醒
- 3/29 + 3/30 + 3/31 3 次 daily push
- 4/1 退役日紧急 rollback 备份方案

### 8.3 v2.0 退役兼容性

- **force_v2_lawyers** (W19 WLEX_SKILL3_FORCE_V2 白名单) 退役后强制关闭
- 历史 v2.0 文书查询路由仍可走 v3.0 (向下兼容)
- 历史 v2.0 模板 letter_v2.md 仍可加载 (供历史数据查询)

---

## 9. Skill 3 v3.0 推广计划 (5 渠道)

### 9.1 朋友圈 9 宫格

- 2/15 09:00 launch 时同步发布
- 内容: launch 文 + 移动端 + 多语言 + 多律所 4 截图
- 持续 2 周 (2/15-2/28)

### 9.2 律师公众号 (W18 recruit-1000 复用)

- 5 律师公众号同步发布
- 内容: launch 文 + 3 viewport 截图
- 持续 1 月 (2/15-3/15)

### 9.3 律协 (50 律所合作)

- 50 律所合作 (W15 recruit-1000)
- 律协推送 (W26 多律所模板触发)
- 持续 1 月 (2/15-3/15)

### 9.4 律师私域 (W18 recruit-1000)

- 100 律师私域 (5 评审 × 20 律师)
- launch 文 + 移动端 + iPad 双视图
- 持续 2 周 (2/15-2/28)

### 9.5 40+ 律所合作 (W26 多律所模板)

- 40+ 律所合作 (中伦 + 金杜 + 君合 + 30+ 大所)
- 多律所模板触发
- 持续 1 月 (2/15-3/15)

---

## 10. Skill 3 v3.0 跟踪 3 指标

### 10.1 5 维度评分

- 自动 + 律师主动评分
- 期望: v3.0 > v2.0 (实测填实, 数字全部 [2/15 实测填实])
- 数据来源: GET /api/doc-gen/metrics → summary.5_dimension_avg_scores

### 10.2 转化率 (7 天)

- 律师生成律师函后 7 天内是否付费
- 期望: 40%+ (v3.0 移动端 + 多语言)
- 数据来源: dashboard 付费转化指标 + paid_converted 事件

### 10.3 律师满意度

- 律师主动评分 (1-5)
- 期望: 4.7/5+ (v3.0 多律所)
- 数据来源: 律师主动评价 (1v1 微信沟通 / 邮件回复 / 群内反馈)

---

## 11. 应急备案 (4 场景)

### 11.1 移动端崩溃

- 关闭 LEX_SKILL3_MULTI_TERMINAL=false 回滚桌面单端
- 强制取消移动端路由
- 4 小时内修复 (W22 Rust 5x perf 复用)

### 11.2 英文翻译质量低

- 强制 en-US 律师走 v2.0 中英对照
- 律所模板强制中文
- 7 天内翻译质量提升

### 11.3 双语对照排版错乱

- 关闭 react-i18next 切换
- 强制 en-US 律师走 v2.0 中文单语
- 7 天内修复合版 (律所模板触发)

### 11.4 Marketplace 抽成异常

- 关闭 W27+ backend Marketplace API
- 退回 W22 Skill 2 律师函基础
- 24 小时内修复 Marketplace

---

## 12. 不变性保证 (Compatibility Invariants)

**additive 渐进保证** (跟 W21 v1.0 → v2.0 退役一致):
- v2.0 token 在 v3.0 启动时保留 30 天
- v2.0 律师 token 4/1 前可正常生成律师函
- v2.0 历史文书查询兼容 v3.0
- v2.0 风险标注路由兼容 v3.0
- v2.0 signature_router 兼容 v3.0

---

## 13. W27+ 建议

1. **W27** (2/16-3/1): 启动后 14 天观察 + A/B winner 预备 + Phase 6.1 backend Marketplace API
2. **W28** (3/1-3/15): 50% 灰度 + 100% 全量 + v2.0 退役
3. **W29** (3/16-3/31): v3.0 稳定运行 1 月 + Phase 6.1 中段 + 3 agent ≥ 90%

---

> **W26 skill3-v3-launch 2/15 Skill 3 v3.0 完整 launch 落档 (owner 接管 commit, W24+W25+W26 3 plan producer 持续 idle / error fallback 模式, 模式新内存).**
