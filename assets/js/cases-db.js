/**
 * 案例数据库 - 交互模块 (2026-07-02)
 *
 * 视图: templates/views/cases-db.html
 * 功能: 多条件检索 (关键词/案由/法院/裁判年份) + 排序 (相关度/裁判日期/法院层级)
 *       + 分页 (每页 10 条) + 结果计数 + 空态 + loading + 详情
 * 依赖: showToast (script.js)
 * 暴露: initCasesDb, searchCases, changeCasesPage, openCaseDetail, changeCasesSort
 */

(function() {
    'use strict';

    // ===== Mock 案例数据集 (16 条, 覆盖 4 案由 / 4 级法院 / 4 年份) =====
    // courtLevel: 1=最高 2=高级 3=中级 4=基层
    var CASES_DB = [
        { id: 'cd-001', title: '张三与李四买卖合同纠纷一审民事判决书', court: '北京市朝阳区人民法院', courtLevel: 4, date: '2025-12-15', cause: '合同纠纷', caseType: '民事一审', summary: '原告张三与被告李四买卖合同纠纷一案，本院于2025年10月20日立案后，依法适用普通程序，公开开庭进行了审理。原告张三及其委托诉讼代理人到庭参加诉讼，被告李四经本院合法传唤无正当理由拒不到庭参加诉讼，本院依法缺席审理。本案现已审理终结。' },
        { id: 'cd-002', title: '王五与某科技公司劳动争议二审民事判决书', court: '北京市第三中级人民法院', courtLevel: 3, date: '2025-11-20', cause: '劳动争议', caseType: '民事二审', summary: '上诉人王五因与被上诉人某科技公司劳动争议一案，不服北京市朝阳区人民法院民事判决，向本院提起上诉。本院于2025年10月8日立案后，依法组成合议庭，开庭进行了审理。上诉人王五及其委托诉讼代理人、被上诉人某科技公司之委托诉讼代理人到庭参加诉讼。本案现已审理终结。' },
        { id: 'cd-003', title: '某房地产公司与某建筑公司建设工程施工合同纠纷一审民事判决书', court: '上海市第一中级人民法院', courtLevel: 3, date: '2025-10-08', cause: '合同纠纷', caseType: '民事一审', summary: '原告某房地产公司与被告某建筑公司建设工程施工合同纠纷一案，本院于2025年6月15日立案后，依法适用普通程序，公开开庭进行了审理。原告某房地产公司之委托诉讼代理人、被告某建筑公司之委托诉讼代理人均到庭参加诉讼。本案现已审理终结。' },
        { id: 'cd-004', title: '高空抛物致害责任纠纷一审民事判决书', court: '最高人民法院', courtLevel: 1, date: '2024-09-15', cause: '侵权责任纠纷', caseType: '民事一审', summary: '原告甲与被告某小区全体业主高空抛物致害责任纠纷一案，经公安机关调查难以确定具体侵权人。原告请求可能加害的建筑物使用人给予补偿。本院依法适用普通程序，公开开庭进行了审理。本案现已审理终结。' },
        { id: 'cd-005', title: '某科技公司侵害发明专利权纠纷二审民事判决书', court: '最高人民法院知识产权法庭', courtLevel: 1, date: '2024-08-22', cause: '知识产权纠纷', caseType: '民事二审', summary: '上诉人某科技公司因与被上诉人某研究院侵害发明专利权纠纷一案，不服北京知识产权法院民事判决，向本院提起上诉。本院依法组成合议庭，开庭进行了审理。上诉人某科技公司之委托诉讼代理人、被上诉人某研究院之委托诉讼代理人到庭参加诉讼。本案现已审理终结。' },
        { id: 'cd-006', title: '某贸易公司与某物流公司运输合同纠纷二审民事判决书', court: '上海市高级人民法院', courtLevel: 2, date: '2026-01-10', cause: '合同纠纷', caseType: '民事二审', summary: '上诉人某贸易公司因与被上诉人某物流公司运输合同纠纷一案，不服上海市第一中级人民法院民事判决，向本院提起上诉。本院依法组成合议庭，开庭进行了审理。上诉人某贸易公司之委托诉讼代理人、被上诉人某物流公司之委托诉讼代理人到庭参加诉讼。本案现已审理终结。' },
        { id: 'cd-007', title: '赵六与某餐饮公司劳动争议二审民事判决书', court: '北京市高级人民法院', courtLevel: 2, date: '2024-06-18', cause: '劳动争议', caseType: '民事二审', summary: '上诉人赵六因与被上诉人某餐饮公司劳动争议一案，不服北京市第二中级人民法院民事判决，向本院提起上诉。本院依法组成合议庭，开庭进行了审理。上诉人赵六及其委托诉讼代理人、被上诉人某餐饮公司之委托诉讼代理人到庭参加诉讼。本案现已审理终结。' },
        { id: 'cd-008', title: '钱七与某物业公司违反安全保障义务责任纠纷一审民事判决书', court: '北京市海淀区人民法院', courtLevel: 4, date: '2023-05-30', cause: '侵权责任纠纷', caseType: '民事一审', summary: '原告钱七与被告某物业公司违反安全保障义务责任纠纷一案，本院于2023年3月12日立案后，依法适用简易程序，公开开庭进行了审理。原告钱七、被告某物业公司之委托诉讼代理人均到庭参加诉讼。本案现已审理终结。' },
        { id: 'cd-009', title: '某服装公司与某商贸公司商标权权属纠纷一审民事判决书', court: '上海知识产权法院', courtLevel: 3, date: '2025-03-12', cause: '知识产权纠纷', caseType: '民事一审', summary: '原告某服装公司与被告某商贸公司商标权权属纠纷一案，本院于2025年1月8日立案后，依法适用普通程序，公开开庭进行了审理。原告某服装公司之委托诉讼代理人、被告某商贸公司之委托诉讼代理人均到庭参加诉讼。本案现已审理终结。' },
        { id: 'cd-010', title: '某投资公司与某担保公司借款合同纠纷二审民事判决书', court: '最高人民法院', courtLevel: 1, date: '2023-11-25', cause: '合同纠纷', caseType: '民事二审', summary: '上诉人某投资公司因与被上诉人某担保公司借款合同纠纷一案，不服北京市高级人民法院民事判决，向本院提起上诉。本院依法组成合议庭，开庭进行了审理。上诉人某投资公司之委托诉讼代理人、被上诉人某担保公司之委托诉讼代理人到庭参加诉讼。本案现已审理终结。' },
        { id: 'cd-011', title: '孙八与某互联网公司竞业限制纠纷一审民事判决书', court: '上海市浦东新区人民法院', courtLevel: 4, date: '2026-02-14', cause: '劳动争议', caseType: '民事一审', summary: '原告孙八与被告某互联网公司竞业限制纠纷一案，本院于2025年12月20日立案后，依法适用简易程序，公开开庭进行了审理。原告孙八、被告某互联网公司之委托诉讼代理人均到庭参加诉讼。本案现已审理终结。' },
        { id: 'cd-012', title: '周九与某保险公司机动车交通事故责任纠纷二审民事判决书', court: '上海市高级人民法院', courtLevel: 2, date: '2025-07-08', cause: '侵权责任纠纷', caseType: '民事二审', summary: '上诉人周九因与被上诉人某保险公司机动车交通事故责任纠纷一案，不服上海市第一中级人民法院民事判决，向本院提起上诉。本院依法组成合议庭，开庭进行了审理。上诉人周九及其委托诉讼代理人、被上诉人某保险公司之委托诉讼代理人到庭参加诉讼。本案现已审理终结。' },
        { id: 'cd-013', title: '某食品公司与某广告公司著作权权属纠纷二审民事判决书', court: '北京市高级人民法院', courtLevel: 2, date: '2024-04-20', cause: '知识产权纠纷', caseType: '民事二审', summary: '上诉人某食品公司因与被上诉人某广告公司著作权权属纠纷一案，不服北京知识产权法院民事判决，向本院提起上诉。本院依法组成合议庭，开庭进行了审理。上诉人某食品公司之委托诉讼代理人、被上诉人某广告公司之委托诉讼代理人到庭参加诉讼。本案现已审理终结。' },
        { id: 'cd-014', title: '吴十与某开发商商品房预售合同纠纷一审民事判决书', court: '北京市第一中级人民法院', courtLevel: 3, date: '2023-08-30', cause: '合同纠纷', caseType: '民事一审', summary: '原告吴十与被告某开发商商品房预售合同纠纷一案，本院于2023年6月10日立案后，依法适用普通程序，公开开庭进行了审理。原告吴十之委托诉讼代理人、被告某开发商之委托诉讼代理人均到庭参加诉讼。本案现已审理终结。' },
        { id: 'cd-015', title: '郑十一与某制造公司工伤保险待遇纠纷再审民事判决书', court: '最高人民法院', courtLevel: 1, date: '2026-03-05', cause: '劳动争议', caseType: '民事再审', summary: '再审申请人郑十一因与被申请人某制造公司工伤保险待遇纠纷一案，不服上海市高级人民法院民事判决，向本院申请再审。本院依法提审后组成合议庭，开庭进行了审理。再审申请人郑十一之委托诉讼代理人、被申请人某制造公司之委托诉讼代理人到庭参加诉讼。本案现已审理终结。' },
        { id: 'cd-016', title: '王十二与某医院医疗损害责任纠纷一审民事判决书', court: '上海市第二中级人民法院', courtLevel: 3, date: '2025-04-16', cause: '侵权责任纠纷', caseType: '民事一审', summary: '原告王十二与被告某医院医疗损害责任纠纷一案，本院于2025年2月8日立案后，依法适用普通程序，公开开庭进行了审理。原告王十二之委托诉讼代理人、被告某医院之委托诉讼代理人均到庭参加诉讼。本案现已审理终结。' }
    ];

    // ===== 状态 =====
    var PAGE_SIZE = 10;
    var _closeCaseDetail = null;
    var state = {
        filtered: [],   // 当前筛选结果
        results: [],    // 当前筛选 + 排序结果
        page: 1,
        sort: 'relevance',  // 'relevance' | 'date' | 'courtLevel'
        keyword: ''
    };

    // ===== 工具 =====
    function $(id) { return document.getElementById(id); }

    // 从日期字符串取年份 (YYYY-MM-DD -> YYYY)
    function yearOf(date) {
        return String(date || '').slice(0, 4);
    }

    // 相关度评分: 关键词命中字段加权 (标题最高, 次为案由/案件类型, 摘要/法院最低)
    function relevanceScore(c, kw) {
        if (!kw) return 0;
        var k = kw.toLowerCase();
        var score = 0;
        if (String(c.title).toLowerCase().indexOf(k) >= 0) score += 5;
        if (String(c.cause).toLowerCase().indexOf(k) >= 0) score += 3;
        if (String(c.caseType).toLowerCase().indexOf(k) >= 0) score += 2;
        if (String(c.court).toLowerCase().indexOf(k) >= 0) score += 2;
        if (String(c.summary).toLowerCase().indexOf(k) >= 0) score += 2;
        return score;
    }

    // 日期比较: 返回 b.date - a.date 的符号 (降序)
    function compareDateDesc(a, b) {
        return (b.date < a.date) ? -1 : (b.date > a.date ? 1 : 0);
    }

    // ===== 筛选 =====
    function applyFilters() {
        var kwInput = $('cases-db-keyword');
        var causeSel = $('cases-db-cause');
        var courtSel = $('cases-db-court');
        var yearSel = $('cases-db-year');

        var kw = (kwInput ? kwInput.value : '').trim();
        var cause = causeSel ? causeSel.value : '全部案由';
        var court = courtSel ? courtSel.value : '全部法院';
        var year = yearSel ? yearSel.value : '全部年份';

        state.keyword = kw;

        var causeActive = cause && cause !== '全部案由';
        var courtActive = court && court !== '全部法院';
        var yearActive = year && year !== '全部年份';
        // 年份选项形如 "2026年", 提取数字
        var yearNum = yearActive ? year.replace(/[^0-9]/g, '') : '';

        state.filtered = CASES_DB.filter(function(c) {
            var matchKw = true;
            if (kw) {
                var k = kw.toLowerCase();
                matchKw = String(c.title).toLowerCase().indexOf(k) >= 0 ||
                          String(c.summary).toLowerCase().indexOf(k) >= 0 ||
                          String(c.cause).toLowerCase().indexOf(k) >= 0 ||
                          String(c.court).toLowerCase().indexOf(k) >= 0 ||
                          String(c.caseType).toLowerCase().indexOf(k) >= 0;
            }
            var matchCause = !causeActive || c.cause === cause;
            // 法院用 includes: "最高人民法院" 可命中 "最高人民法院知识产权法庭"
            var matchCourt = !courtActive || String(c.court).indexOf(court) >= 0;
            var matchYear = !yearActive || yearOf(c.date) === yearNum;
            return matchKw && matchCause && matchCourt && matchYear;
        });
    }

    // ===== 排序 =====
    function applySort() {
        var arr = state.filtered.slice();
        var kw = state.keyword;
        if (state.sort === 'relevance') {
            arr.sort(function(a, b) {
                var sa = relevanceScore(a, kw), sb = relevanceScore(b, kw);
                if (sb !== sa) return sb - sa;
                // 无关键词或同分时按裁判日期降序兜底
                return compareDateDesc(a, b);
            });
        } else if (state.sort === 'date') {
            arr.sort(compareDateDesc);
        } else if (state.sort === 'courtLevel') {
            arr.sort(function(a, b) {
                if (a.courtLevel !== b.courtLevel) return a.courtLevel - b.courtLevel;
                return compareDateDesc(a, b);
            });
        }
        state.results = arr;
    }

    // ===== 渲染: 结果列表 =====
    function renderResults() {
        var list = state.results;
        var container = $('cases-db-results');
        var countEl = $('cases-db-result-count');
        var pager = $('cases-db-pagination');

        if (countEl) {
            countEl.textContent = '共 ' + list.length.toLocaleString() + ' 条结果';
        }
        if (!container) return;

        var totalPages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
        if (state.page > totalPages) state.page = totalPages;
        if (state.page < 1) state.page = 1;

        var start = (state.page - 1) * PAGE_SIZE;
        var end = Math.min(start + PAGE_SIZE, list.length);
        var slice = list.slice(start, end);

        if (slice.length === 0) {
            container.innerHTML =
                '<div class="p-12 text-center">' +
                    '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:file-search-outline"></iconify-icon>' +
                    '<p class="text-sm text-fg-tertiary mt-3">未找到匹配的案例</p>' +
                    '<p class="text-[10px] text-fg-disabled mt-1">试试调整关键词或清除筛选条件</p>' +
                '</div>';
        } else {
            container.innerHTML = slice.map(renderCaseItem).join('');
        }

        renderPagination(pager, totalPages);
    }

    function renderCaseItem(c) {
        return '<div class="p-5 hover:bg-bg-subtle transition-colors cursor-pointer" onclick="openCaseDetail(\'' + c.id + '\')">' +
            '<h3 class="text-sm font-medium text-brand hover:underline mb-2">' + escapeHtml(c.title) + '</h3>' +
            '<div class="flex items-center gap-4 text-[10px] text-fg-tertiary mb-2">' +
                '<span><iconify-icon class="inline" icon="mdi:domain"></iconify-icon> ' + escapeHtml(c.court) + '</span>' +
                '<span><iconify-icon class="inline" icon="mdi:calendar"></iconify-icon> ' + escapeHtml(c.date) + '</span>' +
                '<span><iconify-icon class="inline" icon="mdi:tag-outline"></iconify-icon> ' + escapeHtml(c.caseType) + '</span>' +
            '</div>' +
            '<p class="text-xs text-fg-secondary line-clamp-2">' + escapeHtml(c.summary) + '</p>' +
        '</div>';
    }

    // ===== 渲染: 分页 =====
    function renderPagination(pager, totalPages) {
        if (!pager) return;
        if (totalPages <= 1) {
            pager.innerHTML = '<span class="text-[10px] text-fg-tertiary">第 ' + state.page + ' / ' + totalPages + ' 页</span>';
            return;
        }

        var html = '';
        // 上一页
        html += pageBtn(state.page > 1, '<iconify-icon icon="mdi:chevron-left"></iconify-icon>', state.page - 1, 'text-fg-tertiary');

        // 页码 (窗口式: 首尾 + 当前±2 + 省略号)
        buildPageList(state.page, totalPages).forEach(function(p) {
            if (p === '...') {
                html += '<span class="text-xs text-fg-tertiary px-1">...</span>';
            } else {
                var active = p === state.page;
                html += '<button class="w-8 h-8 rounded-lg flex items-center justify-center text-xs ' +
                    (active ? 'bg-brand text-white font-medium' : 'hover:bg-bg-subtle text-fg-secondary') +
                    '" onclick="changeCasesPage(' + p + ')">' + p + '</button>';
            }
        });

        // 下一页
        html += pageBtn(state.page < totalPages, '<iconify-icon icon="mdi:chevron-right"></iconify-icon>', state.page + 1, 'text-fg-tertiary');

        pager.innerHTML = html;
    }

    function pageBtn(enabled, inner, target, cls) {
        if (!enabled) {
            return '<button class="w-8 h-8 rounded-lg flex items-center justify-center text-xs ' + cls + ' opacity-40 cursor-not-allowed">' + inner + '</button>';
        }
        return '<button class="w-8 h-8 rounded-lg hover:bg-bg-subtle flex items-center justify-center text-xs ' + cls + '" onclick="changeCasesPage(' + target + ')">' + inner + '</button>';
    }

    // 生成页码数组, 含 '...' 占位
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
        nums.sort(function(a, b) { return a - b; });

        var result = [];
        for (var j = 0; j < nums.length; j++) {
            if (j > 0 && nums[j] - nums[j - 1] > 1) result.push('...');
            result.push(nums[j]);
        }
        return result;
    }

    // ===== Loading 状态 =====
    function showLoading() {
        var container = $('cases-db-results');
        if (container) {
            container.innerHTML =
                '<div class="p-12 text-center">' +
                    '<iconify-icon class="text-3xl text-brand animate-spin inline-block" icon="mdi:loading"></iconify-icon>' +
                    '<p class="text-xs text-fg-tertiary mt-2">正在检索案例...</p>' +
                '</div>';
        }
        var countEl = $('cases-db-result-count');
        if (countEl) countEl.textContent = '检索中...';
        var pager = $('cases-db-pagination');
        if (pager) pager.innerHTML = '';
    }

    // ===== 对外 API =====

    // 检索 (搜索按钮): 显示 1s loading 后渲染
    function searchCases() {
        showLoading();
        if (typeof showToast === 'function') showToast('正在检索案例...');
        setTimeout(function() {
            state.page = 1;
            applyFilters();
            applySort();
            renderResults();
        }, 1000);
    }

    // 切换排序: 读取排序下拉, 重新排序并回到第 1 页
    function changeCasesSort() {
        var sel = $('cases-db-sort');
        var label = sel ? sel.value : '相关度';
        var map = { '相关度': 'relevance', '裁判日期': 'date', '法院层级': 'courtLevel' };
        state.sort = map[label] || 'relevance';
        state.page = 1;
        applySort();
        renderResults();
    }

    // 翻页
    function changeCasesPage(page) {
        if (page < 1) return;
        state.page = page;
        renderResults();
        var container = $('cases-db-results');
        if (container && container.scrollIntoView) {
            container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    // 查看案例详情
    function openCaseDetail(id) {
        var c = null;
        for (var i = 0; i < CASES_DB.length; i++) {
            if (CASES_DB[i].id === id) { c = CASES_DB[i]; break; }
        }
        if (!c) {
            if (typeof showToast === 'function') showToast('未找到案例 #' + id);
            return;
        }

        var levelMap = { 1: '最高人民法院', 2: '高级人民法院', 3: '中级人民法院', 4: '基层人民法院' };

        var content = '<div class="space-y-4">' +
            '<div class="p-4 bg-bg-subtle rounded-xl">' +
            '<p class="text-sm font-medium text-fg-primary leading-relaxed">' + escapeHtml(c.title) + '</p>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">审理法院</p>' +
            '<p class="text-sm text-fg-primary font-medium">' + escapeHtml(c.court) + '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">法院层级</p>' +
            '<p class="text-sm text-fg-primary">' + levelMap[c.courtLevel] + '</p>' +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">裁判日期</p>' +
            '<p class="text-sm text-fg-primary">' + escapeHtml(c.date) + '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">案件类型</p>' +
            '<p class="text-sm text-fg-primary">' + escapeHtml(c.caseType) + '</p>' +
            '</div>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">案由</p>' +
            '<span class="text-[10px] bg-brand-tint3 text-brand font-medium px-2 py-0.5 rounded-full">' + escapeHtml(c.cause) + '</span>' +
            '</div>' +
            '<div class="p-4 bg-bg-subtle rounded-xl">' +
            '<p class="text-[11px] text-fg-tertiary mb-2">案件摘要</p>' +
            '<p class="text-xs text-fg-secondary leading-relaxed whitespace-pre-wrap">' + escapeHtml(c.summary) + '</p>' +
            '</div>' +
            '</div>';

        var footer = '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeCaseDetail()">关闭</button>' +
            '<button class="h-9 px-4 text-xs text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="closeCaseDetail()">引用到文书</button>';

        if (_closeCaseDetail) _closeCaseDetail();
        _closeCaseDetail = Utils.showModal({
            id: 'case-detail-modal',
            title: '案例详情',
            icon: 'mdi:file-search-outline',
            content: content,
            footer: footer,
            size: 'lg'
        });
    }

    function closeCaseDetail() {
        if (_closeCaseDetail) {
            _closeCaseDetail();
            _closeCaseDetail = null;
        }
    }

    // 初始化: 重置筛选/排序, 渲染全部案例 (首次进入视图时调用)
    function initCasesDb() {
        state.page = 1;
        state.sort = 'relevance';
        state.keyword = '';

        // 重置输入控件 (避免缓存视图残留上一次的筛选)
        var kw = $('cases-db-keyword'); if (kw) kw.value = '';
        var cause = $('cases-db-cause'); if (cause) cause.selectedIndex = 0;
        var court = $('cases-db-court'); if (court) court.selectedIndex = 0;
        var year = $('cases-db-year'); if (year) year.selectedIndex = 0;
        var sort = $('cases-db-sort'); if (sort) sort.selectedIndex = 0;

        applyFilters();
        applySort();
        renderResults();
    }

    // ===== 双绑定 =====
    globalThis.initCasesDb = initCasesDb;
    globalThis.searchCases = searchCases;
    globalThis.changeCasesPage = changeCasesPage;
    globalThis.openCaseDetail = openCaseDetail;
    globalThis.closeCaseDetail = closeCaseDetail;
    globalThis.changeCasesSort = changeCasesSort;
})();
