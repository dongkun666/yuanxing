(function() {
    'use strict';

    // ===== Mock 数据：统计卡片 =====
    var _statsData = [
        { icon: 'mdi:account-group', iconColor: 'text-brand', iconBg: 'bg-brand-tint3', value: '12', label: '团队成员' },
        { icon: 'mdi:briefcase-check', iconColor: 'text-green-500', iconBg: 'bg-green-50', value: '86', label: '在办案件' },
        { icon: 'mdi:cash-multiple', iconColor: 'text-amber-500', iconBg: 'bg-amber-50', value: '¥58万', label: '本月收费' },
        { icon: 'mdi:file-document-multiple', iconColor: 'text-purple-500', iconBg: 'bg-purple-50', value: '342', label: '合同模板' }
    ];

    // ===== Mock 数据：团队成员（12 人，与统计一致） =====
    var _membersData = [
        { id: 1, name: '张伟律师', position: '高级合伙人', field: '民商事诉讼', online: true },
        { id: 2, name: '李娜律师', position: '合伙人', field: '知识产权', online: true },
        { id: 3, name: '王强律师', position: '执业律师', field: '刑事辩护', online: false },
        { id: 4, name: '刘芳律师', position: '执业律师', field: '劳动争议', online: true },
        { id: 5, name: '陈明律师', position: '执业律师', field: '公司并购', online: true },
        { id: 6, name: '赵琳律师', position: '实习律师', field: '合同审查', online: false },
        { id: 7, name: '孙浩律师', position: '执业律师', field: '建设工程', online: true },
        { id: 8, name: '周婷律师', position: '高级合伙人', field: '国际贸易', online: false },
        { id: 9, name: '吴磊律师', position: '执业律师', field: '行政诉讼', online: true },
        { id: 10, name: '郑雪律师', position: '执业律师', field: '婚姻家事', online: true },
        { id: 11, name: '冯涛律师', position: '实习律师', field: '侵权责任', online: false },
        { id: 12, name: '许静律师', position: '合伙人', field: '金融证券', online: true }
    ];

    // 头像首字背景色循环
    var _avatarColors = [
        { bg: 'bg-brand-tint3', text: 'text-brand' },
        { bg: 'bg-purple-100', text: 'text-purple-600' },
        { bg: 'bg-amber-100', text: 'text-amber-600' },
        { bg: 'bg-blue-100', text: 'text-blue-600' },
        { bg: 'bg-green-100', text: 'text-green-600' },
        { bg: 'bg-pink-100', text: 'text-pink-600' },
        { bg: 'bg-indigo-100', text: 'text-indigo-600' },
        { bg: 'bg-teal-100', text: 'text-teal-600' }
    ];

    // 律所设置项映射
    var _settingLabels = {
        basic: '基本信息',
        members: '成员管理',
        departments: '部门设置',
        fees: '收费标准',
        contracts: '合同模板',
        permissions: '权限管理'
    };

    var _showAllMembers = false;
    var _defaultMemberCount = 4;

    // ===== 渲染统计卡片 =====
    function renderStats() {
        var container = document.getElementById('firm-stats');
        if (!container) return;
        container.innerHTML = _statsData.map(function(item) {
            return '<div class="bg-white rounded-xl border border-bg-border p-5">' +
                '<div class="flex items-center gap-3">' +
                '<div class="w-10 h-10 rounded-lg ' + item.iconBg + ' flex items-center justify-center">' +
                '<iconify-icon class="text-xl ' + item.iconColor + '" icon="' + item.icon + '"></iconify-icon>' +
                '</div>' +
                '<div>' +
                '<p class="text-2xl font-bold text-fg-primary">' + escapeHtml(item.value) + '</p>' +
                '<p class="text-[10px] text-fg-tertiary">' + escapeHtml(item.label) + '</p>' +
                '</div>' +
                '</div>' +
                '</div>';
        }).join('');
    }

    // ===== 渲染团队成员列表 =====
    function renderMemberList() {
        var container = document.getElementById('firm-member-list');
        if (!container) return;
        var list = _showAllMembers ? _membersData : _membersData.slice(0, _defaultMemberCount);
        container.innerHTML = list.map(function(member, idx) {
            var color = _avatarColors[idx % _avatarColors.length];
            var firstChar = member.name.charAt(0);
            var badgeClass = member.online
                ? 'bg-green-50 text-green-600'
                : 'bg-gray-100 text-gray-500';
            var badgeText = member.online ? '在线' : '离线';
            return '<div class="flex items-center gap-3 p-2 rounded-lg hover:bg-bg-subtle transition-colors">' +
                '<div class="w-10 h-10 rounded-full ' + color.bg + ' flex items-center justify-center flex-shrink-0">' +
                '<span class="text-sm font-semibold ' + color.text + '">' + escapeHtml(firstChar) + '</span>' +
                '</div>' +
                '<div class="flex-1 min-w-0">' +
                '<p class="text-sm font-medium text-fg-primary">' + escapeHtml(member.name) + '</p>' +
                '<p class="text-[10px] text-fg-tertiary">' + escapeHtml(member.position) + ' · ' + escapeHtml(member.field) + '</p>' +
                '</div>' +
                '<span class="text-[10px] ' + badgeClass + ' px-2 py-0.5 rounded-full cursor-pointer" onclick="toggleMemberStatus(' + member.id + ')">' + badgeText + '</span>' +
                '</div>';
        }).join('');
    }

    // ===== 成员状态切换（在线/离线） =====
    function toggleMemberStatus(id) {
        var member = _membersData.find(function(x) { return x.id === id; });
        if (!member) return;
        member.online = !member.online;
        renderMemberList();
        if (typeof showToast === 'function') {
            showToast(member.name + ' 已切换为' + (member.online ? '在线' : '离线'));
        }
    }

    // ===== 查看全部成员 =====
    function viewAllMembers() {
        _showAllMembers = !_showAllMembers;
        renderMemberList();
        if (typeof showToast === 'function') {
            showToast(_showAllMembers ? '已展开全部团队成员' : '已收起成员列表');
        }
    }

    // ===== 律所设置入口点击 =====
    function openFirmSetting(key) {
        var label = _settingLabels[key] || key;
        if (typeof showToast === 'function') {
            showToast('打开设置：' + label);
        }
    }

    // ===== 工具函数 =====
    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ===== 初始化（视图加载时调用） =====
    function initFirm() {
        renderStats();
        renderMemberList();
    }

    globalThis.initFirm = initFirm;
    globalThis.openFirmSetting = openFirmSetting;
    globalThis.viewAllMembers = viewAllMembers;
    globalThis.toggleMemberStatus = toggleMemberStatus;
})();
