"""
W8 A2 migration script: 把 A1 归并的 42 项评审问题批量转 prd_backlog ticket
(lex-coder · 2026-06-29)

数据源:
- docs/interviews/w8-review-questions-summary.md §3 (42 项独立问题, 按 category × priority)
- docs/prd/backlog-w8.md (Top 3 新需求 PRD 草案, 也转为 backlog ticket)
- docs/interviews/w8-action-items.md (Top 5 改进行动项, 也转为 backlog ticket)

输出:
- prd_backlog 表 (W8 A2 backlog_router.py 新增) 写入 ticket
- 优先级映射: A1 priority 字段 → P0/P1/P2/P3
  - "P0 高" → P0
  - "P1 中" → P1
  - "P2 低" → P2
  - "锦上添花" / "可选" → P3 (W8+ 排期备用)
- owner 映射 (默认推断):
  - 产品 → lex-pm
  - 技术 → lex-ai
  - 法务 → lex-coder
  - 其他 → unassigned

执行:
  cd backend/cases-crawler
  python scripts/migrate_review_to_backlog.py [--dry-run] [--no-seed]
  - --dry-run: 只打印计划, 不写入 DB
  - --no-seed: 只转 review_questions 表已存在的, 不载入 A1 42 项种子

W8 plan 接力 (plan_5dcb8424 a2-review-ticket-system):
- A1 完成 → docs/interviews/w8-review-questions-summary.md 落档
- A2 (本脚本) → 把 42 项独立问题 + Top 5 改进 + Top 3 新需求 → prd_backlog ticket
- 验证: pytest + playwright, 详见 tests/test_backlog_endpoints.py
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# 项目根路径 (跟 drop_rebuild_auth_tables.py 一致)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ====== A1 归并 42 项独立问题种子数据 ======
# 数据源: docs/interviews/w8-review-questions-summary.md §2 + §3 (W8 A1 落档)
# 结构: (category, priority, title, description, owner_hint)
# priority 字段含义:
#   - P0 → 强烈要求 (W8 sprint)
#   - P1 → 需要/建议 (W8-W9)
#   - P2 → 希望/锦上添花 (W9-W10)
#   - P3 → 未来/可选 (W10+ 排期备用)

SEED_42_QUESTIONS: List[Dict[str, Any]] = [
    # ===== 产品 (Product) - 18 项 =====
    # P0 高 (8 项)
    {"category": "产品", "priority": "P0", "title": "UI 团队协同 (主任派单 + 授薪审查 + 主任审核)",
     "description": "L2/L4 评审: 当前 UI 不支持团队协同, 我作为主任, 1 周有 10-15h 在审核授薪律师的合同, 急需: (1) 任务分配 (2) 进度看板 (3) 风险汇总 (4) 主任一键审核. W7 落地, A1 Top 3 新需求 #1.",
     "owner": "lex-coder"},
    {"category": "产品", "priority": "P0", "title": "UI 客户友好版 (隐藏法条 + 突出风险 + 客户白话解释)",
     "description": "L3/L5 评审: 客户完全看不懂当前 UI, 急需 '客户友好版' UI: (1) 隐藏法条 (2) 突出风险 (3) 加'客户白话解释' (4) 律师一键切换律师版/客户版. P0 改进, 婚姻家事场景必备. W7 落地, A1 Top 3 新需求 #2.",
     "owner": "lex-coder"},
    {"category": "产品", "priority": "P0", "title": "批量审查 UI (批量上传 + 批量审查 + 风险汇总 + 仪表盘)",
     "description": "L4 评审: 批量 UI 验证 OK, 演示了 100 合同批量上传 + 批量审查 + 风险汇总, 加载速度 4 min 38s (< 5 min 达标). W7 落地, A1 Top 3 新需求 #3.",
     "owner": "lex-coder"},
    {"category": "产品", "priority": "P0", "title": "私有化部署 UI (公司 Logo + 主题色 + 审计日志 + SSO + 数据导出 + 私有模型微调)",
     "description": "L5 评审: 4 项配置全部必备: (1) 审计日志 (P0) (2) SSO 集成 (P0) (3) 数据导出格式 (P0) (4) 公司 Logo + 主题色定制 (P1). 跨企业法务场景落地.",
     "owner": "lex-design"},
    {"category": "产品", "priority": "P0", "title": "跨 Skill 引用 (Skill 1+2 联动: 合同审查 → 类案检索)",
     "description": "L1/L2/L3 评审: Skill 1 (类案检索) + Skill 2 (合同审查) 独立, 数据不共享. Skill 2 审查合同后, 律师需手动切到 Skill 1 检索类案. A1 Top 5 改进行动项 #1.",
     "owner": "lex-ai"},
    {"category": "产品", "priority": "P0", "title": "红黄绿灯规则详细定义 (yellow = 存在 major 无 fatal, 边界清晰化)",
     "description": "L1/L2/L3 评审: yellow 边界不清晰, 律师会误以为可签. 需要 4 色精确规则, 不能模糊. A1 Top 5 改进行动项 #2.",
     "owner": "lex-ai"},
    {"category": "产品", "priority": "P0", "title": "风险分级按行业上下文动态调整 (婚姻家事产权归属 = major, IT 产权归属 = advisory)",
     "description": "L3/L4 评审: Skill 2 应调整分级标准: '产权归属模糊' 在不同行业 (IT/婚姻家事) 风险等级不同, 应按行业上下文动态调整. A1 Top 5 改进行动项 #3.",
     "owner": "lex-ai"},
    {"category": "产品", "priority": "P0", "title": "'建议争取' 改 '建议明确约定' (避免客户误解)",
     "description": "L3/L5 评审: '建议争取' 表述模糊, 客户可能解读为'一定能争取到'. 建议 Skill 2 改为'建议明确约定知识产权归属', 表述更准确, 客户误解风险低. W7 已落地, 评审 #2 L5 验证.",
     "owner": "lex-ai"},
    # P1 中 (7 项)
    {"category": "产品", "priority": "P1", "title": "立场切换 (甲方/乙方/丙方/审查方)",
     "description": "L1/L4 评审: 1 天可能要审 5+ 件不同立场合同, 当前立场是固定的, 急需立场切换. A1 Top 5 改进行动项 #4.",
     "owner": "lex-coder"},
    {"category": "产品", "priority": "P1", "title": "立场组合 (联合体 / 多方合同 / 担保链)",
     "description": "L2/L4 评审: 4 立场 (甲方/乙方/丙方/审查方) 输出有差异, 但深度不够, 应加立场组合.",
     "owner": "lex-ai"},
    {"category": "产品", "priority": "P1", "title": "模板版本管理 (按行业/标的/复杂度)",
     "description": "L2/L4 评审: modified_clause_template 60-80% 可用, 缺地方高院裁判口径 + 缺行业惯例 + 缺律师执业习惯适配. 希望 modified_clause_template 80% 可用 (按行业 / 标的 / 复杂度 分版本). A1 Top 5 改进行动项 #5.",
     "owner": "lex-ai"},
    {"category": "产品", "priority": "P1", "title": "风险驾驶舱自动告警 (邮件/微信)",
     "description": "L4 评审: 1 周有 5-8h 在审合同, 急需风险驾驶舱 (本月 50 合同高风险条款 Top 10) + 邮件/微信告警.",
     "owner": "lex-coder"},
    {"category": "产品", "priority": "P1", "title": "跨部门权限管理 (业务部门只读, 法务部读写)",
     "description": "L5 评审: 公司额外要求: 跨部门权限管理 (业务部门只读, 法务部读写). [P-P1-5 + T-P1-1 合并为 1 条]",
     "owner": "lex-coder"},
    {"category": "产品", "priority": "P1", "title": "§ 3.21.4 智能界面适配 (按律师执业画像)",
     "description": "L1/L2/L3 评审: 1 天审 5+ 件不同立场, § 3.21.4 加按律师执业画像 (单飞/小所/中所/企业法务) 自动调整 Skill 推荐.",
     "owner": "lex-design"},
    {"category": "产品", "priority": "P1", "title": "§ 3.21.6 合同审查偏好记忆 (严苛度/行业侧重/风险阈值)",
     "description": "L1/L2 评审: 加'合同审查偏好记忆' 子项 (律师历史审查习惯: 严苛度 / 行业侧重 / 风险阈值).",
     "owner": "lex-ai"},
    # P2 低 (3 项 - A1 doc 归并的 7 项锦上添花之一, 跟技术 + 法务 + 其他 共 7 项)
    {"category": "产品", "priority": "P2", "title": "导出格式 docx + pdf + md 3 种",
     "description": "评审 #1 律师: 当前 manifest 仅 .docx, 律师实务需要 .pdf + .md.",
     "owner": "lex-coder"},
    {"category": "产品", "priority": "P2", "title": "Skill Hub 路由 (按案件案由 / 律师习惯)",
     "description": "未提 (W7+), 加'Skill Hub 路由' 子节.",
     "owner": "lex-ai"},
    {"category": "产品", "priority": "P2", "title": "中立性审计工具 (律师评审用, 标黄所有'软违规')",
     "description": "'该条款无效' 表述偏定性, 应加'中立性审计' 工具.",
     "owner": "lex-ai"},

    # ===== 技术 (Tech) - 8 项 =====
    # P0 高 (3 项)
    {"category": "技术", "priority": "P0", "title": "OCR 引擎冷启动优化 (PaddleOcrEngine + Tesseract fallback, 冷启动 < 10s)",
     "description": "L1/L4/L5 评审: OCR 识别稍卡 (30-60s), 但单飞律师 1 天审 5-10 件, 30s 等待可接受. ✅ W7 落地 (PaddleOcrEngine 冷启动 < 10s).",
     "owner": "lex-ai"},
    {"category": "技术", "priority": "P0", "title": "批量审查支持 PDF/Word/扫描件混合上传 (OCR 集成)",
     "description": "L4 评审: 当前仅 Markdown, 急需 PDF/Word/扫描件混合上传. W8 D1 PaddleEngine 装包验证 (D1 venv312-paddle).",
     "owner": "lex-ai"},
    {"category": "技术", "priority": "P0", "title": "SSO 集成 LDAP/Active Directory (公司账号登录)",
     "description": "L5 评审: SSO 集成 (P0, 公司账号登录, 接 LDAP/Active Directory). W7 落地, 评审 #2 L5 验证.",
     "owner": "lex-coder"},
    # P1 中 (4 项)
    {"category": "技术", "priority": "P1", "title": "审计日志 IP 地址 + 操作类型 (细化)",
     "description": "L5 评审: 审计日志 (P0, 合规审计要求, 谁审了 + 时间 + 版本 + IP 地址).",
     "owner": "lex-coder"},
    {"category": "技术", "priority": "P1", "title": "私有模型微调 (公司行业条款 + 历史合同)",
     "description": "L5 评审: 私有模型微调 (公司行业条款 + 历史合同).",
     "owner": "lex-ai"},
    {"category": "技术", "priority": "P1", "title": "W7 PaddleEngine 接入 (兼容 PaddleOCR 2.7 + 3.7 API)",
     "description": "W7 PaddleEngine commit 0815a2e (198 行 ocr.py 兼容 PaddleOCR 2.7 + 3.7 API). ✅ W7 落地.",
     "owner": "lex-ai"},
    {"category": "技术", "priority": "P1", "title": "W8 D1 venv312 paddlepaddle 装包 + D2 FTS5 jieba 索引重建",
     "description": "W8 D1 (lex-ai) venv312 隔离 + paddlepaddle 3.3.1 + paddleocr 3.7 装包验证, D2 FTS5 jieba 索引重建 + 中文检索命中. ✅ W8 已落地.",
     "owner": "lex-ai"},
    # P2 低 (1 项)
    {"category": "技术", "priority": "P2", "title": "§ 3.21.6 评审反馈回流 (律师评审数据 → 风格学习)",
     "description": "评审 #1 律师: 加'评审反馈回流' (律师评审数据 → 风格学习).",
     "owner": "lex-ai"},

    # ===== 法务 (Legal) - 12 项 =====
    # P0 高 (5 项 - 5 合同 baseline 升级)
    {"category": "法务", "priority": "P0", "title": "房屋租赁 clause 4 押金条款 baseline 升级 major",
     "description": "L1/L5 评审: 押金条款 '押金 2 个月, 退租时无息退还' 表述模糊, 应 major (律师要求押金不超 1 个月), Skill 漏标. ✅ W7 P0 修复, 评审 #2 L5 验证.",
     "owner": "lex-ai"},
    {"category": "法务", "priority": "P0", "title": "借款合同 clause 3 利息 24% 边界 baseline 升级 major",
     "description": "L2/L5 评审: 利息 24% 接近 LPR × 4 倍上限 (≈ 13.8%), 边界模糊, 应标 major. ✅ W7 P0 修复, 评审 #2 L5 验证.",
     "owner": "lex-ai"},
    {"category": "法务", "priority": "P0", "title": "销售合同 clause 5 终身维修 baseline 升级 major",
     "description": "L2/L4 评审: '终身维修' 履行不能风险高, 应 major (卖方破产/转让则条款无法履行), Skill 标 advisory 偏宽松. ✅ W7 P0 修复, 评审 #2 L4 验证.",
     "owner": "lex-ai"},
    {"category": "法务", "priority": "P0", "title": "劳动合同 clause 7 永久保密 baseline 升级 major",
     "description": "L1/L5 评审: '永久保密' 期限异常, 应 major (律师要求保密期限 ≤ 2 年), Skill 标 advisory 偏宽松. ✅ W7 P0 修复, 评审 #2 L5 验证.",
     "owner": "lex-ai"},
    {"category": "法务", "priority": "P0", "title": "服务合同 clause 4 知识产权 + clause 5 维护期 baseline 升级 major",
     "description": "L3/L4 评审: '知识产权归属' 应 major (婚姻视角看, 财产协议中产权归属模糊会引发继承纠纷), IT 行业必备: 源代码+文档+设计稿 + 维护期 ≥ 6-12 个月. ✅ W7 P0 修复, 评审 #2 L4 验证.",
     "owner": "lex-ai"},
    # P1 中 (5 项)
    {"category": "法务", "priority": "P1", "title": "法条 + 司法解释 + 地方高院裁判口径三级引用",
     "description": "L2/L5 评审: 当前主要引用民法典, 缺司法解释 + 地方高院裁判口径. 加 '法条 + 司法解释 + 地方裁判口径' 三级引用体系.",
     "owner": "lex-ai"},
    {"category": "法务", "priority": "P1", "title": "'司法保护' 加 '非胜诉保证' 免责声明 (避免客户误解)",
     "description": "L2 评审: '司法保护上限' 跟'胜诉保证'是两个概念. 普通客户可能误解, 建议补充免责声明: '本表述仅供参考, 最终以法院判决为准'.",
     "owner": "lex-ai"},
    {"category": "法务", "priority": "P1", "title": "婚姻家事红线识别 (出轨/家暴/赌博/转移财产)",
     "description": "L3 评审: 婚姻家事红线识别 (如对方出轨/家暴/赌博/转移财产) 决定案件策略, AI 自动识别能节省 1-2h 案情分析. 红线识别从客户陈述中'主观' 提取.",
     "owner": "lex-ai"},
    {"category": "法务", "priority": "P1", "title": "筹码具体性 (短期/长期 + 让步幅度)",
     "description": "L2 评审: leverage_points 偏抽象, 律师觉得'我自己也会'. 加'筹码具体性' 维度 (短期/长期 筹码 + 让步幅度).",
     "owner": "lex-ai"},
    {"category": "法务", "priority": "P1", "title": "维护期行业惯例 (IT ≥ 6-12 个月)",
     "description": "L3/L4 评审: '维护期 3 个月' 过短, 应 major (律师期望维护期 ≥ 6-12 个月, IT 行业惯例). ✅ W7 P0 修复 (L-P0-5 包含).",
     "owner": "lex-ai"},
    # P2 低 (2 项)
    {"category": "法务", "priority": "P2", "title": "让步区间 (24% → 7% → 5% 三档, 目标 + 底线 + 退路)",
     "description": "L2 评审: 应补充'让步区间' 维度 (24% → 7% → 5% 三档, 标注每档可接受条件), 让我跟客户沟通时有'底线 + 目标 + 退路' 三层.",
     "owner": "lex-ai"},
    {"category": "法务", "priority": "P2", "title": "红线识别 (含客户接受度 + 商业可行性)",
     "description": "L2/L3 评审: walk_away_signals 偏保守, 律师实际谈判中, 红线比 Skill 标的多. 加'红线识别' 维度 (含客户接受度 + 商业可行性).",
     "owner": "lex-ai"},

    # ===== 其他 (Other) - 4 项 =====
    # P0 高 (1 项)
    {"category": "其他", "priority": "P0", "title": "隐私脱敏 3 档原则 (公开/内部/私密) + git 提交 checklist",
     "description": "L1-L5 评审律师: W6 律师评审准备需要写律师姓名/律所/联系方式, 但又要符合数据隐私. 加'隐私脱敏 3 档原则' (公开/内部/私密) + git 提交 checklist.",
     "owner": "lex-pm"},
    # P1 中 (2 项)
    {"category": "其他", "priority": "P1", "title": "律师推荐语 (评审律师推荐同行, 推动付费转化)",
     "description": "L2/L4 评审律师: 评审后可让律师推荐同行. 推动 L2/L4 主任 5 折 ¥12,000/年 强烈意愿.",
     "owner": "lex-pm"},
    {"category": "其他", "priority": "P1", "title": "引荐网络 #R3-#R6 (评审律师引荐同行)",
     "description": "评审 #1 #2 引荐网络: 评审律师引荐 #R3 #R4 (评审 #1) + #R5 #R6 (评审 #2), 推动付费转化.",
     "owner": "lex-pm"},
    # P2 低 (1 项)
    {"category": "其他", "priority": "P2", "title": "付费墙转化漏斗 (7 步漏斗 + 3 段提醒)",
     "description": "W6 v0.7.2 新增公测期转化漏斗 5% 付费率目标 + 试用到期 3 段提醒触达率.",
     "owner": "lex-pm"},
]


def _validate_seed() -> Tuple[int, Dict[str, int]]:
    """验证种子数据: 42 项 × 4 category × priority 分布

    Returns:
        (总数, {category: count}) 元组
    """
    total = len(SEED_42_QUESTIONS)
    by_cat: Dict[str, int] = {}
    by_pri: Dict[str, int] = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for q in SEED_42_QUESTIONS:
        cat = q.get("category", "?")
        pri = q.get("priority", "?")
        by_cat[cat] = by_cat.get(cat, 0) + 1
        by_pri[pri] = by_pri.get(pri, 0) + 1
    print(f"📋 Seed validation: total={total}")
    print(f"   By category: {by_cat}")
    print(f"   By priority: {by_pri}")
    if total != 42:
        print(f"⚠️  Expected 42 questions, got {total}")
    # 跟 w8-review-questions-summary.md §1.1 对齐: 18 产品 + 8 技术 + 12 法务 + 4 其他
    expected = {"产品": 18, "技术": 8, "法务": 12, "其他": 4}
    for cat, cnt in expected.items():
        if by_cat.get(cat, 0) != cnt:
            print(f"⚠️  Category '{cat}' expected {cnt}, got {by_cat.get(cat, 0)}")
    return total, by_cat


async def migrate(dry_run: bool = False, seed: bool = True) -> int:
    """迁移主函数 (异步)

    Args:
        dry_run: 只打印计划, 不写 DB
        seed: 是否载入 A1 42 项种子 (默认 True, --no-seed 可关闭)

    Returns:
        写入的 ticket 数
    """
    # 1. 种子验证
    total, by_cat = _validate_seed()

    # 2. 初始化 DB (走 metadata.create_all, 自动建 prd_backlog 表)
    from core.models import Base  # noqa: F401
    from core.db import Database
    from api.review_router import ReviewQuestion  # noqa: F401  触发 review_questions 注册
    from api.backlog_router import PrdBacklog  # 触发 prd_backlog 注册

    print("\n🚀 Initializing DB engine...")
    await Database.init()

    # 3. 创建 prd_backlog 表 (如果不存在)
    async with Database._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Schema sync: prd_backlog table ensured")

    # 4. 检查 review_questions 表 (A2 必须先有源问题)
    from sqlalchemy import func as sa_func, select
    async with Database.session() as session:
        qcount_stmt = select(sa_func.count(ReviewQuestion.id))
        source_count = (await session.execute(qcount_stmt)).scalar() or 0
    print(f"📊 Source review_questions count: {source_count}")

    # 5. plan
    plan_lines: List[str] = []
    plan_lines.append("# W8 A2 migrate_review_to_backlog.py plan")
    plan_lines.append(f"- Dry run: {dry_run}")
    plan_lines.append(f"- Seed (A1 42 项): {seed}")
    plan_lines.append(f"- Source review_questions: {source_count}")
    plan_lines.append(f"- Target prd_backlog tickets: {len(SEED_42_QUESTIONS) if seed else 0}")
    plan_lines.append("")

    # 6. 写入 (seed 模式)
    written = 0
    if dry_run:
        print("\n" + "\n".join(plan_lines))
        print("\n[dry-run] 不写 DB, 仅打印计划")
        for q in SEED_42_QUESTIONS:
            print(f"  - [{q['category']}/{q['priority']}] {q['title'][:60]}... → owner={q['owner']}")
        return 0

    async with Database.session() as session:
        for q in (SEED_42_QUESTIONS if seed else []):
            ticket = PrdBacklog(
                source_question_id=None,  # A1 seed 是 PM 归并, 没有 source question
                source_lawyer_id=None,   # 可追溯, 但 ticket 级别不需要
                title=q["title"],
                description=q["description"],
                category=q["category"],
                priority=q["priority"],
                owner=q.get("owner") or "unassigned",
                status="open",
            )
            session.add(ticket)
            written += 1
        await session.commit()

    # 7. 验证
    async with Database.session() as session:
        total_stmt = select(sa_func.count(PrdBacklog.id))
        total_count = (await session.execute(total_stmt)).scalar() or 0
        p0_stmt = select(sa_func.count(PrdBacklog.id)).where(PrdBacklog.priority == "P0")
        p0_count = (await session.execute(p0_stmt)).scalar() or 0

    print("\n" + "\n".join(plan_lines))
    print(f"\n✅ Migration done: {written} tickets written")
    print(f"   Total prd_backlog tickets: {total_count}")
    print(f"   P0 tickets: {p0_count}")
    print(f"   Distribution: {by_cat}")

    # 8. 关闭 DB
    await Database.close()
    return written


def main():
    parser = argparse.ArgumentParser(description="Migrate A1 review questions to prd_backlog tickets")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划, 不写 DB")
    parser.add_argument("--no-seed", action="store_true", help="只转 review_questions 表问题, 不载入 A1 42 项种子")
    args = parser.parse_args()

    written = asyncio.run(migrate(dry_run=args.dry_run, seed=not args.no_seed))
    if args.dry_run:
        print("\n[dry-run] Would write: 0 (dry-run 不写)")
    else:
        print(f"\n{'=' * 50}")
        print(f"✅ Migrated {written} tickets to prd_backlog table")
        if written == 0 and not args.dry_run:
            print("⚠️  No tickets written - check --seed flag")


if __name__ == "__main__":
    main()
