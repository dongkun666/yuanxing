/**
 * LexPrime Phase 5.1 全局类型定义
 *
 * 5 大价值主张 + 6 大模块 类型契约 (PRD V5.0 § 5-10, W11 commit 4910305)
 * Phase 5.1 仅重构为 React 组件, 不修改业务语义。
 */

export type Stance = '甲方' | '乙方' | '丙方' | '审查方';
export type RiskLevel = 'fatal' | 'major' | 'ok';
export type CaseStatus = '进行中' | '待开庭' | '已归档' | '仲裁中';
export type CaseRole = '代理原告' | '代理被告' | '第三方';

/** 律师登录用户 */
export interface User {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
}

/** 案件 (核心实体) */
export interface Case {
  id: string;
  name: string;
  role: CaseRole;
  filedAt: string;
  status: CaseStatus;
}

/** 合同审查风险条款 */
export interface RiskClause {
  id: string;
  level: RiskLevel;
  title: string;
  description: string;
  suggestedRevision?: string;
}

/** 立场影响预览 (W8 D3 § __updateStancePreview single source of truth) */
export interface StanceImpact {
  label: Stance;
  shortLabel: string;
  color: string;
  focus: string;
  tips: string[];
  impacts: Record<RiskLevel, { sym: string; cls: string }>;
}

/** 立场矩阵 (4 立场 × 3 风险等级) */
export const STANCE_MATRIX: Record<Stance, StanceImpact> = {
  '甲方': {
    label: '甲方',
    shortLabel: '原告',
    color: 'brand',
    focus: '对方义务 / 自身免责 / 救济成本',
    tips: ['单方解除权', '违约金上限', '管辖法院中立'],
    impacts: {
      fatal: { sym: '↓ 降权', cls: 'text-success' },
      major: { sym: '→ 持平', cls: 'text-warning' },
      ok:    { sym: '↑ 加权', cls: 'text-success' },
    },
  },
  '乙方': {
    label: '乙方',
    shortLabel: '被告',
    color: 'ai',
    focus: '权利失衡 / 显失公平 / 解除权不对等',
    tips: ['违约金过高', '单方解除权不对等', '管辖不利'],
    impacts: {
      fatal: { sym: '↑ 加权', cls: 'text-danger' },
      major: { sym: '→ 持平', cls: 'text-warning' },
      ok:    { sym: '↓ 降权', cls: 'text-success' },
    },
  },
  '丙方': {
    label: '丙方',
    shortLabel: '第三方',
    color: 'warning',
    focus: '连带义务 / 担保范围 / 第三方责任',
    tips: ['连带责任', '担保物范围', '第三方追偿权'],
    impacts: {
      fatal: { sym: '→ 持平', cls: 'text-warning' },
      major: { sym: '↑ 加权', cls: 'text-warning' },
      ok:    { sym: '→ 持平', cls: 'text-fg-tertiary' },
    },
  },
  '审查方': {
    label: '审查方',
    shortLabel: '中立',
    color: 'fg-secondary',
    focus: '全面客观 / 多方均衡 / 中立报告',
    tips: ['完整披露所有风险', '各方权益平衡', '客观描述无偏向'],
    impacts: {
      fatal: { sym: '→ 持平', cls: 'text-warning' },
      major: { sym: '→ 持平', cls: 'text-warning' },
      ok:    { sym: '→ 持平', cls: 'text-fg-tertiary' },
    },
  },
};

/** 6 大模块 (PRD V5.0 § 6 模块清单) */
export type ModuleId =
  | 'workstation'
  | 'case'
  | 'document'
  | 'template'
  | 'knowledge'
  | 'subscription';

export interface ModuleConfig {
  id: ModuleId;
  name: string;
  icon: string;
  path: string;
}

/** 5 大价值主张 (PRD V5.0 § 5 价值主张) */
export const VALUE_PROPOSITIONS = [
  { id: 1, title: '一体化工作站', icon: 'mdi:briefcase-outline' },
  { id: 2, title: 'Skill 合同审查', icon: 'mdi:file-document-check-outline' },
  { id: 3, title: 'Skill 文书生成', icon: 'mdi:file-document-edit-outline' },
  { id: 4, title: '类案检索 RAG', icon: 'mdi:book-search-outline' },
  { id: 5, title: 'AI 辅助不替代', icon: 'mdi:robot-outline' },
] as const;