<!-- Auto-split from PRD.md v0.7.0 on 2026-06-28 -->
> 本文档为 LexPrime 全面 PRD 的分章节版本, 供各 agent 独立阅读
> 主文档: `PRD.md` · 完整 15 章节 42KB · 各章节交叉引用见 `00-index.md`

# Track E: 9 个官方 Skill 首批 3 个 (类案/合同审查/知识问答)

> 来源: PRD § 9.2 Phase 4 计划 · 12 周 Phase 4 第 3-8 周
> 负责人: 全栈 + AI + 律师顾问 · 优先级: P1 · 工时: 6 周

---

## 1. 目标

上线 3 个核心 Skill, 验证 Skill Hub 架构。

## 2. 范围 (In Scope)

- Skill 1: 类案检索与裁判参考 (多维度检索 + 统计参考, 中立用语)
- Skill 2: 合同风险审查 (逐条审查 + 风险等级 + 修改建议)
- Skill 3: 法律知识问答 (RAG 问答)
- Skill Hub UI (技能商店 + 我的技能)
- Skill 包结构 (manifest + prompt + 知识库)

## 3. 不在范围 (Out of Scope)

- 6 个后续 Skill (民间借贷/劳动/离婚/遗嘱/刑事/研究备忘录) Phase 4.5
- 第三方 Skill (Phase 5 生态开放)
- 自定义 Skill (企业版 Phase 5)

## 4. 任务分解

- W3-4: Skill 1 (类案检索) + 数据准备
- W5-6: Skill 2 (合同审查)
- W7-8: Skill 3 (知识问答) + Skill Hub UI

## 5. 验收标准 (Acceptance Criteria)

- [ ] 3 个 Skill 可用, UI 入口完整
- [ ] 类案检索准确率 ≥ 80%
- [ ] 合同审查: 致命/重大/建议 三级风险标注
- [ ] 知识问答: RAG 准确率 ≥ 75%
- [ ] Skill 加载时间 < 3 秒
- [ ] 律师顾问评审通过 (3-5 人)

## 6. 依赖

**前置 Track**: A (Auth) + cncases 数据 (Phase 1 已建基础设施)
**技术依赖**: LanceDB (本地) / Milvus (云端) / Qwen2.5-7B (起步) → 72B (升级)
**资源依赖**: 律师顾问评审 3-5 人

## 7. 风险

- 类案数据不全 → 联邦模式补充 (跳转公开查询)
- AI 输出不稳 → 律师顾问评审 + 持续微调
- Skill 启动慢 → 懒加载 + 预热

## 8. 相关 PRD 章节

- § 5.4 横切面 4: 技能引擎
- § 5.7 横切面 7: 类案大数据
- § 5.5 横切面 5: AI 对话
- § 6 个人知识库

---
**Track 任务已就绪, 等候启动。**
