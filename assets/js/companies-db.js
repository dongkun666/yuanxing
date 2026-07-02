/**
 * 企业信息库模块
 * 包含: 企业搜索 / 热门搜索 / 关注列表渲染 / 管理关注模式 / 企业详情 / 取消关注
 * 加载: 在 script.js 之后同步加载 (依赖 showToast)
 */
(function() {
    'use strict';

    // ===== Mock 企业数据 (8+ 家) =====
    var _companiesData = [
        { id: 1, name: '腾讯科技（深圳）有限公司', creditCode: '914403007192068994', legalRep: '马化腾', registeredCapital: '6,250万人民币', establishDate: '2000-02-24', status: '存续', legalRisk: 12, operatingRisk: 3, ipCount: 52340, iconBg: 'bg-brand-tint3', iconColor: 'text-brand' },
        { id: 2, name: '阿里巴巴（中国）网络技术有限公司', creditCode: '91330100799655058B', legalRep: '蒋芳', registeredCapital: '5,000万人民币', establishDate: '2007-04-11', status: '存续', legalRisk: 8, operatingRisk: 2, ipCount: 41200, iconBg: 'bg-amber-100', iconColor: 'text-amber-600' },
        { id: 3, name: '北京字节跳动科技有限公司', creditCode: '91110108551385082Q', legalRep: '梁汝波', registeredCapital: '500万人民币', establishDate: '2012-03-09', status: '存续', legalRisk: 15, operatingRisk: 6, ipCount: 38900, iconBg: 'bg-purple-100', iconColor: 'text-purple-600' },
        { id: 4, name: '百度在线网络技术（北京）有限公司', creditCode: '91110108717743207K', legalRep: '崔珊珊', registeredCapital: '4,520万美元', establishDate: '2000-01-18', status: '存续', legalRisk: 9, operatingRisk: 4, ipCount: 32100, iconBg: 'bg-blue-100', iconColor: 'text-blue-600' },
        { id: 5, name: '华为技术有限公司', creditCode: '914403001922038216', legalRep: '任正非', registeredCapital: '4,030,470.96万人民币', establishDate: '1987-09-15', status: '存续', legalRisk: 20, operatingRisk: 5, ipCount: 120000, iconBg: 'bg-red-50', iconColor: 'text-red-500' },
        { id: 6, name: '京东集团股份有限公司', creditCode: '91110000802100433C', legalRep: '许冉', registeredCapital: '30,000万人民币', establishDate: '2007-04-20', status: '存续', legalRisk: 7, operatingRisk: 3, ipCount: 25600, iconBg: 'bg-indigo-100', iconColor: 'text-indigo-600' },
        { id: 7, name: '拼多多（上海）网络科技有限公司', creditCode: '91310115MA1K3RJX2Y', legalRep: '朱健翀', registeredCapital: '1,000万人民币', establishDate: '2015-09-22', status: '注销', legalRisk: 4, operatingRisk: 1, ipCount: 8200, iconBg: 'bg-pink-100', iconColor: 'text-pink-600' },
        { id: 8, name: '滴滴出行科技有限公司', creditCode: '91110108592345678X', legalRep: '程维', registeredCapital: '10,000万人民币', establishDate: '2016-08-23', status: '吊销', legalRisk: 18, operatingRisk: 12, ipCount: 4300, iconBg: 'bg-teal-100', iconColor: 'text-teal-600' },
        { id: 9, name: '美团点评科技有限公司', creditCode: '91110108585881234A', legalRep: '王兴', registeredCapital: '5,000万人民币', establishDate: '2015-05-15', status: '存续', legalRisk: 6, operatingRisk: 2, ipCount: 15800, iconBg: 'bg-yellow-100', iconColor: 'text-yellow-600' },
        { id: 10, name: '小米科技有限责任公司', creditCode: '91110108551385099B', legalRep: '雷军', registeredCapital: '18,500万人民币', establishDate: '2010-03-03', status: '存续', legalRisk: 5, operatingRisk: 2, ipCount: 28900, iconBg: 'bg-orange-100', iconColor: 'text-orange-600' }
    ];

    // ===== 状态 =====
    // 默认关注前 8 家 (保留 2 家未关注, 便于演示搜索全量与空态)
    var _followedIds = [1, 2, 3, 4, 5, 6, 7, 8];
    var _manageMode = false;
    var _isLoading = false;
    var _closeCompanyDetail = null;

    function showToastMsg(msg) {
        if (typeof showToast === 'function') {
            showToast(msg);
        }
    }

    // 经营状态 badge: 存续=绿色 / 注销=灰色 / 吊销=红色
    function getStatusBadge(status) {
        if (status === '存续') {
            return '<span class="text-[10px] bg-green-50 text-green-600 px-2 py-0.5 rounded-full flex-shrink-0">存续</span>';
        }
        if (status === '注销') {
            return '<span class="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full flex-shrink-0">注销</span>';
        }
        if (status === '吊销') {
            return '<span class="text-[10px] bg-red-50 text-red-600 px-2 py-0.5 rounded-full flex-shrink-0">吊销</span>';
        }
        return '<span class="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full flex-shrink-0">' + escapeHtml(status) + '</span>';
    }

    function getSearchKeyword() {
        var input = document.getElementById('companies-db-search');
        return input ? (input.value || '').trim() : '';
    }

    // 在关注列表中按 名称 / 统一社会信用代码 / 法定代表人 过滤
    function getFilteredCompanies() {
        var keyword = getSearchKeyword().toLowerCase();
        return _companiesData.filter(function(c) {
            if (_followedIds.indexOf(c.id) === -1) return false;
            if (!keyword) return true;
            return (c.name || '').toLowerCase().indexOf(keyword) > -1 ||
                   (c.creditCode || '').toLowerCase().indexOf(keyword) > -1 ||
                   (c.legalRep || '').toLowerCase().indexOf(keyword) > -1;
        });
    }

    // ===== 渲染 =====
    function renderCompanyCard(company) {
        var manageBtn = '';
        if (_manageMode) {
            manageBtn = '<button class="text-[10px] text-red-500 hover:text-red-600 hover:underline flex-shrink-0 ml-3" onclick="event.stopPropagation(); unfollowCompany(' + company.id + ')">' +
                '<iconify-icon class="inline" icon="mdi:close-circle-outline"></iconify-icon> 取消关注' +
                '</button>';
        }

        return '<div class="p-5 hover:bg-bg-subtle transition-colors cursor-pointer" onclick="openCompanyDetail(' + company.id + ')">' +
            '<div class="flex items-start gap-4">' +
            '<div class="w-12 h-12 rounded-lg ' + company.iconBg + ' flex items-center justify-center flex-shrink-0">' +
            '<iconify-icon class="text-2xl ' + company.iconColor + '" icon="mdi:domain"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-center gap-2 mb-1">' +
            '<h3 class="text-sm font-semibold text-fg-primary truncate">' + escapeHtml(company.name) + '</h3>' +
            getStatusBadge(company.status) +
            '</div>' +
            '<div class="grid grid-cols-3 gap-4 text-[10px] text-fg-tertiary">' +
            '<div><span class="text-fg-disabled">法定代表人：</span><span class="text-fg-secondary">' + escapeHtml(company.legalRep) + '</span></div>' +
            '<div><span class="text-fg-disabled">注册资本：</span><span class="text-fg-secondary">' + escapeHtml(company.registeredCapital) + '</span></div>' +
            '<div><span class="text-fg-disabled">成立日期：</span><span class="text-fg-secondary">' + escapeHtml(company.establishDate) + '</span></div>' +
            '</div>' +
            '<div class="flex items-center gap-4 mt-2 text-[10px]">' +
            '<span class="text-red-500"><iconify-icon class="inline" icon="mdi:alert-circle-outline"></iconify-icon> 法律风险 ' + company.legalRisk + '</span>' +
            '<span class="text-amber-500"><iconify-icon class="inline" icon="mdi:alert-outline"></iconify-icon> 经营风险 ' + company.operatingRisk + '</span>' +
            '<span class="text-blue-500"><iconify-icon class="inline" icon="mdi:information-outline"></iconify-icon> 知识产权 ' + company.ipCount + '</span>' +
            manageBtn +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>';
    }

    function renderLoading() {
        var container = document.getElementById('companies-db-results');
        if (!container) return;
        container.innerHTML =
            '<div class="p-8 text-center">' +
            '<iconify-icon class="text-2xl text-brand animate-spin inline-block" icon="mdi:loading"></iconify-icon>' +
            '<p class="text-xs text-fg-tertiary mt-2">正在查询企业信息...</p>' +
            '</div>';
    }

    function renderEmpty(message) {
        var container = document.getElementById('companies-db-results');
        if (!container) return;
        var msg = message || '暂无关注的企业';
        container.innerHTML =
            '<div class="p-12 text-center">' +
            '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:domain-off"></iconify-icon>' +
            '<p class="text-sm text-fg-tertiary mt-3">' + escapeHtml(msg) + '</p>' +
            '</div>';
    }

    function renderCompanies() {
        var container = document.getElementById('companies-db-results');
        if (!container) return;
        if (_isLoading) return;

        var filtered = getFilteredCompanies();
        if (filtered.length === 0) {
            var keyword = getSearchKeyword();
            renderEmpty(keyword ? '未找到匹配 "' + keyword + '" 的企业' : '暂无关注的企业');
            updateManageButton();
            return;
        }

        container.innerHTML = filtered.map(function(c) {
            return renderCompanyCard(c);
        }).join('');

        updateManageButton();
    }

    function updateManageButton() {
        var btn = document.getElementById('companies-db-manage-btn');
        if (!btn) return;
        btn.textContent = _manageMode ? '完成' : '管理关注';
    }

    // ===== 对外功能 =====
    function searchCompanies() {
        renderLoading();
        _isLoading = true;
        // 1 秒 loading 状态后展示结果
        setTimeout(function() {
            _isLoading = false;
            renderCompanies();
        }, 1000);
    }

    function hotSearch(keyword) {
        var input = document.getElementById('companies-db-search');
        if (input) {
            input.value = keyword;
        }
        searchCompanies();
    }

    function toggleManageMode() {
        _manageMode = !_manageMode;
        if (_manageMode) {
            showToastMsg('已进入管理关注模式，可取消关注企业');
        } else {
            showToastMsg('已退出管理关注模式');
        }
        renderCompanies();
    }

    function openCompanyDetail(id) {
        var company = _companiesData.find(function(c) { return c.id === id; });
        if (!company) {
            showToastMsg('未找到企业 #' + id);
            return;
        }

        var content = '<div class="space-y-4">' +
            '<div class="flex items-center gap-4 p-4 bg-bg-subtle rounded-xl">' +
            '<div class="w-16 h-16 rounded-xl ' + company.iconBg + ' flex items-center justify-center flex-shrink-0">' +
            '<iconify-icon class="text-3xl ' + company.iconColor + '" icon="mdi:domain"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-center gap-2 mb-1">' +
            '<h4 class="text-base font-semibold text-fg-primary">' + escapeHtml(company.name) + '</h4>' +
            getStatusBadge(company.status) +
            '</div>' +
            '<p class="text-xs text-fg-tertiary font-mono">' + escapeHtml(company.creditCode) + '</p>' +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">法定代表人</p>' +
            '<p class="text-sm text-fg-primary font-medium">' + escapeHtml(company.legalRep) + '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">注册资本</p>' +
            '<p class="text-sm text-fg-primary">' + escapeHtml(company.registeredCapital) + '</p>' +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">成立日期</p>' +
            '<p class="text-sm text-fg-primary">' + escapeHtml(company.establishDate) + '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">经营状态</p>' +
            '<p class="text-sm text-fg-primary">' + escapeHtml(company.status) + '</p>' +
            '</div>' +
            '</div>' +
            '<div class="p-4 bg-bg-subtle rounded-xl">' +
            '<p class="text-[11px] text-fg-tertiary mb-3">风险概览</p>' +
            '<div class="grid grid-cols-3 gap-4">' +
            '<div class="text-center">' +
            '<div class="w-12 h-12 mx-auto rounded-full bg-red-50 flex items-center justify-center">' +
            '<iconify-icon class="text-red-500" icon="mdi:alert-circle-outline"></iconify-icon>' +
            '</div>' +
            '<p class="text-lg font-bold text-red-500 mt-2">' + company.legalRisk + '</p>' +
            '<p class="text-[10px] text-fg-tertiary">法律风险</p>' +
            '</div>' +
            '<div class="text-center">' +
            '<div class="w-12 h-12 mx-auto rounded-full bg-amber-50 flex items-center justify-center">' +
            '<iconify-icon class="text-amber-500" icon="mdi:alert-outline"></iconify-icon>' +
            '</div>' +
            '<p class="text-lg font-bold text-amber-500 mt-2">' + company.operatingRisk + '</p>' +
            '<p class="text-[10px] text-fg-tertiary">经营风险</p>' +
            '</div>' +
            '<div class="text-center">' +
            '<div class="w-12 h-12 mx-auto rounded-full bg-blue-50 flex items-center justify-center">' +
            '<iconify-icon class="text-blue-500" icon="mdi:information-outline"></iconify-icon>' +
            '</div>' +
            '<p class="text-lg font-bold text-blue-500 mt-2">' + company.ipCount.toLocaleString() + '</p>' +
            '<p class="text-[10px] text-fg-tertiary">知识产权</p>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>';

        var footer = '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeCompanyDetail()">关闭</button>' +
            '<button class="h-9 px-4 text-xs text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="closeCompanyDetail()">关联案件</button>';

        if (_closeCompanyDetail) _closeCompanyDetail();
        _closeCompanyDetail = Utils.showModal({
            id: 'company-detail-modal',
            title: '企业详情',
            icon: 'mdi:domain',
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

    function unfollowCompany(id) {
        var idx = _followedIds.indexOf(id);
        if (idx === -1) return;
        var company = _companiesData.find(function(c) { return c.id === id; });
        _followedIds.splice(idx, 1);
        if (company) {
            showToastMsg('已取消关注：' + company.name);
        }
        renderCompanies();
    }

    function initCompaniesDb() {
        _manageMode = false;
        _isLoading = false;
        renderCompanies();
    }

    // ===== globalThis 桥接 =====
    globalThis.initCompaniesDb = initCompaniesDb;
    globalThis.searchCompanies = searchCompanies;
    globalThis.hotSearch = hotSearch;
    globalThis.toggleManageMode = toggleManageMode;
    globalThis.openCompanyDetail = openCompanyDetail;
    globalThis.closeCompanyDetail = closeCompanyDetail;
    globalThis.unfollowCompany = unfollowCompany;
})();
