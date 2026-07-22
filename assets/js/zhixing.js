/**
 * 执行案件查询 - UI 逻辑
 *
 * 视图: templates/views/zhixing.html
 * 数据来源: 最高人民法院中国执行信息公开网 (mock)
 * 功能: 多条件查询 / 卡片化结果渲染 / 空态处理 / 案件状态颜色区分 / 分页 / 动画
 */

(function () {
    'use strict';

    var PAGE_SIZE = 8;
    var state = {
        filtered: [],
        results: [],
        page: 1,
        sort: 'date'
    };

    var STATUS_STYLES = {
        执行中: 'bg-gradient-to-r from-amber-50 to-amber-100 text-amber-700 border border-amber-200/50',
        已终结: 'bg-gradient-to-r from-gray-50 to-gray-100 text-gray-600 border border-gray-200/50',
        已结案: 'bg-gradient-to-r from-green-50 to-emerald-100 text-green-600 border border-green-200/50',
        终本: 'bg-gradient-to-r from-rose-50 to-pink-100 text-rose-600 border border-rose-200/50',
        终结本次执行: 'bg-gradient-to-r from-rose-50 to-pink-100 text-rose-600 border border-rose-200/50',
        失信: 'bg-gradient-to-r from-red-50 to-rose-100 text-red-600 border border-red-200/50'
    };

    var mockData = [
        {
            id: 'zx-001',
            caseNum: '(2026)京01执123号',
            name: '张三',
            idcard: '110101199001011234',
            court: '北京市第一中级人民法院',
            date: '2026-03-15',
            amount: '500,000元',
            status: '执行中',
            isShixin: false,
            caseType: '首次执行'
        },
        {
            id: 'zx-002',
            caseNum: '(2025)京02执456号',
            name: '李四',
            idcard: '110102198812120045',
            court: '北京市第二中级人民法院',
            date: '2025-11-20',
            amount: '1,200,000元',
            status: '已终结',
            isShixin: false,
            caseType: '首次执行'
        },
        {
            id: 'zx-003',
            caseNum: '(2026)京03执789号',
            name: '王五',
            idcard: '110103199503030678',
            court: '北京市第三中级人民法院',
            date: '2026-01-10',
            amount: '800,000元',
            status: '执行中',
            isShixin: true,
            caseType: '恢复执行'
        },
        {
            id: 'zx-004',
            caseNum: '(2025)沪01执021号',
            name: '赵六',
            idcard: '310101199207071234',
            court: '上海市第一中级人民法院',
            date: '2025-09-08',
            amount: '350,000元',
            status: '已结案',
            isShixin: false,
            caseType: '首次执行'
        },
        {
            id: 'zx-005',
            caseNum: '(2026)沪0115执115号',
            name: '钱七',
            idcard: '31011519890101567X',
            court: '上海市浦东新区人民法院',
            date: '2026-02-18',
            amount: '2,500,000元',
            status: '终本',
            isShixin: true,
            caseType: '首次执行'
        },
        {
            id: 'zx-006',
            caseNum: '(2026)粤01执330号',
            name: '孙八',
            idcard: '440106199410102345',
            court: '广州市中级人民法院',
            date: '2026-04-02',
            amount: '780,000元',
            status: '执行中',
            isShixin: false,
            caseType: '首次执行'
        },
        {
            id: 'zx-007',
            caseNum: '(2025)粤0304执058号',
            name: '周九',
            idcard: '440304198806063456',
            court: '深圳市中级人民法院',
            date: '2025-12-25',
            amount: '600,000元',
            status: '已结案',
            isShixin: false,
            caseType: '首次执行'
        },
        {
            id: 'zx-008',
            caseNum: '(2025)浙01执212号',
            name: '吴十',
            idcard: '330101199012124567',
            court: '杭州市中级人民法院',
            date: '2025-08-14',
            amount: '920,000元',
            status: '已终结',
            isShixin: false,
            caseType: '首次执行'
        },
        {
            id: 'zx-009',
            caseNum: '(2026)苏01执077号',
            name: '郑十一',
            idcard: '320102198705055678',
            court: '南京市中级人民法院',
            date: '2026-05-06',
            amount: '1,500,000元',
            status: '终本',
            isShixin: true,
            caseType: '恢复执行'
        },
        {
            id: 'zx-010',
            caseNum: '(2026)京0105执886号',
            name: '北京宏达科技有限公司',
            idcard: '91110105MA01ABC234',
            court: '北京市朝阳区人民法院',
            date: '2026-03-28',
            amount: '3,800,000元',
            status: '执行中',
            isShixin: true,
            caseType: '首次执行'
        },
        {
            id: 'zx-011',
            caseNum: '(2025)京0108执666号',
            name: '北京鼎盛贸易有限公司',
            idcard: '91110108MA01DEF567',
            court: '北京市海淀区人民法院',
            date: '2025-06-12',
            amount: '2,100,000元',
            status: '已结案',
            isShixin: false,
            caseType: '首次执行'
        },
        {
            id: 'zx-012',
            caseNum: '(2026)粤03执520号',
            name: '深圳创新科技有限公司',
            idcard: '91440300MA5GHI890',
            court: '深圳市中级人民法院',
            date: '2026-01-20',
            amount: '5,600,000元',
            status: '执行中',
            isShixin: false,
            caseType: '首次执行'
        }
    ];

    var $ = document.getElementById.bind(document);
    function getVal(id) {
        var el = $(id);
        return el ? el.value.trim() : '';
    }

    function getStatusBadge(status) {
        var style = STATUS_STYLES[status] || 'bg-gray-50 text-gray-600 border border-gray-200/50';
        return (
            '<span class="text-[10px] font-semibold ' +
            style +
            ' px-2.5 py-1 rounded-full flex-shrink-0 shadow-sm">' +
            Utils.escapeHtml(status) +
            '</span>'
        );
    }

    function applyFilters() {
        var name = getVal('zhixing-name');
        var idcard = getVal('zhixing-idcard');
        var statusVal = getVal('zhixing-status');
        var court = getVal('zhixing-court');
        var type = getVal('zhixing-type');

        var statusActive = statusVal && statusVal !== '全部状态';
        var courtActive = court && court !== '全部法院';
        var typeActive = type && type !== '全部类型';

        state.filtered = mockData.filter(function (item) {
            var matchName = !name || item.name.indexOf(name) >= 0 || item.idcard.indexOf(name) >= 0;
            var matchId = !idcard || item.idcard.indexOf(idcard) >= 0;
            var matchStatus = !statusActive || item.status === statusVal || (statusVal === '失信' && item.isShixin);
            var matchCourt = !courtActive || item.court.indexOf(court) >= 0;
            var matchType = !typeActive || item.caseType === type;
            return matchName && matchId && matchStatus && matchCourt && matchType;
        });
    }

    function applySort() {
        var arr = state.filtered.slice();
        if (state.sort === 'amount') {
            arr.sort(function (a, b) {
                var numA = parseFloat(String(a.amount).replace(/[^0-9.]/g, '')) || 0;
                var numB = parseFloat(String(b.amount).replace(/[^0-9.]/g, '')) || 0;
                return numB - numA;
            });
        } else if (state.sort === 'date') {
            arr.sort(function (a, b) {
                return b.date < a.date ? -1 : b.date > a.date ? 1 : 0;
            });
        }
        state.results = arr;
    }

    function renderItem(item, idx) {
        var isCompany = item.name.indexOf('公司') >= 0 || item.name.indexOf('有限') >= 0;
        var idLabel = isCompany ? '统一社会信用代码' : '身份证号';
        var shixinBadge = item.isShixin
            ? '<span class="inline-flex items-center gap-1 text-[10px] font-semibold text-red-600 bg-gradient-to-r from-red-50 to-rose-100 border border-red-200/50 px-2 py-0.5 rounded-md shadow-sm">' +
              '<iconify-icon icon="mdi:alert-decagram" class="text-[11px]"></iconify-icon> 失信被执行人' +
              '</span>'
            : '';

        return (
            '<div class="p-4 md:p-5 hover:bg-rose-50/30 transition-all duration-200 cursor-pointer group" data-animate="fade-in-up" data-stagger-group="zhixing-list" data-stagger-index="' +
            idx +
            '" data-delay="0.05" onclick="openZhixingDetail(\'' +
            item.id +
            '\')">' +
            '<div class="flex items-start gap-3 md:gap-4">' +
            '<div class="w-10 h-10 md:w-11 md:h-11 rounded-xl ' +
            (item.isShixin
                ? 'bg-gradient-to-br from-red-100 to-rose-50'
                : 'bg-gradient-to-br from-rose-100 to-orange-50') +
            ' flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform shadow-sm">' +
            '<iconify-icon class="text-lg md:text-xl ' +
            (item.isShixin ? 'text-red-500' : 'text-rose-500') +
            '" icon="mdi:gavel"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-start justify-between gap-3 mb-2">' +
            '<div class="flex-1 min-w-0">' +
            '<h3 class="text-sm md:text-base font-semibold text-fg-primary group-hover:text-rose-600 transition-colors line-clamp-1 font-mono">' +
            Utils.escapeHtml(item.caseNum) +
            '</h3>' +
            '</div>' +
            getStatusBadge(item.status) +
            '</div>' +
            '<div class="flex items-center gap-3 md:gap-4 mb-2 flex-wrap">' +
            '<span class="inline-flex items-center gap-1.5 text-xs md:text-sm text-fg-secondary font-medium">' +
            '<iconify-icon class="text-[13px] text-fg-tertiary" icon="mdi:account-outline"></iconify-icon>' +
            Utils.escapeHtml(item.name) +
            '</span>' +
            shixinBadge +
            '<span class="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 bg-bg-subtle rounded-md text-fg-secondary font-medium">' +
            Utils.escapeHtml(item.caseType) +
            '</span>' +
            '</div>' +
            '<div class="flex items-center gap-3 md:gap-5 text-[10px] md:text-xs text-fg-tertiary flex-wrap">' +
            '<span class="inline-flex items-center gap-1">' +
            '<iconify-icon class="text-[11px]" icon="mdi:domain"></iconify-icon>' +
            Utils.escapeHtml(item.court) +
            '</span>' +
            '<span class="inline-flex items-center gap-1">' +
            '<iconify-icon class="text-[11px]" icon="mdi:calendar"></iconify-icon>' +
            Utils.escapeHtml(item.date) +
            '</span>' +
            '<span class="inline-flex items-center gap-1 font-semibold text-rose-600">' +
            '<iconify-icon class="text-[11px]" icon="mdi:cash"></iconify-icon>' +
            Utils.escapeHtml(item.amount) +
            '</span>' +
            '</div>' +
            '</div>' +
            '<iconify-icon class="text-fg-disabled text-base md:text-lg opacity-0 group-hover:opacity-100 transition-all translate-x-[-4px] group-hover:translate-x-0 flex-shrink-0 mt-1" icon="mdi:chevron-right"></iconify-icon>' +
            '</div>' +
            '</div>'
        );
    }

    function renderResults() {
        var container = $('zhixing-results');
        var countEl = $('zhixing-result-count');
        var pager = $('zhixing-pagination');
        if (!container) return;

        var list = state.results;
        if (countEl) {
            countEl.textContent = '共 ' + list.length.toLocaleString() + ' 条结果';
        }

        var totalPages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
        if (state.page > totalPages) state.page = totalPages;
        if (state.page < 1) state.page = 1;

        var start = (state.page - 1) * PAGE_SIZE;
        var end = Math.min(start + PAGE_SIZE, list.length);
        var slice = list.slice(start, end);

        if (slice.length === 0) {
            container.innerHTML =
                '<div class="flex flex-col items-center justify-center py-16 px-4">' +
                '<div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-rose-50 to-red-50 flex items-center justify-center mb-4">' +
                '<iconify-icon class="text-4xl text-rose-500/60" icon="mdi:file-question-outline"></iconify-icon>' +
                '</div>' +
                '<h4 class="text-base font-semibold text-fg-primary mb-1">未查询到执行信息</h4>' +
                '<p class="text-xs text-fg-tertiary mb-4 text-center max-w-xs">请核对查询条件是否正确，或调整关键词后重试</p>' +
                '<button onclick="resetZhixing()" class="px-4 py-2 text-xs font-medium rounded-xl bg-gradient-to-r from-rose-500 to-red-500 text-white hover:shadow-md hover:shadow-rose-500/20 transition-all duration-200 hover:-translate-y-0.5 flex items-center gap-1.5">' +
                '<iconify-icon class="text-sm" icon="mdi:refresh"></iconify-icon>' +
                '重置查询' +
                '</button>' +
                '</div>';
        } else {
            container.innerHTML = slice
                .map(function (item, idx) {
                    return renderItem(item, start + idx);
                })
                .join('');
        }

        renderPagination(pager, totalPages);

        if (typeof Animations !== 'undefined' && Animations.initPageAnimations) {
            Animations.initPageAnimations(container);
        }
    }

    function renderPagination(pager, totalPages) {
        if (!pager) return;
        if (totalPages <= 1) {
            pager.innerHTML =
                '<span class="text-[10px] text-fg-tertiary">第 ' + state.page + ' / ' + totalPages + ' 页</span>';
            return;
        }

        var html = '';
        html += pageBtn(
            state.page > 1,
            '<iconify-icon icon="mdi:chevron-left"></iconify-icon>',
            state.page - 1,
            'text-fg-tertiary'
        );

        buildPageList(state.page, totalPages).forEach(function (p) {
            if (p === '...') {
                html += '<span class="text-xs text-fg-tertiary px-2">...</span>';
            } else {
                var active = p === state.page;
                html +=
                    '<button class="min-w-[32px] h-8 px-2.5 rounded-xl flex items-center justify-center text-xs font-medium ' +
                    (active
                        ? 'bg-gradient-to-r from-rose-500 to-red-500 text-white shadow-md shadow-rose-500/20'
                        : 'hover:bg-white text-fg-secondary hover:text-rose-600') +
                    ' transition-all duration-200" onclick="changeZhixingPage(' +
                    p +
                    ')">' +
                    p +
                    '</button>';
            }
        });

        html += pageBtn(
            state.page < totalPages,
            '<iconify-icon icon="mdi:chevron-right"></iconify-icon>',
            state.page + 1,
            'text-fg-tertiary'
        );

        pager.innerHTML = html;
    }

    function pageBtn(enabled, inner, target, cls) {
        if (!enabled) {
            return (
                '<button class="w-8 h-8 rounded-lg flex items-center justify-center text-xs ' +
                cls +
                ' opacity-40 cursor-not-allowed">' +
                inner +
                '</button>'
            );
        }
        return (
            '<button class="w-8 h-8 rounded-lg hover:bg-white flex items-center justify-center text-xs ' +
            cls +
            '" onclick="changeZhixingPage(' +
            target +
            ')">' +
            inner +
            '</button>'
        );
    }

    function buildPageList(current, total) {
        var window = 2;
        var set = {};
        var nums = [];
        function add(n) {
            if (n < 1 || n > total || set[n]) return;
            set[n] = true;
            nums.push(n);
        }
        add(1);
        for (var i = current - window; i <= current + window; i++) add(i);
        add(total);
        nums.sort(function (a, b) {
            return a - b;
        });

        var result = [];
        for (var j = 0; j < nums.length; j++) {
            if (j > 0 && nums[j] - nums[j - 1] > 1) result.push('...');
            result.push(nums[j]);
        }
        return result;
    }

    function renderLoading() {
        var container = $('zhixing-results');
        if (!container) return;
        container.innerHTML =
            '<div class="flex flex-col items-center justify-center py-12 px-4">' +
            '<div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-rose-50 to-red-50 flex items-center justify-center mb-3">' +
            '<iconify-icon class="text-3xl text-rose-500 animate-spin" icon="mdi:loading"></iconify-icon>' +
            '</div>' +
            '<p class="text-xs text-fg-tertiary">正在查询执行信息...</p>' +
            '</div>';
    }

    function searchZhixing() {
        renderLoading();
        setTimeout(function () {
            state.page = 1;
            applyFilters();
            applySort();
            renderResults();
            Utils.showToast('查询完成, 共 ' + state.filtered.length + ' 条结果');
        }, 800);
    }

    function hotSearchZhixing(keyword) {
        var nameInput = $('zhixing-name');
        if (nameInput) nameInput.value = keyword;
        searchZhixing();
    }

    function changeZhixingSort() {
        var sel = $('zhixing-sort');
        var label = sel ? sel.value : '立案日期';
        var map = { 立案日期: 'date', 执行标的: 'amount', 相关度: 'relevance' };
        state.sort = map[label] || 'date';
        state.page = 1;
        applySort();
        renderResults();
    }

    function changeZhixingPage(page) {
        if (page < 1) return;
        state.page = page;
        renderResults();
        var container = $('zhixing-results');
        if (container && container.scrollIntoView) {
            container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    function resetZhixing() {
        var nameEl = $('zhixing-name');
        var idcardEl = $('zhixing-idcard');
        var statusEl = $('zhixing-status');
        var courtEl = $('zhixing-court');
        var typeEl = $('zhixing-type');
        var sortEl = $('zhixing-sort');

        if (nameEl) nameEl.value = '';
        if (idcardEl) idcardEl.value = '';
        if (statusEl) statusEl.selectedIndex = 0;
        if (courtEl) courtEl.selectedIndex = 0;
        if (typeEl) typeEl.selectedIndex = 0;
        if (sortEl) sortEl.selectedIndex = 0;

        state.page = 1;
        state.sort = 'date';
        applyFilters();
        applySort();
        renderResults();
        Utils.showToast('已重置查询条件');
    }

    var _closeZhixingDetail = null;

    function openZhixingDetail(id) {
        var item = mockData.find(function (x) {
            return x.id === id;
        });
        if (!item) {
            Utils.showToast('未找到案件');
            return;
        }

        var isCompany = item.name.indexOf('公司') >= 0 || item.name.indexOf('有限') >= 0;
        var idLabel = isCompany ? '统一社会信用代码' : '身份证号';

        var content =
            '<div class="space-y-4">' +
            '<div class="relative overflow-hidden p-4 bg-gradient-to-br from-rose-50 via-red-50 to-orange-50 rounded-xl">' +
            '<div class="absolute top-0 right-0 w-32 h-32 bg-rose-200/20 rounded-full -translate-y-1/2 translate-x-1/2 blur-2xl"></div>' +
            '<div class="relative z-10">' +
            '<div class="flex items-center gap-3 mb-2">' +
            '<div class="w-12 h-12 rounded-xl bg-white/80 backdrop-blur-sm flex items-center justify-center shadow-sm">' +
            '<iconify-icon class="text-2xl text-rose-500" icon="mdi:gavel"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-center gap-2 flex-wrap">' +
            '<span class="text-sm font-bold font-mono text-fg-primary">' +
            Utils.escapeHtml(item.caseNum) +
            '</span>' +
            getStatusBadge(item.status) +
            '</div>' +
            '<p class="text-xs text-fg-tertiary mt-0.5">' +
            Utils.escapeHtml(item.court) +
            '</p>' +
            '</div>' +
            '</div>' +
            (item.isShixin
                ? '<div class="mt-2.5 p-2.5 bg-red-100/80 border border-red-200/50 rounded-lg flex items-start gap-2">' +
                  '<iconify-icon icon="mdi:alert-decagram" class="text-red-500 text-base flex-shrink-0 mt-0.5"></iconify-icon>' +
                  '<div>' +
                  '<p class="text-xs font-semibold text-red-700">失信被执行人</p>' +
                  '<p class="text-[10px] text-red-600/80">该被执行人已被纳入失信被执行人名单</p>' +
                  '</div>' +
                  '</div>'
                : '') +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3.5 bg-bg-subtle rounded-xl border border-bg-border/60 hover:border-rose-200/50 transition-colors">' +
            '<p class="text-[11px] text-fg-tertiary mb-1.5 flex items-center gap-1">' +
            '<iconify-icon class="text-xs" icon="mdi:account-outline"></iconify-icon> 被执行人' +
            '</p>' +
            '<p class="text-sm font-semibold text-fg-primary">' +
            Utils.escapeHtml(item.name) +
            '</p>' +
            '</div>' +
            '<div class="p-3.5 bg-bg-subtle rounded-xl border border-bg-border/60 hover:border-rose-200/50 transition-colors">' +
            '<p class="text-[11px] text-fg-tertiary mb-1.5 flex items-center gap-1">' +
            '<iconify-icon class="text-xs" icon="mdi:card-account-details-outline"></iconify-icon> ' +
            idLabel +
            '</p>' +
            '<p class="text-xs font-mono text-fg-primary">' +
            Utils.escapeHtml(item.idcard) +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3.5 bg-bg-subtle rounded-xl border border-bg-border/60 hover:border-rose-200/50 transition-colors">' +
            '<p class="text-[11px] text-fg-tertiary mb-1.5 flex items-center gap-1">' +
            '<iconify-icon class="text-xs" icon="mdi:domain"></iconify-icon> 执行法院' +
            '</p>' +
            '<p class="text-sm text-fg-primary font-medium">' +
            Utils.escapeHtml(item.court) +
            '</p>' +
            '</div>' +
            '<div class="p-3.5 bg-bg-subtle rounded-xl border border-bg-border/60 hover:border-rose-200/50 transition-colors">' +
            '<p class="text-[11px] text-fg-tertiary mb-1.5 flex items-center gap-1">' +
            '<iconify-icon class="text-xs" icon="mdi:calendar"></iconify-icon> 立案日期' +
            '</p>' +
            '<p class="text-sm text-fg-primary font-medium">' +
            Utils.escapeHtml(item.date) +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="p-4 bg-gradient-to-r from-rose-50 to-orange-50 rounded-xl border border-rose-100/50">' +
            '<div class="flex items-center justify-between">' +
            '<div>' +
            '<p class="text-[11px] text-rose-600/80 mb-1 flex items-center gap-1">' +
            '<iconify-icon class="text-xs" icon="mdi:cash"></iconify-icon> 执行标的' +
            '</p>' +
            '<p class="text-2xl font-bold text-rose-600 kb-tabular-nums">' +
            Utils.escapeHtml(item.amount) +
            '</p>' +
            '</div>' +
            '<div class="text-right">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">案件类型</p>' +
            '<span class="inline-flex items-center gap-1 text-[10px] px-2.5 py-1 bg-white rounded-full text-fg-secondary border border-bg-border font-medium">' +
            Utils.escapeHtml(item.caseType) +
            '</span>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '<div class="text-[11px] text-fg-tertiary flex items-center gap-1">' +
            '<iconify-icon icon="mdi:information-outline"></iconify-icon>' +
            '数据来源: 中国执行信息公开网 (最高人民法院)' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-xl hover:bg-bg transition-colors" onclick="closeZhixingDetail()">关闭</button>' +
            '<button class="h-9 px-4 text-xs text-white bg-gradient-to-r from-rose-500 to-red-500 hover:shadow-md hover:shadow-rose-500/20 rounded-xl transition-all duration-200" onclick="closeZhixingDetail()">查看关联案件</button>';

        if (_closeZhixingDetail) _closeZhixingDetail();
        _closeZhixingDetail = Utils.showModal({
            id: 'zhixing-detail-modal',
            title: '执行案件详情',
            icon: 'mdi:gavel',
            content: content,
            footer: footer,
            size: 'md'
        });
    }

    function closeZhixingDetail() {
        if (_closeZhixingDetail) {
            _closeZhixingDetail();
            _closeZhixingDetail = null;
        }
    }

    function initZhixing() {
        var view = $('view-zhixing');
        if (!view) return;
        if (view.dataset.zhixingInit) return;
        view.dataset.zhixingInit = '1';

        var inputIds = ['zhixing-name', 'zhixing-idcard'];
        inputIds.forEach(function (id) {
            var el = $(id);
            if (el) {
                el.addEventListener('keydown', function (e) {
                    if (e.key === 'Enter' || e.keyCode === 13) {
                        e.preventDefault();
                        searchZhixing();
                    }
                });
            }
        });

        state.page = 1;
        state.sort = 'date';
        applyFilters();
        applySort();
        renderResults();
    }

    globalThis.initZhixing = initZhixing;
    globalThis.searchZhixing = searchZhixing;
    globalThis.hotSearchZhixing = hotSearchZhixing;
    globalThis.changeZhixingSort = changeZhixingSort;
    globalThis.changeZhixingPage = changeZhixingPage;
    globalThis.resetZhixing = resetZhixing;
    globalThis.openZhixingDetail = openZhixingDetail;
    globalThis.closeZhixingDetail = closeZhixingDetail;
})();
