(function () {
    'use strict';

    function escapeHtml(s) {
        if (s === null || s === undefined) return '';
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    // ===== Mock 数据：统计卡片 =====
    var _statsData = [
        {
            icon: 'mdi:account-group',
            iconColor: 'text-brand',
            iconBg: 'bg-brand-tint3',
            value: '12',
            label: '团队成员'
        },
        {
            icon: 'mdi:briefcase-check',
            iconColor: 'text-green-500',
            iconBg: 'bg-green-50',
            value: '86',
            label: '在办案件'
        },
        {
            icon: 'mdi:cash-multiple',
            iconColor: 'text-amber-500',
            iconBg: 'bg-amber-50',
            value: '¥58万',
            label: '本月收费'
        },
        {
            icon: 'mdi:file-document-multiple',
            iconColor: 'text-purple-500',
            iconBg: 'bg-purple-50',
            value: '342',
            label: '合同模板'
        }
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
    var _closeFirmSetting = null;
    var _closeMemberDetail = null;

    // ===== 渲染统计卡片 =====
    function renderStats() {
        var container = document.getElementById('firm-stats');
        if (!container) return;
        container.innerHTML = _statsData
            .map(function (item) {
                return (
                    '<div class="bg-white rounded-xl border border-bg-border p-5">' +
                    '<div class="flex items-center gap-3">' +
                    '<div class="w-10 h-10 rounded-lg ' +
                    item.iconBg +
                    ' flex items-center justify-center">' +
                    '<iconify-icon class="text-xl ' +
                    item.iconColor +
                    '" icon="' +
                    item.icon +
                    '"></iconify-icon>' +
                    '</div>' +
                    '<div>' +
                    '<p class="text-2xl font-bold text-fg-primary">' +
                    escapeHtml(item.value) +
                    '</p>' +
                    '<p class="text-[10px] text-fg-tertiary">' +
                    escapeHtml(item.label) +
                    '</p>' +
                    '</div>' +
                    '</div>' +
                    '</div>'
                );
            })
            .join('');
    }

    // ===== 渲染团队成员列表 =====
    function renderMemberList() {
        var container = document.getElementById('firm-member-list');
        if (!container) return;
        var list = _showAllMembers ? _membersData : _membersData.slice(0, _defaultMemberCount);
        container.innerHTML = list
            .map(function (member, idx) {
                var color = _avatarColors[idx % _avatarColors.length];
                var firstChar = member.name.charAt(0);
                var badgeClass = member.online ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-500';
                var badgeText = member.online ? '在线' : '离线';
                return (
                    '<div class="flex items-center gap-3 p-2 rounded-lg hover:bg-bg-subtle transition-colors cursor-pointer" onclick="openMemberDetail(' +
                    member.id +
                    ')">' +
                    '<div class="w-10 h-10 rounded-full ' +
                    color.bg +
                    ' flex items-center justify-center flex-shrink-0">' +
                    '<span class="text-sm font-semibold ' +
                    color.text +
                    '">' +
                    escapeHtml(firstChar) +
                    '</span>' +
                    '</div>' +
                    '<div class="flex-1 min-w-0">' +
                    '<p class="text-sm font-medium text-fg-primary">' +
                    escapeHtml(member.name) +
                    '</p>' +
                    '<p class="text-[10px] text-fg-tertiary">' +
                    escapeHtml(member.position) +
                    ' · ' +
                    escapeHtml(member.field) +
                    '</p>' +
                    '</div>' +
                    '<span class="text-[10px] ' +
                    badgeClass +
                    ' px-2 py-0.5 rounded-full cursor-pointer" onclick="toggleMemberStatus(' +
                    member.id +
                    ')">' +
                    badgeText +
                    '</span>' +
                    '</div>'
                );
            })
            .join('');
    }

    // ===== 成员状态切换（在线/离线） =====
    function toggleMemberStatus(id) {
        var member = _membersData.find(function (x) {
            return x.id === id;
        });
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

        var tabs = Object.keys(_settingLabels);
        var tabsHtml = '<div class="flex flex-wrap gap-1 p-1 bg-bg-subtle rounded-lg">';
        tabs.forEach(function (t) {
            var active = t === key;
            tabsHtml +=
                '<button class="flex-1 min-w-[70px] text-[11px] py-1.5 px-2 rounded-md transition-colors ' +
                (active
                    ? 'bg-white text-fg-primary shadow-sm font-medium'
                    : 'text-fg-tertiary hover:text-fg-secondary') +
                '" onclick="switchFirmSettingTab(\'' +
                t +
                '\')">' +
                _settingLabels[t] +
                '</button>';
        });
        tabsHtml += '</div>';

        var contentHtml = renderFirmSettingContent(key);

        var content =
            '<div class="space-y-4">' +
            tabsHtml +
            '<div id="firm-setting-content">' +
            contentHtml +
            '</div>' +
            '</div>';

        var footer =
            '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeFirmSetting()">关闭</button>' +
            '<button class="h-9 px-4 text-xs text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="saveFirmSetting()">保存设置</button>';

        if (_closeFirmSetting) _closeFirmSetting();
        _closeFirmSetting = Utils.showModal({
            id: 'firm-setting-modal',
            title: '律所设置 - ' + escapeHtml(label),
            icon: 'mdi:cog-outline',
            content: content,
            footer: footer,
            size: 'lg'
        });

        _currentSettingTab = key;
    }

    var _currentSettingTab = 'basic';

    function switchFirmSettingTab(key) {
        _currentSettingTab = key;
        var label = _settingLabels[key] || key;
        var content = document.getElementById('firm-setting-content');
        if (content) content.innerHTML = renderFirmSettingContent(key);
        var modal = document.getElementById('firm-setting-modal');
        if (modal) {
            var titleEl = modal.querySelector('h3');
            if (titleEl)
                titleEl.innerHTML =
                    '<iconify-icon icon="mdi:cog-outline" class="text-brand text-lg"></iconify-icon>律所设置 - ' +
                    escapeHtml(label);
        }
        var tabs = modal.querySelectorAll('[onclick^="switchFirmSettingTab"]');
        tabs.forEach(function (btn) {
            var tabKey = btn.getAttribute('onclick').replace(/switchFirmSettingTab\('(\w+)'\)/, '$1');
            if (tabKey === key) {
                btn.className =
                    'flex-1 min-w-[70px] text-[11px] py-1.5 px-2 rounded-md transition-colors bg-white text-fg-primary shadow-sm font-medium';
            } else {
                btn.className =
                    'flex-1 min-w-[70px] text-[11px] py-1.5 px-2 rounded-md transition-colors text-fg-tertiary hover:text-fg-secondary';
            }
        });
    }

    function renderFirmSettingContent(key) {
        if (key === 'basic') {
            return (
                '<div class="space-y-3">' +
                '<div><label class="firm-label">律所名称</label><input class="firm-input" value="北京宏达律师事务所" placeholder="请输入律所名称"></div>' +
                '<div><label class="firm-label">统一社会信用代码</label><input class="firm-input" value="31110000MD0123456X" placeholder="请输入信用代码"></div>' +
                '<div class="grid grid-cols-2 gap-3">' +
                '<div><label class="firm-label">成立日期</label><input class="firm-input" type="date" value="2010-05-18"></div>' +
                '<div><label class="firm-label">律师人数</label><input class="firm-input" type="number" value="12"></div>' +
                '</div>' +
                '<div><label class="firm-label">联系地址</label><input class="firm-input" value="北京市朝阳区建国路88号SOHO现代城A座18层" placeholder="请输入地址"></div>' +
                '<div class="grid grid-cols-2 gap-3">' +
                '<div><label class="firm-label">联系电话</label><input class="firm-input" value="010-88888888"></div>' +
                '<div><label class="firm-label">官方邮箱</label><input class="firm-input" value="contact@hongda-law.com"></div>' +
                '</div>' +
                '<div><label class="firm-label">律所简介</label><textarea class="firm-input" rows="3" placeholder="请输入律所简介">北京宏达律师事务所成立于2010年，专注于民商事诉讼、知识产权、公司并购等领域，拥有资深律师团队。</textarea></div>' +
                '</div>'
            );
        }
        if (key === 'members') {
            return (
                '<div class="space-y-3">' +
                '<div class="flex items-center justify-between">' +
                '<p class="text-xs text-fg-tertiary">共 ' +
                _membersData.length +
                ' 名成员</p>' +
                '<button class="text-[11px] text-brand hover:underline">+ 添加成员</button>' +
                '</div>' +
                '<div class="space-y-2">' +
                _membersData
                    .map(function (m, idx) {
                        var color = _avatarColors[idx % _avatarColors.length];
                        return (
                            '<div class="flex items-center gap-3 p-2 rounded-lg hover:bg-bg-subtle">' +
                            '<div class="w-9 h-9 rounded-full ' +
                            color.bg +
                            ' flex items-center justify-center flex-shrink-0">' +
                            '<span class="text-xs font-semibold ' +
                            color.text +
                            '">' +
                            escapeHtml(m.name.charAt(0)) +
                            '</span>' +
                            '</div>' +
                            '<div class="flex-1 min-w-0">' +
                            '<p class="text-xs font-medium text-fg-primary">' +
                            escapeHtml(m.name) +
                            '</p>' +
                            '<p class="text-[10px] text-fg-tertiary">' +
                            escapeHtml(m.position) +
                            ' · ' +
                            escapeHtml(m.field) +
                            '</p>' +
                            '</div>' +
                            '<button class="text-[10px] text-brand hover:underline">编辑</button>' +
                            '</div>'
                        );
                    })
                    .join('') +
                '</div>' +
                '</div>'
            );
        }
        if (key === 'departments') {
            var depts = [
                { name: '民商事诉讼部', count: 4, head: '张伟律师' },
                { name: '知识产权部', count: 2, head: '李娜律师' },
                { name: '公司法律部', count: 2, head: '陈明律师' },
                { name: '刑事辩护部', count: 1, head: '王强律师' },
                { name: '劳动争议部', count: 1, head: '刘芳律师' },
                { name: '行政诉讼部', count: 1, head: '吴磊律师' }
            ];
            return (
                '<div class="space-y-2">' +
                depts
                    .map(function (d) {
                        return (
                            '<div class="flex items-center justify-between p-3 bg-white border border-bg-border rounded-lg">' +
                            '<div>' +
                            '<p class="text-xs font-medium text-fg-primary">' +
                            escapeHtml(d.name) +
                            '</p>' +
                            '<p class="text-[10px] text-fg-tertiary mt-0.5">负责人: ' +
                            escapeHtml(d.head) +
                            '</p>' +
                            '</div>' +
                            '<span class="text-[11px] text-fg-secondary bg-bg-subtle px-2 py-0.5 rounded">' +
                            d.count +
                            ' 人</span>' +
                            '</div>'
                        );
                    })
                    .join('') +
                '</div>'
            );
        }
        if (key === 'fees') {
            var fees = [
                { type: '法律咨询', rate: '¥500 / 小时' },
                { type: '合同审查', rate: '¥2,000 起' },
                { type: '民商事诉讼', rate: '标的额 3-5%' },
                { type: '刑事辩护', rate: '¥10,000 起 / 阶段' },
                { type: '法律顾问', rate: '¥30,000 / 年起' },
                { type: '知识产权', rate: '¥5,000 起' }
            ];
            return (
                '<div class="space-y-2">' +
                fees
                    .map(function (f) {
                        return (
                            '<div class="flex items-center justify-between p-3 bg-white border border-bg-border rounded-lg">' +
                            '<span class="text-xs text-fg-primary">' +
                            escapeHtml(f.type) +
                            '</span>' +
                            '<span class="text-xs font-semibold text-brand">' +
                            escapeHtml(f.rate) +
                            '</span>' +
                            '</div>'
                        );
                    })
                    .join('') +
                '<p class="text-[10px] text-fg-tertiary pt-2">* 具体收费可根据案件复杂程度协商调整</p>' +
                '</div>'
            );
        }
        if (key === 'contracts') {
            var contracts = [
                { name: '买卖合同（通用）', count: 86, icon: 'mdi:file-document-outline' },
                { name: '劳动合同', count: 52, icon: 'mdi:briefcase-outline' },
                { name: '租赁合同', count: 45, icon: 'mdi:home-outline' },
                { name: '借款合同', count: 38, icon: 'mdi:cash-multiple' },
                { name: '保密协议', count: 34, icon: 'mdi:lock-outline' },
                { name: '股权转让协议', count: 28, icon: 'mdi:swap-horizontal' },
                { name: '合伙协议', count: 25, icon: 'mdi:account-group' },
                { name: '建设工程合同', count: 18, icon: 'mdi:domain' }
            ];
            return (
                '<div class="grid grid-cols-2 gap-2">' +
                contracts
                    .map(function (c) {
                        return (
                            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
                            '<div class="flex items-center gap-2 mb-1">' +
                            '<iconify-icon icon="' +
                            c.icon +
                            '" class="text-brand"></iconify-icon>' +
                            '<span class="text-xs font-medium text-fg-primary">' +
                            escapeHtml(c.name) +
                            '</span>' +
                            '</div>' +
                            '<p class="text-[10px] text-fg-tertiary">累计使用 ' +
                            c.count +
                            ' 次</p>' +
                            '</div>'
                        );
                    })
                    .join('') +
                '</div>'
            );
        }
        if (key === 'permissions') {
            var roles = [
                { name: '高级合伙人', desc: '全部权限', color: 'text-purple-600 bg-purple-50' },
                { name: '合伙人', desc: '案件管理 / 合同审批 / 成员查看', color: 'text-brand bg-brand-tint' },
                { name: '执业律师', desc: '案件办理 / 合同审查 / 客户管理', color: 'text-green-600 bg-green-50' },
                { name: '实习律师', desc: '案件协办 / 文档编辑 / 受限查看', color: 'text-amber-600 bg-amber-50' },
                { name: '行政人员', desc: '日程管理 / 文档归档 / 财务查看', color: 'text-blue-600 bg-blue-50' }
            ];
            return (
                '<div class="space-y-2">' +
                roles
                    .map(function (r) {
                        return (
                            '<div class="flex items-center justify-between p-3 bg-white border border-bg-border rounded-lg">' +
                            '<div>' +
                            '<span class="text-[10px] ' +
                            r.color +
                            ' font-medium px-2 py-0.5 rounded-full">' +
                            escapeHtml(r.name) +
                            '</span>' +
                            '<p class="text-[11px] text-fg-tertiary mt-1">' +
                            escapeHtml(r.desc) +
                            '</p>' +
                            '</div>' +
                            '<button class="text-[10px] text-brand hover:underline">配置</button>' +
                            '</div>'
                        );
                    })
                    .join('') +
                '</div>'
            );
        }
        return '<div class="text-center text-fg-tertiary py-8">暂无内容</div>';
    }

    function saveFirmSetting() {
        if (typeof showToast === 'function') {
            showToast('设置已保存', 'success');
        }
        closeFirmSetting();
    }

    function closeFirmSetting() {
        if (_closeFirmSetting) {
            _closeFirmSetting();
            _closeFirmSetting = null;
        }
    }

    // ===== 成员详情弹窗 =====
    function openMemberDetail(id) {
        var member = _membersData.find(function (x) {
            return x.id === id;
        });
        if (!member) {
            if (typeof showToast === 'function') showToast('未找到成员');
            return;
        }
        var idx = _membersData.indexOf(member);
        var color = _avatarColors[idx % _avatarColors.length];

        var content =
            '<div class="space-y-4">' +
            '<div class="flex items-center gap-4 p-3 bg-bg-subtle rounded-xl">' +
            '<div class="w-16 h-16 rounded-full ' +
            color.bg +
            ' flex items-center justify-center flex-shrink-0">' +
            '<span class="text-2xl font-bold ' +
            color.text +
            '">' +
            escapeHtml(member.name.charAt(0)) +
            '</span>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<h3 class="text-base font-semibold text-fg-primary">' +
            escapeHtml(member.name) +
            '</h3>' +
            '<p class="text-xs text-fg-tertiary mb-1">' +
            escapeHtml(member.position) +
            '</p>' +
            '<span class="text-[10px] ' +
            (member.online ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-500') +
            ' font-medium px-2 py-0.5 rounded-full">' +
            (member.online ? '在线' : '离线') +
            '</span>' +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">执业领域</p>' +
            '<p class="text-sm text-fg-primary font-medium">' +
            escapeHtml(member.field) +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">入职时间</p>' +
            '<p class="text-sm text-fg-primary font-medium">20' +
            (15 + (id % 10)) +
            '-' +
            String(((id * 3) % 12) + 1).padStart(2, '0') +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="p-3 bg-bg-subtle rounded-xl space-y-2">' +
            '<div class="flex items-center justify-between text-sm">' +
            '<span class="text-fg-tertiary">执业证号</span>' +
            '<span class="text-fg-primary font-mono text-xs">110' +
            (100000 + id * 12345) +
            '</span>' +
            '</div>' +
            '<div class="flex items-center justify-between text-sm">' +
            '<span class="text-fg-tertiary">联系电话</span>' +
            '<span class="text-fg-primary text-xs">138****' +
            String(1000 + id * 137).slice(-4) +
            '</span>' +
            '</div>' +
            '<div class="flex items-center justify-between text-sm">' +
            '<span class="text-fg-tertiary">电子邮箱</span>' +
            '<span class="text-fg-primary text-xs">lawyer' +
            id +
            '@hongda-law.com</span>' +
            '</div>' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeMemberDetail()">关闭</button>' +
            '<button class="h-9 px-4 text-xs text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="closeMemberDetail()">发送消息</button>';

        if (_closeMemberDetail) _closeMemberDetail();
        _closeMemberDetail = Utils.showModal({
            id: 'member-detail-modal',
            title: '成员详情',
            icon: 'mdi:account-circle-outline',
            content: content,
            footer: footer,
            size: 'md'
        });
    }

    function closeMemberDetail() {
        if (_closeMemberDetail) {
            _closeMemberDetail();
            _closeMemberDetail = null;
        }
    }

    // ===== 初始化（视图加载时调用） =====
    function initFirm() {
        renderStats();
        renderMemberList();
    }

    globalThis.initFirm = initFirm;
    globalThis.openFirmSetting = openFirmSetting;
    globalThis.closeFirmSetting = closeFirmSetting;
    globalThis.switchFirmSettingTab = switchFirmSettingTab;
    globalThis.saveFirmSetting = saveFirmSetting;
    globalThis.viewAllMembers = viewAllMembers;
    globalThis.toggleMemberStatus = toggleMemberStatus;
    globalThis.openMemberDetail = openMemberDetail;
    globalThis.closeMemberDetail = closeMemberDetail;
})();
