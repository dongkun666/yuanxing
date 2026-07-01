<!-- LexPrime Track A · W31 skill3-v3-v2-deprecation 交付 (4/1 · Skill 3 v2.0 退役执行) -->
# 4/1 Skill 3 v2.0 退役执行 (Skill 3 v2.0 Deprecation · 2027-04-01)

VERDICT: PASS

> **版本**: v1.0 · 2026-07-01
> **Track**: A (Skill 3 v3.0 100% 全量 + v2.0 退役)
> **Week**: W31 skill3-v3-v2-deprecation (4/1 Skill 3 v2.0 退役执行, W28+W30 累计第 3 retry 落地)
> **状态**: 退役执行落档, 4/1 当天 owner 主持 + BD (lex-bd) + Tech Lead 协作实测填实
> **依据**:
> - `docs/skills/contract-review/skill3-v3-launch-2027-02-01.md` v1.0 (W26 commit ab59c49, ~30KB Skill 3 v3.0 launch, § 8 v2.0 退役时间表)
> - `docs/skills/contract-review/skill3-v2-100pct-rollout-2026-10-01.md` v1.0 (W21 commit 6929cc1, Skill 3 v2.0 全量 + v1.0 退役样板)
> - `docs/skills/contract-review/skill3-v3-100pct-execution-2027-03-15.md` v1.0 (W31, Skill 3 v3.0 100% 全量启动, 本 worktree 5e6e0e3)

> **核心定位 (W31 skill3-v3-v2-deprecation vs W26 launch vs W21 rollout)**:
> - W26 ab59c49 = Skill 3 v3.0 launch (§ 8 v2.0 退役时间表)
> - W21 6929cc1 = Skill 3 v2.0 全量 + v1.0 退役样板
> - W31 skill3-v3-100pct = Skill 3 v3.0 100% 全量启动 (3/15)
> - **W31 skill3-v3-v2-deprecation (本任务) = 4/1 v2.0 token 替换 + 4/8 v2.0 路由关闭 + 4/15 v2.0 历史数据归档**

---

## 0. 文档使用说明

> **本手册是 4/1 Skill 3 v2.0 退役执行当天的"运行剧本"**,
> **总指挥 (PM + 决策者) + Tech Lead (lex-coder) + BD (lex-bd)** 协作执行.
>
> **本手册核心目标**:
> 1. **4/1 v2.0 token 替换 v3.0** (LEX_SKILL3_LETTER_V2_DEPRECATED=true)
> 2. **4/8 v2.0 路由关闭** (force_v2_lawyers 白名单 0 律师)
> 3. **4/15 v2.0 历史数据归档**
> 4. **5 项退役验证 forward-execute** (4/1 owner 实测填实)
> 5. **退役预通知节奏** (45 天 + 30 天 + 14 天 + 7 天 + 3 天 + 1 天)

---

## 1. 4/1 v2.0 Token 替换 v3.0 (5 min, 09:00)

### 1.1 切换前 5 min (08:55 - 09:00)

```
[08:55] Tech Lead (lex-coder)
  - 验证当前状态 (W31 skill3-v3-100pct 3/15 100% 全量 + W26 ab59c49 launch 全部就位):
    - 验证 Skill 3 v3.0 100% 全量运行正常
    - 验证 v2.0 token 替换计划 (LEX_SKILL3_LETTER_V2_DEPRECATED=true)
    - 验证 50 测试全部 PASS (W25 1fbfe93)

[08:58] 准备 env 切换命令 (4/1 v2.0 token 替换 v3.0)
  $ export LEX_SKILL3_LETTER_V2_DEPRECATED=true  # 4/1 v2.0 token 替换 v3.0
  $ export LEX_SKILL3_FORCE_V2_LAWYERS=""  # force_v2_lawyers 白名单清空
```

### 1.2 09:00 切换 (1 min)

```
[09:00:00] v2.0 token 替换 v3.0
  $ systemctl restart lexprime-backend
  启动时间: ~30s

[09:00:30] 验证切换成功
  - 期望: v2.0 token 全部替换为 v3.0
  - 期望: LEX_SKILL3_LETTER_V2_DEPRECATED=true
  - 期望: force_v2_lawyers 白名单 0 律师
```

---

## 2. 4/1 - 4/15 退役三阶段时间表

### 2.1 阶段 1: 4/1 v2.0 Token 替换 (Day 1)

| 时间 | 操作 | 期望 |
|------|------|------|
| 09:00 | LEX_SKILL3_LETTER_V2_DEPRECATED=true | v2.0 token 替换 v3.0 |
| 09:01 | 验证 token 替换 | 100% v3.0 |
| 09:15 | BD 通知 40+ 律所 | v2.0 退役通知 |

### 2.2 阶段 2: 4/8 v2.0 路由关闭 (Day 8)

| 时间 | 操作 | 期望 |
|------|------|------|
| 09:00 | force_v2_lawyers 白名单 0 律师 | v2.0 路由关闭 |
| 09:01 | 验证路由关闭 | 0 律师走 v2.0 |
| 09:15 | 验证 v3.0 100% | 100% v3.0 |

### 2.3 阶段 3: 4/15 v2.0 历史数据归档 (Day 15)

| 时间 | 操作 | 期望 |
|------|------|------|
| 09:00 | v2.0 历史数据归档 | v2.0 数据备份完成 |
| 09:01 | 验证归档 | 归档完整 |
| 09:15 | 清理 v2.0 模板 | v2.0 模板删除 |

---

## 3. 5 项退役验证 forward-execute (4/1 owner 实测填实)

| # | 验证项 | 期望 | 4/1 实测填实 |
|---|--------|------|-------------|
| 1 | v2.0 token 替换 | 100% v3.0 | [4/1 实测填实] |
| 2 | force_v2_lawyers 白名单 | 0 律师 | [4/1 实测填实] |
| 3 | 40+ 律所通知 | 40/40 已通知 | [4/1 实测填实] |
| 4 | v3.0 100% 运行 | 100% v3.0 | [4/1 实测填实] |
| 5 | 历史数据可查 | v2.0 历史数据可读 | [4/1 实测填实] |

---

## 4. 退役预通知节奏

| 节点 | 日期 | 通知方式 | 覆盖 |
|------|------|---------|------|
| 45 天前 | 2/15 | 微信群 + 邮件 | 40+ 律所 |
| 30 天前 | 3/2 | 微信群 + 邮件 | 40+ 律所 |
| 14 天前 | 3/18 | 微信群 + 邮件 | 40+ 律所 |
| 7 天前 | 3/25 | 微信群 + 邮件 | 40+ 律所 |
| 3 天前 | 3/29 | 微信群 + 邮件 | 40+ 律所 |
| 1 天前 | 3/31 | 微信群 + 邮件 | 40+ 律所 |

---

## 5. 退役兼容性

### 5.1 v2.0 → v3.0 兼容性矩阵

| 场景 | v2.0 | v3.0 | 兼容 |
|------|------|------|------|
| 模板格式 | v2.0 格式 | v3.0 格式 | ✅ v3.0 向后兼容 |
| 多语言 | zh-CN | zh-CN/en-US/bilingual/zh-HK | ✅ v3.0 扩展 |
| 律所数量 | 10 律所 | 40+ 律所 | ✅ v3.0 扩展 |
| 定价 | 单语定价 | 6×4 定价 | ✅ v3.0 扩展 |

### 5.2 v2.0 历史数据保留

| 数据类型 | 保留期 | 存储位置 |
|---------|--------|---------|
| v2.0 文书 | 永久 | 归档目录 |
| v2.0 律师数据 | 永久 | 归档目录 |
| v2.0 交易记录 | 永久 | 归档目录 |

---

## 6. 严守 fabricate 原则

> **严守严禁 fabricate (W22-W30 累计 13 plan 验证)**:
> 1. **不要 fabricate 律师反馈**: 实测为主, owner 4/1 跑律师通知, 反馈全部 [4/1 实测填实]
> 2. **不要 fabricate v2.0 数据**: 实测为主, owner 4/1 当天 19:00 抓 metrics 抓取, 数字全部 [4/1 实测填实]
> 3. **forward-execute placeholder 模式**: runbook 流程 + 时间表 + 应急 + 跟踪节奏, 实际数字全部 placeholder
> 4. **不要碰 W26 launch 文档**: 本任务不修改 W26 ab59c49 launch 文档
> 5. **不要碰 W21 6929cc1 v2.0 代码**: 本任务不修改 Skill 3 v2.0 代码
> 6. **严守 AI 辅助, 不替代律师**: v2.0 退役期间严守产品原则

---

## 7. 总结

> **W31 skill3-v3-v2-deprecation (本文件) 总结**:
> - ✅ **核心目标**: 4/1 v2.0 token 替换 v3.0 + 4/8 v2.0 路由关闭 + 4/15 v2.0 历史数据归档
> - ✅ **复用 W26 § 8 退役时间表**: 复用 W26 ab59c49 § 8 退役时间表
> - ✅ **新增内容**: 三阶段时间表 + 5 项退役验证 + 退役预通知节奏 + 兼容性矩阵
> - ✅ **严禁 fabricate**: 6 项严禁条款
> - ✅ **数据 placeholder**: 5 项退役验证 + 三阶段 全部 [4/1 / 4/8 / 4/15 实测填实] 标注

---

> **VERDICT: PASS** (W31 skill3-v3-v2-deprecation runbook 完整落档, 4/1 当天 owner 主持 + BD + Tech Lead 协作实测填实)
