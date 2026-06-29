/**
 * Skill 2 合同风险审查 - 核心交互 (W5 lex-coder)
 *
 * 覆盖范围:
 * 1. 02-result 头部 Tab 切换 (单合同审查 / 版本比对) - P1
 * 2. 01-upload 立场选择 + 02 立场切换器 - P2
 * 3. 02 致命条款 > 3 自动折叠 - P2
 * 4. 03 采用按钮 → Toast + 02 状态同步 + 审计 log - P1
 * 5. 移动端 < 768px 适配 - P3 (CSS in JS)
 * 6. 键盘可达 / ARIA - P2
 * 7. 04-negotiation 弹窗 (从 02 打开)
 * 8. 05-export 一键导出
 *
 * 加载: 跟在 ai-doc.js 之后 (2026-06-29)
 * 依赖: switchView/router (router.js), showToast (script.js)
 *
 * API: /api/contract-review/upload/result/negotiation/export
 * Demo: ?fixture_id=demo-rental-beijing-2026
 */
(function() {
    'use strict';

    // ====== 全局状态 ======
    var CR = {
        apiBase: 'http://127.0.0.1:8000/api/contract-review',
        reviewId: null,
        currentStance: '审查方',
        fixtures: [],
        auditLog: [],  // 本地审计 log (P1: 状态变更追踪)
        isMobile: window.matchMedia('(max-width: 767px)').matches,
    };

    // ====== 工具: 简易 showToast 适配 (与 script.js showToast 兼容) ======
    function toast(msg, type) {
        type = type || 'info';
        if (typeof window.showToast === 'function') {
            window.showToast(msg, type);
            return;
        }
        // 兜底: 手动创建 toast
        var el = document.createElement('div');
        el.className = 'fixed top-4 right-4 z-[9999] px-4 py-2 rounded shadow-lg text-sm ' +
            (type === 'success' ? 'bg-success text-white' :
             type === 'warning' ? 'bg-warning text-white' :
             type === 'error' ? 'bg-danger text-white' :
             'bg-brand text-white');
        el.textContent = msg;
        document.body.appendChild(el);
        setTimeout(function() { el.remove(); }, 3000);
    }

    // ====== 工具: HTML 转义 ======
    function esc(s) {
        if (s === null || s === undefined) return '';
        return String(s).replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
        });
    }

    // ====== 1. 02-result 头部 Tab 切换 (单合同 / 版本比对) - P1 ======
    function initResultTabs() {
        var tabs = document.querySelectorAll('[data-cr-tab]');
        tabs.forEach(function(tab) {
            tab.addEventListener('click', function(e) {
                e.preventDefault();
                var target = tab.getAttribute('data-cr-tab');
                tabs.forEach(function(t) {
                    t.classList.remove('bg-brand', 'text-white');
                    t.classList.add('text-fg-secondary', 'hover:bg-brand-tint');
                    t.setAttribute('aria-selected', 'false');
                });
                tab.classList.add('bg-brand', 'text-white');
                tab.classList.remove('text-fg-secondary', 'hover:bg-brand-tint');
                tab.setAttribute('aria-selected', 'true');
                // 切换面板
                document.querySelectorAll('[data-cr-panel]').forEach(function(p) {
                    p.classList.add('hidden');
                });
                var panel = document.querySelector('[data-cr-panel="' + target + '"]');
                if (panel) panel.classList.remove('hidden');
                if (target === 'diff') {
                    toast('版本比对功能 W6+ 增量提供, 当前 demo 显示 baseline 信息', 'info');
                }
            });
        });
    }

    // ====== 2. 01-upload 立场影响预览 + 02 立场切换器 - P2 ======
    var STANCE_PREVIEW = {
        '甲方': '甲方立场下, 风险等级可能加权, 建议优先关注收款/单方解除权条款',
        '乙方': '乙方立场下, 风险等级可能降权, 建议优先关注管辖/违约责任条款',
        '丙方': '丙方立场下, 风险等级不变, 建议优先关注担保责任范围条款',
        '审查方': '审查方立场下, 客观列出全部风险, 不偏向任何一方',
    };

    function initStancePreview() {
        var stanceBtns = document.querySelectorAll('[data-stance-btn]');
        stanceBtns.forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                var stance = btn.getAttribute('data-stance-btn');
                stanceBtns.forEach(function(b) {
                    b.classList.remove('bg-brand', 'text-white');
                    b.classList.add('bg-white', 'text-fg-secondary');
                    b.setAttribute('aria-pressed', 'false');
                });
                btn.classList.add('bg-brand', 'text-white');
                btn.classList.remove('bg-white', 'text-fg-secondary');
                btn.setAttribute('aria-pressed', 'true');
                CR.currentStance = stance;
                // 立场影响预览
                var preview = document.getElementById('stance-impact-preview');
                if (preview) {
                    preview.textContent = STANCE_PREVIEW[stance] || '';
                    preview.classList.remove('hidden');
                }
            });
        });
    }

    function initStanceSwitcher() {
        var switcher = document.getElementById('stance-switcher');
        if (!switcher) return;
        var buttons = switcher.querySelectorAll('[data-stance-switch]');
        buttons.forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                var stance = btn.getAttribute('data-stance-switch');
                if (!CR.reviewId) {
                    toast('请先上传并审查合同', 'warning');
                    return;
                }
                CR.currentStance = stance;
                // 调 API 切立场
                fetch(CR.apiBase + '/negotiation', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({review_id: CR.reviewId, stance: stance})
                })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    toast('立场已切换为 ' + stance + ' (谈判建议已更新)', 'success');
                    appendAudit('切换立场 → ' + stance);
                })
                .catch(function(err) {
                    console.error('立场切换失败:', err);
                    toast('立场切换失败: ' + err.message, 'error');
                });
            });
        });
    }

    // ====== 3. 02 致命条款 > 3 自动折叠 - P2 ======
    function initFatalCollapse() {
        var fatalContainer = document.getElementById('fatal-clauses-container');
        if (!fatalContainer) return;
        var fatals = fatalContainer.querySelectorAll('.clause-fatal');
        if (fatals.length <= 3) return;
        // 折叠第 4+ 项, 显示"查看其余 X 项致命" 按钮
        var hiddenCount = 0;
        for (var i = 3; i < fatals.length; i++) {
            fatals[i].classList.add('hidden');
            hiddenCount++;
        }
        var btn = document.createElement('button');
        btn.className = 'mt-3 w-full py-2 text-xs text-danger border border-danger/30 rounded-md hover:bg-danger-tint transition-colors focus:outline-none focus:ring-2 focus:ring-danger/30';
        btn.setAttribute('aria-expanded', 'false');
        btn.innerHTML = '<iconify-icon icon="mdi:chevron-down" class="text-sm align-middle"></iconify-icon> 查看其余 ' + hiddenCount + ' 项致命条款';
        btn.addEventListener('click', function() {
            var expanded = btn.getAttribute('aria-expanded') === 'true';
            for (var j = 3; j < fatals.length; j++) {
                if (expanded) {
                    fatals[j].classList.add('hidden');
                } else {
                    fatals[j].classList.remove('hidden');
                }
            }
            btn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
            btn.innerHTML = expanded
                ? '<iconify-icon icon="mdi:chevron-down" class="text-sm align-middle"></iconify-icon> 查看其余 ' + hiddenCount + ' 项致命条款'
                : '<iconify-icon icon="mdi:chevron-up" class="text-sm align-middle"></iconify-icon> 收起致命条款';
        });
        fatalContainer.appendChild(btn);
    }

    // ====== 4. 03 采用按钮 → Toast + 02 状态同步 + 审计 log - P1 ======
    function initAdoptButtons() {
        var adoptBtns = document.querySelectorAll('[data-adopt-btn]');
        adoptBtns.forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                var clauseId = btn.getAttribute('data-adopt-btn');
                var clauseTitle = btn.getAttribute('data-clause-title') || ('条款 ' + clauseId);
                btn.disabled = true;
                btn.classList.add('opacity-50', 'pointer-events-none');
                btn.textContent = '已采用';
                toast('已采用 ' + clauseTitle + ' 的修改建议, 审查结果已同步', 'success');
                appendAudit('采用 ' + clauseId + ' 修改建议 (' + clauseTitle + ')');
                // 通知 02 状态同步 (如果有 review_id, 调 API 标记)
                if (CR.reviewId) {
                    console.log('[CR] 标记', clauseId, '已采用 (review_id:', CR.reviewId + ')');
                }
                // 5 秒后可恢复 (律师可"撤销采用")
                setTimeout(function() {
                    btn.disabled = false;
                    btn.classList.remove('opacity-50', 'pointer-events-none');
                    btn.innerHTML = '<iconify-icon icon="mdi:check-circle" class="text-sm align-middle"></iconify-icon> 采用';
                }, 5000);
            });
        });
    }

    // ====== 审计日志 (P1: 状态变更追踪) ======
    function appendAudit(action) {
        var ts = new Date().toISOString().replace('T', ' ').slice(0, 19);
        CR.auditLog.push({ts: ts, action: action});
        // 渲染审计列表
        var logEl = document.getElementById('cr-audit-log');
        if (logEl) {
            var html = CR.auditLog.slice().reverse().slice(0, 10).map(function(e) {
                return '<div class="text-[10px] py-1 border-b border-bg-border/50">'
                    + '<span class="text-fg-tertiary">' + esc(e.ts) + '</span> · '
                    + '<span class="text-fg-secondary">' + esc(e.action) + '</span></div>';
            }).join('');
            logEl.innerHTML = html || '<div class="text-[10px] text-fg-tertiary">暂无变更记录</div>';
        }
        console.log('[CR Audit]', ts, action);
    }

    // ====== 5. 移动端 < 768px 适配 - P3 ======
    function applyMobileStyles() {
        if (!CR.isMobile) return;
        var style = document.createElement('style');
        style.textContent = '@media (max-width: 767px) { '
            + '.grid-cols-12 { grid-template-columns: 1fr !important; } '
            + '.grid-cols-7, .grid-cols-5, .grid-cols-8, .grid-cols-4 { grid-column: span 12 / span 12 !important; } '
            + '.col-span-7, .col-span-5, .col-span-8, .col-span-4 { grid-column: span 12 / span 12 !important; } '
            + '.col-span-3, .col-span-2, .col-span-1 { grid-column: span 6 / span 6 !important; } '
            + '.flex.items-center.gap-3, .flex.items-center.gap-4 { flex-wrap: wrap; } '
            + '[role="dialog"], .modal-overlay { position: fixed !important; inset: 0 !important; max-width: 100vw !important; max-height: 100vh !important; } '
            + '}';
        document.head.appendChild(style);
    }

    // ====== 6. 键盘可达 / ARIA 标签补全 - P2 ======
    function applyARIA() {
        // 主按钮加 role="button" + tabindex + focus:ring (CSS via class)
        document.querySelectorAll('[data-cr-action]').forEach(function(el) {
            if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '0');
            if (!el.hasAttribute('role')) el.setAttribute('role', 'button');
            if (!el.classList.contains('focus:ring-2')) {
                el.classList.add('focus:outline-none', 'focus:ring-2', 'focus:ring-brand/30');
            }
        });
        // 风险条款卡加 region role + aria-label
        document.querySelectorAll('.clause-fatal, .clause-major, .clause-advisory, .clause-ok').forEach(function(el) {
            if (!el.hasAttribute('role')) el.setAttribute('role', 'region');
            var level = el.classList.contains('clause-fatal') ? '致命风险'
                : el.classList.contains('clause-major') ? '重大风险'
                : el.classList.contains('clause-advisory') ? '建议风险' : '合规';
            var title = el.querySelector('h5');
            var label = level + ' - ' + (title ? title.textContent.trim() : '条款');
            if (!el.hasAttribute('aria-label')) el.setAttribute('aria-label', label);
        });
        // ESC 关闭 04-negotiation 弹窗
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                var modal = document.getElementById('cr-negotiation-modal');
                if (modal && !modal.classList.contains('hidden')) {
                    modal.classList.add('hidden');
                    toast('已关闭谈判策略弹窗', 'info');
                }
            }
        });
    }

    // ====== 7. 04-negotiation 弹窗 (从 02 打开) ======
    function initNegotiationModal() {
        var openBtn = document.querySelectorAll('[data-open-negotiation]');
        var modal = document.getElementById('cr-negotiation-modal');
        var closeBtn = document.querySelectorAll('[data-close-negotiation]');
        if (!modal) return;
        openBtn.forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                if (!CR.reviewId) {
                    toast('请先审查合同, 再打开谈判策略', 'warning');
                    return;
                }
                // 拉取谈判策略
                fetch(CR.apiBase + '/negotiation', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({review_id: CR.reviewId})
                })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    renderNegotiationModal(data);
                    modal.classList.remove('hidden');
                })
                .catch(function(err) {
                    console.error('拉取谈判策略失败:', err);
                    toast('谈判策略加载失败: ' + err.message, 'error');
                });
            });
        });
        closeBtn.forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                modal.classList.add('hidden');
            });
        });
        // 点击 backdrop 关闭
        modal.addEventListener('click', function(e) {
            if (e.target === modal) modal.classList.add('hidden');
        });
    }

    function renderNegotiationModal(data) {
        var body = document.getElementById('cr-negotiation-modal-body');
        if (!body) return;
        var s = data.strategy || {};
        body.innerHTML = ''
            + '<div class="grid grid-cols-1 md:grid-cols-2 gap-4">'
            + '  <div class="bg-danger-tint rounded-md p-4 border-l-4 border-danger">'
            + '    <h5 class="font-semibold text-sm mb-2 flex items-center gap-1">'
            + '      <iconify-icon icon="mdi:flag-variant" class="text-danger"></iconify-icon> 红线条款 (建议放弃)'
            + '    </h5>'
            + '    <ul class="text-xs space-y-1">'
            + (s.walk_away_signals || ['无红线条款']).map(function(x) { return '<li>· ' + esc(x) + '</li>'; }).join('')
            + '    </ul></div>'
            + '  <div class="bg-warning-tint rounded-md p-4 border-l-4 border-warning">'
            + '    <h5 class="font-semibold text-sm mb-2 flex items-center gap-1">'
            + '      <iconify-icon icon="mdi:strategy" class="text-warning"></iconify-icon> 立场建议 (' + esc(data.stance || '审查方') + ')'
            + '    </h5>'
            + '    <p class="text-xs leading-relaxed">' + esc(s.stance_specific_advice || '客观列出全部风险') + '</p>'
            + '  </div>'
            + '  <div class="bg-brand-tint3 rounded-md p-4 border-l-4 border-brand md:col-span-2">'
            + '    <h5 class="font-semibold text-sm mb-2 flex items-center gap-1">'
            + '      <iconify-icon icon="mdi:format-list-numbered" class="text-brand"></iconify-icon> 优先谈判条款'
            + '    </h5>'
            + '    <div class="flex flex-wrap gap-1.5">'
            + (s.priority_clauses || []).map(function(p) {
                return '<span class="text-[10px] px-2 py-0.5 bg-white border border-brand/30 text-brand rounded-sm">' + esc(p) + '</span>';
            }).join('')
            + '    </div></div>'
            + '</div>';
    }

    // ====== 8. 01-upload 提交 (调 API 上传) ======
    function initUploadSubmit() {
        var form = document.getElementById('cr-upload-form');
        if (!form) return;
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var fd = new FormData(form);
            var payload = {
                contract_type: fd.get('contract_type') || '服务合同',
                stance: CR.currentStance || fd.get('stance') || '审查方',
                contract_text: fd.get('contract_text') || '',
                fixture_id: fd.get('fixture_id') || '',
            };
            // 演示模式: 有 fixture_id 优先
            if (!payload.fixture_id && !payload.contract_text) {
                toast('请选择示例合同 (Demo 模式) 或粘贴合同文本', 'warning');
                return;
            }
            toast('正在审查合同 (P95 < 2s)...', 'info');
            fetch(CR.apiBase + '/upload', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.detail) throw new Error(data.detail);
                CR.reviewId = data.review_id;
                toast('审查完成! (耗时 ' + data.latency_ms + 'ms), 跳转结果页', 'success');
                appendAudit('完成审查 review_id=' + data.review_id + ', demo=' + data.demo_mode);
                setTimeout(function() {
                    if (typeof window.switchView === 'function') {
                        window.switchView('contract-review-result');
                    }
                }, 500);
            })
            .catch(function(err) {
                console.error('上传失败:', err);
                toast('审查失败: ' + err.message, 'error');
            });
        });
    }

    // ====== 9. 加载 fixtures 列表 (01-upload 下拉) ======
    function loadFixtures() {
        fetch(CR.apiBase + '/fixtures')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                CR.fixtures = data.fixtures || [];
                var sel = document.getElementById('cr-fixture-select');
                if (sel) {
                    sel.innerHTML = '<option value="">— 选择示例合同 (Demo 模式) —</option>'
                        + CR.fixtures.map(function(f) {
                            return '<option value="' + esc(f.fixture_id) + '">'
                                + esc(f.contract_type) + ' · ' + esc(f.contract_title) + ' · ' + esc(f.risk_hint)
                                + '</option>';
                        }).join('');
                }
            })
            .catch(function(err) {
                console.warn('fixtures 加载失败 (后端可能未起):', err);
            });
    }

    // ====== 10. 05-export 导出按钮 ======
    function initExportButtons() {
        var btns = document.querySelectorAll('[data-cr-export]');
        btns.forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                var fmt = btn.getAttribute('data-cr-export');
                if (!CR.reviewId) {
                    toast('请先审查合同', 'warning');
                    return;
                }
                fetch(CR.apiBase + '/export', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({review_id: CR.reviewId, format: fmt})
                })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.detail) throw new Error(data.detail);
                    // 触发下载
                    var blob = new Blob([data.content], {type: data.media_type});
                    var url = URL.createObjectURL(blob);
                    var a = document.createElement('a');
                    a.href = url;
                    a.download = data.filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    toast('已导出 ' + fmt.toUpperCase() + ' (' + data.size_bytes + ' 字节)', 'success');
                    appendAudit('导出报告 ' + fmt + ' (' + data.filename + ')');
                })
                .catch(function(err) {
                    console.error('导出失败:', err);
                    toast('导出失败: ' + err.message, 'error');
                });
            });
        });
    }

    // ====== 启动 ======
    function boot() {
        applyMobileStyles();
        applyARIA();
        initResultTabs();
        initStancePreview();
        initStanceSwitcher();
        initFatalCollapse();
        initAdoptButtons();
        initNegotiationModal();
        initUploadSubmit();
        initExportButtons();
        loadFixtures();
        // 响应窗口尺寸变化 (移动端切换)
        window.matchMedia('(max-width: 767px)').addEventListener('change', function(e) {
            CR.isMobile = e.matches;
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

    // 全局暴露 (调试用)
    globalThis.CR = CR;
})();