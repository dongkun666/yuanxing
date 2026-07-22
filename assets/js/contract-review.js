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
(function () {
    'use strict';

    // ====== 全局状态 ======
    var CR = {
        apiBase: 'http://127.0.0.1:8000/api/contract-review',
        reviewId: null,
        currentStance: '审查方',
        fixtures: [],
        auditLog: [], // 本地审计 log (P1: 状态变更追踪)
        isMobile: window.matchMedia('(max-width: 767px)').matches,
        // ====== 规则引擎相关状态 ======
        ruleEngine: {
            isLoading: false,
            reviewResult: null,
            currentContractText: '',
            currentContractType: '其他',
            rules: [],
            categories: [],
            rulesStats: {},
            activeCategory: 'all'
        }
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
        el.className =
            'fixed top-4 right-4 z-[9999] px-4 py-2 rounded shadow-lg text-sm ' +
            (type === 'success'
                ? 'bg-success text-white'
                : type === 'warning'
                    ? 'bg-warning text-white'
                    : type === 'error'
                        ? 'bg-danger text-white'
                        : 'bg-brand text-white');
        el.textContent = msg;
        document.body.appendChild(el);
        setTimeout(function () {
            el.remove();
        }, 3000);
    }

    // ====== 工具: HTML 转义 ======
    function esc(s) {
        if (s === null || s === undefined) return '';
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', '\'': '&#39;' }[c];
        });
    }

    // ====== 1. 02-result 头部 Tab 切换 (单合同 / 版本比对) - P1 ======
    function initResultTabs() {
        var tabs = document.querySelectorAll('[data-cr-tab]');
        tabs.forEach(function (tab) {
            tab.addEventListener('click', function (e) {
                e.preventDefault();
                var target = tab.getAttribute('data-cr-tab');
                tabs.forEach(function (t) {
                    t.classList.remove('bg-brand', 'text-white');
                    t.classList.add('text-fg-secondary', 'hover:bg-brand-tint');
                    t.setAttribute('aria-selected', 'false');
                });
                tab.classList.add('bg-brand', 'text-white');
                tab.classList.remove('text-fg-secondary', 'hover:bg-brand-tint');
                tab.setAttribute('aria-selected', 'true');
                // 切换面板
                document.querySelectorAll('[data-cr-panel]').forEach(function (p) {
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
    // D3 W8: __updateStancePreview(stance) 是立场影响预览的 single source of truth
    // 4 立场 × 3 风险等级 (fatal/major/ok) 加权方向 + 关注重点 + 立场标签
    // 4 立场映射到 3 类常用立场 (原告/被告/中立 = 甲方/乙方/审查方)
    var STANCE_MATRIX = {
        甲方: {
            label: '甲方',
            color: 'brand',
            shortLabel: '原告', // 律师常见用语
            impacts: {
                fatal: { sym: '↓ 降权', cls: 'text-success' },
                major: { sym: '→ 持平', cls: 'text-warning' },
                ok: { sym: '↑ 加权', cls: 'text-success' }
            },
            focus: '对方义务 / 自身免责 / 救济成本',
            tips: ['单方解除权', '违约金上限', '管辖法院中立']
        },
        乙方: {
            label: '乙方',
            color: 'ai',
            shortLabel: '被告',
            impacts: {
                fatal: { sym: '↑ 加权', cls: 'text-danger' },
                major: { sym: '→ 持平', cls: 'text-warning' },
                ok: { sym: '↓ 降权', cls: 'text-success' }
            },
            focus: '权利失衡 / 显失公平 / 解除权不对等',
            tips: ['违约金过高', '单方解除权不对等', '管辖不利']
        },
        丙方: {
            label: '丙方',
            color: 'warning',
            shortLabel: '第三方',
            impacts: {
                fatal: { sym: '→ 持平', cls: 'text-warning' },
                major: { sym: '↑ 加权', cls: 'text-warning' },
                ok: { sym: '→ 持平', cls: 'text-fg-tertiary' }
            },
            focus: '连带义务 / 担保范围 / 第三方责任',
            tips: ['连带责任', '担保物范围', '第三方追偿权']
        },
        审查方: {
            label: '审查方',
            color: 'fg-secondary',
            shortLabel: '中立',
            impacts: {
                fatal: { sym: '→ 持平', cls: 'text-warning' },
                major: { sym: '→ 持平', cls: 'text-warning' },
                ok: { sym: '→ 持平', cls: 'text-fg-tertiary' }
            },
            focus: '全面客观 / 多方均衡 / 中立报告',
            tips: ['完整披露所有风险', '各方权益平衡', '客观描述无偏向']
        }
    };

    // 兼容旧 inline 脚本: STANCE_PREVIEW 文本降级
    var STANCE_PREVIEW = {
        甲方: '甲方立场下, 风险等级可能加权, 建议优先关注收款/单方解除权条款',
        乙方: '乙方立场下, 风险等级可能降权, 建议优先关注管辖/违约责任条款',
        丙方: '丙方立场下, 风险等级不变, 建议优先关注担保责任范围条款',
        审查方: '审查方立场下, 客观列出全部风险, 不偏向任何一方'
    };

    /**
     * D3 W8: __updateStancePreview(stance) - 立场影响预览的 single source of truth
     * @param {string} stance - '甲方' | '乙方' | '丙方' | '审查方'
     * @returns {Object} {label, shortLabel, color, impacts, focus, tips} 或默认审查方
     */
    function __updateStancePreview(stance) {
        var matrix = STANCE_MATRIX[stance] || STANCE_MATRIX['审查方'];
        CR.currentStance = stance;
        // 尝试同步 DOM (如果有 .cr-stance-btn 按钮组, 更新 aria-pressed 状态)
        try {
            var btns = document.querySelectorAll('.cr-stance-btn');
            btns.forEach(function (b) {
                var on = b.getAttribute('data-stance') === stance;
                b.setAttribute('aria-checked', on ? 'true' : 'false');
                b.classList.toggle('bg-brand', on);
                b.classList.toggle('text-white', on);
                b.classList.toggle('border-brand', on);
                b.classList.toggle('shadow-sm', on);
                b.classList.toggle('font-medium', on);
                b.classList.toggle('bg-white', !on);
                b.classList.toggle('text-fg-secondary', !on);
                b.classList.toggle('border-bg-border', !on);
            });
        } catch (e) {
            /* DOM 还没就绪时 swallow */
        }
        return matrix;
    }

    function initStancePreview() {
        var stanceBtns = document.querySelectorAll('[data-stance-btn]');
        stanceBtns.forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                var stance = btn.getAttribute('data-stance-btn');
                stanceBtns.forEach(function (b) {
                    b.classList.remove('bg-brand', 'text-white');
                    b.classList.add('bg-white', 'text-fg-secondary');
                    b.setAttribute('aria-pressed', 'false');
                });
                btn.classList.add('bg-brand', 'text-white');
                btn.classList.remove('bg-white', 'text-fg-secondary');
                btn.setAttribute('aria-pressed', 'true');
                // 调用 single source of truth
                __updateStancePreview(stance);
                // 立场影响预览 (兼容旧版 preview 区域)
                var preview = document.getElementById('stance-impact-preview');
                if (preview) {
                    preview.textContent = STANCE_PREVIEW[stance] || '';
                    preview.classList.remove('hidden');
                }
            });
        });
        // 兼容 .cr-stance-btn (W7 upload 页面) 委托到 __updateStancePreview
        var crBtns = document.querySelectorAll('.cr-stance-btn');
        crBtns.forEach(function (btn) {
            // 避免重复绑定 (data-stance-btn 优先)
            if (btn.hasAttribute('data-stance-btn')) return;
            btn.addEventListener('click', function (e) {
                var stance = btn.getAttribute('data-stance');
                if (stance) __updateStancePreview(stance);
            });
        });
    }

    function initStanceSwitcher() {
        var switcher = document.getElementById('stance-switcher');
        if (!switcher) return;
        var buttons = switcher.querySelectorAll('[data-stance-switch]');
        buttons.forEach(function (btn) {
            btn.addEventListener('click', function (e) {
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
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ review_id: CR.reviewId, stance: stance })
                })
                    .then(function (r) {
                        return r.json();
                    })
                    .then(function (data) {
                        toast('立场已切换为 ' + stance + ' (谈判建议已更新)', 'success');
                        appendAudit('切换立场 → ' + stance);
                    })
                    .catch(function (err) {
                        console.error('立场切换失败:', err);
                        toast('立场切换失败: ' + err.message, 'error');
                    });
            });
        });
    }

    // ====== 3. 02 致命条款 > 3 自动折叠 - P2 (D3 W8 修复) ======
    // D3 W8: __applyFatalCollapse(visibleLimit) 是 single source of truth
    // 设计: fatalCount > 3 时, 折叠第 4+ 项, 显示"查看其余 X 项致命" 按钮
    // 测试 0/3/5 三种情况: 0/3 隐藏按钮, 5 显示按钮 + 折叠 4-5
    var FATAL_VISIBLE_LIMIT = 3;

    function __applyFatalCollapse(visibleLimit) {
        visibleLimit = visibleLimit || FATAL_VISIBLE_LIMIT;
        var container = document.getElementById('fatal-clauses-container');
        var btn = document.getElementById('cr-fatal-toggle');
        if (!container) return { visible: 0, hidden: 0, buttonVisible: false };
        // 只数 .clause-fatal 元素 (D3 W8 修复: 之前 .cr-fatal-clause 包含 major, 不准)
        var fatals = container.querySelectorAll('.clause-fatal');
        var fatalCount = fatals.length;
        // 0 致命或 ≤ visibleLimit: 按钮隐藏
        if (fatalCount <= visibleLimit) {
            // 全部显示
            fatals.forEach(function (c) {
                c.classList.remove('cr-fatal-overflow');
                c.style.display = '';
            });
            if (btn) {
                btn.classList.add('hidden');
                btn.setAttribute('aria-expanded', 'false');
            }
            return { visible: fatalCount, hidden: 0, buttonVisible: false };
        }
        // > visibleLimit: 折叠第 4+ 项
        var hiddenCount = 0;
        fatals.forEach(function (c, idx) {
            if (idx >= visibleLimit) {
                c.classList.add('cr-fatal-overflow');
                c.style.display = 'none';
                hiddenCount += 1;
            } else {
                c.classList.remove('cr-fatal-overflow');
                c.style.display = '';
            }
        });
        if (btn) {
            btn.classList.remove('hidden');
            btn.setAttribute('aria-expanded', 'false');
            var textEl = document.getElementById('cr-fatal-toggle-text');
            var countEl = document.getElementById('cr-fatal-toggle-count');
            if (textEl) textEl.textContent = '查看其余致命条款';
            if (countEl) countEl.textContent = '+' + hiddenCount;
            // 重新绑定 click (避免 inline onclick 与 .onclick 冲突)
            btn.onclick = function () {
                var expanded = btn.getAttribute('aria-expanded') === 'true';
                btn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
                container.querySelectorAll('.cr-fatal-overflow').forEach(function (c) {
                    c.style.display = expanded ? 'none' : '';
                });
                var icon = btn.querySelector('.cr-fatal-toggle-icon');
                if (icon) icon.style.transform = expanded ? '' : 'rotate(180deg)';
                if (textEl) textEl.textContent = expanded ? '查看其余致命条款' : '收起致命条款';
            };
        }
        return { visible: visibleLimit, hidden: hiddenCount, buttonVisible: true };
    }

    function initFatalCollapse() {
        __applyFatalCollapse(FATAL_VISIBLE_LIMIT);
    }

    // ====== 4. 03 采用按钮 → Toast + 02 状态同步 + 审计 log - P1 ======
    function initAdoptButtons() {
        var adoptBtns = document.querySelectorAll('[data-adopt-btn]');
        adoptBtns.forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                var clauseId = btn.getAttribute('data-adopt-btn');
                var clauseTitle = btn.getAttribute('data-clause-title') || '条款 ' + clauseId;
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
                setTimeout(function () {
                    btn.disabled = false;
                    btn.classList.remove('opacity-50', 'pointer-events-none');
                    btn.innerHTML =
                        '<iconify-icon icon="mdi:check-circle" class="text-sm align-middle"></iconify-icon> 采用';
                }, 5000);
            });
        });
    }

    // ====== 审计日志 (P1: 状态变更追踪) ======
    function appendAudit(action) {
        var ts = new Date().toISOString().replace('T', ' ').slice(0, 19);
        CR.auditLog.push({ ts: ts, action: action });
        // 渲染审计列表
        var logEl = document.getElementById('cr-audit-log');
        if (logEl) {
            var html = CR.auditLog
                .slice()
                .reverse()
                .slice(0, 10)
                .map(function (e) {
                    return (
                        '<div class="text-[10px] py-1 border-b border-bg-border/50">' +
                        '<span class="text-fg-tertiary">' +
                        esc(e.ts) +
                        '</span> · ' +
                        '<span class="text-fg-secondary">' +
                        esc(e.action) +
                        '</span></div>'
                    );
                })
                .join('');
            logEl.innerHTML = html || '<div class="text-[10px] text-fg-tertiary">暂无变更记录</div>';
        }
        console.log('[CR Audit]', ts, action);
    }

    // ====== 5. 移动端 < 768px 适配 - P3 ======
    function applyMobileStyles() {
        if (!CR.isMobile) return;
        var style = document.createElement('style');
        style.textContent =
            '@media (max-width: 767px) { ' +
            '.grid-cols-12 { grid-template-columns: 1fr !important; } ' +
            '.grid-cols-7, .grid-cols-5, .grid-cols-8, .grid-cols-4 { grid-column: span 12 / span 12 !important; } ' +
            '.col-span-7, .col-span-5, .col-span-8, .col-span-4 { grid-column: span 12 / span 12 !important; } ' +
            '.col-span-3, .col-span-2, .col-span-1 { grid-column: span 6 / span 6 !important; } ' +
            '.flex.items-center.gap-3, .flex.items-center.gap-4 { flex-wrap: wrap; } ' +
            '[role="dialog"], .modal-overlay { position: fixed !important; inset: 0 !important; max-width: 100vw !important; max-height: 100vh !important; } ' +
            '}';
        document.head.appendChild(style);
    }

    // ====== 6. 键盘可达 / ARIA 标签补全 - P2 ======
    function applyARIA() {
        // 主按钮加 role="button" + tabindex + focus:ring (CSS via class)
        document.querySelectorAll('[data-cr-action]').forEach(function (el) {
            if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '0');
            if (!el.hasAttribute('role')) el.setAttribute('role', 'button');
            if (!el.classList.contains('focus:ring-2')) {
                el.classList.add('focus:outline-none', 'focus:ring-2', 'focus:ring-brand/30');
            }
        });
        // 风险条款卡加 region role + aria-label
        document.querySelectorAll('.clause-fatal, .clause-major, .clause-advisory, .clause-ok').forEach(function (el) {
            if (!el.hasAttribute('role')) el.setAttribute('role', 'region');
            var level = el.classList.contains('clause-fatal')
                ? '致命风险'
                : el.classList.contains('clause-major')
                    ? '重大风险'
                    : el.classList.contains('clause-advisory')
                        ? '建议风险'
                        : '合规';
            var title = el.querySelector('h5');
            var label = level + ' - ' + (title ? title.textContent.trim() : '条款');
            if (!el.hasAttribute('aria-label')) el.setAttribute('aria-label', label);
        });
        // ESC 关闭 04-negotiation 弹窗
        document.addEventListener('keydown', function (e) {
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
        openBtn.forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                if (!CR.reviewId) {
                    toast('请先审查合同, 再打开谈判策略', 'warning');
                    return;
                }
                // 拉取谈判策略
                fetch(CR.apiBase + '/negotiation', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ review_id: CR.reviewId })
                })
                    .then(function (r) {
                        return r.json();
                    })
                    .then(function (data) {
                        renderNegotiationModal(data);
                        modal.classList.remove('hidden');
                    })
                    .catch(function (err) {
                        console.error('拉取谈判策略失败:', err);
                        toast('谈判策略加载失败: ' + err.message, 'error');
                    });
            });
        });
        closeBtn.forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                modal.classList.add('hidden');
            });
        });
        // 点击 backdrop 关闭
        modal.addEventListener('click', function (e) {
            if (e.target === modal) modal.classList.add('hidden');
        });
    }

    function renderNegotiationModal(data) {
        var body = document.getElementById('cr-negotiation-modal-body');
        if (!body) return;
        var s = data.strategy || {};
        body.innerHTML =
            '' +
            '<div class="grid grid-cols-1 md:grid-cols-2 gap-4">' +
            '  <div class="bg-danger-tint rounded-md p-4 border-l-4 border-danger">' +
            '    <h5 class="font-semibold text-sm mb-2 flex items-center gap-1">' +
            '      <iconify-icon icon="mdi:flag-variant" class="text-danger"></iconify-icon> 红线条款 (建议放弃)' +
            '    </h5>' +
            '    <ul class="text-xs space-y-1">' +
            (s.walk_away_signals || ['无红线条款'])
                .map(function (x) {
                    return '<li>· ' + esc(x) + '</li>';
                })
                .join('') +
            '    </ul></div>' +
            '  <div class="bg-warning-tint rounded-md p-4 border-l-4 border-warning">' +
            '    <h5 class="font-semibold text-sm mb-2 flex items-center gap-1">' +
            '      <iconify-icon icon="mdi:strategy" class="text-warning"></iconify-icon> 立场建议 (' +
            esc(data.stance || '审查方') +
            ')' +
            '    </h5>' +
            '    <p class="text-xs leading-relaxed">' +
            esc(s.stance_specific_advice || '客观列出全部风险') +
            '</p>' +
            '  </div>' +
            '  <div class="bg-brand-tint3 rounded-md p-4 border-l-4 border-brand md:col-span-2">' +
            '    <h5 class="font-semibold text-sm mb-2 flex items-center gap-1">' +
            '      <iconify-icon icon="mdi:format-list-numbered" class="text-brand"></iconify-icon> 优先谈判条款' +
            '    </h5>' +
            '    <div class="flex flex-wrap gap-1.5">' +
            (s.priority_clauses || [])
                .map(function (p) {
                    return (
                        '<span class="text-[10px] px-2 py-0.5 bg-white border border-brand/30 text-brand rounded-sm">' +
                        esc(p) +
                        '</span>'
                    );
                })
                .join('') +
            '    </div></div>' +
            '</div>';
    }

    // ====== 8. 01-upload 提交 (调 API 上传) ======
    function initUploadSubmit() {
        var form = document.getElementById('cr-upload-form');
        if (!form) return;
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var fd = new FormData(form);
            var payload = {
                contract_type: fd.get('contract_type') || '服务合同',
                stance: CR.currentStance || fd.get('stance') || '审查方',
                contract_text: fd.get('contract_text') || '',
                fixture_id: fd.get('fixture_id') || ''
            };
            // 演示模式: 有 fixture_id 优先
            if (!payload.fixture_id && !payload.contract_text) {
                toast('请选择示例合同 (Demo 模式) 或粘贴合同文本', 'warning');
                return;
            }
            toast('正在审查合同 (P95 < 2s)...', 'info');
            fetch(CR.apiBase + '/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
                .then(function (r) {
                    return r.json();
                })
                .then(function (data) {
                    if (data.detail) throw new Error(data.detail);
                    CR.reviewId = data.review_id;
                    toast('审查完成! (耗时 ' + data.latency_ms + 'ms), 跳转结果页', 'success');
                    appendAudit('完成审查 review_id=' + data.review_id + ', demo=' + data.demo_mode);
                    setTimeout(function () {
                        if (typeof window.switchView === 'function') {
                            window.switchView('contract-review-result');
                        }
                    }, 500);
                })
                .catch(function (err) {
                    console.error('上传失败:', err);
                    toast('审查失败: ' + err.message, 'error');
                });
        });
    }

    // ====== 9. 加载 fixtures 列表 (01-upload 下拉) ======
    function loadFixtures() {
        fetch(CR.apiBase + '/fixtures')
            .then(function (r) {
                return r.json();
            })
            .then(function (data) {
                CR.fixtures = data.fixtures || [];
                var sel = document.getElementById('cr-fixture-select');
                if (sel) {
                    sel.innerHTML =
                        '<option value="">— 选择示例合同 (Demo 模式) —</option>' +
                        CR.fixtures
                            .map(function (f) {
                                return (
                                    '<option value="' +
                                    esc(f.fixture_id) +
                                    '">' +
                                    esc(f.contract_type) +
                                    ' · ' +
                                    esc(f.contract_title) +
                                    ' · ' +
                                    esc(f.risk_hint) +
                                    '</option>'
                                );
                            })
                            .join('');
                }
            })
            .catch(function (err) {
                console.warn('fixtures 加载失败 (后端可能未起):', err);
            });
    }

    // ====== 10. 05-export 导出按钮 ======
    function initExportButtons() {
        var btns = document.querySelectorAll('[data-cr-export]');
        btns.forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                var fmt = btn.getAttribute('data-cr-export');
                if (!CR.reviewId) {
                    toast('请先审查合同', 'warning');
                    return;
                }
                fetch(CR.apiBase + '/export', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ review_id: CR.reviewId, format: fmt })
                })
                    .then(function (r) {
                        return r.json();
                    })
                    .then(function (data) {
                        if (data.detail) throw new Error(data.detail);
                        // 触发下载
                        var blob = new Blob([data.content], { type: data.media_type });
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
                    .catch(function (err) {
                        console.error('导出失败:', err);
                        toast('导出失败: ' + err.message, 'error');
                    });
            });
        });
    }

    // ============================================================
    // 规则引擎 - 文本审查 & 风险分级展示
    // ============================================================

    // 风险等级颜色映射
    var SEVERITY_COLORS = {
        high: { bg: 'bg-danger', text: 'text-danger', tint: 'bg-danger-tint', border: 'border-danger', label: '高危' },
        medium: {
            bg: 'bg-warning',
            text: 'text-warning',
            tint: 'bg-warning-tint',
            border: 'border-warning',
            label: '中危'
        },
        low: {
            bg: 'bg-yellow-500',
            text: 'text-yellow-600',
            tint: 'bg-yellow-50',
            border: 'border-yellow-400',
            label: '低危'
        },
        info: { bg: 'bg-brand', text: 'text-brand', tint: 'bg-brand-tint', border: 'border-brand', label: '提示' }
    };

    var RISK_LEVEL_COLORS = {
        safe: {
            bg: 'bg-green-500',
            text: 'text-green-600',
            tint: 'bg-green-50',
            border: 'border-green-400',
            label: '安全'
        },
        low: {
            bg: 'bg-blue-500',
            text: 'text-blue-600',
            tint: 'bg-blue-50',
            border: 'border-blue-400',
            label: '低风险'
        },
        medium: {
            bg: 'bg-orange-500',
            text: 'text-orange-600',
            tint: 'bg-orange-50',
            border: 'border-orange-400',
            label: '中风险'
        },
        high: { bg: 'bg-red-500', text: 'text-red-600', tint: 'bg-red-50', border: 'border-red-400', label: '高风险' }
    };

    // ====== 文本审查提交 ======
    function initTextReview() {
        var form = document.getElementById('cr-text-review-form');
        if (!form) return;

        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var textarea = form.querySelector('textarea[name="contract_text"]');
            var typeSelect = form.querySelector('select[name="contract_type"]');
            var text = textarea ? textarea.value : '';
            var type = typeSelect ? typeSelect.value : '其他';

            if (!text || text.trim().length < 10) {
                toast('请输入至少 10 个字的合同文本', 'warning');
                return;
            }

            runTextReview(text, type);
        });
    }

    function runTextReview(contractText, contractType) {
        CR.ruleEngine.isLoading = true;
        CR.ruleEngine.currentContractText = contractText;
        CR.ruleEngine.currentContractType = contractType;
        CR.ruleEngine.reviewResult = null;

        showReviewLoading();

        var api = typeof API !== 'undefined' && API.contractReview ? API.contractReview : null;

        if (api) {
            api.reviewText(contractText, contractType, { stance: CR.currentStance })
                .then(function (res) {
                    CR.ruleEngine.isLoading = false;
                    if (res.ok && res.data) {
                        CR.ruleEngine.reviewResult = res.data;
                        renderReviewResult(res.data);
                        toast('审查完成！发现 ' + res.data.match_count + ' 个风险点', 'success');
                        appendAudit('规则引擎审查完成，风险点=' + res.data.match_count);
                    } else {
                        hideReviewLoading();
                        toast('审查失败: ' + (res.data && res.data.detail ? res.data.detail : '未知错误'), 'error');
                    }
                })
                .catch(function (err) {
                    CR.ruleEngine.isLoading = false;
                    hideReviewLoading();
                    console.error('文本审查失败:', err);
                    toast('审查失败: ' + err.message, 'error');
                });
        } else {
            // 兼容旧版，用 fetch
            fetch(CR.apiBase + '/review-text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contract_text: contractText,
                    contract_type: contractType,
                    stance: CR.currentStance
                })
            })
                .then(function (r) {
                    return r.json();
                })
                .then(function (data) {
                    CR.ruleEngine.isLoading = false;
                    if (data.detail) throw new Error(data.detail);
                    CR.ruleEngine.reviewResult = data;
                    renderReviewResult(data);
                    toast('审查完成！发现 ' + data.match_count + ' 个风险点', 'success');
                    appendAudit('规则引擎审查完成，风险点=' + data.match_count);
                })
                .catch(function (err) {
                    CR.ruleEngine.isLoading = false;
                    hideReviewLoading();
                    console.error('文本审查失败:', err);
                    toast('审查失败: ' + err.message, 'error');
                });
        }
    }

    function showReviewLoading() {
        var container = document.getElementById('cr-review-result-container');
        if (!container) return;
        container.innerHTML =
            '<div class="flex flex-col items-center justify-center py-16">' +
            '  <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-brand mb-4"></div>' +
            '  <p class="text-fg-secondary text-sm">正在分析合同条款...</p>' +
            '</div>';
    }

    function hideReviewLoading() {
        var container = document.getElementById('cr-review-result-container');
        if (!container) return;
        container.innerHTML = '';
    }

    // ====== 渲染审查结果 ======
    function renderReviewResult(data) {
        var container = document.getElementById('cr-review-result-container');
        if (!container) return;

        var summary = data.risk_summary || {};
        var viz = data.visualization || {};
        var riskLevel = summary.risk_level || 'low';
        var levelInfo = RISK_LEVEL_COLORS[riskLevel] || RISK_LEVEL_COLORS.low;

        var html =
            // 风险总览卡片
            '<div class="cr-risk-overview mb-6">' +
            '  <div class="bg-white rounded-lg shadow-card p-6 border border-bg-border">' +
            '    <div class="flex flex-wrap items-start justify-between gap-4 mb-6">' +
            '      <div class="flex items-center gap-4">' +
            '        <div class="w-20 h-20 rounded-full flex items-center justify-center ' +
            levelInfo.tint +
            ' border-2 ' +
            levelInfo.border +
            '">' +
            '          <span class="text-2xl font-bold ' +
            levelInfo.text +
            '">' +
            (summary.total_score || 0) +
            '</span>' +
            '        </div>' +
            '        <div>' +
            '          <div class="flex items-center gap-2 mb-1">' +
            '            <span class="px-3 py-1 rounded-full text-white text-sm font-semibold ' +
            levelInfo.bg +
            '">' +
            (summary.risk_level_name || levelInfo.label) +
            '            </span>' +
            '            <span class="text-fg-tertiary text-xs">综合风险评分</span>' +
            '          </div>' +
            '          <p class="text-fg-secondary text-sm">共发现 <span class="font-semibold text-fg-primary">' +
            data.match_count +
            '</span> 个风险点</p>' +
            '        </div>' +
            '      </div>' +
            '      <div class="flex gap-2">' +
            '        <button id="cr-export-report-btn" class="px-4 py-2 text-sm bg-white border border-bg-border rounded hover:bg-bg-secondary transition-colors">' +
            '          <iconify-icon icon="mdi:download" class="mr-1"></iconify-icon>导出报告' +
            '        </button>' +
            '        <button id="cr-rules-btn" class="px-4 py-2 text-sm bg-brand text-white rounded hover:bg-brand-dark transition-colors">' +
            '          <iconify-icon icon="mdi:cog" class="mr-1"></iconify-icon>规则管理' +
            '        </button>' +
            '      </div>' +
            '    </div>' +
            // 风险等级数量统计
            '    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">' +
            renderSeverityStat('high', summary.high_count || 0) +
            renderSeverityStat('medium', summary.medium_count || 0) +
            renderSeverityStat('low', summary.low_count || 0) +
            renderSeverityStat('info', summary.info_count || 0) +
            '    </div>' +
            // 风险分布图表
            '    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">' +
            '      <div class="bg-bg-secondary/50 rounded-lg p-4">' +
            '        <h5 class="font-semibold text-sm mb-3 text-fg-primary">风险等级分布</h5>' +
            renderSeverityBarChart(viz.severity_chart) +
            '      </div>' +
            '      <div class="bg-bg-secondary/50 rounded-lg p-4">' +
            '        <h5 class="font-semibold text-sm mb-3 text-fg-primary">分类分布</h5>' +
            renderCategoryBarChart(viz.category_chart) +
            '      </div>' +
            '    </div>' +
            '  </div>' +
            '</div>' +
            // 优先修改清单
            '<div class="cr-priority-list mb-6">' +
            '  <div class="bg-white rounded-lg shadow-card border border-bg-border overflow-hidden">' +
            '    <div class="px-6 py-4 border-b border-bg-border flex items-center justify-between">' +
            '      <h3 class="font-semibold text-fg-primary flex items-center gap-2">' +
            '        <iconify-icon icon="mdi:alert-circle" class="text-danger"></iconify-icon>' +
            '        优先修改清单' +
            '      </h3>' +
            '      <button id="cr-apply-all-fix-btn" class="text-sm text-brand hover:underline">' +
            '        <iconify-icon icon="mdi:auto-fix" class="mr-1"></iconify-icon>一键修复' +
            '      </button>' +
            '    </div>' +
            '    <div class="divide-y divide-bg-border">' +
            renderPriorityList(data.priority_list || []) +
            '    </div>' +
            '  </div>' +
            '</div>' +
            // 按分类的审查结果列表（可折叠）
            '<div class="cr-category-results">' +
            renderCategoryResults(data.matches || []) +
            '</div>';

        container.innerHTML = html;

        // 绑定事件
        bindReviewResultEvents();
    }

    function renderSeverityStat(severity, count) {
        var info = SEVERITY_COLORS[severity] || SEVERITY_COLORS.info;
        return (
            '<div class="bg-white rounded-lg border border-bg-border p-4 text-center">' +
            '  <div class="text-3xl font-bold ' +
            info.text +
            ' mb-1">' +
            count +
            '</div>' +
            '  <div class="text-xs text-fg-tertiary">' +
            info.label +
            '</div>' +
            '</div>'
        );
    }

    function renderSeverityBarChart(chartData) {
        if (!chartData || !chartData.labels || chartData.labels.length === 0) {
            return '<p class="text-fg-tertiary text-sm text-center py-4">暂无数据</p>';
        }

        var max = Math.max.apply(null, chartData.values);
        if (max === 0) max = 1;

        var colorMap = {
            高危: 'bg-danger',
            中危: 'bg-warning',
            低危: 'bg-yellow-500',
            提示: 'bg-brand'
        };

        var bars = '';
        for (var i = 0; i < chartData.labels.length; i++) {
            var label = chartData.labels[i];
            var value = chartData.values[i];
            var pct = Math.round((value / max) * 100);
            var color = colorMap[label] || 'bg-brand';
            bars +=
                '<div class="mb-3 last:mb-0">' +
                '  <div class="flex justify-between text-xs mb-1">' +
                '    <span class="text-fg-secondary">' +
                label +
                '</span>' +
                '    <span class="text-fg-tertiary">' +
                value +
                '</span>' +
                '  </div>' +
                '  <div class="h-2 bg-bg-border rounded-full overflow-hidden">' +
                '    <div class="h-full ' +
                color +
                ' rounded-full transition-all" style="width: ' +
                pct +
                '%"></div>' +
                '  </div>' +
                '</div>';
        }

        return bars;
    }

    function renderCategoryBarChart(chartData) {
        if (!chartData || !chartData.labels || chartData.labels.length === 0) {
            return '<p class="text-fg-tertiary text-sm text-center py-4">暂无数据</p>';
        }

        var max = Math.max.apply(null, chartData.values);
        if (max === 0) max = 1;

        var bars = '';
        for (var i = 0; i < chartData.labels.length; i++) {
            var label = chartData.labels[i];
            var value = chartData.values[i];
            var pct = Math.round((value / max) * 100);
            bars +=
                '<div class="mb-3 last:mb-0">' +
                '  <div class="flex justify-between text-xs mb-1">' +
                '    <span class="text-fg-secondary">' +
                label +
                '</span>' +
                '    <span class="text-fg-tertiary">' +
                value +
                '</span>' +
                '  </div>' +
                '  <div class="h-2 bg-bg-border rounded-full overflow-hidden">' +
                '    <div class="h-full bg-brand rounded-full transition-all" style="width: ' +
                pct +
                '%"></div>' +
                '  </div>' +
                '</div>';
        }

        return bars;
    }

    function renderPriorityList(priorityList) {
        if (!priorityList || priorityList.length === 0) {
            return '<div class="p-4 text-center text-fg-tertiary text-sm">暂无优先修改项</div>';
        }

        var html = '';
        priorityList.slice(0, 10).forEach(function (item, idx) {
            var sevInfo = SEVERITY_COLORS[item.severity] || SEVERITY_COLORS.info;
            html +=
                '<div class="p-4 hover:bg-bg-secondary/30 transition-colors">' +
                '  <div class="flex items-start gap-3">' +
                '    <div class="flex-shrink-0 w-6 h-6 rounded-full ' +
                sevInfo.bg +
                ' text-white text-xs font-bold flex items-center justify-center">' +
                (idx + 1) +
                '    </div>' +
                '    <div class="flex-1 min-w-0">' +
                '      <div class="flex items-center gap-2 mb-1">' +
                '        <span class="text-sm font-medium text-fg-primary truncate">' +
                esc(item.rule_name) +
                '</span>' +
                '        <span class="px-1.5 py-0.5 text-[10px] rounded ' +
                sevInfo.tint +
                ' ' +
                sevInfo.text +
                ' font-medium">' +
                (item.severity_name || sevInfo.label) +
                '        </span>' +
                '        <span class="text-[10px] text-fg-tertiary">' +
                esc(item.category_name || '') +
                '</span>' +
                '      </div>' +
                '      <p class="text-xs text-fg-secondary line-clamp-2 mb-2">' +
                esc(item.problem_description || '') +
                '</p>' +
                '      <div class="flex items-center gap-2">' +
                '        <button class="cr-copy-suggestion text-[11px] text-brand hover:underline" data-suggestion="' +
                esc(item.modification_suggestion || '') +
                '">' +
                '          <iconify-icon icon="mdi:content-copy" class="mr-0.5"></iconify-icon>复制建议' +
                '        </button>' +
                '        <button class="cr-view-detail text-[11px] text-fg-tertiary hover:text-fg-secondary">' +
                '          查看详情 →' +
                '        </button>' +
                '      </div>' +
                '    </div>' +
                '  </div>' +
                '</div>';
        });

        return html;
    }

    function renderCategoryResults(matches) {
        // 按分类分组
        var groups = {};
        matches.forEach(function (m) {
            var cat = m.category_name || m.category || '其他';
            if (!groups[cat]) groups[cat] = [];
            groups[cat].push(m);
        });

        var html = '';
        var catOrder = Object.keys(groups);

        catOrder.forEach(function (catName, idx) {
            var group = groups[catName];
            var isOpen = idx === 0; // 第一个默认展开

            // 统计该分类的风险等级
            var sevCounts = { high: 0, medium: 0, low: 0, info: 0 };
            group.forEach(function (m) {
                var sev = m.severity || 'info';
                if (sevCounts[sev] !== undefined) sevCounts[sev]++;
            });

            html +=
                '<div class="bg-white rounded-lg shadow-card border border-bg-border overflow-hidden mb-4 last:mb-0">' +
                '  <button class="cr-category-toggle w-full px-6 py-4 flex items-center justify-between hover:bg-bg-secondary/30 transition-colors" data-category="' +
                esc(catName) +
                '" aria-expanded="' +
                isOpen +
                '">' +
                '    <div class="flex items-center gap-3">' +
                '      <iconify-icon icon="mdi:folder-outline" class="text-brand text-lg"></iconify-icon>' +
                '      <span class="font-semibold text-fg-primary">' +
                esc(catName) +
                '</span>' +
                '      <span class="text-xs text-fg-tertiary bg-bg-secondary px-2 py-0.5 rounded-full">' +
                group.length +
                ' 项</span>' +
                '      <div class="flex gap-1 ml-2">' +
                (sevCounts.high > 0 ? '<span class="w-2 h-2 rounded-full bg-danger" title="高危"></span>' : '') +
                (sevCounts.medium > 0 ? '<span class="w-2 h-2 rounded-full bg-warning" title="中危"></span>' : '') +
                (sevCounts.low > 0 ? '<span class="w-2 h-2 rounded-full bg-yellow-500" title="低危"></span>' : '') +
                (sevCounts.info > 0 ? '<span class="w-2 h-2 rounded-full bg-brand" title="提示"></span>' : '') +
                '      </div>' +
                '    </div>' +
                '    <iconify-icon icon="mdi:chevron-down" class="text-fg-tertiary transition-transform ' +
                (isOpen ? 'rotate-180' : '') +
                ' cr-category-icon"></iconify-icon>' +
                '  </button>' +
                '  <div class="cr-category-content ' +
                (isOpen ? '' : 'hidden') +
                '" data-category-content="' +
                esc(catName) +
                '">' +
                '    <div class="border-t border-bg-border divide-y divide-bg-border">' +
                group.map(renderMatchItem).join('') +
                '    </div>' +
                '  </div>' +
                '</div>';
        });

        return html;
    }

    function renderMatchItem(match) {
        var sevInfo = SEVERITY_COLORS[match.severity] || SEVERITY_COLORS.info;
        return (
            '<div class="p-4 hover:bg-bg-secondary/20 transition-colors cr-match-item" data-rule-id="' +
            esc(match.rule_id || '') +
            '">' +
            '  <div class="flex items-start gap-3">' +
            '    <div class="flex-shrink-0 mt-0.5">' +
            '      <span class="w-2 h-2 rounded-full ' +
            sevInfo.bg +
            ' inline-block"></span>' +
            '    </div>' +
            '    <div class="flex-1 min-w-0">' +
            '      <div class="flex items-center gap-2 mb-2 flex-wrap">' +
            '        <span class="text-sm font-medium text-fg-primary">' +
            esc(match.rule_name || '') +
            '</span>' +
            '        <span class="px-2 py-0.5 text-[10px] rounded font-medium ' +
            sevInfo.tint +
            ' ' +
            sevInfo.text +
            '">' +
            (match.severity_name || sevInfo.label) +
            '        </span>' +
            '      </div>' +
            // 原文
            (match.original_text
                ? '<div class="mb-2 p-2 bg-bg-secondary/50 rounded text-xs text-fg-secondary font-mono break-all">' +
                  '  <span class="text-fg-tertiary text-[10px] block mb-1">原文:</span>' +
                  esc(match.original_text) +
                  '</div>'
                : '') +
            // 问题描述
            '      <p class="text-xs text-fg-secondary mb-2">' +
            esc(match.problem_description || '') +
            '</p>' +
            // 修改建议
            (match.modification_suggestion
                ? '<div class="p-3 bg-green-50 border border-green-200 rounded mb-2">' +
                  '  <div class="flex items-center gap-1 mb-1">' +
                  '    <iconify-icon icon="mdi:lightbulb-on" class="text-green-600 text-xs"></iconify-icon>' +
                  '    <span class="text-xs font-medium text-green-700">修改建议</span>' +
                  '  </div>' +
                  '  <p class="text-xs text-green-800">' +
                  esc(match.modification_suggestion) +
                  '</p>' +
                  '</div>'
                : '') +
            // 操作按钮
            '      <div class="flex items-center gap-3 mt-2">' +
            (match.one_click_fix
                ? '<button class="cr-one-click-fix text-xs text-brand hover:underline flex items-center gap-1" data-fix="' +
                  esc(match.one_click_fix || '') +
                  '">' +
                  '  <iconify-icon icon="mdi:auto-fix"></iconify-icon>一键修复' +
                  '</button>'
                : '') +
            '        <button class="cr-copy-suggestion text-xs text-fg-tertiary hover:text-fg-secondary flex items-center gap-1" data-suggestion="' +
            esc(match.modification_suggestion || '') +
            '">' +
            '          <iconify-icon icon="mdi:content-copy"></iconify-icon>复制建议' +
            '        </button>' +
            (match.legal_basis && match.legal_basis.length > 0
                ? '<button class="cr-legal-basis-toggle text-xs text-fg-tertiary hover:text-fg-secondary flex items-center gap-1">' +
                  '  <iconify-icon icon="mdi:scale-balance"></iconify-icon>法律依据' +
                  '  <iconify-icon icon="mdi:chevron-down" class="text-[10px]"></iconify-icon>' +
                  '</button>'
                : '') +
            '      </div>' +
            // 法律依据（可折叠）
            (match.legal_basis && match.legal_basis.length > 0
                ? '<div class="cr-legal-basis-content hidden mt-2 p-2 bg-blue-50 rounded text-xs text-blue-800">' +
                  '  <div class="font-medium mb-1">相关法律依据:</div>' +
                  '  <ul class="list-disc list-inside space-y-0.5">' +
                  match.legal_basis
                      .map(function (b) {
                          return '<li>' + esc(b) + '</li>';
                      })
                      .join('') +
                  '  </ul>' +
                  '</div>'
                : '') +
            '    </div>' +
            '  </div>' +
            '</div>'
        );
    }

    function bindReviewResultEvents() {
        // 分类折叠/展开
        document.querySelectorAll('.cr-category-toggle').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var cat = btn.getAttribute('data-category');
                var content = document.querySelector('[data-category-content="' + cat + '"]');
                var icon = btn.querySelector('.cr-category-icon');
                var isOpen = btn.getAttribute('aria-expanded') === 'true';

                if (isOpen) {
                    content.classList.add('hidden');
                    icon.classList.remove('rotate-180');
                    btn.setAttribute('aria-expanded', 'false');
                } else {
                    content.classList.remove('hidden');
                    icon.classList.add('rotate-180');
                    btn.setAttribute('aria-expanded', 'true');
                }
            });
        });

        // 复制建议
        document.querySelectorAll('.cr-copy-suggestion').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                var text = btn.getAttribute('data-suggestion');
                if (text) {
                    copyToClipboard(text);
                    toast('已复制修改建议', 'success');
                }
            });
        });

        // 法律依据展开
        document.querySelectorAll('.cr-legal-basis-toggle').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                var item = btn.closest('.cr-match-item');
                var content = item.querySelector('.cr-legal-basis-content');
                if (content) {
                    content.classList.toggle('hidden');
                }
            });
        });

        // 一键修复（单条）
        document.querySelectorAll('.cr-one-click-fix').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                toast('单条一键修复功能开发中...', 'info');
            });
        });

        // 导出报告按钮
        var exportBtn = document.getElementById('cr-export-report-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', function () {
                exportRuleEngineReport();
            });
        }

        // 规则管理按钮
        var rulesBtn = document.getElementById('cr-rules-btn');
        if (rulesBtn) {
            rulesBtn.addEventListener('click', function () {
                openRulesModal();
            });
        }

        // 一键修复全部
        var applyAllBtn = document.getElementById('cr-apply-all-fix-btn');
        if (applyAllBtn) {
            applyAllBtn.addEventListener('click', function () {
                applyAllFixes();
            });
        }
    }

    function copyToClipboard(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).catch(function () {
                fallbackCopy(text);
            });
        } else {
            fallbackCopy(text);
        }
    }

    function fallbackCopy(text) {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try {
            document.execCommand('copy');
        } catch (e) {
            console.warn('复制失败:', e);
        }
        document.body.removeChild(ta);
    }

    // ====== 导出规则引擎报告 ======
    function exportRuleEngineReport() {
        var result = CR.ruleEngine.reviewResult;
        if (!result) {
            toast('请先进行审查', 'warning');
            return;
        }

        var summary = result.risk_summary || {};
        var matches = result.matches || [];

        // 生成 Markdown 报告
        var md = '# 合同审查报告\n\n';
        md += '## 一、风险概览\n\n';
        md += '- **风险等级**: ' + (summary.risk_level_name || '未知') + '\n';
        md += '- **综合评分**: ' + (summary.total_score || 0) + ' 分\n';
        md += '- **风险点总数**: ' + (result.match_count || 0) + ' 个\n';
        md += '- **高危**: ' + (summary.high_count || 0) + ' 个\n';
        md += '- **中危**: ' + (summary.medium_count || 0) + ' 个\n';
        md += '- **低危**: ' + (summary.low_count || 0) + ' 个\n';
        md += '- **提示**: ' + (summary.info_count || 0) + ' 个\n\n';

        md += '## 二、详细风险列表\n\n';

        // 按分类分组
        var groups = {};
        matches.forEach(function (m) {
            var cat = m.category_name || m.category || '其他';
            if (!groups[cat]) groups[cat] = [];
            groups[cat].push(m);
        });

        Object.keys(groups).forEach(function (cat) {
            md += '### ' + cat + '\n\n';
            groups[cat].forEach(function (m, idx) {
                md +=
                    '#### ' +
                    (idx + 1) +
                    '. ' +
                    (m.rule_name || '未知规则') +
                    ' (' +
                    (m.severity_name || m.severity) +
                    ')\n\n';
                if (m.original_text) {
                    md += '**原文**: ' + m.original_text + '\n\n';
                }
                md += '**问题描述**: ' + (m.problem_description || '无') + '\n\n';
                if (m.modification_suggestion) {
                    md += '**修改建议**: ' + m.modification_suggestion + '\n\n';
                }
                if (m.legal_basis && m.legal_basis.length > 0) {
                    md += '**法律依据**:\n';
                    m.legal_basis.forEach(function (b) {
                        md += '- ' + b + '\n';
                    });
                    md += '\n';
                }
            });
        });

        md += '---\n\n';
        md += '*本报告由 LexPrime 合同审查规则引擎自动生成，仅供参考，不构成法律意见。*\n';

        // 下载
        var blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'contract-review-report.md';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        toast('报告已导出', 'success');
        appendAudit('导出规则引擎审查报告');
    }

    // ====== 一键修复全部 ======
    function applyAllFixes() {
        var result = CR.ruleEngine.reviewResult;
        if (!result || !result.matches) {
            toast('请先进行审查', 'warning');
            return;
        }

        var api = typeof API !== 'undefined' && API.contractReview ? API.contractReview : null;

        if (api) {
            api.applyFix(CR.ruleEngine.currentContractText, result.matches, null)
                .then(function (res) {
                    if (res.ok && res.data) {
                        handleFixResult(res.data);
                    } else {
                        toast('一键修复失败', 'error');
                    }
                })
                .catch(function (err) {
                    console.error('一键修复失败:', err);
                    toast('一键修复失败: ' + err.message, 'error');
                });
        } else {
            fetch(CR.apiBase + '/apply-fix', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contract_text: CR.ruleEngine.currentContractText,
                    matches: result.matches
                })
            })
                .then(function (r) {
                    return r.json();
                })
                .then(function (data) {
                    handleFixResult(data);
                })
                .catch(function (err) {
                    console.error('一键修复失败:', err);
                    toast('一键修复失败: ' + err.message, 'error');
                });
        }
    }

    function handleFixResult(data) {
        // 显示修复结果
        var msg = '已应用 ' + data.applied_count + ' 处修复';
        if (data.skipped_count > 0) {
            msg += '，跳过 ' + data.skipped_count + ' 处';
        }
        toast(msg, 'success');
        appendAudit('一键修复: 应用=' + data.applied_count + ', 跳过=' + data.skipped_count);

        // 将修复后的文本填入文本框
        var textarea = document.querySelector('textarea[name="contract_text"]');
        if (textarea && data.fixed_text) {
            textarea.value = data.fixed_text;
            CR.ruleEngine.currentContractText = data.fixed_text;
        }
    }

    // ============================================================
    // 规则引擎可视化 - 规则列表弹窗
    // ============================================================

    function openRulesModal() {
        var modal = document.getElementById('cr-rules-modal');
        if (!modal) {
            createRulesModal();
            modal = document.getElementById('cr-rules-modal');
        }

        loadRules();
        modal.classList.remove('hidden');
    }

    function closeRulesModal() {
        var modal = document.getElementById('cr-rules-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    function createRulesModal() {
        var modal = document.createElement('div');
        modal.id = 'cr-rules-modal';
        modal.className = 'fixed inset-0 z-50 hidden items-center justify-center p-4 bg-black/50 modal-overlay';
        modal.innerHTML =
            '<div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col" role="dialog" aria-labelledby="cr-rules-modal-title">' +
            '  <div class="flex items-center justify-between px-6 py-4 border-b border-bg-border">' +
            '    <h3 id="cr-rules-modal-title" class="text-lg font-semibold text-fg-primary flex items-center gap-2">' +
            '      <iconify-icon icon="mdi:cog" class="text-brand"></iconify-icon>' +
            '      规则引擎管理' +
            '    </h3>' +
            '    <button id="cr-rules-close-btn" class="text-fg-tertiary hover:text-fg-primary p-1">' +
            '      <iconify-icon icon="mdi:close" class="text-xl"></iconify-icon>' +
            '    </button>' +
            '  </div>' +
            '  <div class="flex-1 overflow-auto p-6" id="cr-rules-content">' +
            '    <div class="flex items-center justify-center py-8">' +
            '      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>' +
            '    </div>' +
            '  </div>' +
            '</div>';

        document.body.appendChild(modal);

        // 关闭按钮
        modal.querySelector('#cr-rules-close-btn').addEventListener('click', closeRulesModal);
        modal.addEventListener('click', function (e) {
            if (e.target === modal) closeRulesModal();
        });

        // ESC 关闭
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeRulesModal();
        });
    }

    function loadRules() {
        var content = document.getElementById('cr-rules-content');
        if (!content) return;

        var api = typeof API !== 'undefined' && API.contractReview ? API.contractReview : null;

        var onSuccess = function (data) {
            CR.ruleEngine.rules = data.rules || [];
            CR.ruleEngine.categories = data.categories || [];
            CR.ruleEngine.rulesStats = data.stats || {};
            renderRulesList();
        };

        if (api) {
            api.getRules()
                .then(function (res) {
                    if (res.ok && res.data) {
                        onSuccess(res.data);
                    } else {
                        content.innerHTML = '<p class="text-danger text-center py-4">加载规则失败</p>';
                    }
                })
                .catch(function (err) {
                    console.error('加载规则失败:', err);
                    content.innerHTML =
                        '<p class="text-danger text-center py-4">加载规则失败: ' + esc(err.message) + '</p>';
                });
        } else {
            fetch(CR.apiBase + '/rules')
                .then(function (r) {
                    return r.json();
                })
                .then(function (data) {
                    onSuccess(data);
                })
                .catch(function (err) {
                    console.error('加载规则失败:', err);
                    content.innerHTML = '<p class="text-danger text-center py-4">加载规则失败</p>';
                });
        }
    }

    function renderRulesList() {
        var content = document.getElementById('cr-rules-content');
        if (!content) return;

        var stats = CR.ruleEngine.rulesStats || {};
        var categories = CR.ruleEngine.categories || [];
        var rules = CR.ruleEngine.rules || [];

        var html =
            // 统计概览
            '<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">' +
            '  <div class="bg-bg-secondary/50 rounded-lg p-4 text-center">' +
            '    <div class="text-2xl font-bold text-fg-primary mb-1">' +
            (stats.total || 0) +
            '</div>' +
            '    <div class="text-xs text-fg-tertiary">总规则数</div>' +
            '  </div>' +
            '  <div class="bg-green-50 rounded-lg p-4 text-center">' +
            '    <div class="text-2xl font-bold text-green-600 mb-1">' +
            (stats.enabled || 0) +
            '</div>' +
            '    <div class="text-xs text-fg-tertiary">已启用</div>' +
            '  </div>' +
            '  <div class="bg-gray-100 rounded-lg p-4 text-center">' +
            '    <div class="text-2xl font-bold text-gray-600 mb-1">' +
            (stats.disabled || 0) +
            '</div>' +
            '    <div class="text-xs text-fg-tertiary">已禁用</div>' +
            '  </div>' +
            '  <div class="bg-brand-tint rounded-lg p-4 text-center">' +
            '    <div class="text-2xl font-bold text-brand mb-1">' +
            categories.length +
            '</div>' +
            '    <div class="text-xs text-fg-tertiary">分类数</div>' +
            '  </div>' +
            '</div>' +
            // 分类筛选 Tab
            '<div class="flex flex-wrap gap-2 mb-4 border-b border-bg-border pb-4">' +
            '  <button class="cr-rule-cat-tab px-3 py-1.5 text-sm rounded-md bg-brand text-white" data-cat="all">全部</button>' +
            categories
                .map(function (cat) {
                    return (
                        '<button class="cr-rule-cat-tab px-3 py-1.5 text-sm rounded-md bg-bg-secondary text-fg-secondary hover:bg-bg-tertiary" data-cat="' +
                        esc(cat.value) +
                        '">' +
                        esc(cat.label) +
                        ' (' +
                        cat.count +
                        ')' +
                        '</button>'
                    );
                })
                .join('') +
            '</div>' +
            // 规则列表
            '<div class="space-y-3" id="cr-rules-list">' +
            renderRulesByCategory('all') +
            '</div>';

        content.innerHTML = html;

        // 绑定分类切换
        content.querySelectorAll('.cr-rule-cat-tab').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var cat = btn.getAttribute('data-cat');
                CR.ruleEngine.activeCategory = cat;

                // 更新 Tab 样式
                content.querySelectorAll('.cr-rule-cat-tab').forEach(function (b) {
                    b.classList.remove('bg-brand', 'text-white');
                    b.classList.add('bg-bg-secondary', 'text-fg-secondary', 'hover:bg-bg-tertiary');
                });
                btn.classList.add('bg-brand', 'text-white');
                btn.classList.remove('bg-bg-secondary', 'text-fg-secondary', 'hover:bg-bg-tertiary');

                // 更新列表
                var listEl = document.getElementById('cr-rules-list');
                if (listEl) {
                    listEl.innerHTML = renderRulesByCategory(cat);
                    bindRuleItemEvents();
                }
            });
        });

        bindRuleItemEvents();
    }

    function renderRulesByCategory(category) {
        var rules = CR.ruleEngine.rules || [];
        var filtered = rules;

        if (category !== 'all') {
            filtered = rules.filter(function (r) {
                return r.category === category;
            });
        }

        if (filtered.length === 0) {
            return '<p class="text-fg-tertiary text-center py-8">暂无规则</p>';
        }

        return filtered
            .map(function (rule) {
                var sevInfo = SEVERITY_COLORS[rule.severity] || SEVERITY_COLORS.info;
                return (
                    '<div class="bg-white border border-bg-border rounded-lg p-4 hover:shadow-md transition-shadow" data-rule-id="' +
                    esc(rule.rule_id) +
                    '">' +
                    '  <div class="flex items-start justify-between gap-4">' +
                    '    <div class="flex-1 min-w-0">' +
                    '      <div class="flex items-center gap-2 mb-2 flex-wrap">' +
                    '        <span class="font-medium text-fg-primary text-sm">' +
                    esc(rule.name) +
                    '</span>' +
                    '        <span class="px-2 py-0.5 text-[10px] rounded font-medium ' +
                    sevInfo.tint +
                    ' ' +
                    sevInfo.text +
                    '">' +
                    sevInfo.label +
                    '        </span>' +
                    '        <span class="text-[10px] text-fg-tertiary bg-bg-secondary px-2 py-0.5 rounded-full">' +
                    esc(rule.rule_id) +
                    '</span>' +
                    '      </div>' +
                    '      <p class="text-xs text-fg-secondary mb-2">' +
                    esc(rule.description || '') +
                    '</p>' +
                    '      <div class="flex items-center gap-3 text-[11px] text-fg-tertiary">' +
                    '        <span>分类: ' +
                    esc(rule.category || '') +
                    '</span>' +
                    '        <span>权重: ' +
                    (rule.weight || 1.0) +
                    '</span>' +
                    (rule.applicable_contract_types
                        ? '<span>适用: ' +
                          (Array.isArray(rule.applicable_contract_types)
                              ? rule.applicable_contract_types.join(', ')
                              : rule.applicable_contract_types) +
                          '</span>'
                        : '') +
                    '      </div>' +
                    '    </div>' +
                    '    <div class="flex-shrink-0 flex items-center gap-2">' +
                    '      <label class="relative inline-flex items-center cursor-pointer">' +
                    '        <input type="checkbox" class="sr-only peer cr-rule-toggle" ' +
                    (rule.enabled ? 'checked' : '') +
                    ' data-rule-id="' +
                    esc(rule.rule_id) +
                    '">' +
                    '        <div class="w-9 h-5 bg-bg-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[' +
                    '\'\'' +
                    '] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-brand"></div>' +
                    '      </label>' +
                    '    </div>' +
                    '  </div>' +
                    '</div>'
                );
            })
            .join('');
    }

    function bindRuleItemEvents() {
        document.querySelectorAll('.cr-rule-toggle').forEach(function (toggle) {
            toggle.addEventListener('change', function () {
                var ruleId = toggle.getAttribute('data-rule-id');
                var enabled = toggle.checked;

                var api = typeof API !== 'undefined' && API.contractReview ? API.contractReview : null;

                if (api) {
                    api.updateRule(ruleId, { enabled: enabled })
                        .then(function (res) {
                            if (res.ok && res.data && res.data.success) {
                                toast('规则已' + (enabled ? '启用' : '禁用'), 'success');
                                appendAudit((enabled ? '启用' : '禁用') + '规则: ' + ruleId);
                                // 更新本地规则状态
                                var rule = CR.ruleEngine.rules.find(function (r) {
                                    return r.rule_id === ruleId;
                                });
                                if (rule) rule.enabled = enabled;
                            } else {
                                toast('操作失败', 'error');
                                toggle.checked = !enabled; // 回滚
                            }
                        })
                        .catch(function (err) {
                            console.error('更新规则失败:', err);
                            toast('操作失败: ' + err.message, 'error');
                            toggle.checked = !enabled; // 回滚
                        });
                } else {
                    fetch(CR.apiBase + '/rules/' + ruleId, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ enabled: enabled })
                    })
                        .then(function (r) {
                            return r.json();
                        })
                        .then(function (data) {
                            if (data.success) {
                                toast('规则已' + (enabled ? '启用' : '禁用'), 'success');
                                var rule = CR.ruleEngine.rules.find(function (r) {
                                    return r.rule_id === ruleId;
                                });
                                if (rule) rule.enabled = enabled;
                            } else {
                                toast('操作失败', 'error');
                                toggle.checked = !enabled;
                            }
                        })
                        .catch(function (err) {
                            console.error('更新规则失败:', err);
                            toast('操作失败', 'error');
                            toggle.checked = !enabled;
                        });
                }
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
        // D3 W8: URL param ?test_fatals=0|3|5 注入测试用致命条款 (0/3/5 验证)
        var urlTestFatals = null;
        try {
            var sp = new URLSearchParams(window.location.search);
            var t = sp.get('test_fatals');
            if (t !== null && /^[0-9]+$/.test(t)) {
                urlTestFatals = parseInt(t, 10);
            }
        } catch (e) {
            /* ignore */
        }
        if (urlTestFatals !== null && document.getElementById('fatal-clauses-container')) {
            __testInjectFatalClauses(urlTestFatals);
        }
        initFatalCollapse();
        initAdoptButtons();
        initNegotiationModal();
        initUploadSubmit();
        initExportButtons();
        loadFixtures();
        // 规则引擎相关初始化
        initTextReview();
        // 响应窗口尺寸变化 (移动端切换)
        window.matchMedia('(max-width: 767px)').addEventListener('change', function (e) {
            CR.isMobile = e.matches;
        });
    }

    /**
     * D3 W8 测试辅助: __testInjectFatalClauses(n) - 注入 n 个致命条款到容器
     * 用于 0/3/5 三种情况验证. 不在生产路径调用.
     */
    function __testInjectFatalClauses(n) {
        var container = document.getElementById('fatal-clauses-container');
        if (!container) return;
        // 清除已有 .clause-fatal
        container.querySelectorAll('.clause-fatal').forEach(function (c) {
            c.remove();
        });
        for (var i = 0; i < n; i++) {
            var div = document.createElement('div');
            div.className = 'bg-white rounded-md shadow-card clause-fatal overflow-hidden cr-fatal-clause';
            div.setAttribute('data-fatal-index', String(i));
            div.setAttribute('data-test-injected', 'true');
            div.innerHTML =
                '<div class="px-4 py-3 border-b border-danger/20">' +
                '<span class="text-xs font-mono font-bold text-danger bg-danger-tint px-2 py-0.5 rounded">测试致命 #' +
                (i + 1) +
                '</span>' +
                '<span class="text-[10px] px-1.5 py-0.5 bg-danger text-white rounded-sm font-bold ml-2">致命</span>' +
                '</div><div class="p-4 text-xs text-fg-secondary">这是 D3 W8 测试注入的第 ' +
                (i + 1) +
                ' 个致命条款, 用于验证 ' +
                n +
                ' 致命折叠行为。</div>';
            container.appendChild(div);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

    // 全局暴露 (调试用)
    // D3 W8: 暴露 __updateStancePreview + __applyFatalCollapse + __testInjectFatalClauses 给 inline 脚本 + 测试用
    globalThis.CR = CR;
    globalThis.CR.__updateStancePreview = __updateStancePreview;
    globalThis.CR.__applyFatalCollapse = __applyFatalCollapse;
    globalThis.CR.__testInjectFatalClauses = __testInjectFatalClauses;
    globalThis.CR.__STANCE_MATRIX = STANCE_MATRIX;
    globalThis.CR.__FATAL_VISIBLE_LIMIT = FATAL_VISIBLE_LIMIT;
    // 规则引擎相关方法暴露
    globalThis.CR.runTextReview = runTextReview;
    globalThis.CR.renderReviewResult = renderReviewResult;
    globalThis.CR.openRulesModal = openRulesModal;
    globalThis.CR.exportRuleEngineReport = exportRuleEngineReport;
    globalThis.CR.applyAllFixes = applyAllFixes;
})();
