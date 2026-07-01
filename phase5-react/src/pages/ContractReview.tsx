/**
 * ContractReview 页面 - W5 contract-review.js + templates 重构为 React 组件 + TypeScript
 *
 * 保留功能 (Skill 2 合同审查 - 5 大价值主张之一, PRD V5.0 § 6):
 *  - 4 立场切换 (甲方/乙方/丙方/审查方) - W8 D3 § __updateStancePreview single source of truth
 *  - 立场影响预览 (3 风险等级 fatal/major/ok 加权方向)
 *  - 上传区 + 审查结果区 (Phase 5.1 W19 重构为单页, W20+ 拆分为 upload/result/negotiation/export 子路由)
 *  - 致命条款 > 3 自动折叠
 *  - 键盘可达 / ARIA
 *
 * 重构点:
 *  - 4 立场 + 3 风险矩阵 → STANCE_MATRIX (类型化, 跟 vanilla STANCE_MATRIX 一致)
 *  - 6 个独立 vanilla 模板 + globalThis 桥接 → 单页 React 状态
 *  - insertAdjacentHTML + IIFE → JSX + useState
 */
import { useState, type ChangeEvent } from 'react';
import { STANCE_MATRIX, type RiskClause, type RiskLevel, type Stance } from '../types';

type Tab = 'single' | 'diff';

// W5 vanilla contract-review-upload.html 复用 - 演示数据
const MOCK_CLAUSES: RiskClause[] = [
  {
    id: 'c-1',
    level: 'fatal',
    title: '单方解除权不对等',
    description: '甲方可单方解除合同, 但乙方需承担违约责任, 显失公平',
    suggestedRevision: '建议改为双方协商解除或同等条件下互享单方解除权',
  },
  {
    id: 'c-2',
    level: 'fatal',
    title: '违约金上限过高',
    description: '违约金为本合同总额 30%, 远超法定上限 (实际损失 30% 为合理上限)',
    suggestedRevision: '建议降低至 20% 或与实际损失挂钩',
  },
  {
    id: 'c-3',
    level: 'major',
    title: '管辖法院约定不利',
    description: '约定甲方所在地法院管辖, 对乙方产生管辖不便',
    suggestedRevision: '建议改为被告所在地或合同履行地法院',
  },
  {
    id: 'c-4',
    level: 'major',
    title: '保密期限约定不明',
    description: '保密条款未明确保密期限, 存在争议风险',
    suggestedRevision: '建议明确保密期限 (e.g. 合同终止后 3 年)',
  },
  {
    id: 'c-5',
    level: 'ok',
    title: '争议解决方式',
    description: '约定仲裁解决, 条款清晰',
  },
];

const RISK_BADGE: Record<RiskLevel, { label: string; className: string; icon: string }> = {
  fatal: { label: '致命', className: 'bg-danger-tint text-danger', icon: 'mdi:alert-octagon' },
  major: { label: '严重', className: 'bg-warning-tint text-warning', icon: 'mdi:alert' },
  ok:    { label: 'OK',   className: 'bg-success-tint text-success', icon: 'mdi:check-circle' },
};

export default function ContractReview() {
  const [tab, setTab] = useState<Tab>('single');
  const [stance, setStance] = useState<Stance>('审查方');
  const [fileName, setFileName] = useState<string | null>(null);
  const [hasResult, setHasResult] = useState(false);
  const [auditLog, setAuditLog] = useState<string[]>([]);

  const currentMatrix = STANCE_MATRIX[stance];
  const fatalCount = MOCK_CLAUSES.filter((c) => c.level === 'fatal').length;
  const autoCollapse = fatalCount > 3;

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      setHasResult(false);
    }
  }

  function handleReview() {
    if (!fileName) {
      alert('请先选择合同文件');
      return;
    }
    // Phase 5.1 placeholder: 真实审查走 FastAPI /api/contract-review/upload (W5 已就位)
    console.info('[Phase 5.1] 触发合同审查:', { fileName, stance });
    setHasResult(true);
  }

  function handleAdopt(clauseId: string, clauseTitle: string) {
    setAuditLog((prev) => [
      `${new Date().toLocaleTimeString('zh-CN')} · 采用条款 ${clauseId}: ${clauseTitle}`,
      ...prev,
    ]);
    console.info('[Phase 5.1] 采用条款:', clauseId);
  }

  function handleExport() {
    console.info('[Phase 5.1] 一键导出 (W20+ 增量, 真实走 /api/contract-review/export)');
    alert('导出功能 W20+ 增量提供, 当前 demo 跳过');
  }

  return (
    <div className="flex-1 flex flex-col overflow-y-auto p-3 space-y-3" data-view="contract-review">
      {/* ===== 01 Upload 区 ===== */}
      <section className="arco-card p-4 space-y-4">
        <header>
          <h3 className="font-bold text-sm flex items-center gap-2">
            <span className="iconify text-brand" data-icon="mdi:upload-outline" />
            01 上传合同
          </h3>
          <p className="text-xs text-fg-tertiary mt-1">支持 PDF / Word / 图片 (OCR), 单文件 ≤ 50MB</p>
        </header>

        {/* 立场选择 (4 立场) */}
        <div>
          <p className="text-xs text-fg-secondary font-medium mb-2">请选择您所在的立场</p>
          <div className="grid grid-cols-4 gap-2">
            {(Object.keys(STANCE_MATRIX) as Stance[]).map((s) => {
              const matrix = STANCE_MATRIX[s];
              const on = stance === s;
              return (
                <button
                  key={s}
                  type="button"
                  onClick={() => setStance(s)}
                  aria-checked={on}
                  aria-pressed={on}
                  className={
                    'cr-stance-btn px-3 py-2 rounded-lg border text-sm transition-all ' +
                    (on
                      ? 'bg-brand text-white border-brand shadow-sm font-medium'
                      : 'bg-white text-fg-secondary border-bg-border hover:border-brand-tint4')
                  }
                >
                  {matrix.label}
                  <span className="text-[10px] ml-1 opacity-70">({matrix.shortLabel})</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 立场影响预览 (single source of truth 跟 vanilla 一致) */}
        <div className="bg-bg-subtle border border-bg-border rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-medium text-fg-primary">
              {currentMatrix.label}立场影响预览
            </p>
            <p className="text-[10px] text-fg-tertiary">关注: {currentMatrix.focus}</p>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            {(['fatal', 'major', 'ok'] as RiskLevel[]).map((level) => {
              const imp = currentMatrix.impacts[level];
              const badge = RISK_BADGE[level];
              return (
                <div key={level} className="flex items-center justify-between bg-white rounded p-2 border border-bg-border">
                  <span className={`flex items-center gap-1 ${badge.className} text-[10px] font-medium px-1.5 py-0.5 rounded`}>
                    <span className="iconify text-[10px]" data-icon={badge.icon} />
                    {badge.label}
                  </span>
                  <span className={`text-xs font-medium ${imp.cls}`}>{imp.sym}</span>
                </div>
              );
            })}
          </div>
          <p className="text-[10px] text-fg-tertiary mt-2">
            建议优先关注: {currentMatrix.tips.join(' · ')}
          </p>
        </div>

        {/* 文件上传 */}
        <div className="flex items-center gap-3">
          <label className="flex-1 flex items-center gap-2 px-4 py-3 border-2 border-dashed border-bg-border rounded-lg cursor-pointer hover:border-brand-tint4 transition-colors">
            <span className="iconify text-brand text-xl" data-icon="mdi:file-document-outline" />
            <span className="text-sm text-fg-secondary flex-1">
              {fileName || '点击选择文件 (PDF / Word / 图片)'}
            </span>
            <input
              type="file"
              accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              className="hidden"
              aria-label="选择合同文件"
            />
          </label>
          <button
            type="button"
            onClick={handleReview}
            disabled={!fileName}
            className="btn-primary flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="iconify" data-icon="mdi:magnify-scan" />
            启动审查
          </button>
        </div>
      </section>

      {/* ===== 02 Result 区 (条件渲染) ===== */}
      {hasResult && (
        <section className="arco-card p-4 space-y-4">
          <header className="flex items-center justify-between">
            <h3 className="font-bold text-sm flex items-center gap-2">
              <span className="iconify text-brand" data-icon="mdi:file-document-check-outline" />
              02 审查结果
              <span className="bg-brand text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                {MOCK_CLAUSES.length} 条
              </span>
            </h3>

            {/* Tab 切换 (单合同 / 版本比对) */}
            <div className="flex items-center gap-1 bg-bg-subtle rounded-lg p-0.5">
              <button
                type="button"
                onClick={() => setTab('single')}
                aria-selected={tab === 'single'}
                className={
                  'px-2 py-1 rounded text-xs transition-colors ' +
                  (tab === 'single' ? 'bg-brand text-white' : 'text-fg-secondary hover:bg-brand-tint')
                }
              >
                单合同
              </button>
              <button
                type="button"
                onClick={() => setTab('diff')}
                aria-selected={tab === 'diff'}
                className={
                  'px-2 py-1 rounded text-xs transition-colors ' +
                  (tab === 'diff' ? 'bg-brand text-white' : 'text-fg-secondary hover:bg-brand-tint')
                }
              >
                版本比对
              </button>
            </div>
          </header>

          {tab === 'single' ? (
            <div className="space-y-2">
              {autoCollapse && (
                <p className="text-[10px] text-fg-tertiary bg-warning-tint px-2 py-1 rounded">
                  ⚠ 致命条款 &gt; 3 条, 已自动折叠细节 (仅显示标题)
                </p>
              )}
              {MOCK_CLAUSES.map((c) => (
                <div
                  key={c.id}
                  className="border border-bg-border rounded-lg p-3 hover:border-brand-tint4 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <span className={`flex items-center gap-1 ${RISK_BADGE[c.level].className} text-[10px] font-medium px-1.5 py-0.5 rounded`}>
                      <span className="iconify text-[10px]" data-icon={RISK_BADGE[c.level].icon} />
                      {RISK_BADGE[c.level].label}
                    </span>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-fg-primary">{c.title}</h4>
                      {!autoCollapse && (
                        <p className="text-xs text-fg-tertiary mt-1">{c.description}</p>
                      )}
                      {c.suggestedRevision && !autoCollapse && (
                        <p className="text-xs text-success mt-1 bg-success-tint px-2 py-1 rounded">
                          💡 {c.suggestedRevision}
                        </p>
                      )}
                      {/* 立场影响加权 */}
                      <p className={`text-[10px] mt-1 ${currentMatrix.impacts[c.level].cls}`}>
                        {currentMatrix.label}立场: {currentMatrix.impacts[c.level].sym}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleAdopt(c.id, c.title)}
                      className="text-[10px] text-brand hover:text-brand-hover bg-brand-tint3 hover:bg-brand-tint px-2 py-1 rounded transition-colors flex items-center gap-0.5"
                    >
                      <span className="iconify text-[10px]" data-icon="mdi:check" />
                      采用
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-bg-subtle border border-bg-border rounded-lg p-6 text-center">
              <span className="iconify text-3xl text-fg-tertiary" data-icon="mdi:compare-horizontal" />
              <p className="text-xs text-fg-tertiary mt-2">版本比对功能 W6+ 增量提供, 当前 demo 显示 baseline 信息</p>
            </div>
          )}

          {/* 审计 log (本地状态) */}
          {auditLog.length > 0 && (
            <details className="bg-bg-subtle border border-bg-border rounded-lg p-2">
              <summary className="text-xs text-fg-secondary cursor-pointer">
                审计 log ({auditLog.length})
              </summary>
              <div className="mt-2 space-y-1 text-[10px] font-mono text-fg-tertiary max-h-40 overflow-y-auto">
                {auditLog.map((line, idx) => (
                  <div key={idx}>{line}</div>
                ))}
              </div>
            </details>
          )}

          {/* 05 Export */}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={handleExport}
              className="btn-secondary flex items-center gap-1"
            >
              <span className="iconify" data-icon="mdi:download-outline" />
              一键导出
            </button>
          </div>
        </section>
      )}
    </div>
  );
}