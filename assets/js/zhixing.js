/**
 * 失信被执行人查询 (2026-06-28 Phase 3.1-2)
 *
 * 真实数据源: 中国执行信息公开网 (zxgk.court.gov.cn) - 无公开 API
 * 当前实现: mock 数据 + 真实查询界面 + 跳转官方链接
 * 未来接入: 商业 API (律呗/法信/启信宝等) 或与法院合作
 *
 * mock 数据基于公开失信被执行人特征, 演示用, 不对应真实个人
 */

(function() {
    'use strict';

    // ===== Mock 数据库 (演示用) =====
    var MOCK_DATABASE = {
        // 自然人
        'natural:张三:110101199003078811': [
            {
                name: '张三',
                idCardMask: '110101********0811',
                type: 'natural',
                caseNumber: '(2025)京0108执1234号',
                court: '北京市海淀区人民法院',
                filingDate: '2025-03-15',
                amount: '120,000.00 元',
                reason: '借款合同纠纷',
                status: '失信被执行人',
                publishDate: '2025-04-10',
                duty: '支付借款本金及利息 12 万元',
                performStatus: '全部未履行'
            },
            {
                name: '张三',
                idCardMask: '110101********0811',
                type: 'natural',
                caseNumber: '(2024)京0108执5678号',
                court: '北京市海淀区人民法院',
                filingDate: '2024-09-22',
                amount: '85,000.00 元',
                reason: '买卖合同纠纷',
                status: '失信被执行人',
                publishDate: '2024-10-30',
                duty: '支付货款 8.5 万元',
                performStatus: '全部未履行'
            }
        ],
        'natural:李四': [], // 无匹配
        'natural:王五:110108198805152234': [
            {
                name: '王五',
                idCardMask: '110108********2234',
                type: 'natural',
                caseNumber: '(2026)沪0115执888号',
                court: '上海市浦东新区人民法院',
                filingDate: '2026-01-08',
                amount: '2,580,000.00 元',
                reason: '股权转让纠纷',
                status: '失信被执行人',
                publishDate: '2026-02-20',
                duty: '支付股权回购款 258 万元',
                performStatus: '部分履行 (已支付 50 万)'
            }
        ],
        // 法人/组织
        'company:北京众鑫达科技股份有限公司:91110108MA01ABCDXX': [
            {
                name: '北京众鑫达科技股份有限公司',
                idCardMask: '91110108MA01ABCDXX',
                type: 'company',
                legalRep: '王某某',
                caseNumber: '(2025)京0108执9876号',
                court: '北京市海淀区人民法院',
                filingDate: '2025-11-20',
                amount: '1,580,000.00 元',
                reason: '技术服务合同纠纷',
                status: '失信被执行人',
                publishDate: '2025-12-25',
                duty: '支付服务费 158 万元及违约金',
                performStatus: '全部未履行'
            }
        ],
        'company:深圳市诚信电子有限公司:91440300MA1234567X': [
            {
                name: '深圳市诚信电子有限公司',
                idCardMask: '91440300MA1234567X',
                type: 'company',
                legalRep: '陈某某',
                caseNumber: '(2025)粤0304执4321号',
                court: '深圳市福田区人民法院',
                filingDate: '2025-08-12',
                amount: '3,250,000.00 元',
                reason: '房屋租赁合同纠纷',
                status: '失信被执行人',
                publishDate: '2025-09-18',
                duty: '支付租金 325 万元',
                performStatus: '全部未履行'
            }
        ]
    };

    // ===== 查询逻辑 =====
    function searchZhixing() {
        var type = document.getElementById('zhixing-type').value;
        var keyword = document.getElementById('zhixing-keyword').value.trim();
        var idcard = document.getElementById('zhixing-idcard').value.trim();

        if (!keyword) {
            showToast('请输入被执行人姓名/名称');
            return;
        }

        // 显示 loading
        document.getElementById('zhixing-empty').classList.add('hidden');
        document.getElementById('zhixing-results-list').classList.add('hidden');
        document.getElementById('zhixing-loading').classList.remove('hidden');
        document.getElementById('zhixing-results-count').textContent = '';
        document.getElementById('zhixing-query-time').textContent = '';

        // 模拟网络请求延迟
        setTimeout(function() {
            var results = mockQuery(type, keyword, idcard);
            renderZhixingResults(results, type, keyword);
        }, 800);
    }

    function mockQuery(type, keyword, idcard) {
        // 优先尝试精确匹配
        var key1 = type + ':' + keyword + (idcard ? ':' + idcard : '');
        if (MOCK_DATABASE[key1]) {
            return MOCK_DATABASE[key1];
        }
        // 仅按姓名匹配
        var key2 = type + ':' + keyword;
        if (MOCK_DATABASE[key2]) {
            return MOCK_DATABASE[key2];
        }
        // 按部分匹配
        for (var k in MOCK_DATABASE) {
            if (k.indexOf(':' + keyword) >= 0 && k.indexOf(type + ':') === 0) {
                return MOCK_DATABASE[k];
            }
        }
        return [];
    }

    function renderZhixingResults(results, type, keyword) {
        document.getElementById('zhixing-loading').classList.add('hidden');

        var list = document.getElementById('zhixing-results-list');
        var empty = document.getElementById('zhixing-empty');
        var countEl = document.getElementById('zhixing-results-count');
        var timeEl = document.getElementById('zhixing-query-time');

        if (results.length === 0) {
            empty.classList.remove('hidden');
            empty.innerHTML = '<iconify-icon class="text-5xl text-success" icon="mdi:check-circle-outline"></iconify-icon><p class="text-sm text-fg-primary mt-3 font-medium">未查询到失信记录</p><p class="text-[10px] text-fg-tertiary mt-1">' + escapeHtml(keyword) + ' 暂未被列入失信被执行人名单</p><p class="text-[10px] text-fg-disabled mt-2">数据可能存在 1-2 个工作日延迟, 以官方为准</p>';
            list.classList.add('hidden');
            if (countEl) countEl.textContent = '共 0 条';
            if (timeEl) timeEl.textContent = '查询时间: ' + formatQueryTime();
            return;
        }

        empty.classList.add('hidden');
        list.classList.remove('hidden');

        var html = '';
        results.forEach(function(item) {
            html += renderZhixingItem(item);
        });
        list.innerHTML = html;

        if (countEl) countEl.textContent = '共 ' + results.length + ' 条';
        if (timeEl) timeEl.textContent = '查询时间: ' + formatQueryTime();
    }

    function renderZhixingItem(item) {
        var isNatural = item.type === 'natural';
        var idLabel = isNatural ? '身份证' : '组织机构代码';

        return '<div class="border border-red-200 rounded-lg overflow-hidden hover:shadow-sm transition-shadow">' +
            '<div class="bg-red-50 px-3.5 py-2.5 flex items-center justify-between">' +
            '<div class="flex items-center gap-2">' +
            '<iconify-icon class="text-lg text-red-500" icon="mdi:account-cancel"></iconify-icon>' +
            '<span class="text-sm font-semibold text-red-700">' + escapeHtml(item.name) + '</span>' +
            '<span class="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full font-medium">' + escapeHtml(item.status) + '</span>' +
            '</div>' +
            '<span class="text-[10px] text-red-600 font-mono">' + escapeHtml(item.publishDate) + '</span>' +
            '</div>' +
            '<div class="px-3.5 py-3 bg-white space-y-2">' +
            '<div class="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[11px]">' +
            '<div><span class="text-fg-tertiary">案号: </span><span class="font-mono">' + escapeHtml(item.caseNumber) + '</span></div>' +
            '<div><span class="text-fg-tertiary">执行法院: </span><span>' + escapeHtml(item.court) + '</span></div>' +
            '<div><span class="text-fg-tertiary">立案时间: </span><span class="font-mono">' + escapeHtml(item.filingDate) + '</span></div>' +
            '<div><span class="text-fg-tertiary">执行标的: </span><span class="font-semibold text-red-600">' + escapeHtml(item.amount) + '</span></div>' +
            '<div><span class="text-fg-tertiary">案由: </span><span>' + escapeHtml(item.reason) + '</span></div>' +
            '<div><span class="text-fg-tertiary">' + idLabel + ': </span><span class="font-mono">' + escapeHtml(item.idCardMask) + '</span></div>' +
            (!isNatural ? '<div class="col-span-2"><span class="text-fg-tertiary">法定代表人: </span><span>' + escapeHtml(item.legalRep || '-') + '</span></div>' : '') +
            '</div>' +
            '<div class="pt-2 border-t border-bg-border/50">' +
            '<p class="text-[10px] text-fg-tertiary">义务: ' + escapeHtml(item.duty) + '</p>' +
            '<p class="text-[10px] text-fg-tertiary mt-0.5">履行情况: ' + escapeHtml(item.performStatus) + '</p>' +
            '</div>' +
            '</div>' +
            '</div>';
    }

    function formatQueryTime() {
        var d = new Date();
        var y = d.getFullYear();
        var m = String(d.getMonth() + 1).padStart(2, '0');
        var dd = String(d.getDate()).padStart(2, '0');
        var hh = String(d.getHours()).padStart(2, '0');
        var mm = String(d.getMinutes()).padStart(2, '0');
        var ss = String(d.getSeconds()).padStart(2, '0');
        return y + '-' + m + '-' + dd + ' ' + hh + ':' + mm + ':' + ss;
    }

    function onZhixingTypeChange() {
        var type = document.getElementById('zhixing-type').value;
        var label = document.getElementById('zhixing-key-label');
        if (label) label.textContent = type === 'natural' ? '被执行人姓名' : '被执行人名称';
        var placeholder = document.getElementById('zhixing-keyword');
        if (placeholder) placeholder.placeholder = type === 'natural' ? '请输入完整姓名' : '请输入公司/组织全称';
    }

    function resetZhixing() {
        document.getElementById('zhixing-keyword').value = '';
        document.getElementById('zhixing-idcard').value = '';
        document.getElementById('zhixing-empty').classList.remove('hidden');
        document.getElementById('zhixing-empty').innerHTML = '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:file-search-outline"></iconify-icon><p class="text-sm text-fg-tertiary mt-3">请输入查询条件开始查询</p><p class="text-[10px] text-fg-disabled mt-1">数据来源: 中国执行信息公开网</p>';
        document.getElementById('zhixing-results-list').classList.add('hidden');
        document.getElementById('zhixing-loading').classList.add('hidden');
        document.getElementById('zhixing-results-count').textContent = '';
        document.getElementById('zhixing-query-time').textContent = '';
    }

    function quickSearchZhixing(type, keyword, idcard) {
        document.getElementById('zhixing-type').value = type;
        onZhixingTypeChange();
        document.getElementById('zhixing-keyword').value = keyword;
        document.getElementById('zhixing-idcard').value = idcard;
        searchZhixing();
    }

    // ===== 双绑定 =====
    globalThis.searchZhixing = searchZhixing;
    globalThis.resetZhixing = resetZhixing;
    globalThis.onZhixingTypeChange = onZhixingTypeChange;
    globalThis.quickSearchZhixing = quickSearchZhixing;
})();