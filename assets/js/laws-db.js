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
        法律: 'bg-red-50 text-red-600',
        行政法规: 'bg-amber-50 text-amber-600',
        司法解释: 'bg-blue-50 text-blue-600',
        部门规章: 'bg-green-50 text-green-600'
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

    // ===== 读取检索条件并过滤 =====
    function getFilteredLaws() {
        var kwInput = document.getElementById('laws-db-keyword');
        var levelSel = document.getElementById('laws-db-level');
        var organSel = document.getElementById('laws-db-organ');
        var keyword = ((kwInput && kwInput.value) || '').trim().toLowerCase();
        var level = (levelSel && levelSel.value) || '全部层级';
        var organ = (organSel && organSel.value) || '全部机关';

        return LAWS.filter(function (law) {
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

    // ===== 渲染法规列表 =====
    function renderLaws(list) {
        var container = document.getElementById('laws-db-results');
        if (!container) return;

        if (!list || list.length === 0) {
            container.innerHTML =
                '<div class="text-center py-12">' +
                '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:file-search-outline"></iconify-icon>' +
                '<p class="text-sm text-fg-tertiary mt-3">未找到匹配的法规</p>' +
                '<p class="text-xs text-fg-disabled mt-1">请调整关键词或筛选条件后重试</p>' +
                '</div>';
            return;
        }

        container.innerHTML = list
            .map(function (law, idx) {
                var levelBadge = LEVEL_STYLES[law.level] || 'bg-gray-50 text-gray-600';
                var statusHtml =
                    law.status === '已废止'
                        ? '<span class="text-gray-400"> · 已废止</span>'
                        : '<span class="text-fg-tertiary"> · 现行有效</span>';
                return (
                    '' +
                    '<div class="flex items-center gap-3 p-4 hover:bg-bg-subtle transition-colors cursor-pointer" onclick="openLawDetail(\'' +
                    law.id +
                    '\')">' +
                    '<span class="text-xs font-bold text-brand w-6">' +
                    (idx + 1) +
                    '</span>' +
                    '<div class="flex-1 min-w-0">' +
                    '<h3 class="text-sm font-medium text-fg-primary hover:text-brand transition-colors truncate">' +
                    escapeHtml(law.name) +
                    '</h3>' +
                    '<p class="text-[10px] text-fg-tertiary mt-0.5 truncate">' +
                    escapeHtml(law.publishInfo) +
                    statusHtml +
                    '</p>' +
                    '</div>' +
                    '<span class="text-[10px] ' +
                    levelBadge +
                    ' px-2 py-0.5 rounded-full flex-shrink-0">' +
                    law.level +
                    '</span>' +
                    '</div>'
                );
            })
            .join('');
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

    // ===== 检索 (带 1s loading) =====
    function searchLaws() {
        showLoading();
        setTimeout(function () {
            renderLaws(getFilteredLaws());
        }, 1000);
    }

    // ===== 分类卡片筛选 =====
    function filterByCategory(category) {
        var levelSel = document.getElementById('laws-db-level');
        if (levelSel) levelSel.value = category;
        renderLaws(getFilteredLaws());
    }

    var _closeLawDetail = null;

    // ===== 法规详情 (toast 提示) =====
    function openLawDetail(id) {
        var law = LAWS.find(function (x) {
            return x.id === id;
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
        renderLaws(LAWS);

        var keywordInput = document.getElementById('laws-db-keyword');
        if (keywordInput) {
            keywordInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') searchLaws();
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
})();
