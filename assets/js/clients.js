/**
 * 客户管理模块
 * 包含: 客户分类切换 + 详情页 + 新建/冲突检查 + 沟通日志 + 标签管理
 * 加载: 在 script.js 之前同步加载
 */

(function() {
    'use strict';

    var clientsData = [
        { id: 0, name: '李明', avatar: '李', grade: 'A', status: 'active', phone: '138****1234', caseCount: 3, lastContact: '2026-08-18', tags: ['企业客户', '高价值', '合同纠纷'], source: '介绍推荐' },
        { id: 1, name: '王华', avatar: '王', grade: 'B', status: 'active', phone: '139****5678', caseCount: 2, lastContact: '2026-08-15', tags: ['个人客户', '民间借贷'], source: '电话咨询' },
        { id: 2, name: '某科技有限公司', avatar: '某', grade: 'A', status: 'active', phone: '010-8888****', caseCount: 5, lastContact: '2026-08-14', tags: ['企业客户', '高价值', '知识产权'], source: '到所咨询' },
        { id: 3, name: '赵六', avatar: '赵', grade: 'C', status: 'pending', phone: '136****9012', caseCount: 1, lastContact: '2026-08-05', tags: ['个人客户', '劳动争议'], source: '微信咨询' },
        { id: 4, name: '张三', avatar: '张', grade: 'C', status: 'silent', phone: '137****3456', caseCount: 1, lastContact: '2026-07-28', tags: ['个人客户', '合同纠纷'], source: '介绍推荐' }
    ];

    var currentClientTab = 'all';
    var currentClientIndex = 0;

    var communicationLogs = [
        [
            { id: 0, type: 'phone', title: '电话沟通 · 开庭提醒', content: '通知李明 8/25 开庭事项，确认其会准时到庭。', time: '08-18 10:30', author: '张', authorType: 'lawyer' },
            { id: 1, type: 'wechat', title: 'AI 摘要 · 微信沟通', content: '客户询问案件进展，已回复当前处于证据交换阶段。', time: '08-15 14:20', author: 'AI', authorType: 'ai' },
            { id: 2, type: 'meeting', title: 'AI 摘要 · 会面记录', content: '委托代理合同签署，代理费 ¥85,000 已收。', time: '08-10 09:00', author: 'AI', authorType: 'ai' }
        ],
        [
            { id: 0, type: 'phone', title: '电话沟通 · 案情确认', content: '确认借贷纠纷案件细节，补充证据材料。', time: '08-15 11:00', author: '张', authorType: 'lawyer' },
            { id: 1, type: 'wechat', title: 'AI 摘要 · 微信沟通', content: '客户咨询财产保全流程，已发送操作指南。', time: '08-12 16:30', author: 'AI', authorType: 'ai' }
        ],
        [
            { id: 0, type: 'meeting', title: 'AI 摘要 · 首次会面', content: '客户委托知识产权侵权案件，已签署委托合同。', time: '08-14 10:00', author: 'AI', authorType: 'ai' },
            { id: 1, type: 'phone', title: '电话沟通 · 证据收集指导', content: '指导客户收集相关证据材料，确定举证期限。', time: '08-10 15:00', author: '李', authorType: 'lawyer' }
        ],
        [
            { id: 0, type: 'phone', title: '电话沟通 · 结案回访', content: '劳动争议案件已结案，进行客户满意度回访。', time: '08-05 09:30', author: '王', authorType: 'lawyer' }
        ],
        [
            { id: 0, type: 'wechat', title: 'AI 摘要 · 微信沟通', content: '客户咨询合同纠纷相关问题，已给出初步建议。', time: '07-28 14:00', author: 'AI', authorType: 'ai' }
        ]
    ];

    function getGradeClass(grade) {
        switch (grade) {
            case 'A': return 'bg-danger-tint text-danger';
            case 'B': return 'bg-warning-tint text-urgent';
            case 'C': return 'bg-bg-subtle text-fg-tertiary';
            default: return 'bg-bg-subtle text-fg-tertiary';
        }
    }

    function getGradeText(grade) {
        return grade + ' 级';
    }

    function getStatusText(status) {
        switch (status) {
            case 'active': return '活跃';
            case 'pending': return '待回访';
            case 'silent': return '静默';
            default: return '未知';
        }
    }

    function getStatusClass(status) {
        switch (status) {
            case 'active': return 'bg-green-50 text-success';
            case 'pending': return 'bg-warning-tint text-urgent';
            case 'silent': return 'bg-bg text-fg-disabled';
            default: return 'bg-bg-subtle text-fg-tertiary';
        }
    }

    function getAvatarColor(name) {
        var colors = [
            'bg-brand/10 text-brand',
            'bg-purple-50 text-wiki',
            'bg-brand-tint3 text-brand',
            'bg-bg text-fg-tertiary',
            'bg-green-50 text-success',
            'bg-orange-50 text-urgent',
            'bg-red-50 text-danger'
        ];
        var index = name.charCodeAt(0) % colors.length;
        return colors[index];
    }

    function filterClients(tab) {
        return clientsData.filter(function(c) {
            switch (tab) {
                case 'all': return true;
                case 'a': return c.grade === 'A';
                case 'b': return c.grade === 'B';
                case 'c': return c.grade === 'C';
                case 'active': return c.status === 'active';
                case 'pending': return c.status === 'pending';
                default: return true;
            }
        });
    }

    function renderClientList() {
        var tbody = document.querySelector('#view-client tbody');
        if (!tbody) return;

        var filtered = filterClients(currentClientTab);
        var html = '';

        filtered.forEach(function(c, index) {
            var realIndex = clientsData.indexOf(c);
            var avatarColor = getAvatarColor(c.name);
            html +=
                '<tr class="hover:bg-bg-subtle transition-colors">' +
                    '<td class="py-3 px-4">' +
                        '<div class="flex items-center gap-3">' +
                            '<div class="w-8 h-8 rounded-full ' + avatarColor + ' flex items-center justify-center text-xs font-bold">' + c.avatar + '</div>' +
                            '<span class="text-xs font-medium text-fg-primary">' + c.name + '</span>' +
                        '</div>' +
                    '</td>' +
                    '<td class="py-3 px-4 text-xs text-fg-secondary">' + c.phone + '</td>' +
                    '<td class="py-3 px-4 text-xs text-fg-secondary">' + c.caseCount + '</td>' +
                    '<td class="text-center py-3 px-4"><span class="text-[10px] ' + getGradeClass(c.grade) + ' font-medium px-2 py-0.5 rounded">' + getGradeText(c.grade) + '</span></td>' +
                    '<td class="text-center py-3 px-4 text-xs text-fg-secondary">' + c.lastContact + '</td>' +
                    '<td class="text-center py-3 px-4"><span class="text-[10px] ' + getStatusClass(c.status) + ' font-medium px-2 py-0.5 rounded">' + getStatusText(c.status) + '</span></td>' +
                    '<td class="text-center py-3 px-4">' +
                        '<button class="text-xs text-brand hover:underline" onclick="openClientDetail(' + realIndex + ')">详情</button>' +
                    '</td>' +
                '</tr>';
        });

        tbody.innerHTML = html;
    }

    function switchClientTab(el, tab) {
        currentClientTab = tab;

        var tabBar = el.closest('.flex.items-center.gap-1');
        if (tabBar) {
            tabBar.querySelectorAll('button').forEach(function(btn) {
                btn.classList.remove('bg-brand', 'text-white');
                btn.classList.add('text-fg-secondary', 'hover:bg-bg-subtle');
            });
        }

        el.classList.remove('text-fg-secondary', 'hover:bg-bg-subtle');
        el.classList.add('bg-brand', 'text-white');

        renderClientList();
    }

    function openClientDetail(index) {
        currentClientIndex = index;
        var c = clientsData[index] || clientsData[0];

        var viewClientDetail = document.getElementById('view-client-detail');
        if (viewClientDetail) {
            showClientDetail(c);
        } else {
            if (typeof loadView === 'function') {
                loadView('client-detail', function() {
                    showClientDetail(c);
                });
            }
        }
    }

    function showClientDetail(c) {
        document.querySelectorAll('.view-content').forEach(function(v) {
            v.classList.add('hidden');
        });

        document.getElementById('view-client-detail').classList.remove('hidden');

        document.getElementById('client-detail-name').textContent = c.name;
        document.getElementById('client-detail-name-text').textContent = c.name;
        document.getElementById('client-detail-avatar').textContent = c.avatar;
        document.getElementById('client-detail-avatar').className = 'w-14 h-14 rounded-full ' + getAvatarColor(c.name) + ' flex items-center justify-center text-xl font-bold';
        document.getElementById('client-detail-grade').textContent = getGradeText(c.grade);
        document.getElementById('client-detail-grade').className = 'text-[10px] font-medium px-2 py-0.5 rounded ' + getGradeClass(c.grade);
        document.getElementById('client-detail-status').textContent = getStatusText(c.status);
        document.getElementById('client-detail-status').className = 'text-[10px] font-medium px-2 py-0.5 rounded ' + getStatusClass(c.status);
        document.getElementById('client-detail-phone').textContent = c.phone;
        document.getElementById('client-detail-cases').textContent = c.caseCount;

        renderClientTags();
        renderCommunicationLogs();
    }

    function backToClientList() {
        var viewClient = document.getElementById('view-client');
        if (!viewClient) {
            if (typeof loadView === 'function') {
                loadView('client', function() {
                    showClientListView();
                });
            }
            return;
        }
        showClientListView();
    }

    function showClientListView() {
        document.querySelectorAll('.view-content').forEach(function(v) {
            v.classList.add('hidden');
        });
        document.getElementById('view-client').classList.remove('hidden');
        renderClientList();
    }

    function renderClientTags() {
        var c = clientsData[currentClientIndex];
        var tagsContainer = document.querySelector('#view-client-detail .bg-white.rounded-xl.border.border-bg-border.p-5 .flex.flex-wrap.gap-1\\.5');
        if (!tagsContainer || !c) return;

        var html = '';
        c.tags.forEach(function(tag) {
            html += '<span class="text-[10px] bg-brand-tint text-brand px-2 py-1 rounded font-medium">' + tag + '</span>';
        });
        html += '<span class="text-[10px] bg-warning-tint text-urgent px-2 py-1 rounded font-medium cursor-pointer" onclick="showAddTagModal()">+ 添加</span>';

        tagsContainer.innerHTML = html;
    }

    function renderCommunicationLogs() {
        var logs = communicationLogs[currentClientIndex] || [];
        var logsContainer = document.querySelector('#view-client-detail .space-y-0');
        if (!logsContainer) return;

        var html = '';
        logs.forEach(function(log) {
            var authorClass = log.authorType === 'ai' 
                ? (log.type === 'wechat' ? 'bg-warning-tint text-urgent' : 'bg-green-50 text-success')
                : 'bg-brand/10 text-brand';

            html +=
                '<div class="flex items-start gap-3 py-3 border-b border-bg-border last:border-b-0">' +
                    '<div class="w-7 h-7 rounded-full ' + authorClass + ' flex items-center justify-center flex-shrink-0 text-[10px] font-bold">' + log.author + '</div>' +
                    '<div class="flex-1">' +
                        '<div class="flex items-center gap-2">' +
                            '<p class="text-xs font-medium text-fg-primary">' + log.title + '</p>' +
                            '<span class="text-[10px] text-fg-disabled ml-auto">' + log.time + '</span>' +
                        '</div>' +
                        '<p class="text-[10px] text-fg-secondary mt-0.5">' + log.content + '</p>' +
                    '</div>' +
                '</div>';
        });

        logsContainer.innerHTML = html;
    }

    function showNewClientModal() {
        document.getElementById('new-client-modal').classList.remove('hidden');
    }

    function closeNewClientModal() {
        document.getElementById('new-client-modal').classList.add('hidden');
    }

    function submitNewClient() {
        var nameInput = document.querySelector('#new-client-modal input[placeholder*="客户姓名"]');
        var phoneInput = document.querySelector('#new-client-modal input[placeholder*="手机号"]');
        var name = nameInput ? nameInput.value.trim() : '';
        var phone = phoneInput ? phoneInput.value.trim() : '';

        if (!name) {
            if (typeof showToast === 'function') {
                showToast('请输入客户姓名');
            } else {
                alert('请输入客户姓名');
            }
            return;
        }

        var avatar = name.charAt(0);
        var newClient = {
            id: clientsData.length,
            name: name,
            avatar: avatar,
            grade: 'C',
            status: 'active',
            phone: phone || '暂无',
            caseCount: 0,
            lastContact: '2026-08-20',
            tags: ['新客户'],
            source: '电话咨询'
        };

        clientsData.unshift(newClient);
        communicationLogs.unshift([]);

        renderClientList();
        closeNewClientModal();

        if (typeof showToast === 'function') {
            showToast('客户创建成功');
        } else {
            alert('客户创建成功');
        }

        if (nameInput) nameInput.value = '';
        if (phoneInput) phoneInput.value = '';
    }

    function runNewClientConflictCheck() {
        var result = document.getElementById('new-client-conflict-result');
        if (result) {
            result.classList.remove('hidden');
        }
        if (typeof showToast === 'function') {
            showToast('利益冲突检索完成，未发现冲突');
        } else {
            alert('利益冲突检索完成，未发现冲突');
        }
    }

    function runConflictCheck() {
        var result = document.getElementById('conflict-result');
        if (result) {
            result.classList.remove('hidden');
        }
        if (typeof showToast === 'function') {
            showToast('利益冲突审查完成');
        } else {
            alert('利益冲突审查完成');
        }
    }

    function showAddTagModal() {
        var tagName = prompt('请输入标签名称：');
        if (tagName && tagName.trim()) {
            var c = clientsData[currentClientIndex];
            if (c && c.tags.indexOf(tagName.trim()) === -1) {
                c.tags.push(tagName.trim());
                renderClientTags();
                if (typeof showToast === 'function') {
                    showToast('标签添加成功');
                }
            }
        }
    }

    function initClientModule() {
        renderClientList();
    }

    globalThis.switchClientTab = switchClientTab;
    globalThis.openClientDetail = openClientDetail;
    globalThis.backToClientList = backToClientList;
    globalThis.showNewClientModal = showNewClientModal;
    globalThis.closeNewClientModal = closeNewClientModal;
    globalThis.submitNewClient = submitNewClient;
    globalThis.runNewClientConflictCheck = runNewClientConflictCheck;
    globalThis.runConflictCheck = runConflictCheck;
    globalThis.showAddTagModal = showAddTagModal;
    globalThis.initClientModule = initClientModule;
    globalThis.clientsData = clientsData;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initClientModule);
    } else {
        setTimeout(initClientModule, 100);
    }
})();
