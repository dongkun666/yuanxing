/**
 * 企业信息库模块
 * 包含: 企业搜索 / 热门搜索 / 多条件筛选 / 排序 / 分页 / 企业详情
 * 加载: 在 script.js 之后同步加载 (依赖 showToast)
 */
(function () {
    'use strict';

    var STATUS_STYLES = {
        存续: 'bg-gradient-to-r from-green-50 to-emerald-100 text-green-600 border border-green-200/50',
        在业: 'bg-gradient-to-r from-blue-50 to-cyan-100 text-blue-600 border border-blue-200/50',
        注销: 'bg-gradient-to-r from-gray-50 to-gray-100 text-gray-500 border border-gray-200/50',
        吊销: 'bg-gradient-to-r from-red-50 to-rose-100 text-red-600 border border-red-200/50',
        迁入: 'bg-gradient-to-r from-purple-50 to-violet-100 text-purple-600 border border-purple-200/50',
        迁出: 'bg-gradient-to-r from-amber-50 to-orange-100 text-amber-600 border border-amber-200/50'
    };

    var PAGE_SIZE = 8;
    var state = {
        filtered: [],
        results: [],
        page: 1,
        sort: 'relevance'
    };

    var _companiesData = [
        {
            id: 1,
            name: '腾讯科技（深圳）有限公司',
            creditCode: '914403007192068994',
            legalRep: '马化腾',
            registeredCapital: '6,250万人民币',
            establishDate: '2000-02-24',
            status: '存续',
            industry: '信息传输、软件和信息技术服务业',
            legalRisk: 12,
            operatingRisk: 3,
            ipCount: 52340,
            iconBg: 'bg-gradient-to-br from-green-100 to-emerald-50',
            iconColor: 'text-green-600'
        },
        {
            id: 2,
            name: '阿里巴巴（中国）网络技术有限公司',
            creditCode: '91330100799655058B',
            legalRep: '蒋芳',
            registeredCapital: '5,000万人民币',
            establishDate: '2007-04-11',
            status: '存续',
            industry: '信息传输、软件和信息技术服务业',
            legalRisk: 8,
            operatingRisk: 2,
            ipCount: 41200,
            iconBg: 'bg-gradient-to-br from-amber-100 to-yellow-50',
            iconColor: 'text-amber-600'
        },
        {
            id: 3,
            name: '北京字节跳动科技有限公司',
            creditCode: '91110108551385082Q',
            legalRep: '梁汝波',
            registeredCapital: '500万人民币',
            establishDate: '2012-03-09',
            status: '存续',
            industry: '信息传输、软件和信息技术服务业',
            legalRisk: 15,
            operatingRisk: 6,
            ipCount: 38900,
            iconBg: 'bg-gradient-to-br from-purple-100 to-violet-50',
            iconColor: 'text-purple-600'
        },
        {
            id: 4,
            name: '百度在线网络技术（北京）有限公司',
            creditCode: '91110108717743207K',
            legalRep: '崔珊珊',
            registeredCapital: '4,520万美元',
            establishDate: '2000-01-18',
            status: '存续',
            industry: '信息传输、软件和信息技术服务业',
            legalRisk: 9,
            operatingRisk: 4,
            ipCount: 32100,
            iconBg: 'bg-gradient-to-br from-blue-100 to-cyan-50',
            iconColor: 'text-blue-600'
        },
        {
            id: 5,
            name: '华为技术有限公司',
            creditCode: '914403001922038216',
            legalRep: '任正非',
            registeredCapital: '4,030,470.96万人民币',
            establishDate: '1987-09-15',
            status: '存续',
            industry: '制造业',
            legalRisk: 20,
            operatingRisk: 5,
            ipCount: 120000,
            iconBg: 'bg-gradient-to-br from-red-100 to-rose-50',
            iconColor: 'text-red-500'
        },
        {
            id: 6,
            name: '京东集团股份有限公司',
            creditCode: '91110000802100433C',
            legalRep: '许冉',
            registeredCapital: '30,000万人民币',
            establishDate: '2007-04-20',
            status: '存续',
            industry: '批发和零售业',
            legalRisk: 7,
            operatingRisk: 3,
            ipCount: 25600,
            iconBg: 'bg-gradient-to-br from-indigo-100 to-blue-50',
            iconColor: 'text-indigo-600'
        },
        {
            id: 7,
            name: '拼多多（上海）网络科技有限公司',
            creditCode: '91310115MA1K3RJX2Y',
            legalRep: '朱健翀',
            registeredCapital: '1,000万人民币',
            establishDate: '2015-09-22',
            status: '注销',
            industry: '信息传输、软件和信息技术服务业',
            legalRisk: 4,
            operatingRisk: 1,
            ipCount: 8200,
            iconBg: 'bg-gradient-to-br from-pink-100 to-rose-50',
            iconColor: 'text-pink-600'
        },
        {
            id: 8,
            name: '滴滴出行科技有限公司',
            creditCode: '91110108592345678X',
            legalRep: '程维',
            registeredCapital: '10,000万人民币',
            establishDate: '2016-08-23',
            status: '吊销',
            industry: '信息传输、软件和信息技术服务业',
            legalRisk: 18,
            operatingRisk: 12,
            ipCount: 4300,
            iconBg: 'bg-gradient-to-br from-teal-100 to-cyan-50',
            iconColor: 'text-teal-600'
        },
        {
            id: 9,
            name: '美团点评科技有限公司',
            creditCode: '91110108585881234A',
            legalRep: '王兴',
            registeredCapital: '5,000万人民币',
            establishDate: '2015-05-15',
            status: '存续',
            industry: '租赁和商务服务业',
            legalRisk: 6,
            operatingRisk: 2,
            ipCount: 15800,
            iconBg: 'bg-gradient-to-br from-yellow-100 to-amber-50',
            iconColor: 'text-yellow-600'
        },
        {
            id: 10,
            name: '小米科技有限责任公司',
            creditCode: '91110108551385099B',
            legalRep: '雷军',
            registeredCapital: '18,500万人民币',
            establishDate: '2010-03-03',
            status: '存续',
            industry: '制造业',
            legalRisk: 5,
            operatingRisk: 2,
            ipCount: 28900,
            iconBg: 'bg-gradient-to-br from-orange-100 to-amber-50',
            iconColor: 'text-orange-600'
        },
        {
            id: 11,
            name: '网易（杭州）网络有限公司',
            creditCode: '91330108799655058C',
            legalRep: '丁磊',
            registeredCapital: '3,000万美元',
            establishDate: '2006-04-12',
            status: '存续',
            industry: '信息传输、软件和信息技术服务业',
            legalRisk: 6,
            operatingRisk: 2,
            ipCount: 21500,
            iconBg: 'bg-gradient-to-br from-red-100 to-orange-50',
            iconColor: 'text-red-500'
        },
        {
            id: 12,
            name: '美的集团股份有限公司',
            creditCode: '914406067224733444',
            legalRep: '方洪波',
            registeredCapital: '696,160万人民币',
            establishDate: '2000-04-07',
            status: '存续',
            industry: '制造业',
            legalRisk: 10,
            operatingRisk: 3,
            ipCount: 45600,
            iconBg: 'bg-gradient-to-br from-blue-100 to-indigo-50',
            iconColor: 'text-blue-600'
        }
    ];

    // ===== API 联调状态 =====
    // _COMPANIES_FALLBACK: mock 兜底数据 (不可变); _companiesData: 当前数据集 (API 成功覆盖)
    var _COMPANIES_FALLBACK = _companiesData.slice();
    var _companiesApiFailed = false; // 后端不可达标记, 命中后本次会话不再重试

    var _isLoading = false;
    var _closeCompanyDetail = null;

    function showToastMsg(msg) {
        if (typeof showToast === 'function') {
            showToast(msg);
        }
    }

    function $(id) {
        return document.getElementById(id);
    }

    function getStatusBadge(status) {
        var style = STATUS_STYLES[status] || 'bg-gray-50 text-gray-500 border border-gray-200/50';
        return (
            '<span class="text-[10px] font-semibold ' +
            style +
            ' px-2.5 py-1 rounded-full flex-shrink-0 shadow-sm">' +
            escapeHtml(status) +
            '</span>'
        );
    }

    function applyFilters() {
        var keyword = ($('companies-db-keyword') ? $('companies-db-keyword').value : '').trim().toLowerCase();
        var legal = ($('companies-db-legal') ? $('companies-db-legal').value : '').trim().toLowerCase();
        var status = $('companies-db-status') ? $('companies-db-status').value : '全部状态';
        var industry = $('companies-db-industry') ? $('companies-db-industry').value : '全部行业';

        var statusActive = status && status !== '全部状态';
        var industryActive = industry && industry !== '全部行业';

        state.filtered = _companiesData.filter(function (c) {
            var matchKw =
                !keyword ||
                (c.name || '').toLowerCase().indexOf(keyword) > -1 ||
                (c.creditCode || '').toLowerCase().indexOf(keyword) > -1;
            var matchLegal = !legal || (c.legalRep || '').toLowerCase().indexOf(legal) > -1;
            var matchStatus = !statusActive || c.status === status;
            var matchIndustry = !industryActive || (c.industry || '').indexOf(industry) >= 0;
            return matchKw && matchLegal && matchStatus && matchIndustry;
        });
    }

    function applySort() {
        var arr = state.filtered.slice();
        if (state.sort === 'capital') {
            arr.sort(function (a, b) {
                var numA = parseFloat(String(a.registeredCapital).replace(/[^0-9.]/g, '')) || 0;
                var numB = parseFloat(String(b.registeredCapital).replace(/[^0-9.]/g, '')) || 0;
                return numB - numA;
            });
        } else if (state.sort === 'date') {
            arr.sort(function (a, b) {
                return b.establishDate < a.establishDate ? -1 : b.establishDate > a.establishDate ? 1 : 0;
            });
        }
        state.results = arr;
    }

    function renderCompanyCard(company, idx) {
        return (
            '<div class="p-4 md:p-5 hover:bg-orange-50/30 transition-all duration-200 cursor-pointer group" data-animate="fade-in-up" data-stagger-group="companies-list" data-stagger-index="' +
            idx +
            '" data-delay="0.05" onclick="openCompanyDetail(' +
            company.id +
            ')">' +
            '<div class="flex items-start gap-3 md:gap-4">' +
            '<div class="w-12 h-12 md:w-13 md:h-13 rounded-xl ' +
            company.iconBg +
            ' flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform shadow-sm">' +
            '<iconify-icon class="text-2xl md:text-2xl ' +
            company.iconColor +
            '" icon="mdi:office-building"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-start justify-between gap-3 mb-2">' +
            '<div class="flex-1 min-w-0">' +
            '<h3 class="text-sm md:text-base font-semibold text-fg-primary group-hover:text-orange-600 transition-colors line-clamp-1">' +
            escapeHtml(company.name) +
            '</h3>' +
            '<p class="text-[10px] text-fg-tertiary mt-0.5 font-mono truncate">' +
            escapeHtml(company.creditCode) +
            '</p>' +
            '</div>' +
            getStatusBadge(company.status) +
            '</div>' +
            '<div class="grid grid-cols-2 md:grid-cols-3 gap-2 md:gap-4 text-[10px] md:text-xs mb-2.5">' +
            '<div class="flex items-center gap-1.5 text-fg-tertiary">' +
            '<iconify-icon class="text-[11px]" icon="mdi:account-outline"></iconify-icon>' +
            '<span class="text-fg-secondary">' +
            escapeHtml(company.legalRep) +
            '</span>' +
            '</div>' +
            '<div class="flex items-center gap-1.5 text-fg-tertiary">' +
            '<iconify-icon class="text-[11px]" icon="mdi:cash-multiple"></iconify-icon>' +
            '<span class="text-fg-secondary">' +
            escapeHtml(company.registeredCapital) +
            '</span>' +
            '</div>' +
            '<div class="flex items-center gap-1.5 text-fg-tertiary col-span-2 md:col-span-1">' +
            '<iconify-icon class="text-[11px]" icon="mdi:calendar-star"></iconify-icon>' +
            '<span class="text-fg-secondary">' +
            escapeHtml(company.establishDate) +
            '</span>' +
            '</div>' +
            '</div>' +
            '<div class="flex items-center gap-3 md:gap-4 flex-wrap">' +
            '<span class="inline-flex items-center gap-1 text-[10px] text-red-500 bg-red-50 px-2 py-0.5 rounded-md">' +
            '<iconify-icon class="text-[11px]" icon="mdi:alert-circle-outline"></iconify-icon> 法律风险 ' +
            company.legalRisk +
            '</span>' +
            '<span class="inline-flex items-center gap-1 text-[10px] text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md">' +
            '<iconify-icon class="text-[11px]" icon="mdi:alert-outline"></iconify-icon> 经营风险 ' +
            company.operatingRisk +
            '</span>' +
            '<span class="inline-flex items-center gap-1 text-[10px] text-blue-500 bg-blue-50 px-2 py-0.5 rounded-md">' +
            '<iconify-icon class="text-[11px]" icon="mdi:lightbulb-outline"></iconify-icon> 知产 ' +
            company.ipCount.toLocaleString() +
            '</span>' +
            '</div>' +
            '</div>' +
            '<iconify-icon class="text-fg-disabled text-base md:text-lg opacity-0 group-hover:opacity-100 transition-all translate-x-[-4px] group-hover:translate-x-0 flex-shrink-0 mt-2" icon="mdi:chevron-right"></iconify-icon>' +
            '</div>' +
            '</div>'
        );
    }

    function renderResults() {
        var container = $('companies-db-results');
        var countEl = $('companies-db-result-count');
        var pager = $('companies-db-pagination');
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
                '<div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-orange-50 to-amber-50 flex items-center justify-center mb-4">' +
                '<iconify-icon class="text-4xl text-orange-500/60" icon="mdi:domain-off"></iconify-icon>' +
                '</div>' +
                '<h4 class="text-base font-semibold text-fg-primary mb-1">未找到匹配的企业</h4>' +
                '<p class="text-xs text-fg-tertiary mb-4 text-center max-w-xs">请调整关键词或筛选条件后重试，或尝试其他搜索词</p>' +
                '<button onclick="resetCompaniesDb()" class="px-4 py-2 text-xs font-medium rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 text-white hover:shadow-md hover:shadow-orange-500/20 transition-all duration-200 hover:-translate-y-0.5 flex items-center gap-1.5">' +
                '<iconify-icon class="text-sm" icon="mdi:refresh"></iconify-icon>' +
                '重置筛选' +
                '</button>' +
                '</div>';
        } else {
            container.innerHTML = slice
                .map(function (c, idx) {
                    return renderCompanyCard(c, start + idx);
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
                        ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-md shadow-orange-500/20'
                        : 'hover:bg-white text-fg-secondary hover:text-orange-600') +
                    ' transition-all duration-200" onclick="changeCompaniesPage(' +
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
            '" onclick="changeCompaniesPage(' +
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
        var container = $('companies-db-results');
        if (!container) return;
        container.innerHTML =
            '<div class="flex flex-col items-center justify-center py-12 px-4">' +
            '<div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-50 to-amber-50 flex items-center justify-center mb-3">' +
            '<iconify-icon class="text-3xl text-orange-500 animate-spin" icon="mdi:loading"></iconify-icon>' +
            '</div>' +
            '<p class="text-xs text-fg-tertiary">正在查询企业信息...</p>' +
            '</div>';
    }

    // ===== API 联调 (mock 兜底) =====
    var _COMPANY_ICON_COLORS = [
        ['bg-gradient-to-br from-orange-100 to-amber-50', 'text-orange-600'],
        ['bg-gradient-to-br from-blue-100 to-cyan-50', 'text-blue-600'],
        ['bg-gradient-to-br from-green-100 to-emerald-50', 'text-green-600'],
        ['bg-gradient-to-br from-purple-100 to-violet-50', 'text-purple-600'],
        ['bg-gradient-to-br from-red-100 to-rose-50', 'text-red-500']
    ];

    function pickCompanyIcon(name) {
        var n = name || '';
        var hash = 0;
        for (var i = 0; i < n.length; i++) {
            hash = (hash + n.charCodeAt(i)) % _COMPANY_ICON_COLORS.length;
        }
        return _COMPANY_ICON_COLORS[hash];
    }

    // 将后端 CompanyOut 归一化为前端结构 (兼容已归一化对象)
    function normalizeCompany(c) {
        if (!c) return null;
        var name = c.company_name || c.name || '';
        var ic = pickCompanyIcon(name);
        return {
            id: c.id !== undefined && c.id !== null ? c.id : c.unified_id,
            name: name,
            creditCode: c.unified_id || c.credit_code || c.creditCode || '',
            legalRep: c.legal_rep || c.legalRep || '—',
            registeredCapital: c.registered_capital || c.registeredCapital || '—',
            establishDate: c.establish_date || c.establishDate || '',
            status: c.business_status || c.status || '存续',
            industry: c.industry || '',
            legalRisk: c.legal_risk || c.legalRisk || 0,
            operatingRisk: c.operating_risk || c.operatingRisk || 0,
            ipCount: c.ip_count || c.ipCount || 0,
            iconBg: c.iconBg || ic[0],
            iconColor: c.iconColor || ic[1]
        };
    }

    // 从 API 加载企业列表 (失败 reject)
    function loadCompaniesFromAPI(params) {
        if (typeof API === 'undefined' || !API.companies || !API.companies.list) {
            return Promise.reject(new Error('API unavailable'));
        }
        return API.companies.list(params || { limit: 50 }, { showError: false }).then(function (res) {
            if (res && res.ok && Array.isArray(res.data)) {
                var list = res.data.map(normalizeCompany).filter(function (x) {
                    return x;
                });
                if (list.length > 0) return list;
            }
            throw new Error('API response invalid');
        });
    }

    // 回退到 mock 数据并提示
    function fallbackToMockCompanies(reason) {
        console.warn('[companies-db] API 调用失败, 回退 mock:', reason);
        _companiesApiFailed = true;
        _companiesData = _COMPANIES_FALLBACK.slice();
        showToastMsg('后端不可达, 已切换本地示例数据');
    }

    // 搜索: 优先 API (关键词走 name 过滤), 失败回退 mock; status/industry/legal 本地二次过滤
    function searchCompanies() {
        renderLoading();
        _isLoading = true;
        state.page = 1;

        function renderLocal() {
            _isLoading = false;
            applyFilters();
            applySort();
            renderResults();
        }

        // 后端此前已判定不可达 → 直接走 mock
        if (_companiesApiFailed || typeof API === 'undefined' || !API.companies || !API.companies.list) {
            _companiesData = _COMPANIES_FALLBACK.slice();
            renderLocal();
            return;
        }

        var kw = ($('companies-db-keyword') ? $('companies-db-keyword').value : '').trim();
        var params = { limit: 100 };
        if (kw) params.name = kw;

        loadCompaniesFromAPI(params)
            .then(function (list) {
                _companiesData = list;
                renderLocal();
            })
            .catch(function (err) {
                fallbackToMockCompanies(err && err.message ? err.message : err);
                renderLocal();
            });
    }

    function quickSearchIndustry(keyword) {
        var input = $('companies-db-keyword');
        if (input) input.value = keyword;
        searchCompanies();
    }

    function changeCompaniesSort() {
        var sel = $('companies-db-sort');
        var label = sel ? sel.value : '相关度';
        var map = { 相关度: 'relevance', 注册资本: 'capital', 成立日期: 'date' };
        state.sort = map[label] || 'relevance';
        state.page = 1;
        applySort();
        renderResults();
    }

    function changeCompaniesPage(page) {
        if (page < 1) return;
        state.page = page;
        renderResults();
        var container = $('companies-db-results');
        if (container && container.scrollIntoView) {
            container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    function resetCompaniesDb() {
        var kw = $('companies-db-keyword');
        if (kw) kw.value = '';
        var legal = $('companies-db-legal');
        if (legal) legal.value = '';
        var status = $('companies-db-status');
        if (status) status.selectedIndex = 0;
        var industry = $('companies-db-industry');
        if (industry) industry.selectedIndex = 0;
        var sort = $('companies-db-sort');
        if (sort) sort.selectedIndex = 0;
        state.page = 1;
        state.sort = 'relevance';
        applyFilters();
        applySort();
        renderResults();
    }

    function openCompanyDetail(id) {
        var company = _companiesData.find(function (c) {
            return c.id === id;
        });
        if (!company) {
            showToastMsg('未找到企业 #' + id);
            return;
        }

        var content =
            '<div class="space-y-4">' +
            '<div class="relative overflow-hidden p-4 bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50 rounded-xl">' +
            '<div class="absolute top-0 right-0 w-32 h-32 bg-orange-200/20 rounded-full -translate-y-1/2 translate-x-1/2 blur-2xl"></div>' +
            '<div class="relative z-10 flex items-center gap-4">' +
            '<div class="w-16 h-16 rounded-2xl ' +
            company.iconBg +
            ' flex items-center justify-center flex-shrink-0 shadow-lg">' +
            '<iconify-icon class="text-3xl ' +
            company.iconColor +
            '" icon="mdi:office-building"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-center gap-2 mb-1">' +
            '<h4 class="text-base font-semibold text-fg-primary">' +
            escapeHtml(company.name) +
            '</h4>' +
            getStatusBadge(company.status) +
            '</div>' +
            '<p class="text-xs text-fg-tertiary font-mono">' +
            escapeHtml(company.creditCode) +
            '</p>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3.5 bg-bg-subtle rounded-xl border border-bg-border/60 hover:border-orange-200/50 transition-colors">' +
            '<p class="text-[11px] text-fg-tertiary mb-1.5 flex items-center gap-1">' +
            '<iconify-icon class="text-xs" icon="mdi:account-outline"></iconify-icon> 法定代表人' +
            '</p>' +
            '<p class="text-sm text-fg-primary font-semibold">' +
            escapeHtml(company.legalRep) +
            '</p>' +
            '</div>' +
            '<div class="p-3.5 bg-bg-subtle rounded-xl border border-bg-border/60 hover:border-orange-200/50 transition-colors">' +
            '<p class="text-[11px] text-fg-tertiary mb-1.5 flex items-center gap-1">' +
            '<iconify-icon class="text-xs" icon="mdi:cash-multiple"></iconify-icon> 注册资本' +
            '</p>' +
            '<p class="text-sm text-fg-primary font-semibold">' +
            escapeHtml(company.registeredCapital) +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3.5 bg-bg-subtle rounded-xl border border-bg-border/60 hover:border-orange-200/50 transition-colors">' +
            '<p class="text-[11px] text-fg-tertiary mb-1.5 flex items-center gap-1">' +
            '<iconify-icon class="text-xs" icon="mdi:calendar-star"></iconify-icon> 成立日期' +
            '</p>' +
            '<p class="text-sm text-fg-primary font-semibold">' +
            escapeHtml(company.establishDate) +
            '</p>' +
            '</div>' +
            '<div class="p-3.5 bg-bg-subtle rounded-xl border border-bg-border/60 hover:border-orange-200/50 transition-colors">' +
            '<p class="text-[11px] text-fg-tertiary mb-1.5 flex items-center gap-1">' +
            '<iconify-icon class="text-xs" icon="mdi:domain"></iconify-icon> 所属行业' +
            '</p>' +
            '<p class="text-sm text-fg-primary font-semibold">' +
            escapeHtml(company.industry) +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="p-4 bg-bg-subtle rounded-xl">' +
            '<p class="text-[11px] text-fg-tertiary mb-3 font-semibold flex items-center gap-1.5">' +
            '<iconify-icon class="text-xs" icon="mdi:shield-alert-outline"></iconify-icon> 风险概览' +
            '</p>' +
            '<div class="grid grid-cols-3 gap-3">' +
            '<div class="text-center p-3 bg-gradient-to-b from-red-50 to-white rounded-xl border border-red-100/50 hover:scale-105 transition-transform cursor-pointer">' +
            '<div class="w-10 h-10 mx-auto rounded-full bg-red-100/80 flex items-center justify-center mb-2">' +
            '<iconify-icon class="text-red-500 text-lg" icon="mdi:alert-circle-outline"></iconify-icon>' +
            '</div>' +
            '<p class="text-xl font-bold text-red-500 kb-tabular-nums">' +
            company.legalRisk +
            '</p>' +
            '<p class="text-[10px] text-fg-tertiary mt-0.5">法律风险</p>' +
            '</div>' +
            '<div class="text-center p-3 bg-gradient-to-b from-amber-50 to-white rounded-xl border border-amber-100/50 hover:scale-105 transition-transform cursor-pointer">' +
            '<div class="w-10 h-10 mx-auto rounded-full bg-amber-100/80 flex items-center justify-center mb-2">' +
            '<iconify-icon class="text-amber-500 text-lg" icon="mdi:alert-outline"></iconify-icon>' +
            '</div>' +
            '<p class="text-xl font-bold text-amber-500 kb-tabular-nums">' +
            company.operatingRisk +
            '</p>' +
            '<p class="text-[10px] text-fg-tertiary mt-0.5">经营风险</p>' +
            '</div>' +
            '<div class="text-center p-3 bg-gradient-to-b from-blue-50 to-white rounded-xl border border-blue-100/50 hover:scale-105 transition-transform cursor-pointer">' +
            '<div class="w-10 h-10 mx-auto rounded-full bg-blue-100/80 flex items-center justify-center mb-2">' +
            '<iconify-icon class="text-blue-500 text-lg" icon="mdi:lightbulb-outline"></iconify-icon>' +
            '</div>' +
            '<p class="text-xl font-bold text-blue-500 kb-tabular-nums">' +
            company.ipCount.toLocaleString() +
            '</p>' +
            '<p class="text-[10px] text-fg-tertiary mt-0.5">知识产权</p>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-xl hover:bg-bg transition-colors" onclick="closeCompanyDetail()">关闭</button>' +
            '<button class="h-9 px-4 text-xs text-white bg-gradient-to-r from-orange-500 to-amber-500 hover:shadow-md hover:shadow-orange-500/20 rounded-xl transition-all duration-200" onclick="closeCompanyDetail()">关联案件查询</button>';

        if (_closeCompanyDetail) _closeCompanyDetail();
        _closeCompanyDetail = Utils.showModal({
            id: 'company-detail-modal',
            title: '企业详情',
            icon: 'mdi:office-building',
            content: content,
            footer: footer,
            size: 'md'
        });
    }

    function closeCompanyDetail() {
        if (_closeCompanyDetail) {
            _closeCompanyDetail();
            _closeCompanyDetail = null;
        }
    }

    function initCompaniesDb() {
        _isLoading = false;
        state.page = 1;
        state.sort = 'relevance';

        // 先渲染 mock (立即可见)
        _companiesData = _COMPANIES_FALLBACK.slice();
        applyFilters();
        applySort();
        renderResults();

        // 尝试从 API 加载真实数据覆盖 (失败保持 mock)
        if (!_companiesApiFailed && typeof API !== 'undefined' && API.companies && API.companies.list) {
            renderLoading();
            loadCompaniesFromAPI({ limit: 50 })
                .then(function (list) {
                    _companiesData = list;
                    applyFilters();
                    applySort();
                    renderResults();
                })
                .catch(function (err) {
                    console.warn(
                        '[companies-db] 初始化 API 加载失败, 使用 mock:',
                        err && err.message ? err.message : err
                    );
                    _companiesApiFailed = true;
                    applyFilters();
                    applySort();
                    renderResults();
                });
        }
    }

    globalThis.initCompaniesDb = initCompaniesDb;
    globalThis.searchCompanies = searchCompanies;
    globalThis.quickSearchIndustry = quickSearchIndustry;
    globalThis.changeCompaniesSort = changeCompaniesSort;
    globalThis.changeCompaniesPage = changeCompaniesPage;
    globalThis.resetCompaniesDb = resetCompaniesDb;
    globalThis.openCompanyDetail = openCompanyDetail;
    globalThis.closeCompanyDetail = closeCompanyDetail;
})();
