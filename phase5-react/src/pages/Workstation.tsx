/**
 * Workstation 页面 - W5 workstation.html 重构为 React 组件 + TypeScript
 *
 * 保留 5 大价值主张之一: 一体化工作站 (PRD V5.0 § 5)
 * 6 大模块入口 (案件/合同/文书/类案/日程/知识库) 在 Phase 5.1 W20+ 增量
 *
 * 重构点:
 *  - 静态 HTML + inline onclick → React state + onClick
 *  - 4 个统计卡片 + 今日日程 + 需要关注 + 案件动态 + 本周效率 + 最近案件 → 子组件 + 数据 props
 *  - switchView('case-detail') → onSelectCase → W20+ 接 case-detail
 */
import { useState } from 'react';
import type { Case, CaseRole, CaseStatus } from '../types';

interface StatCardData {
  label: string;
  value: number | string;
  trend: { type: 'up' | 'warning' | 'success'; text: string; color: string };
  icon: string;
  iconBg: string;
  iconColor: string;
}

const STATS: StatCardData[] = [
  { label: '当前案件数', value: 12, trend: { type: 'up', text: '20% 较上月', color: 'text-green-500' }, icon: 'mdi:briefcase-outline', iconBg: 'bg-brand-tint3', iconColor: 'text-brand' },
  { label: '即将开庭', value: 3, trend: { type: 'warning', text: '最近：6月25日', color: 'text-red-500' }, icon: 'mdi:gavel', iconBg: 'bg-red-50', iconColor: 'text-red-600' },
  { label: '待处理案件', value: 5, trend: { type: 'warning', text: '3 份即将超期', color: 'text-orange-500' }, icon: 'mdi:file-clock-outline', iconBg: 'bg-warning-tint', iconColor: 'text-warning' },
  { label: '已完结案件', value: 36, trend: { type: 'success', text: '全部归档完成', color: 'text-green-500' }, icon: 'mdi:check-circle', iconBg: 'bg-green-50', iconColor: 'text-success' },
];

interface TodayScheduleItem {
  id: number;
  title: string;
  time: string;
  done: boolean;
}

const TODAY_SCHEDULES: TodayScheduleItem[] = [
  { id: 1, title: '李明案证据整理', time: '09:00', done: false },
  { id: 2, title: '王华案起诉状修订', time: '11:30', done: false },
  { id: 3, title: '张三合同纠纷开庭', time: '14:00', done: false },
  { id: 4, title: '客户咨询会', time: '16:00', done: true },
  { id: 5, title: '案卷归档', time: '17:30', done: false },
];

interface AlertItem {
  id: number;
  emoji: string;
  title: string;
  meta: string;
  borderClass: string;
  bgClass: string;
  textClass: string;
  metaClass: string;
}

const ALERTS: AlertItem[] = [
  {
    id: 1,
    emoji: '⚠️',
    title: '证据提交截止 — 李明案',
    meta: '剩余 2 天 · 请尽快提交补充证据材料',
    borderClass: 'border-red-100',
    bgClass: 'bg-red-50/80 hover:bg-red-50',
    textClass: 'text-red-800',
    metaClass: 'text-red-500',
  },
  {
    id: 2,
    emoji: '⏰',
    title: '诉讼费缴纳 — 王华案',
    meta: '今日到期 · 请及时完成缴费',
    borderClass: 'border-orange-100',
    bgClass: 'bg-warning-tint/80 hover:bg-warning-tint',
    textClass: 'text-orange-800',
    metaClass: 'text-orange-500',
  },
];

interface CaseDynamicsItem {
  id: number;
  icon: string;
  iconBg: string;
  iconColor: string;
  title: string;
  meta: string;
  time: string;
  urgent?: boolean;
}

const CASE_DYNAMICS: CaseDynamicsItem[] = [
  { id: 1, icon: 'mdi:file-document-outline', iconBg: 'bg-brand-tint3', iconColor: 'text-brand', title: '起诉状已完成', meta: '李明诉XX公司买卖合同纠纷 · 张律师', time: '10:30' },
  { id: 2, icon: 'mdi:clock-outline', iconBg: 'bg-warning-tint', iconColor: 'text-urgent', title: '证据提交即将截止', meta: '李明案 · 剩余 2 天', time: '紧急', urgent: true },
  { id: 3, icon: 'mdi:check-circle-outline', iconBg: 'bg-green-50', iconColor: 'text-success', title: '案件已归档', meta: '张三合同纠纷 · 归档完成', time: '昨天' },
  { id: 4, icon: 'mdi:gavel', iconBg: 'bg-purple-50', iconColor: 'text-wiki', title: '开庭日期已确定', meta: '王华借贷纠纷 · 2026-08-28 14:00', time: '昨天' },
];

const RECENT_CASES: Case[] = [
  { id: 'c-1', name: '李明诉XX公司买卖合同纠纷', role: '代理原告' as CaseRole, filedAt: '2026-06-10', status: '进行中' as CaseStatus },
  { id: 'c-2', name: '王华借贷纠纷', role: '代理被告' as CaseRole, filedAt: '2026-06-08', status: '待开庭' as CaseStatus },
  { id: 'c-3', name: '张三合同纠纷', role: '代理原告' as CaseRole, filedAt: '2026-06-05', status: '已归档' as CaseStatus },
  { id: 'c-4', name: '某科技公司股权纠纷', role: '代理原告' as CaseRole, filedAt: '2026-06-01', status: '进行中' as CaseStatus },
  { id: 'c-5', name: '赵六劳动争议仲裁', role: '代理被告' as CaseRole, filedAt: '2026-05-28', status: '仲裁中' as CaseStatus },
];

const STATUS_BADGE: Record<CaseStatus, string> = {
  '进行中': 'bg-brand-tint text-brand',
  '待开庭': 'bg-warning-tint text-orange-700',
  '已归档': 'bg-success-tint text-success',
  '仲裁中': 'bg-wiki-tint text-wiki',
};

function TrendArrow({ type }: { type: StatCardData['trend']['type'] }) {
  const icon = type === 'up' ? 'mdi:arrow-up' : type === 'warning' ? 'mdi:calendar-alert' : 'mdi:check-circle';
  return <span className="iconify mr-0.5" data-icon={icon} />;
}

export default function Workstation() {
  const [todayFilter, setTodayFilter] = useState<'all' | 'pending' | 'done'>('pending');

  const filteredSchedules = TODAY_SCHEDULES.filter((s) => {
    if (todayFilter === 'all') return true;
    if (todayFilter === 'done') return s.done;
    return !s.done;
  });

  function openCaseDetail(caseId: string) {
    // Phase 5.1 placeholder: W20+ 接 case-detail 路由
    console.info('[Phase 5.1] 打开案件详情:', caseId);
  }

  function openScheduleModal() {
    console.info('[Phase 5.1] 打开添加日程弹窗 (W20+ 增量)');
  }

  return (
    <div className="flex-1 flex flex-col overflow-y-auto p-3 space-y-3" data-view="workstation">
      {/* 顶部统计卡片 */}
      <div className="grid grid-cols-4 gap-3">
        {STATS.map((s) => (
          <div key={s.label} className="arco-card p-4 flex items-center justify-between">
            <div>
              <p className="text-fg-tertiary text-xs mb-1">{s.label}</p>
              <h3 className="text-2xl font-bold">{s.value}</h3>
              <p className={`text-[10px] mt-1 flex items-center ${s.trend.color}`}>
                <TrendArrow type={s.trend.type} />
                {s.trend.text}
              </p>
            </div>
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${s.iconBg} ${s.iconColor}`}>
              <span className="iconify text-xl" data-icon={s.icon} />
            </div>
          </div>
        ))}
      </div>

      {/* 双栏: 今日日程 + 需要关注 */}
      <div className="space-y-3 flex-1">
        <div className="grid grid-cols-12 gap-3 min-h-0">
          {/* 左栏: 今日日程 */}
          <div className="col-span-7">
            <div className="arco-card p-3 h-full flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-bold text-sm flex items-center gap-1.5">
                  <span className="iconify text-brand text-sm" data-icon="mdi:calendar-text-outline" />
                  今日日程
                  <span className="bg-brand text-white text-[10px] font-bold min-w-[18px] h-[18px] flex items-center justify-center rounded-full px-1">
                    {filteredSchedules.length}
                  </span>
                </h4>
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={openScheduleModal}
                    className="flex items-center gap-0.5 text-[10px] font-medium text-brand hover:text-brand-hover bg-brand-tint3 hover:bg-brand-tint px-1.5 py-0.5 rounded transition-colors"
                    title="添加日程"
                  >
                    <span className="iconify text-[10px]" data-icon="mdi:plus" />
                    <span>添加日程</span>
                  </button>
                </div>
              </div>

              {/* 三态过滤 */}
              <div className="flex items-center gap-1 mb-2">
                {(['all', 'pending', 'done'] as const).map((k) => (
                  <button
                    key={k}
                    type="button"
                    onClick={() => setTodayFilter(k)}
                    aria-pressed={todayFilter === k}
                    className={
                      'px-2 py-0.5 text-[10px] rounded transition-colors ' +
                      (todayFilter === k
                        ? 'bg-brand text-white'
                        : 'text-fg-tertiary hover:bg-bg-subtle')
                    }
                  >
                    {k === 'all' ? '全部' : k === 'pending' ? '待办' : '已完成'}
                  </button>
                ))}
              </div>

              <div className="flex-1 space-y-0">
                {filteredSchedules.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-8 text-fg-tertiary">
                    <span className="iconify text-3xl mb-2" data-icon="mdi:calendar-check-outline" />
                    <p className="text-xs">今日没有日程</p>
                  </div>
                ) : (
                  <div className="space-y-0.5">
                    {filteredSchedules.map((s) => (
                      <div
                        key={s.id}
                        className="flex items-center gap-2 p-2 rounded hover:bg-bg-subtle transition-colors"
                      >
                        <input
                          type="checkbox"
                          checked={s.done}
                          onChange={() => {/* Phase 5.1 toggle - 真实切换由 W20 schedule 子模块接 */}}
                          className="w-3.5 h-3.5 rounded border-bg-border text-brand focus:ring-brand"
                          aria-label={`标记 ${s.title} ${s.done ? '未完成' : '已完成'}`}
                        />
                        <span className={`text-xs flex-1 ${s.done ? 'line-through text-fg-tertiary' : 'text-fg-primary'}`}>
                          {s.title}
                        </span>
                        <span className="text-[10px] text-fg-tertiary">{s.time}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 右栏: 需要关注 */}
          <div className="col-span-5">
            <div className="arco-card p-3 h-full flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-bold text-sm flex items-center gap-1.5">
                  <span className="iconify text-sm text-danger" data-icon="mdi:alert-circle-outline" />
                  需要关注
                  <span className="bg-red-500 text-white text-[10px] font-bold min-w-[20px] h-[20px] flex items-center justify-center rounded-full px-1.5">
                    {ALERTS.length}
                  </span>
                </h4>
              </div>
              <div className="flex-1 space-y-2">
                {ALERTS.map((a) => (
                  <div
                    key={a.id}
                    className={`p-2 rounded-lg border ${a.borderClass} ${a.bgClass} transition-colors cursor-pointer group`}
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-white/60 flex items-center justify-center flex-shrink-0 text-sm">
                        {a.emoji}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-xs font-medium ${a.textClass}`}>{a.title}</p>
                        <p className={`text-[10px] mt-0.5 ${a.metaClass}`}>{a.meta}</p>
                      </div>
                      <span className="iconify text-fg-disabled text-sm opacity-0 group-hover:opacity-100 transition-opacity" data-icon="mdi:chevron-right" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 双栏: 案件动态 + 本周效率 */}
      <div className="grid grid-cols-12 gap-3">
        {/* 左栏: 案件动态 */}
        <div className="col-span-7">
          <div className="arco-card p-3 h-full">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-bold text-sm flex items-center gap-1.5">
                <span className="iconify text-sm text-brand" data-icon="mdi:bell-ring-outline" />
                案件动态
              </h4>
            </div>
            <div className="space-y-0">
              {CASE_DYNAMICS.map((d) => (
                <div key={d.id} className="flex items-start gap-2.5 py-2 border-b border-bg-border last:border-b-0">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${d.iconBg}`}>
                    <span className={`iconify text-xs ${d.iconColor}`} data-icon={d.icon} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-fg-primary">{d.title}</p>
                    <p className="text-[10px] text-fg-tertiary mt-0.5">{d.meta}</p>
                  </div>
                  <span className={`text-[10px] flex-shrink-0 ${d.urgent ? 'text-danger font-medium' : 'text-fg-disabled'}`}>
                    {d.time}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 右栏: 本周效率 */}
        <div className="col-span-5">
          <div className="arco-card p-3 h-full flex flex-col">
            <div className="flex items-center gap-2 mb-3 flex-none">
              <div className="w-7 h-7 rounded-lg bg-brand-tint3 flex items-center justify-center text-brand">
                <span className="iconify text-sm" data-icon="mdi:chart-timeline-variant" />
              </div>
              <h4 className="font-bold text-sm">本周效率</h4>
              <span className="text-[10px] text-fg-tertiary ml-auto bg-bg-subtle px-1.5 py-0.5 rounded-full">
                08-14 ~ 08-20
              </span>
            </div>
            <div className="flex-1 flex flex-col justify-between">
              <div className="grid grid-cols-3 gap-2 mb-3">
                <div className="text-center p-2.5 rounded-lg bg-bg-subtle border border-bg-border">
                  <p className="text-lg font-bold text-brand">3</p>
                  <p className="text-[10px] text-fg-tertiary mt-0.5">文书生成</p>
                </div>
                <div className="text-center p-2.5 rounded-lg bg-bg-subtle border border-bg-border">
                  <p className="text-lg font-bold text-brand">5</p>
                  <p className="text-[10px] text-fg-tertiary mt-0.5">类案检索</p>
                </div>
                <div className="text-center p-2.5 rounded-lg bg-bg-subtle border border-bg-border">
                  <p className="text-lg font-bold text-brand">2</p>
                  <p className="text-[10px] text-fg-tertiary mt-0.5">案件跟进</p>
                </div>
              </div>
              {/* 本周进度 */}
              <div className="space-y-2.5">
                {[
                  { label: '案件处理', value: '5/12', percent: 42, color: 'bg-brand' },
                  { label: '庭审准备', value: '2/3', percent: 66, color: 'bg-urgent' },
                  { label: '归档进度', value: '1/2', percent: 50, color: 'bg-green-500' },
                ].map((p) => (
                  <div key={p.label}>
                    <div className="flex justify-between text-[10px] text-fg-tertiary mb-1">
                      <span>{p.label}</span>
                      <span className="font-medium text-fg-secondary">{p.value}</span>
                    </div>
                    <div className="w-full h-2 bg-bg rounded-full overflow-hidden">
                      <div className={`h-full ${p.color} rounded-full`} style={{ width: `${p.percent}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 最近案件 */}
      <div className="arco-card p-3">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-bold text-sm flex items-center gap-2">
            <span className="iconify" data-icon="mdi:folder-multiple-outline" />
            最近案件
          </h4>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="pb-2 text-[10px] font-semibold text-fg-tertiary uppercase tracking-wider">案件名称</th>
                <th className="pb-2 text-[10px] font-semibold text-fg-tertiary uppercase tracking-wider">角色</th>
                <th className="pb-2 text-[10px] font-semibold text-fg-tertiary uppercase tracking-wider">立案日期</th>
                <th className="pb-2 text-[10px] font-semibold text-fg-tertiary uppercase tracking-wider">状态</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {RECENT_CASES.map((c) => (
                <tr
                  key={c.id}
                  onClick={() => openCaseDetail(c.id)}
                  className="hover:bg-gray-50 transition-colors cursor-pointer"
                >
                  <td className="py-2.5 text-sm font-medium text-brand truncate max-w-[180px]">{c.name}</td>
                  <td className="py-2.5 text-sm text-fg-secondary">{c.role}</td>
                  <td className="py-2.5 text-sm text-fg-tertiary">{c.filedAt}</td>
                  <td className="py-2.5">
                    <span className={`${STATUS_BADGE[c.status]} text-[10px] font-medium px-2 py-0.5 rounded-full`}>
                      {c.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}