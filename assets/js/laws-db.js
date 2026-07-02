/**
 * 法律法规库 - 交互模块
 *
 * 包含: 法规检索 (关键词 / 效力层级 / 制定机关) + 分类统计卡片筛选 +
 *       法规列表渲染 + 法规详情 (toast) + 空态 + loading 状态
 * 依赖: showToast (script.js 全局), escapeHtml (本模块内实现)
 * 暴露: initLawsDb, searchLaws, filterByCategory, openLawDetail
 */

(function () {
    'use strict';

    // ===== 效力层级 -> badge 颜色映射 =====
    var LEVEL_STYLES = {
        法律: 'bg-gradient-to-r from-red-50 to-red-100 text-red-600 border border-red-200/50',
        行政法规: 'bg-gradient-to-r from-amber-50 to-amber-100 text-amber-700 border border-amber-200/50',
        司法解释: 'bg-gradient-to-r from-blue-50 to-blue-100 text-blue-600 border border-blue-200/50',
        部门规章: 'bg-gradient-to-r from-green-50 to-green-100 text-green-600 border border-green-200/50'
    };

    // ===== 分类统计 (数据库总量, 动态渲染到卡片) =====
    var STATS = [
        { category: '法律', total: 2156 },
        { category: '行政法规', total: 6342 },
        { category: '司法解释', total: 1897 },
        { category: '部门规章', total: 12458 }
    ];

    // ===== Mock 法规数据 (覆盖不同效力层级与制定机关) =====
    var LAWS = [
        // ----- 法律 (全国人大常委会) -----
        {
            id: 'law-001',
            name: '中华人民共和国民法典',
            publishInfo: '2020年5月28日第十三届全国人民代表大会第三次会议通过 · 2021年1月1日施行',
            level: '法律',
            organ: '全国人大常委会',
            status: '现行有效'
        },
        {
            id: 'law-002',
            name: '中华人民共和国民事诉讼法',
            publishInfo: '2023年9月1日修正 · 2024年1月1日施行',
            level: '法律',
            organ: '全国人大常委会',
            status: '现行有效'
        },
        {
            id: 'law-003',
            name: '中华人民共和国劳动合同法',
            publishInfo: '2012年12月28日修正',
            level: '法律',
            organ: '全国人大常委会',
            status: '现行有效'
        },
        {
            id: 'law-004',
            name: '中华人民共和国公司法',
            publishInfo: '2023年12月29日修订 · 2024年7月1日施行',
            level: '法律',
            organ: '全国人大常委会',
            status: '现行有效'
        },
        {
            id: 'law-005',
            name: '中华人民共和国刑法',
            publishInfo: '1997年3月14日修订 · 历经十二次修正',
            level: '法律',
            organ: '全国人大常委会',
            status: '现行有效'
        },
        {
            id: 'law-006',
            name: '中华人民共和国经济合同法',
            publishInfo: '1981年12月13日第五届全国人大第四次会议通过',
            level: '法律',
            organ: '全国人大常委会',
            status: '已废止'
        },

        // ----- 行政法规 (国务院) -----
        {
            id: 'law-007',
            name: '中华人民共和国劳动合同法实施条例',
            publishInfo: '2008年9月18日国务院令第535号公布',
            level: '行政法规',
            organ: '国务院',
            status: '现行有效'
        },
        {
            id: 'law-008',
            name: '女职工劳动保护特别规定',
            publishInfo: '2012年4月28日国务院令第619号公布',
            level: '行政法规',
            organ: '国务院',
            status: '现行有效'
        },
        {
            id: 'law-009',
            name: '物业管理条例',
            publishInfo: '2007年8月26日修订 · 国务院令第504号',
            level: '行政法规',
            organ: '国务院',
            status: '现行有效'
        },

        // ----- 司法解释 (最高人民法院 / 最高人民检察院) -----
        {
            id: 'law-010',
            name: '最高人民法院关于审理民间借贷案件适用法律若干问题的规定',
            publishInfo: '法释〔2020〕17号 · 2021年1月1日施行',
            level: '司法解释',
            organ: '最高人民法院',
            status: '现行有效'
        },
        {
            id: 'law-011',
            name: '最高人民法院关于适用《中华人民共和国民法典》合同编通则若干问题的解释',
            publishInfo: '法释〔2023〕13号 · 2023年12月5日施行',
            level: '司法解释',
            organ: '最高人民法院',
            status: '现行有效'
        },
        {
            id: 'law-012',
            name: '最高人民法院关于审理劳动争议案件适用法律问题的解释（一）',
            publishInfo: '法释〔2020〕26号 · 2021年1月1日施行',
            level: '司法解释',
            organ: '最高人民法院',
            status: '现行有效'
        },
        {
            id: 'law-013',
            name: '最高人民检察院关于人民检察院直接受理立案侦查案件立案标准的规定（试行）',
            publishInfo: '高检发研字〔1999〕10号',
            level: '司法解释',
            organ: '最高人民检察院',
            status: '已废止'
        },

        // ----- 部门规章 (各部委) -----
        {
            id: 'law-014',
            name: '公安机关办理刑事案件程序规定',
            publishInfo: '2020年7月20日公安部令第159号',
            level: '部门规章',
            organ: '公安部',
            status: '现行有效'
        },
        {
            id: 'law-015',
            name: '律师事务所管理办法',
            publishInfo: '2018年9月18日司法部令第133号',
            level: '部门规章',
            organ: '司法部',
            status: '现行有效'
        },
        {
            id: 'law-016',
            name: '劳动人事争议仲裁办案规则',
            publishInfo: '2017年5月8日人社部令第33号',
            level: '部门规章',
            organ: '人社部',
            status: '现行有效'
        },
        {
            id: 'law-017',
            name: '市场监督管理行政处罚程序规定',
            publishInfo: '2021年6月24日市场监管总局令第42号',
            level: '部门规章',
            organ: '市场监管总局',
            status: '现行有效'
        }
    ];

    // ===== API 联调状态 =====
    // _lawsData: 当前数据集 (API 成功 → API 数据; 失败 → LAWS 兜底)
    var _lawsData = LAWS.slice();
    var _lawsApiFailed = false; // 后端不可达标记, 命中后本次会话不再重试

    // ===== 读取检索条件并过滤 =====
    function getFilteredLaws() {
        var kwInput = document.getElementById('laws-db-keyword');
        var levelSel = document.getElementById('laws-db-level');
        var organSel = document.getElementById('laws-db-organ');
        var keyword = ((kwInput && kwInput.value) || '').trim().toLowerCase();
        var level = (levelSel && levelSel.value) || '全部层级';
        var organ = (organSel && organSel.value) || '全部机关';

        return _lawsData.filter(function (law) {
            var matchKw =
                !keyword ||
                law.name.toLowerCase().indexOf(keyword) > -1 ||
                law.publishInfo.toLowerCase().indexOf(keyword) > -1 ||
                law.organ.toLowerCase().indexOf(keyword) > -1;
            var matchLevel = level === '全部层级' || law.level === level;
            var matchOrgan = organ === '全部机关' || law.organ === organ;
            return matchKw && matchLevel && matchOrgan;
        });
    }

    var PAGE_SIZE = 8;
    var state = {
        page: 1
    };

    // ===== 工具函数 =====
    function $(id) {
        return document.getElementById(id);
    }

    // ===== 渲染法规列表 =====
    function renderLaws(list) {
        var container = $('laws-db-results');
        var countEl = $('laws-db-result-count');
        var pager = $('laws-db-pagination');
        if (!container) return;

        if (countEl && list) {
            countEl.textContent = '共 ' + list.length + ' 条';
        }

        if (!list || list.length === 0) {
            container.innerHTML =
                '<div class="flex flex-col items-center justify-center py-16 px-4">' +
                '<div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-50 to-teal-50 flex items-center justify-center mb-4">' +
                '<iconify-icon class="text-4xl text-emerald-500/60" icon="mdi:file-search-outline"></iconify-icon>' +
                '</div>' +
                '<h4 class="text-base font-semibold text-fg-primary mb-1">未找到匹配的法规</h4>' +
                '<p class="text-xs text-fg-tertiary mb-4 text-center max-w-xs">请调整关键词或筛选条件后重试，或尝试其他搜索词</p>' +
                '<button onclick="resetLawsSearch()" class="px-4 py-2 text-xs font-medium rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:shadow-md hover:shadow-emerald-500/20 transition-all duration-200 hover:-translate-y-0.5 flex items-center gap-1.5">' +
                '<iconify-icon class="text-sm" icon="mdi:refresh"></iconify-icon>' +
                '重置筛选' +
                '</button>' +
                '</div>';
            if (pager) pager.innerHTML = '';
            return;
        }

        var totalPages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
        if (state.page > totalPages) state.page = totalPages;
        if (state.page < 1) state.page = 1;

        var start = (state.page - 1) * PAGE_SIZE;
        var end = Math.min(start + PAGE_SIZE, list.length);
        var slice = list.slice(start, end);

        container.innerHTML = slice
            .map(function (law, idx) {
                var levelBadge = LEVEL_STYLES[law.level] || 'bg-gray-50 text-gray-600 border border-gray-200/50';
                var statusHtml =
                    law.status === '已废止'
                        ? '<span class="inline-flex items-center gap-1 text-[10px] text-gray-400"><iconify-icon icon="mdi:close-circle-outline" class="text-[10px]"></iconify-icon> 已废止</span>'
                        : '<span class="inline-flex items-center gap-1 text-[10px] text-success"><iconify-icon icon="mdi:check-circle-outline" class="text-[10px]"></iconify-icon> 现行有效</span>';
                return (
                    '' +
                    '<div class="p-4 md:p-5 hover:bg-emerald-50/30 transition-all duration-200 cursor-pointer group" data-animate="fade-in-up" data-stagger-group="laws-list" data-stagger-index="' + idx + '" data-delay="0.1" onclick="openLawDetail(\'' +
                    law.id +
                    '\')">' +
                    '<div class="flex items-start gap-3 md:gap-4">' +
                    '<div class="w-10 h-10 md:w-11 md:h-11 rounded-xl bg-gradient-to-br from-emerald-100 to-teal-50 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform shadow-sm">' +
                    '<iconify-icon class="text-lg md:text-xl text-emerald-600" icon="mdi:file-document-outline"></iconify-icon>' +
                    '</div>' +
                    '<div class="flex-1 min-w-0">' +
                    '<div class="flex items-start justify-between gap-3 mb-1.5">' +
                    '<h3 class="text-sm md:text-base font-semibold text-fg-primary group-hover:text-emerald-600 transition-colors line-clamp-1">' +
                    escapeHtml(law.name) +
                    '</h3>' +
                    '<span class="text-[10px] font-semibold ' +
                    levelBadge +
                    ' px-2.5 py-1 rounded-full flex-shrink-0 shadow-sm">' +
                    law.level +
                    '</span>' +
                    '</div>' +
                    '<p class="text-[11px] md:text-xs text-fg-secondary mb-2 line-clamp-1">' +
                    escapeHtml(law.publishInfo) +
                    '</p>' +
                    '<div class="flex items-center gap-3 md:gap-4 flex-wrap">' +
                    '<span class="inline-flex items-center gap-1 text-[10px] text-fg-tertiary">' +
                    '<iconify-icon icon="mdi:domain" class="text-[11px]"></iconify-icon>' +
                    escapeHtml(law.organ) +
                    '</span>' +
                    statusHtml +
                    '</div>' +
                    '</div>' +
                    '<iconify-icon class="text-fg-disabled text-base md:text-lg opacity-0 group-hover:opacity-100 transition-all translate-x-[-4px] group-hover:translate-x-0 flex-shrink-0 mt-1" icon="mdi:chevron-right"></iconify-icon>' +
                    '</div>' +
                    '</div>'
                );
            })
            .join('');

        renderPagination(pager, totalPages);

        if (typeof Animations !== 'undefined' && Animations.initPageAnimations) {
            Animations.initPageAnimations(container);
        }
    }

    // ===== 分页渲染 =====
    function renderPagination(pager, totalPages) {
        if (!pager) return;
        if (totalPages <= 1) {
            pager.innerHTML = '<span class="text-[10px] text-fg-tertiary">第 ' + state.page + ' / ' + totalPages + ' 页</span>';
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
                    (active ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-md shadow-emerald-500/20' : 'hover:bg-white text-fg-secondary hover:text-emerald-600') +
                    ' transition-all duration-200" onclick="changeLawsPage(' +
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
            return '<button class="w-8 h-8 rounded-lg flex items-center justify-center text-xs ' + cls + ' opacity-40 cursor-not-allowed">' + inner + '</button>';
        }
        return '<button class="w-8 h-8 rounded-lg hover:bg-white flex items-center justify-center text-xs ' + cls + '" onclick="changeLawsPage(' + target + ')">' + inner + '</button>';
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
        nums.sort(function (a, b) { return a - b; });

        var result = [];
        for (var j = 0; j < nums.length; j++) {
            if (j > 0 && nums[j] - nums[j - 1] > 1) result.push('...');
            result.push(nums[j]);
        }
        return result;
    }

    // ===== 翻页 =====
    function changeLawsPage(page) {
        if (page < 1) return;
        state.page = page;
        renderLaws(getFilteredLaws());
        var container = $('laws-db-results');
        if (container && container.scrollIntoView) {
            container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    // ===== loading 状态 =====
    function showLoading() {
        var container = document.getElementById('laws-db-results');
        if (!container) return;
        container.innerHTML =
            '<div class="flex items-center justify-center gap-2 py-12">' +
            '<iconify-icon class="text-xl text-brand animate-spin" icon="mdi:loading"></iconify-icon>' +
            '<span class="text-sm text-fg-tertiary">检索中...</span>' +
            '</div>';
    }

    // ===== 渲染分类统计数字 =====
    function renderStats() {
        STATS.forEach(function (stat) {
            var card = document.querySelector('#view-laws-db [data-category="' + stat.category + '"]');
            if (!card) return;
            var numEl = card.querySelector('p');
            if (numEl) numEl.textContent = stat.total.toLocaleString('en-US');
        });
    }

    // ===== API 联调 (mock 兜底) =====
    // 后端 law_type → 前端 level (中文效力层级, 用于 LEVEL_STYLES 与下拉过滤)
    function mapLawLevel(t) {
        if (!t) return '法律';
        var s = String(t);
        if (LEVEL_STYLES[s]) return s;
        if (s.indexOf('法律') >= 0) return '法律';
        if (s.indexOf('行政') >= 0) return '行政法规';
        if (s.indexOf('司法') >= 0) return '司法解释';
        if (s.indexOf('规章') >= 0 || s.indexOf('部门') >= 0) return '部门规章';
        return s;
    }

    // 将后端 LawOut 归一化为前端结构 (兼容已归一化对象)
    function normalizeLaw(l) {
        if (!l) return null;
        var publishInfo = l.publishInfo;
        if (!publishInfo) {
            var parts = [];
            if (l.issue_date) parts.push(String(l.issue_date).slice(0, 10) + ' 公布');
            if (l.effective_date) parts.push(String(l.effective_date).slice(0, 10) + ' 施行');
            publishInfo = parts.join(' · ') || (l.title || '');
        }
        return {
            id: l.law_id || ('api-' + l.id),
            name: l.title || l.name || '',
            publishInfo: publishInfo,
            level: mapLawLevel(l.law_type || l.level),
            organ: l.organ || '',
            status: l.status || '现行有效'
        };
    }

    // 从 API 加载法规列表 (失败 reject)
    function loadLawsFromAPI(params) {
        if (typeof API === 'undefined' || !API.laws || !API.laws.list) {
            return Promise.reject(new Error('API unavailable'));
        }
        return API.laws.list(params || { limit: 50 }, { showError: false }).then(function (res) {
            if (res && res.ok && Array.isArray(res.data)) {
                var list = res.data.map(normalizeLaw).filter(function (x) { return x; });
                if (list.length > 0) return list;
            }
            throw new Error('API response invalid');
        });
    }

    // 回退到 mock 数据并提示
    function fallbackToMockLaws(reason) {
        console.warn('[laws-db] API 调用失败, 回退 mock:', reason);
        _lawsApiFailed = true;
        _lawsData = LAWS.slice();
        if (typeof showToast === 'function') showToast('后端不可达, 已切换本地示例数据');
    }

    // ===== 检索: 优先 API, 失败回退 mock =====
    function searchLaws() {
        showLoading();
        state.page = 1;

        function renderLocal() {
            renderLaws(getFilteredLaws());
        }

        // 后端此前已判定不可达 → 直接走 mock
        if (_lawsApiFailed || typeof API === 'undefined' || !API.laws || !API.laws.list) {
            _lawsData = LAWS.slice();
            renderLocal();
            return;
        }

        // API list 仅支持 law_type/status 过滤, 关键词/机关在本地 getFilteredLaws 二次过滤
        loadLawsFromAPI({ limit: 100 }).then(function (list) {
            _lawsData = list;
            renderLocal();
        }).catch(function (err) {
            fallbackToMockLaws(err && err.message ? err.message : err);
            renderLocal();
        });
    }

    // ===== 分类卡片筛选 =====
    function filterByCategory(category) {
        var levelSel = document.getElementById('laws-db-level');
        if (levelSel) levelSel.value = category;
        state.page = 1;
        renderLaws(getFilteredLaws());
    }

    // ===== 热门搜索 =====
    function hotSearchLaw(keyword) {
        var kwInput = document.getElementById('laws-db-keyword');
        if (kwInput) kwInput.value = keyword;
        searchLaws();
    }

    // ===== 重置搜索 =====
    function resetLawsSearch() {
        var kwInput = document.getElementById('laws-db-keyword');
        var levelSel = document.getElementById('laws-db-level');
        var organSel = document.getElementById('laws-db-organ');
        if (kwInput) kwInput.value = '';
        if (levelSel) levelSel.selectedIndex = 0;
        if (organSel) organSel.selectedIndex = 0;
        state.page = 1;
        renderLaws(_lawsData);
    }

    var _closeLawDetail = null;

    // ===== 法规详情 (toast 提示) =====
    function openLawDetail(id) {
        var law = _lawsData.find(function (x) {
            return String(x.id) === String(id);
        });
        if (!law) {
            if (typeof showToast === 'function') showToast('未找到法规 #' + id);
            return;
        }

        var levelBadge = LEVEL_STYLES[law.level] || 'bg-gray-50 text-gray-600';
        var statusCls = law.status === '已废止' ? 'bg-gray-50 text-gray-500' : 'bg-green-50 text-success';

        var content =
            '<div class="space-y-4">' +
            '<div class="p-4 bg-bg-subtle rounded-xl">' +
            '<h4 class="text-base font-semibold text-fg-primary mb-2">' +
            escapeHtml(law.name) +
            '</h4>' +
            '<div class="flex items-center gap-2 flex-wrap">' +
            '<span class="text-[10px] ' +
            levelBadge +
            ' font-medium px-2 py-0.5 rounded-full">' +
            escapeHtml(law.level) +
            '</span>' +
            '<span class="text-[10px] ' +
            statusCls +
            ' font-medium px-2 py-0.5 rounded-full">' +
            escapeHtml(law.status) +
            '</span>' +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">制定机关</p>' +
            '<p class="text-sm text-fg-primary font-medium">' +
            escapeHtml(law.organ) +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">效力层级</p>' +
            '<p class="text-sm text-fg-primary">' +
            escapeHtml(law.level) +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="p-3 bg-bg-subtle rounded-xl">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">发布信息</p>' +
            '<p class="text-xs text-fg-secondary leading-relaxed">' +
            escapeHtml(law.publishInfo) +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-bg-subtle rounded-xl">' +
            '<p class="text-[11px] text-fg-tertiary mb-2">法规内容摘要</p>' +
            '<p class="text-xs text-fg-secondary leading-relaxed">本法规涵盖' +
            escapeHtml(law.level) +
            '层面的相关规定，由' +
            escapeHtml(law.organ) +
            '制定发布，目前状态为' +
            escapeHtml(law.status) +
            '。具体条款内容请查阅全文。</p>' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeLawDetail()">关闭</button>' +
            '<button class="h-9 px-4 text-xs text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="closeLawDetail()">引用到文书</button>';

        if (_closeLawDetail) _closeLawDetail();
        _closeLawDetail = Utils.showModal({
            id: 'law-detail-modal',
            title: '法规详情',
            icon: 'mdi:book-open-outline',
            content: content,
            footer: footer,
            size: 'lg'
        });
    }

    function closeLawDetail() {
        if (_closeLawDetail) {
            _closeLawDetail();
            _closeLawDetail = null;
        }
    }

    // ===== 初始化 =====
    function initLawsDb() {
        var view = document.getElementById('view-laws-db');
        if (!view || view.dataset.lawsDbInit === '1') return;
        view.dataset.lawsDbInit = '1';

        renderStats();
        // 先渲染 mock (立即可见)
        _lawsData = LAWS.slice();
        renderLaws(_lawsData);

        var keywordInput = document.getElementById('laws-db-keyword');
        if (keywordInput) {
            keywordInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') searchLaws();
            });
        }

        // 尝试从 API 加载真实数据覆盖 (失败保持 mock)
        if (!_lawsApiFailed && typeof API !== 'undefined' && API.laws && API.laws.list) {
            showLoading();
            loadLawsFromAPI({ limit: 100 }).then(function (list) {
                _lawsData = list;
                renderLaws(getFilteredLaws());
            }).catch(function (err) {
                console.warn('[laws-db] 初始化 API 加载失败, 使用 mock:', err && err.message ? err.message : err);
                _lawsApiFailed = true;
                renderLaws(getFilteredLaws());
            });
        }
    }

    // ===== 视图首次可见时自动初始化 (router 懒加载 view, MutationObserver 监听其出现) =====
    if (document.body) {
        var observer = new MutationObserver(function () {
            var view = document.getElementById('view-laws-db');
            if (view && !view.classList.contains('hidden')) {
                initLawsDb();
                observer.disconnect();
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    // ===== 双绑定 =====
    globalThis.initLawsDb = initLawsDb;
    globalThis.searchLaws = searchLaws;
    globalThis.filterByCategory = filterByCategory;
    globalThis.openLawDetail = openLawDetail;
    globalThis.closeLawDetail = closeLawDetail;
    globalThis.hotSearchLaw = hotSearchLaw;
    globalThis.resetLawsSearch = resetLawsSearch;
    globalThis.changeLawsPage = changeLawsPage;
})();
