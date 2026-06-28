/*
 * LexPrime 律所版 0.1 - UI 逻辑
 * 2026-06-28
 *
 * 功能:
 * 1. 律所 dashboard 4 概念卡
 * 2. 律师列表 (含筛选)
 * 3. 快速记工时
 * 4. 最近工时记录
 *
 * 数据源:
 * - 默认: firm-data.js (mock)
 * - 可选: FastAPI 后端 (api/cases-crawler/api/main.py)
 *
 * 切换: 启动后端后, fetchFirmData() 自动 fallback
 */

(function() {
    'use strict';

    // ===== 状态 =====
    var currentFilter = 'all';
    var useApi = false;  // 是否使用 API (运行时检测)

    // ===== API 检测 =====
    function detectApi() {
        // 检查全局 API_BASE 或 window.SERVER_API
        if (typeof window.SERVER_API !== 'undefined' && window.SERVER_API) {
            return window.SERVER_API;
        }
        // 默认尝试 localhost:8000
        return 'http://localhost:8000';
    }

    async function tryFetch(path) {
        try {
            var resp = await fetch(detectApi() + path, {
                signal: AbortSignal.timeout(2000),  // 2s 超时
            });
            if (resp.ok) {
                useApi = true;
                return await resp.json();
            }
        } catch (e) {
            // API 不可用, 继续用 mock
        }
        return null;
    }

    // ===== 工具 =====
    function escapeHtml(s) {
        if (s == null) return '';
        return String(s).replace(/[&<>"']/g, function(c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    function formatMoney(n) {
        if (n == null || n === 0) return '¥0';
        return '¥' + n.toLocaleString('zh-CN');
    }

    function getRoleLabel(role) {
        var map = {
            'partner': { label: '合伙人', cls: 'bg-brand-tint text-brand' },
            'senior':  { label: '高级律师', cls: 'bg-purple-tint text-purple' },
            'lawyer':  { label: '律师', cls: 'bg-green-tint text-success' },
            'assistant': { label: '律师助理', cls: 'bg-gray-tint text-fg-tertiary' },
            'admin':   { label: '行政', cls: 'bg-amber-tint text-urgent' }
        };
        return map[role] || { label: role, cls: 'bg-gray-tint text-fg-tertiary' };
    }

    // ===== 渲染函数 =====
    function renderStats() {
        var stats = globalThis.FIRM_STATS || globalThis.MOCK_FIRM_STATS || {};
        var el = function(id, val) { var e = document.getElementById(id); if (e) e.textContent = val; };
        el('firm-stat-lawyers', stats.lawyers_total);
        el('firm-stat-lawyers-active', stats.lawyers_active);
        el('firm-stat-partners', stats.partners);
        el('firm-stat-month-hours', stats.month_hours);
        el('firm-stat-hours-growth', stats.hours_growth);
        el('firm-stat-cases', stats.cases_count);
        el('firm-stat-new-cases', stats.new_cases_week);
        el('firm-stat-billable-rate', stats.billable_rate);
    }

    function renderLawyers() {
        var container = document.getElementById('firm-lawyers-list');
        if (!container) return;

        var lawyers = globalThis.FIRM_LAWYERS || globalThis.MOCK_FIRM_LAWYERS || [];
        var filtered = currentFilter === 'all'
            ? lawyers
            : lawyers.filter(function(l) { return l.role === currentFilter; });

        if (filtered.length === 0) {
            container.innerHTML = '<div class="p-8 text-center text-fg-tertiary text-xs">'
                + '<iconify-icon class="text-3xl text-fg-disabled mb-2" icon="mdi:account-off-outline"></iconify-icon>'
                + '<p>没有匹配的律师</p></div>';
            return;
        }

        container.innerHTML = filtered.map(function(l) {
            var role = getRoleLabel(l.role);
            var activeBadge = l.is_active
                ? '<span class="w-2 h-2 rounded-full bg-success inline-block"></span> 在职'
                : '<span class="w-2 h-2 rounded-full bg-fg-disabled inline-block"></span> 离职';
            return '<div class="p-4 hover:bg-bg-subtle transition-colors cursor-pointer" onclick="openLawyerDetail(\'' + l.id + '\')">'
                + '<div class="flex items-start gap-3">'
                +   '<div class="w-10 h-10 rounded-full ' + l.avatar_color + ' text-white flex items-center justify-center text-sm font-semibold flex-shrink-0">'
                +     l.name.charAt(0)
                +   '</div>'
                +   '<div class="flex-1 min-w-0">'
                +     '<div class="flex items-center gap-2 flex-wrap">'
                +       '<h5 class="text-sm font-semibold text-fg-primary">' + escapeHtml(l.name) + '</h5>'
                +       '<span class="text-[9px] px-1.5 py-0.5 rounded ' + role.cls + ' font-medium">' + role.label + '</span>'
                +       '<span class="text-[10px] text-fg-tertiary">' + activeBadge + '</span>'
                +     '</div>'
                +     '<p class="text-[11px] text-fg-tertiary mt-0.5">' + escapeHtml(l.bio || '') + '</p>'
                +     '<div class="flex items-center gap-3 mt-2 text-[10px] text-fg-tertiary">'
                +       '<span><iconify-icon class="text-xs" icon="mdi:briefcase-outline"></iconify-icon> ' + l.cases_count + ' 案件</span>'
                +       '<span><iconify-icon class="text-xs" icon="mdi:clock-outline"></iconify-icon> ' + l.month_hours + ' h/月</span>'
                +       '<span><iconify-icon class="text-xs" icon="mdi:star-outline"></iconify-icon> ' + (l.specialties || []).join(' · ') + '</span>'
                +     '</div>'
                +   '</div>'
                +   '<iconify-icon class="text-fg-disabled text-base flex-shrink-0" icon="mdi:chevron-right"></iconify-icon>'
                + '</div>'
            + '</div>';
        }).join('');
    }

    function renderTimeEntries() {
        var tbody = document.getElementById('firm-time-entries-tbody');
        if (!tbody) return;

        var entries = globalThis.FIRM_TIME_ENTRIES || globalThis.MOCK_FIRM_TIME_ENTRIES || [];

        // 更新本月条数
        var monthCount = document.getElementById('firm-entries-month-count');
        if (monthCount) monthCount.textContent = entries.length;

        if (entries.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="p-8 text-center text-fg-tertiary text-xs">暂无工时记录</td></tr>';
            return;
        }

        var statusMap = {
            'draft': { label: '草稿', cls: 'bg-gray-tint text-fg-tertiary' },
            'submitted': { label: '已提交', cls: 'bg-amber-tint text-urgent' },
            'approved': { label: '已审核', cls: 'bg-green-tint text-success' },
            'invoiced': { label: '已开票', cls: 'bg-brand-tint text-brand' }
        };

        tbody.innerHTML = entries.map(function(e) {
            var status = statusMap[e.status] || statusMap.draft;
            var dateObj = new Date(e.date);
            var dateStr = (dateObj.getMonth() + 1) + '月' + dateObj.getDate() + '日';
            return '<tr class="hover:bg-bg-subtle transition-colors">'
                + '<td class="py-2.5 px-4 text-xs text-fg-secondary">' + dateStr + '</td>'
                + '<td class="py-2.5 px-4 text-xs text-fg-primary font-medium">' + escapeHtml(e.lawyer_name) + '</td>'
                + '<td class="py-2.5 px-4 text-xs text-fg-secondary max-w-md">'
                +   '<div class="flex items-center gap-1.5">'
                +     '<iconify-icon class="text-sm text-fg-tertiary flex-shrink-0" icon="mdi:briefcase-outline"></iconify-icon>'
                +     '<span class="truncate">' + escapeHtml(e.case_title) + '</span>'
                +   '</div>'
                +   '<p class="text-[10px] text-fg-tertiary mt-0.5 pl-5">' + escapeHtml(e.description) + '</p>'
                + '</td>'
                + '<td class="py-2.5 px-4 text-xs text-center font-semibold text-fg-primary">' + e.hours + '</td>'
                + '<td class="py-2.5 px-4 text-center">'
                +   (e.billable
                    ? '<iconify-icon class="text-base text-success" icon="mdi:check-circle"></iconify-icon>'
                    : '<iconify-icon class="text-base text-fg-disabled" icon="mdi:minus-circle-outline"></iconify-icon>')
                + '</td>'
                + '<td class="py-2.5 px-4 text-xs text-right font-semibold text-fg-primary">' + formatMoney(e.amount) + '</td>'
                + '<td class="py-2.5 px-4 text-center">'
                +   '<span class="text-[10px] px-1.5 py-0.5 rounded ' + status.cls + ' font-medium">' + status.label + '</span>'
                + '</td>'
                + '</tr>';
        }).join('');
    }

    function populateLawyerSelect() {
        var select = document.getElementById('time-entry-lawyer');
        if (!select) return;
        var lawyers = globalThis.FIRM_LAWYERS || globalThis.MOCK_FIRM_LAWYERS || [];
        select.innerHTML = '<option value="">-- 选择律师 --</option>'
            + lawyers.filter(function(l) { return l.is_active; }).map(function(l) {
                return '<option value="' + l.id + '">' + escapeHtml(l.name) + ' (' + getRoleLabel(l.role).label + ')</option>';
            }).join('');

        // 默认日期今天
        var dateInput = document.getElementById('time-entry-date');
        if (dateInput && !dateInput.value) {
            dateInput.value = new Date().toISOString().split('T')[0];
        }
    }

    function renderAll() {
        renderStats();
        renderLawyers();
        renderTimeEntries();
        populateLawyerSelect();
    }

    // ===== 交互 =====
    window.filterFirmLawyers = function(role) {
        currentFilter = role;
        renderLawyers();
    };

    window.openLawyerDetail = function(lawyerId) {
        var lawyers = globalThis.FIRM_LAWYERS || globalThis.MOCK_FIRM_LAWYERS || [];
        var l = lawyers.find(function(x) { return x.id === lawyerId; });
        if (!l) return;
        if (typeof showToast === 'function') {
            showToast('律师详情: ' + l.name + ' · ' + l.cases_count + ' 案件 · ' + l.month_hours + 'h/月 (开发中)');
        }
    };

    window.openAddLawyerModal = function() {
        if (typeof showToast === 'function') {
            showToast('添加律师功能开发中, 可通过律所管理后台操作');
        }
    };

    window.submitTimeEntry = async function() {
        var lawyerId = document.getElementById('time-entry-lawyer').value;
        var date = document.getElementById('time-entry-date').value;
        var hours = parseFloat(document.getElementById('time-entry-hours').value);
        var desc = document.getElementById('time-entry-desc').value;
        var billable = document.getElementById('time-entry-billable').checked;
        var rate = parseFloat(document.getElementById('time-entry-rate').value) || 0;

        if (!lawyerId) { if (typeof showToast === 'function') showToast('请选择律师'); return; }
        if (!date) { if (typeof showToast === 'function') showToast('请选择日期'); return; }
        if (!hours || hours <= 0) { if (typeof showToast === 'function') showToast('请输入有效工时'); return; }

        // 尝试 API
        if (useApi) {
            try {
                var resp = await fetch(detectApi() + '/api/firm/time-entries?firm_id=firm-demo-001', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        lawyer_id: lawyerId,
                        entry_date: date,
                        hours: hours,
                        description: desc,
                        billable: billable,
                        rate: rate
                    })
                });
                if (resp.ok) {
                    if (typeof showToast === 'function') showToast('✓ 工时已保存到后端');
                    return;
                }
            } catch (e) {
                // fallback to mock
            }
        }

        // Mock: 添加到内存
        var lawyers = globalThis.FIRM_LAWYERS || globalThis.MOCK_FIRM_LAWYERS || [];
        var lawyer = lawyers.find(function(x) { return x.id === lawyerId; });
        var amount = billable ? hours * rate : 0;
        var newEntry = {
            id: 'te-' + Date.now(),
            date: date,
            lawyer_id: lawyerId,
            lawyer_name: lawyer ? lawyer.name : '未知',
            case_title: '(未指定案件)',
            description: desc || '(无说明)',
            hours: hours,
            billable: billable,
            rate: rate,
            amount: amount,
            status: 'draft'
        };
        var entries = globalThis.FIRM_TIME_ENTRIES || globalThis.MOCK_FIRM_TIME_ENTRIES || [];
        entries.unshift(newEntry);
        globalThis.FIRM_TIME_ENTRIES = entries;

        if (typeof showToast === 'function') showToast('✓ 工时已保存 (mock)');

        // 清空表单 + 重新渲染
        document.getElementById('time-entry-hours').value = '';
        document.getElementById('time-entry-desc').value = '';
        document.getElementById('time-entry-rate').value = '';
        renderTimeEntries();
    };

    // ===== 自动初始化 (view 切换时) =====
    var initObserver = new MutationObserver(function() {
        var view = document.getElementById('view-firm');
        if (view && !view.classList.contains('hidden') && !view.dataset.firmInit) {
            view.dataset.firmInit = '1';
            renderAll();
        }
    });
    if (document.body) {
        initObserver.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
    }

    // ===== 双绑定 =====
    globalThis.renderFirmView = renderAll;
})();
