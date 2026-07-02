/**
 * 执行案件查询 - UI 逻辑
 *
 * 视图: templates/views/zhixing.html
 * 数据来源: 最高人民法院中国执行信息公开网 (mock)
 * 功能: 多条件查询 (姓名/企业名称、身份证号/统一社会信用代码、执行法院)
 *       查询结果表格渲染 / 空态处理 / 案件状态颜色区分 / 重置
 */

(function() {
    'use strict';

    // ===== Mock 数据 (覆盖 执行中 / 已终结 / 已结案 / 终结本次执行) =====
    var mockData = [
        { caseNum: '(2026)京01执123号', name: '张三', idcard: '110101199001011234', court: '北京市第一中级人民法院', date: '2026-03-15', amount: '500,000元', status: '执行中' },
        { caseNum: '(2025)京02执456号', name: '李四', idcard: '110102198812120045', court: '北京市第二中级人民法院', date: '2025-11-20', amount: '1,200,000元', status: '已终结' },
        { caseNum: '(2026)京03执789号', name: '王五', idcard: '110103199503030678', court: '北京市第三中级人民法院', date: '2026-01-10', amount: '800,000元', status: '执行中' },
        { caseNum: '(2025)沪01执021号', name: '赵六', idcard: '310101199207071234', court: '上海市第一中级人民法院', date: '2025-09-08', amount: '350,000元', status: '已结案' },
        { caseNum: '(2026)沪0115执115号', name: '钱七', idcard: '31011519890101567X', court: '上海市浦东新区人民法院', date: '2026-02-18', amount: '2,500,000元', status: '终结本次执行' },
        { caseNum: '(2026)粤01执330号', name: '孙八', idcard: '440106199410102345', court: '广州市中级人民法院', date: '2026-04-02', amount: '780,000元', status: '执行中' },
        { caseNum: '(2025)粤0304执058号', name: '周九', idcard: '440304198806063456', court: '深圳市中级人民法院', date: '2025-12-25', amount: '600,000元', status: '已结案' },
        { caseNum: '(2025)浙01执212号', name: '吴十', idcard: '330101199012124567', court: '杭州市中级人民法院', date: '2025-08-14', amount: '920,000元', status: '已终结' },
        { caseNum: '(2026)苏01执077号', name: '郑十一', idcard: '320102198705055678', court: '南京市中级人民法院', date: '2026-05-06', amount: '1,500,000元', status: '终结本次执行' },
        { caseNum: '(2026)京0105执886号', name: '北京宏达科技有限公司', idcard: '91110105MA01ABC234', court: '北京市朝阳区人民法院', date: '2026-03-28', amount: '3,800,000元', status: '执行中' }
    ];

    // ===== 工具 =====
    function escapeHtml(s) {
        if (s == null) return '';
        return String(s).replace(/[&<>"']/g, function(c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    function toast(msg) {
        if (typeof showToast === 'function') showToast(msg);
    }

    function getEl(id) { return document.getElementById(id); }
    function getVal(id) { var el = getEl(id); return el ? el.value.trim() : ''; }

    // 案件状态颜色映射
    // 执行中=amber, 已终结=gray, 已结案=green, 终结本次执行=red
    var statusColorMap = {
        '执行中': 'bg-amber-100 text-amber-700',
        '已终结': 'bg-gray-100 text-gray-600',
        '已结案': 'bg-green-100 text-green-700',
        '终结本次执行': 'bg-red-100 text-red-700'
    };

    function getStatusColor(status) {
        return statusColorMap[status] || 'bg-gray-100 text-gray-600';
    }

    // 初始空态 HTML (重置时恢复)
    var initialEmptyHtml =
        '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:gavel"></iconify-icon>' +
        '<p class="text-sm text-fg-tertiary mt-3">请输入查询条件开始搜索</p>' +
        '<p class="text-[10px] text-fg-disabled mt-1">数据来源: 中国执行信息公开网</p>';

    // 无结果空态 HTML
    var noResultEmptyHtml =
        '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:file-question-outline"></iconify-icon>' +
        '<p class="text-sm text-fg-primary mt-3 font-medium">未查询到执行信息</p>' +
        '<p class="text-[10px] text-fg-tertiary mt-1">请核对查询条件是否正确</p>';

    // ===== 查询 =====
    function searchZhixing() {
        var name = getVal('zhixing-name');
        var idcard = getVal('zhixing-idcard');
        var court = getVal('zhixing-court');

        var empty = getEl('zhixing-empty');
        var results = getEl('zhixing-results');
        var tbody = getEl('zhixing-table-body');
        var countEl = getEl('zhixing-result-count');

        if (!results || !tbody) return;

        if (empty) empty.classList.add('hidden');
        results.classList.remove('hidden');

        tbody.innerHTML =
            '<tr><td colspan="6" class="py-10 text-center text-fg-tertiary">' +
                '<iconify-icon class="text-base animate-spin align-middle" icon="mdi:loading"></iconify-icon>' +
                ' <span class="text-xs align-middle">查询中...</span>' +
            '</td></tr>';
        if (countEl) countEl.textContent = '';

        setTimeout(function() {
            var filtered = mockData.filter(function(item) {
                if (name && item.name.indexOf(name) < 0) return false;
                if (idcard && item.idcard.indexOf(idcard) < 0) return false;
                if (court && item.court.indexOf(court) < 0) return false;
                return true;
            });

            if (filtered.length === 0) {
                if (empty) {
                    empty.classList.remove('hidden');
                    empty.innerHTML = noResultEmptyHtml;
                }
                results.classList.add('hidden');
                toast('未查询到符合条件的执行案件');
                return;
            }

            tbody.innerHTML = filtered.map(function(item) {
                return '<tr class="hover:bg-bg-subtle transition-colors cursor-pointer" onclick="openZhixingDetail(\'' + escapeHtml(item.caseNum) + '\')">' +
                    '<td class="py-3 px-4 text-xs font-mono text-fg-primary">' + escapeHtml(item.caseNum) + '</td>' +
                    '<td class="py-3 px-4 text-xs text-fg-secondary">' + escapeHtml(item.name) + '</td>' +
                    '<td class="py-3 px-4 text-xs text-fg-secondary">' + escapeHtml(item.court) + '</td>' +
                    '<td class="py-3 px-4 text-xs text-fg-tertiary">' + escapeHtml(item.date) + '</td>' +
                    '<td class="py-3 px-4 text-xs text-fg-secondary">' + escapeHtml(item.amount) + '</td>' +
                    '<td class="text-center py-3 px-4">' +
                        '<span class="text-[10px] ' + getStatusColor(item.status) + ' font-medium px-2 py-0.5 rounded-full">' + escapeHtml(item.status) + '</span>' +
                    '</td>' +
                '</tr>';
            }).join('');

            if (countEl) countEl.textContent = '共 ' + filtered.length + ' 条结果';
            toast('查询完成, 共 ' + filtered.length + ' 条结果');
        }, 1000);
    }

    // ===== 重置 =====
    function resetZhixing() {
        var nameEl = getEl('zhixing-name');
        var idcardEl = getEl('zhixing-idcard');
        var courtEl = getEl('zhixing-court');
        var empty = getEl('zhixing-empty');
        var results = getEl('zhixing-results');

        if (nameEl) nameEl.value = '';
        if (idcardEl) idcardEl.value = '';
        if (courtEl) courtEl.value = '';

        if (empty) {
            empty.classList.remove('hidden');
            empty.innerHTML = initialEmptyHtml;
        }
        if (results) results.classList.add('hidden');

        toast('已重置查询条件');
    }

    var _closeZhixingDetail = null;

    // ===== 执行案件详情弹窗 =====
    function openZhixingDetail(caseNum) {
        var item = mockData.find(function(x) { return x.caseNum === caseNum; });
        if (!item) {
            toast('未找到案件 ' + caseNum);
            return;
        }
        var statusColor = getStatusColor(item.status);

        var idLabel = (item.name && item.name.indexOf('公司') >= 0 || item.name.indexOf('有限') >= 0) ? '统一社会信用代码' : '身份证号';

        var content = '<div class="space-y-4">' +
            '<div class="p-3 bg-bg-subtle rounded-xl">' +
            '<div class="flex items-center gap-2 flex-wrap mb-2">' +
            '<span class="text-sm font-semibold font-mono text-fg-primary">' + escapeHtml(item.caseNum) + '</span>' +
            '<span class="text-[10px] ' + statusColor + ' font-medium px-2 py-0.5 rounded-full">' + escapeHtml(item.status) + '</span>' +
            '</div>' +
            '<p class="text-xs text-fg-secondary">' + escapeHtml(item.court) + '</p>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">被执行人</p>' +
            '<p class="text-sm font-semibold text-fg-primary">' + escapeHtml(item.name) + '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">' + idLabel + '</p>' +
            '<p class="text-xs font-mono text-fg-primary">' + escapeHtml(item.idcard) + '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">执行法院</p>' +
            '<p class="text-sm text-fg-primary">' + escapeHtml(item.court) + '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">立案日期</p>' +
            '<p class="text-sm text-fg-primary">' + escapeHtml(item.date) + '</p>' +
            '</div>' +
            '</div>' +
            '<div class="p-4 bg-brand-tint rounded-xl">' +
            '<p class="text-[11px] text-brand mb-1">执行标的</p>' +
            '<p class="text-2xl font-bold text-brand">' + escapeHtml(item.amount) + '</p>' +
            '</div>' +
            '<div class="text-[11px] text-fg-tertiary flex items-center gap-1">' +
            '<iconify-icon icon="mdi:information-outline"></iconify-icon>' +
            '数据来源: 中国执行信息公开网 (最高人民法院)' +
            '</div>' +
            '</div>';

        var footer = '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeZhixingDetail()">关闭</button>' +
            '<button class="h-9 px-4 text-xs text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="closeZhixingDetail()">返回列表</button>';

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

    // ===== 初始化 (视图加载时绑定事件) =====
    function initZhixing() {
        var view = getEl('view-zhixing');
        if (!view) return;
        if (view.dataset.zhixingInit) return;
        view.dataset.zhixingInit = '1';

        var inputIds = ['zhixing-name', 'zhixing-idcard', 'zhixing-court'];
        inputIds.forEach(function(id) {
            var el = getEl(id);
            if (el) {
                el.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' || e.keyCode === 13) {
                        e.preventDefault();
                        searchZhixing();
                    }
                });
            }
        });
    }

    // ===== 暴露 =====
    globalThis.initZhixing = initZhixing;
    globalThis.searchZhixing = searchZhixing;
    globalThis.resetZhixing = resetZhixing;
    globalThis.openZhixingDetail = openZhixingDetail;
    globalThis.closeZhixingDetail = closeZhixingDetail;
})();
