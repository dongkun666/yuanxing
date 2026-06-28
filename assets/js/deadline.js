/**
 * 法律期限计算器 (2026-06-28 Phase 3.1)
 *
 * 核心功能: 选择案件类型 + 触发事件 + 起始日期, 自动计算所有相关期限
 * 数据来源: 民事诉讼法 / 行政诉讼法 / 刑事诉讼法 / 民法典
 *
 * 注意: 实际办案请以现行法律法规和司法机关通知为准, 本工具仅作参考
 */

(function() {
    'use strict';

    // ===== 案件类型 + 触发事件定义 =====
    var CASE_TYPES = {
        'civil-first': {
            name: '民事一审',
            icon: 'mdi:gavel',
            color: 'brand',
            events: [
                { id: 'filed', name: '立案受理', hint: '法院受理案件日期' },
                { id: 'summons-served', name: '送达起诉状副本', hint: '对方收到起诉状副本的日期' },
                { id: 'judgment-served', name: '收到一审判决', hint: '收到一审判决书的日期' },
                { id: 'ruling-served', name: '收到一审裁定', hint: '收到一审裁定书的日期' }
            ]
        },
        'civil-second': {
            name: '民事二审',
            icon: 'mdi:scale-balance',
            color: 'brand',
            events: [
                { id: 'judgment-served', name: '收到二审判决', hint: '二审判决送达日期 (终审)' }
            ]
        },
        'admin': {
            name: '行政诉讼',
            icon: 'mdi:bank-outline',
            color: 'purple',
            events: [
                { id: 'knew-act', name: '知道行政行为之日', hint: '知道具体行政行为作出之日起算' },
                { id: 'received-decision', name: '收到复议决定', hint: '收到行政复议决定书的日期' }
            ]
        },
        'criminal': {
            name: '刑事案件',
            icon: 'mdi:shield-alert-outline',
            color: 'red',
            events: [
                { id: 'judgment-served', name: '收到一审判决', hint: '收到一审判决书的日期' },
                { id: 'ruling-served', name: '收到一审裁定', hint: '收到一审裁定书的日期' },
                { id: 'judgment-effective', name: '判决生效之日', hint: '判决生效的日期' }
            ]
        },
        'execution': {
            name: '申请执行',
            icon: 'mdi:file-document-check-outline',
            color: 'orange',
            events: [
                { id: 'judgment-effective', name: '判决/调解生效', hint: '生效法律文书确定的履行期届满' }
            ]
        },
        'payment-order': {
            name: '支付令',
            icon: 'mdi:cash-fast',
            color: 'orange',
            events: [
                { id: 'payment-order-served', name: '收到支付令', hint: '收到支付令的日期' }
            ]
        },
        'work-injury': {
            name: '工伤认定',
            icon: 'mdi:medical-bag',
            color: 'red',
            events: [
                { id: 'injury-date', name: '事故伤害发生之日', hint: '事故伤害发生之日 (或职业病诊断之日)' },
                { id: 'identification-decision', name: '收到工伤认定结论', hint: '收到工伤认定决定书的日期' },
                { id: 'appraisal-decision', name: '收到伤残鉴定结论', hint: '收到初次劳动能力鉴定结论的日期' }
            ]
        },
        'divorce': {
            name: '婚姻家事',
            icon: 'mdi:heart-broken',
            color: 'pink',
            events: [
                { id: 'divorce-registration', name: '离婚登记申请', hint: '民政局收到离婚登记申请之日' },
                { id: 'judgment-dismissed', name: '判决不准离婚', hint: '收到判决不准离婚的日期' }
            ]
        },
        'arbitration': {
            name: '商事仲裁',
            icon: 'mdi:scale-balance',
            color: 'indigo',
            events: [
                { id: 'award-received', name: '收到仲裁裁决', hint: '收到仲裁裁决书的日期' }
            ]
        },
        'public-notice': {
            name: '公示催告',
            icon: 'mdi:bullhorn-outline',
            color: 'warning',
            events: [
                { id: 'public-notice-published', name: '公告发布之日', hint: '法院公示催告公告发布之日' }
            ]
        }
    };

    // ===== 期限规则库 (核心算法数据) =====
    // days: 期限天数, unit: 'day'(自然日) | 'month'(月) | 'year'(年)
    // inclusive: 起算日是否计入 (民诉法起算日通常不计入, 当日到不算过期)
    // urgency: critical > 7天 / warning > 30天 / normal 其他
    var DEADLINE_RULES = [
        // ===== 民事一审 =====
        { caseType: 'civil-first', eventType: 'filed', name: '立案审批期限', days: 7, unit: 'day', legalBasis: '民诉法第126条', desc: '法院应在 7 日内决定是否立案', urgency: 'normal' },
        { caseType: 'civil-first', eventType: 'filed', name: '送达起诉状副本', days: 5, unit: 'day', legalBasis: '民诉法第128条', desc: '法院应在立案后 5 日内将副本送达被告', urgency: 'normal' },
        { caseType: 'civil-first', eventType: 'summons-served', name: '提交答辩状', days: 15, unit: 'day', legalBasis: '民诉法第128条', desc: '被告应在收到副本后 15 日内提交答辩状', urgency: 'warning' },
        { caseType: 'civil-first', eventType: 'judgment-served', name: '一审判决上诉期', days: 15, unit: 'day', legalBasis: '民诉法第171条', desc: '不服一审判决可在 15 日内提起上诉', urgency: 'critical' },
        { caseType: 'civil-first', eventType: 'ruling-served', name: '一审裁定上诉期', days: 10, unit: 'day', legalBasis: '民诉法第171条', desc: '不服一审裁定可在 10 日内提起上诉', urgency: 'critical' },
        { caseType: 'civil-first', eventType: 'judgment-served', name: '申请再审期限', days: 6, unit: 'month', legalBasis: '民诉法第211条', desc: '当事人申请再审应在判决/裁定发生法律效力后 6 个月内提出', urgency: 'warning' },

        // ===== 民事二审 =====
        { caseType: 'civil-second', eventType: 'judgment-served', name: '二审判决生效', days: 0, unit: 'day', legalBasis: '民诉法第183条', desc: '二审判决/裁定为终审裁判, 送达即生效', urgency: 'normal' },
        { caseType: 'civil-second', eventType: 'judgment-served', name: '申请再审期限', days: 6, unit: 'month', legalBasis: '民诉法第211条', desc: '二审判决生效后 6 个月内可申请再审', urgency: 'warning' },

        // ===== 行政诉讼 =====
        { caseType: 'admin', eventType: 'knew-act', name: '行政诉讼起诉期 (一般)', days: 6, unit: 'month', legalBasis: '行政诉讼法第46条第1款', desc: '知道行政行为之日起 6 个月内起诉', urgency: 'critical' },
        { caseType: 'admin', eventType: 'knew-act', name: '行政诉讼最长起诉期', days: 5, unit: 'year', legalBasis: '行政诉讼法第46条第2款', desc: '其他法律另有规定的除外, 最长不超过 5 年', urgency: 'normal' },
        { caseType: 'admin', eventType: 'received-decision', name: '复议后起诉期', days: 15, unit: 'day', legalBasis: '行政诉讼法第46条', desc: '不服复议决定的, 15 日内起诉', urgency: 'critical' },

        // ===== 刑事 =====
        { caseType: 'criminal', eventType: 'judgment-served', name: '刑事一审判决上诉期', days: 10, unit: 'day', legalBasis: '刑事诉讼法第230条', desc: '不服一审判决的, 10 日内提起上诉', urgency: 'critical' },
        { caseType: 'criminal', eventType: 'ruling-served', name: '刑事一审裁定上诉期', days: 5, unit: 'day', legalBasis: '刑事诉讼法第230条', desc: '不服一审裁定的, 5 日内提起上诉', urgency: 'critical' },
        { caseType: 'criminal', eventType: 'judgment-effective', name: '刑事申诉期限', days: 5, unit: 'year', legalBasis: '刑事诉讼法第305条', desc: '刑罚执行完毕后 5 年内可申诉 (有例外)', urgency: 'warning' },

        // ===== 申请执行 =====
        { caseType: 'execution', eventType: 'judgment-effective', name: '申请执行期限', days: 2, unit: 'year', legalBasis: '民诉法第293条', desc: '申请执行的期间为 2 年, 从法律文书规定履行期间的最后一日起算', urgency: 'critical' },

        // ===== 支付令 =====
        { caseType: 'payment-order', eventType: 'payment-order-served', name: '支付令异议期', days: 15, unit: 'day', legalBasis: '民诉法第221条', desc: '收到支付令后 15 日内清偿债务或提出书面异议', urgency: 'critical' },

        // ===== 工伤认定 =====
        { caseType: 'work-injury', eventType: 'injury-date', name: '单位申请工伤认定', days: 30, unit: 'day', legalBasis: '工伤保险条例第17条第1款', desc: '用人单位应在事故伤害发生之日 30 日内申请', urgency: 'critical' },
        { caseType: 'work-injury', eventType: 'injury-date', name: '个人/家属申请工伤认定', days: 1, unit: 'year', legalBasis: '工伤保险条例第17条第2款', desc: '用人单位未申请的, 职工本人可在 1 年内申请', urgency: 'critical' },
        { caseType: 'work-injury', eventType: 'identification-decision', name: '工伤认定复议期', days: 60, unit: 'day', legalBasis: '工伤保险条例第55条', desc: '对认定结论不服, 60 日内申请行政复议', urgency: 'warning' },
        { caseType: 'work-injury', eventType: 'appraisal-decision', name: '再次鉴定申请期', days: 15, unit: 'day', legalBasis: '工伤职工劳动能力鉴定管理办法第18条', desc: '对鉴定结论不服, 15 日内申请再次鉴定', urgency: 'critical' },

        // ===== 婚姻家事 =====
        { caseType: 'divorce', eventType: 'divorce-registration', name: '离婚冷静期', days: 30, unit: 'day', legalBasis: '民法典第1077条', desc: '自婚姻登记机关收到离婚登记申请之日起 30 日内, 任何一方不愿意离婚的可撤回', urgency: 'warning' },
        { caseType: 'divorce', eventType: 'divorce-registration', name: '离婚冷静期后领证期', days: 30, unit: 'day', legalBasis: '民法典第1077条', desc: '冷静期届满后 30 日内双方应共同申请发给离婚证, 逾期视为撤回', urgency: 'critical' },
        { caseType: 'divorce', eventType: 'judgment-dismissed', name: '再次起诉期', days: 6, unit: 'month', legalBasis: '民诉法第127条第7项', desc: '判决不准离婚后, 6 个月内无新情况/新理由再次起诉不予受理', urgency: 'warning' },

        // ===== 商事仲裁 =====
        { caseType: 'arbitration', eventType: 'award-received', name: '申请撤销仲裁裁决', days: 6, unit: 'month', legalBasis: '仲裁法第59条', desc: '当事人申请撤销裁决, 应自收到裁决书之日起 6 个月内提出', urgency: 'critical' },
        { caseType: 'arbitration', eventType: 'award-received', name: '申请执行仲裁裁决', days: 2, unit: 'year', legalBasis: '民诉法第293条', desc: '申请执行仲裁裁决, 期间为 2 年', urgency: 'critical' },

        // ===== 公示催告 =====
        { caseType: 'public-notice', eventType: 'public-notice-published', name: '申报权利期', days: 60, unit: 'day', legalBasis: '民诉法第231条', desc: '公示催告期间, 利害关系人应于公告之日起 60 日内申报', urgency: 'critical' },
        { caseType: 'public-notice', eventType: 'public-notice-published', name: '除权判决后票据灭失', days: 0, unit: 'day', legalBasis: '民诉法第234条', desc: '公示催告期满, 无人申报, 可申请除权判决, 票据失效', urgency: 'normal' }
    ];

    // ===== 状态 =====
    var currentCaseType = 'civil-first';
    var currentEventType = 'filed';

    // ===== 日期计算核心 =====
    function addDays(date, days) {
        var d = new Date(date);
        d.setDate(d.getDate() + days);
        return d;
    }

    function addMonths(date, months) {
        var d = new Date(date);
        var targetMonth = d.getMonth() + months;
        d.setMonth(targetMonth);
        // 处理月末溢出 (如 1/31 + 1 月 = 3/3 而不是 2/31)
        if (d.getMonth() !== (targetMonth % 12 + 12) % 12) {
            d.setDate(0); // 上月最后一天
        }
        return d;
    }

    function addYears(date, years) {
        var d = new Date(date);
        d.setFullYear(d.getFullYear() + years);
        return d;
    }

    function calculateDeadline(rule, baseDate) {
        var result;
        if (rule.unit === 'day') {
            // 民事诉讼法: 起算日不计入, 当日不算过期 (起算日次日为第1天)
            // 简化: 直接加 rule.days 天, 含/不含起算日通过此逻辑处理
            // 按主流理解: 从 baseDate 后一天开始算, 加 days 天 = 截止日
            // 例: 5/20 收到判决, 15天上诉期, 截止 = 5/20 + 15 = 6/4
            result = addDays(baseDate, rule.days);
        } else if (rule.unit === 'month') {
            // 自然月: 6 个月 = 6 月后同日
            result = addMonths(baseDate, rule.days);
        } else if (rule.unit === 'year') {
            result = addYears(baseDate, rule.days);
        }
        return result;
    }

    function formatDate(date) {
        var d = new Date(date);
        var y = d.getFullYear();
        var m = String(d.getMonth() + 1).padStart(2, '0');
        var dd = String(d.getDate()).padStart(2, '0');
        return y + '-' + m + '-' + dd;
    }

    function getDeadlineStatus(deadlineDate, today) {
        if (!deadlineDate) return 'unknown';
        var diffMs = new Date(deadlineDate) - today;
        var diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        if (diffDays < 0) return 'overdue';
        if (diffDays === 0) return 'today';
        if (diffDays <= 3) return 'urgent';
        if (diffDays <= 7) return 'critical';
        if (diffDays <= 30) return 'warning';
        return 'normal';
    }

    function getStatusConfig(status) {
        var map = {
            'overdue': { label: '已过期', cls: 'bg-red-100 text-red-700 border-red-200', icon: 'mdi:alert-circle', color: 'red' },
            'today': { label: '今天到期', cls: 'bg-red-100 text-red-700 border-red-200', icon: 'mdi:alarm', color: 'red' },
            'urgent': { label: '3 天内', cls: 'bg-orange-100 text-orange-700 border-orange-200', icon: 'mdi:clock-alert', color: 'orange' },
            'critical': { label: '一周内', cls: 'bg-amber-100 text-amber-700 border-amber-200', icon: 'mdi:clock', color: 'amber' },
            'warning': { label: '一月内', cls: 'bg-blue-100 text-blue-700 border-blue-200', icon: 'mdi:clock-outline', color: 'blue' },
            'normal': { label: '远期', cls: 'bg-gray-100 text-gray-600 border-gray-200', icon: 'mdi:calendar-outline', color: 'gray' },
            'unknown': { label: '未知', cls: 'bg-gray-100 text-gray-500 border-gray-200', icon: 'mdi:help', color: 'gray' }
        };
        return map[status] || map['normal'];
    }

    // ===== UI 控制 =====
    function selectDeadlineCaseType(type, btn) {
        currentCaseType = type;
        document.querySelectorAll('#deadline-case-type-chips .deadline-chip').forEach(function(c) {
            c.classList.remove('active');
        });
        if (btn) btn.classList.add('active');

        // 重新填充 event 列表
        var caseDef = CASE_TYPES[type];
        var sel = document.getElementById('deadline-event-select');
        if (sel) {
            sel.innerHTML = '';
            if (caseDef && caseDef.events) {
                caseDef.events.forEach(function(ev, i) {
                    var opt = document.createElement('option');
                    opt.value = ev.id;
                    opt.textContent = ev.name;
                    if (i === 0) currentEventType = ev.id;
                    sel.appendChild(opt);
                });
            }
            // 更新 hint
            var firstEvent = caseDef.events[0];
            var hint = document.getElementById('deadline-event-hint');
            if (hint && firstEvent) hint.textContent = firstEvent.hint;
        }

        recalculateDeadlines();
    }

    function setDeadlineDate(offset) {
        var today = new Date();
        today.setHours(0, 0, 0, 0);
        if (offset < 0) {
            today.setDate(today.getDate() + offset);
        }
        var dateStr = formatDate(today);
        var input = document.getElementById('deadline-start-date');
        if (input) input.value = dateStr;
        recalculateDeadlines();
    }

    function recalculateDeadlines() {
        var eventSel = document.getElementById('deadline-event-select');
        var dateInput = document.getElementById('deadline-start-date');
        if (!eventSel || !dateInput) return;

        currentEventType = eventSel.value;
        var baseDateStr = dateInput.value;
        var eventHint = document.getElementById('deadline-event-hint');
        var caseDef = CASE_TYPES[currentCaseType];
        if (caseDef) {
            var ev = caseDef.events.find(function(e) { return e.id === currentEventType; });
            if (eventHint && ev) eventHint.textContent = ev.hint;
        }

        if (!baseDateStr) {
            document.getElementById('deadline-empty').classList.remove('hidden');
            document.getElementById('deadline-results-list').classList.add('hidden');
            document.getElementById('deadline-results-count').textContent = '';
            return;
        }

        var baseDate = new Date(baseDateStr);
        if (isNaN(baseDate.getTime())) {
            document.getElementById('deadline-empty').classList.remove('hidden');
            document.getElementById('deadline-results-list').classList.add('hidden');
            return;
        }

        var today = new Date();
        today.setHours(0, 0, 0, 0);
        var todayHint = document.getElementById('deadline-today-hint');
        if (todayHint) todayHint.textContent = '今天: ' + formatDate(today);

        // 筛选匹配当前案件类型 + 触发事件的规则
        var matched = DEADLINE_RULES.filter(function(r) {
            return r.caseType === currentCaseType && r.eventType === currentEventType;
        });

        // 渲染
        var resultsList = document.getElementById('deadline-results-list');
        var empty = document.getElementById('deadline-empty');
        var countEl = document.getElementById('deadline-results-count');

        if (matched.length === 0) {
            empty.classList.remove('hidden');
            empty.innerHTML = '<iconify-icon class="text-4xl text-fg-disabled" icon="mdi:information-outline"></iconify-icon><p class="text-sm text-fg-tertiary mt-2">该触发事件暂无标准期限规则</p><p class="text-[10px] text-fg-disabled mt-1">请查阅具体法律法规或咨询专业人员</p>';
            resultsList.classList.add('hidden');
            if (countEl) countEl.textContent = '';
            return;
        }

        empty.classList.add('hidden');
        resultsList.classList.remove('hidden');

        // 按截止日期排序
        matched.sort(function(a, b) {
            return calculateDeadline(a, baseDate) - calculateDeadline(b, baseDate);
        });

        var html = '';
        matched.forEach(function(rule) {
            var deadline = calculateDeadline(rule, baseDate);
            var status = getDeadlineStatus(deadline, today);
            var statusCfg = getStatusConfig(status);
            var diffDays = Math.floor((deadline - today) / (1000 * 60 * 60 * 24));
            var diffText = diffDays === 0 ? '今天到期' :
                diffDays > 0 ? '还有 ' + diffDays + ' 天' :
                '已过 ' + (-diffDays) + ' 天';

            var unitText = rule.unit === 'day' ? '天' : (rule.unit === 'month' ? '个月' : '年');
            var periodText = rule.days === 0 ? '即时' : (rule.days + ' ' + unitText);

            html +=
                '<div class="border rounded-lg p-3.5 ' + statusCfg.cls + ' transition-all hover:shadow-sm">' +
                '<div class="flex items-start justify-between gap-3">' +
                '<div class="flex-1 min-w-0">' +
                '<div class="flex items-center gap-2 mb-1.5 flex-wrap">' +
                '<iconify-icon class="text-base ' + statusCfg.cls + '" style="color: currentColor;" icon="' + statusCfg.icon + '"></iconify-icon>' +
                '<span class="text-sm font-semibold">' + escapeHtml(rule.name) + '</span>' +
                '<span class="text-[10px] px-1.5 py-0.5 rounded-full bg-white/60 font-medium">' + periodText + '</span>' +
                '</div>' +
                '<p class="text-xs leading-relaxed">' + escapeHtml(rule.desc) + '</p>' +
                '<div class="flex items-center gap-2 mt-2 text-[10px] flex-wrap">' +
                '<span class="inline-flex items-center gap-0.5"><iconify-icon class="text-xs" icon="mdi:scale-balance"></iconify-icon> ' + escapeHtml(rule.legalBasis) + '</span>' +
                '<span class="text-fg-tertiary">·</span>' +
                '<span class="font-mono">' + formatDate(deadline) + '</span>' +
                '</div>' +
                '</div>' +
                '<div class="text-right flex-shrink-0">' +
                '<div class="text-base font-bold leading-none">' + diffText + '</div>' +
                '<div class="text-[10px] mt-0.5">' + statusCfg.label + '</div>' +
                '<button class="text-[10px] mt-1.5 inline-flex items-center gap-0.5 px-2 py-1 rounded bg-white/80 hover:bg-white border border-current/20 transition-colors" onclick="copyDeadlineDate(\'' + formatDate(deadline) + '\', \'' + escapeHtml(rule.name) + '\')">' +
                '<iconify-icon class="text-xs" icon="mdi:content-copy"></iconify-icon>' +
                '复制日期' +
                '</button>' +
                '</div>' +
                '</div>' +
                '</div>';
        });

        resultsList.innerHTML = html;
        if (countEl) countEl.textContent = '共 ' + matched.length + ' 项期限';
    }

    function copyDeadlineDate(date, name) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(date).then(function() {
                showToast('已复制: ' + name + ' - ' + date);
            });
        } else {
            showToast('截止: ' + date);
        }
    }

    // ===== 规则库说明渲染 =====
    function renderRuleRefs() {
        var container = document.getElementById('deadline-rule-refs');
        if (!container) return;

        // 收集所有法律依据
        var lawSet = new Set();
        DEADLINE_RULES.forEach(function(r) {
            var law = r.legalBasis.split('第')[0];
            lawSet.add(law);
        });

        var html = '';
        lawSet.forEach(function(law) {
            var count = DEADLINE_RULES.filter(function(r) { return r.legalBasis.indexOf(law) === 0; }).length;
            html +=
                '<div class="flex items-center gap-2 p-2.5 rounded-lg bg-bg-subtle/50">' +
                '<iconify-icon class="text-base text-brand flex-shrink-0" icon="mdi:book-open-variant"></iconify-icon>' +
                '<span class="flex-1 truncate">' + escapeHtml(law) + '</span>' +
                '<span class="text-[10px] text-fg-tertiary whitespace-nowrap">' + count + ' 项</span>' +
                '</div>';
        });

        container.innerHTML = html;
    }

    // ===== 初始化 =====
    function initDeadlineView() {
        // 默认日期 = 今天
        var today = new Date();
        today.setHours(0, 0, 0, 0);
        var dateInput = document.getElementById('deadline-start-date');
        if (dateInput && !dateInput.value) {
            dateInput.value = formatDate(today);
        }

        // 渲染案件类型 (默认 civil-first, 已在 HTML 中 active)
        selectDeadlineCaseType('civil-first', document.querySelector('.deadline-chip[data-type="civil-first"]'));

        // 渲染规则库说明
        renderRuleRefs();
    }

    // 当 view-deadline 变为可见时初始化
    var deadlineInitObserver = new MutationObserver(function() {
        var el = document.getElementById('view-deadline');
        if (el && !el.classList.contains('hidden') && !el.dataset.init) {
            el.dataset.init = '1';
            initDeadlineView();
        }
    });
    if (document.body) {
        deadlineInitObserver.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
    }

    // ===== 双绑定 =====
    globalThis.selectDeadlineCaseType = selectDeadlineCaseType;
    globalThis.setDeadlineDate = setDeadlineDate;
    globalThis.recalculateDeadlines = recalculateDeadlines;
    globalThis.copyDeadlineDate = copyDeadlineDate;
    globalThis.initDeadlineView = initDeadlineView;
})();