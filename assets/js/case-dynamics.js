(function () {
    'use strict';

    var _dynamics = [
        {
            id: 0,
            type: '紧急',
            title: '证据提交即将截止',
            desc: '案件：李明诉XX公司买卖合同纠纷 · 剩余 2 天',
            time: '今天 10:30',
            user: '张律师',
            icon: 'mdi:clock-alert-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-red-50',
            borderColor: 'border-l-red-500',
            badgeBg: 'bg-red-100',
            badgeColor: 'text-red-700',
            action: '去处理'
        },
        {
            id: 1,
            type: '文书',
            title: '起诉状已完成',
            desc: '李明诉XX公司买卖合同纠纷 · 民事起诉状已由AI生成并保存',
            time: '今天 10:30',
            user: '张律师',
            icon: 'mdi:file-document-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-brand-tint3',
            borderColor: 'border-l-blue-500',
            badgeBg: 'bg-brand-tint',
            badgeColor: 'text-brand',
            action: '查看'
        },
        {
            id: 2,
            type: '开庭',
            title: '开庭日期已确定',
            desc: '王华借贷纠纷 · 2026-08-28 14:00 第5法庭',
            time: '昨天 16:00',
            user: '李律师',
            icon: 'mdi:gavel',
            iconColor: 'text-purple-500',
            iconBg: 'bg-purple-50',
            borderColor: 'border-l-purple-500',
            badgeBg: 'bg-wiki-tint',
            badgeColor: 'text-wiki',
            action: '查看日程'
        },
        {
            id: 3,
            type: '归档',
            title: '案件已归档',
            desc: '张三合同纠纷 · 全部卷宗已完成归档',
            time: '昨天 14:30',
            user: '张律师',
            icon: 'mdi:check-circle-outline',
            iconColor: 'text-green-500',
            iconBg: 'bg-green-50',
            borderColor: 'border-l-green-500',
            badgeBg: 'bg-success-tint',
            badgeColor: 'text-success',
            action: '查看归档'
        },
        {
            id: 4,
            type: '提醒',
            title: '续约提醒',
            desc: '某科技公司法律顾问合同即将到期（2026-09-30）',
            time: '昨天 09:00',
            user: '系统',
            icon: 'mdi:calendar-check-outline',
            iconColor: 'text-amber-500',
            iconBg: 'bg-amber-50',
            borderColor: 'border-l-amber-500',
            badgeBg: 'bg-amber-100',
            badgeColor: 'text-amber-700',
            action: '去处理'
        },
        {
            id: 5,
            type: '文书',
            title: '证据目录已更新',
            desc: '某科技公司股权纠纷 · 新增3份补充证据',
            time: '2天前 11:20',
            user: '王律师',
            icon: 'mdi:file-compare',
            iconColor: 'text-brand',
            iconBg: 'bg-brand-tint3',
            borderColor: 'border-l-blue-500',
            badgeBg: 'bg-brand-tint',
            badgeColor: 'text-brand',
            action: '查看'
        },
        {
            id: 6,
            type: '开庭',
            title: '合议庭组成已确定',
            desc: '赵六劳动争议仲裁 · 审判长：王法官',
            time: '3天前 09:45',
            user: '系统',
            icon: 'mdi:account-group-outline',
            iconColor: 'text-purple-500',
            iconBg: 'bg-purple-50',
            borderColor: 'border-l-purple-500',
            badgeBg: 'bg-wiki-tint',
            badgeColor: 'text-wiki',
            action: '详情'
        },
        {
            id: 7,
            type: '归档',
            title: '判决书已上传',
            desc: '王华借贷纠纷 · 一审判决书已归档',
            time: '3天前 16:20',
            user: '张律师',
            icon: 'mdi:file-document-check-outline',
            iconColor: 'text-green-500',
            iconBg: 'bg-green-50',
            borderColor: 'border-l-green-500',
            badgeBg: 'bg-success-tint',
            badgeColor: 'text-success',
            action: '查看'
        }
    ];

    var _currentFilter = 'all';
    var _searchKeyword = '';
    var _currentView = 'list';
    var _searchTimer = null;
    var _closeDynamicDetail = null;
    var _closeNewDynamicModal = null;

    function getFilteredDynamics() {
        return _dynamics.filter(function (item) {
            var matchType = _currentFilter === 'all' || item.type === _currentFilter;
            var keyword = _searchKeyword.toLowerCase();
            var matchSearch =
                !keyword ||
                item.title.toLowerCase().indexOf(keyword) > -1 ||
                item.desc.toLowerCase().indexOf(keyword) > -1;
            return matchType && matchSearch;
        });
    }

    function renderListItem(item) {
        return (
            '<div class="bg-white rounded-xl border border-bg-border p-4 hover:shadow-sm transition-shadow border-l-4 ' +
            item.borderColor +
            '">' +
            '<div class="flex items-start gap-3">' +
            '<div class="w-9 h-9 rounded-lg ' +
            item.iconBg +
            ' flex items-center justify-center flex-shrink-0">' +
            '<iconify-icon class="' +
            item.iconColor +
            ' text-lg" icon="' +
            item.icon +
            '"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-center gap-2 mb-1">' +
            '<span class="text-[10px] ' +
            item.badgeBg +
            ' ' +
            item.badgeColor +
            ' font-medium px-1.5 py-0.5 rounded-full">' +
            item.type +
            '</span>' +
            '<span class="font-medium text-sm text-fg-primary">' +
            escapeHtml(item.title) +
            '</span>' +
            '</div>' +
            '<p class="text-xs text-fg-tertiary">' +
            escapeHtml(item.desc) +
            '</p>' +
            '<div class="flex items-center gap-3 mt-2">' +
            '<span class="text-[10px] text-fg-tertiary"><iconify-icon class="inline" icon="mdi:clock-outline"></iconify-icon> ' +
            item.time +
            '</span>' +
            '<span class="text-[10px] text-fg-tertiary"><iconify-icon class="inline" icon="mdi:account-outline"></iconify-icon> ' +
            item.user +
            '</span>' +
            '</div>' +
            '</div>' +
            '<button class="text-[10px] text-brand hover:underline flex-shrink-0 mt-1" onclick="openCaseDynamicDetail(' +
            item.id +
            ')">' +
            item.action +
            '</button>' +
            '</div>' +
            '</div>'
        );
    }

    function renderTimelineItem(item, index) {
        return (
            '<div class="relative pb-8">' +
            '<div class="absolute -left-8 top-1 w-6 h-6 rounded-full ' +
            item.iconBg +
            ' border-2 border-white flex items-center justify-center z-10">' +
            '<iconify-icon class="' +
            item.iconColor +
            ' text-sm" icon="' +
            item.icon +
            '"></iconify-icon>' +
            '</div>' +
            '<div class="bg-white rounded-xl border border-bg-border p-4 hover:shadow-sm transition-shadow ml-4">' +
            '<div class="flex items-center gap-2 mb-1">' +
            '<span class="text-[10px] ' +
            item.badgeBg +
            ' ' +
            item.badgeColor +
            ' font-medium px-1.5 py-0.5 rounded-full">' +
            item.type +
            '</span>' +
            '<span class="font-medium text-sm text-fg-primary">' +
            escapeHtml(item.title) +
            '</span>' +
            '</div>' +
            '<p class="text-xs text-fg-tertiary">' +
            escapeHtml(item.desc) +
            '</p>' +
            '<div class="flex items-center gap-3 mt-2">' +
            '<span class="text-[10px] text-fg-tertiary"><iconify-icon class="inline" icon="mdi:clock-outline"></iconify-icon> ' +
            item.time +
            '</span>' +
            '<span class="text-[10px] text-fg-tertiary"><iconify-icon class="inline" icon="mdi:account-outline"></iconify-icon> ' +
            item.user +
            '</span>' +
            '<button class="text-[10px] text-brand hover:underline ml-auto" onclick="openCaseDynamicDetail(' +
            item.id +
            ')">' +
            item.action +
            '</button>' +
            '</div>' +
            '</div>' +
            '</div>'
        );
    }

    function renderDynamics() {
        var listView = document.getElementById('dynamics-list-view');
        var timelineView = document.getElementById('dynamics-timeline-view');
        var emptyState = document.getElementById('dynamics-empty-state');
        var countEl = document.getElementById('dynamics-count');

        var filtered = getFilteredDynamics();

        if (filtered.length === 0) {
            if (listView) listView.classList.add('hidden');
            if (timelineView) timelineView.classList.add('hidden');
            if (emptyState) emptyState.classList.remove('hidden');
        } else {
            if (emptyState) emptyState.classList.add('hidden');

            if (_currentView === 'list') {
                if (listView) {
                    listView.classList.remove('hidden');
                    listView.innerHTML =
                        filtered
                            .map(function (item) {
                                return renderListItem(item);
                            })
                            .join('') +
                        '<div class="text-center py-4"><span class="text-[10px] text-gray-300">— 没有更多动态 —</span></div>';
                }
                if (timelineView) timelineView.classList.add('hidden');
            } else {
                if (timelineView) {
                    timelineView.classList.remove('hidden');
                    timelineView.innerHTML =
                        '<div class="relative pl-8 ml-4 space-y-0">' +
                        '<div class="absolute left-3 top-3 bottom-3 w-0.5 bg-bg-border"></div>' +
                        filtered
                            .map(function (item, idx) {
                                return renderTimelineItem(item, idx);
                            })
                            .join('') +
                        '</div>';
                }
                if (listView) listView.classList.add('hidden');
            }
        }

        if (countEl) countEl.textContent = '共 ' + filtered.length + ' 条';
    }

    function filterDynamics(type, el) {
        _currentFilter = type;
        renderDynamics();

        var btns = document.querySelectorAll('.dyn-filter-btn');
        btns.forEach(function (btn) {
            btn.classList.add('bg-bg', 'text-fg-secondary', 'hover:bg-bg-border');
            btn.classList.remove('bg-brand', 'text-white');
        });
        if (el) {
            el.classList.add('bg-brand', 'text-white');
            el.classList.remove('bg-bg', 'text-fg-secondary', 'hover:bg-bg-border');
        }
    }

    function searchDynamics() {
        var input = document.getElementById('dynamics-search-input');
        if (input) {
            clearTimeout(_searchTimer);
            var val = input.value;
            _searchTimer = setTimeout(function () {
                _searchKeyword = val;
                renderDynamics();
            }, 300);
        }
    }

    function switchDynamicsView(view) {
        _currentView = view;

        var listBtn = document.getElementById('dyn-view-list');
        var timelineBtn = document.getElementById('dyn-view-timeline');

        function setActive(activeBtn, inactiveBtn) {
            if (activeBtn) {
                activeBtn.classList.add('bg-brand', 'text-white');
                activeBtn.classList.remove('bg-white', 'text-fg-secondary', 'hover:bg-gray-50');
            }
            if (inactiveBtn) {
                inactiveBtn.classList.add('bg-white', 'text-fg-secondary', 'hover:bg-gray-50');
                inactiveBtn.classList.remove('bg-brand', 'text-white');
            }
        }

        if (view === 'list') {
            setActive(listBtn, timelineBtn);
        } else {
            setActive(timelineBtn, listBtn);
        }

        renderDynamics();
    }

    function openCaseDynamicDetail(id) {
        var item = _dynamics.find(function (x) {
            return x.id === id;
        });
        if (!item) {
            if (typeof showToast === 'function') showToast('未找到动态 #' + id);
            return;
        }

        var content =
            '<div class="space-y-4">' +
            '<div class="flex items-center gap-3 p-3 bg-bg-subtle rounded-xl">' +
            '<div class="w-12 h-12 rounded-lg ' +
            item.iconBg +
            ' flex items-center justify-center flex-shrink-0">' +
            '<iconify-icon class="' +
            item.iconColor +
            ' text-xl" icon="' +
            item.icon +
            '"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-center gap-2 mb-0.5">' +
            '<span class="text-[10px] ' +
            item.badgeBg +
            ' ' +
            item.badgeColor +
            ' font-medium px-1.5 py-0.5 rounded-full">' +
            escapeHtml(item.type) +
            '</span>' +
            '<span class="font-medium text-sm text-fg-primary">' +
            escapeHtml(item.title) +
            '</span>' +
            '</div>' +
            '<p class="text-xs text-fg-tertiary">' +
            escapeHtml(item.desc) +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">发布时间</p>' +
            '<p class="text-sm text-fg-primary">' +
            escapeHtml(item.time) +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">发布人</p>' +
            '<p class="text-sm text-fg-primary">' +
            escapeHtml(item.user) +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="p-3 bg-bg-subtle rounded-xl">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">关联案件</p>' +
            '<p class="text-sm text-fg-primary">' +
            escapeHtml(item.desc.split('·')[0] || '未关联案件') +
            '</p>' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeDynamicDetail()">关闭</button>' +
            '<button class="h-9 px-4 text-xs text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="closeDynamicDetail(); openNewDynamicModal()">发布新动态</button>';

        if (_closeDynamicDetail) _closeDynamicDetail();
        _closeDynamicDetail = Utils.showModal({
            id: 'dynamic-detail-modal',
            title: '动态详情',
            icon: item.icon,
            content: content,
            footer: footer,
            size: 'md'
        });
    }

    function closeDynamicDetail() {
        if (_closeDynamicDetail) {
            _closeDynamicDetail();
            _closeDynamicDetail = null;
        }
    }

    function openNewDynamicModal() {
        var content =
            '<div class="space-y-4">' +
            '<div>' +
            '<label class="flex items-center gap-1.5 text-xs font-medium text-fg-secondary mb-1.5">动态类型 <span class="text-danger">*</span></label>' +
            '<div class="flex flex-wrap gap-2" id="new-dynamic-type-group">' +
            '<button data-type="紧急" class="new-dyn-type-btn text-xs px-3 py-1.5 rounded-full bg-red-50 text-red-700 border border-red-200 hover:bg-red-100">紧急</button>' +
            '<button data-type="文书" class="new-dyn-type-btn text-xs px-3 py-1.5 rounded-full bg-brand-tint text-brand border border-brand/20 hover:bg-brand-tint30">文书</button>' +
            '<button data-type="开庭" class="new-dyn-type-btn text-xs px-3 py-1.5 rounded-full bg-wiki-tint text-wiki border border-wiki/20 hover:bg-wiki-tint30">开庭</button>' +
            '<button data-type="归档" class="new-dyn-type-btn text-xs px-3 py-1.5 rounded-full bg-success-tint text-success border border-success/20 hover:bg-success-tint30">归档</button>' +
            '<button data-type="提醒" class="new-dyn-type-btn text-xs px-3 py-1.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200 hover:bg-amber-200">提醒</button>' +
            '</div>' +
            '</div>' +
            '<div>' +
            '<label class="flex items-center gap-1.5 text-xs font-medium text-fg-secondary mb-1.5" for="new-dynamic-title">标题 <span class="text-danger">*</span></label>' +
            '<input id="new-dynamic-title" type="text" maxlength="50" placeholder="请输入动态标题（最多 50 字）" class="w-full h-10 px-3 text-sm bg-white border border-bg-border rounded-lg focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/20 transition-colors"/>' +
            '</div>' +
            '<div>' +
            '<label class="flex items-center gap-1.5 text-xs font-medium text-fg-secondary mb-1.5" for="new-dynamic-desc">描述</label>' +
            '<textarea id="new-dynamic-desc" rows="3" maxlength="200" placeholder="请输入动态描述（最多 200 字）" class="w-full px-3 py-2 text-sm bg-white border border-bg-border rounded-lg focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/20 transition-colors resize-none"></textarea>' +
            '</div>' +
            '<div>' +
            '<label class="flex items-center gap-1.5 text-xs font-medium text-fg-secondary mb-1.5" for="new-dynamic-case">关联案件</label>' +
            '<input id="new-dynamic-case" type="text" placeholder="选填，例如：李明诉XX公司买卖合同纠纷" class="w-full h-10 px-3 text-sm bg-white border border-bg-border rounded-lg focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/20 transition-colors"/>' +
            '</div>' +
            '<div class="text-[11px] text-fg-tertiary flex items-center gap-1">' +
            '<iconify-icon icon="mdi:information-outline"></iconify-icon>' +
            '动态发布后将显示在案件动态列表顶部' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeNewDynamicModal()">取消</button>' +
            '<button class="h-9 px-4 text-xs text-white bg-brand hover:bg-brand-hover rounded-lg flex items-center gap-1" onclick="submitNewDynamic()">' +
            '<iconify-icon icon="mdi:check"></iconify-icon>' +
            '发布动态' +
            '</button>';

        if (_closeNewDynamicModal) _closeNewDynamicModal();
        _closeNewDynamicModal = Utils.showModal({
            id: 'new-dynamic-modal',
            title: '发布动态',
            icon: 'mdi:plus-circle-outline',
            content: content,
            footer: footer,
            size: 'md'
        });

        var modal = document.getElementById('new-dynamic-modal');
        if (modal) {
            var typeBtns = modal.querySelectorAll('.new-dyn-type-btn');
            typeBtns.forEach(function (btn) {
                btn.addEventListener('click', function () {
                    typeBtns.forEach(function (b) {
                        b.dataset.selected = 'false';
                        b.style.outline = 'none';
                        b.style.outlineOffset = '0';
                    });
                    btn.dataset.selected = 'true';
                    btn.style.outline = '2px solid currentColor';
                    btn.style.outlineOffset = '1px';
                });
            });
        }
    }

    function closeNewDynamicModal() {
        if (_closeNewDynamicModal) {
            _closeNewDynamicModal();
            _closeNewDynamicModal = null;
        }
    }

    function submitNewDynamic() {
        var modal = document.getElementById('new-dynamic-modal');
        if (!modal) return;

        var selectedTypeBtn = modal.querySelector('.new-dyn-type-btn[data-selected="true"]');
        var type = selectedTypeBtn ? selectedTypeBtn.dataset.type : '';
        var titleInput = document.getElementById('new-dynamic-title');
        var descInput = document.getElementById('new-dynamic-desc');
        var caseInput = document.getElementById('new-dynamic-case');

        var title = titleInput ? titleInput.value.trim() : '';
        var desc = descInput ? descInput.value.trim() : '';
        var caseName = caseInput ? caseInput.value.trim() : '';

        if (!type) {
            if (typeof showToast === 'function') showToast('请选择动态类型', 'warning');
            return;
        }
        if (!title) {
            if (typeof showToast === 'function') showToast('请输入动态标题', 'warning');
            if (titleInput) titleInput.focus();
            return;
        }

        var typeMeta = {
            紧急: {
                icon: 'mdi:clock-alert-outline',
                iconColor: 'text-red-500',
                iconBg: 'bg-red-50',
                borderColor: 'border-l-red-500',
                badgeBg: 'bg-red-100',
                badgeColor: 'text-red-700'
            },
            文书: {
                icon: 'mdi:file-document-outline',
                iconColor: 'text-brand',
                iconBg: 'bg-brand-tint3',
                borderColor: 'border-l-blue-500',
                badgeBg: 'bg-brand-tint',
                badgeColor: 'text-brand'
            },
            开庭: {
                icon: 'mdi:gavel',
                iconColor: 'text-purple-500',
                iconBg: 'bg-purple-50',
                borderColor: 'border-l-purple-500',
                badgeBg: 'bg-wiki-tint',
                badgeColor: 'text-wiki'
            },
            归档: {
                icon: 'mdi:check-circle-outline',
                iconColor: 'text-green-500',
                iconBg: 'bg-green-50',
                borderColor: 'border-l-green-500',
                badgeBg: 'bg-success-tint',
                badgeColor: 'text-success'
            },
            提醒: {
                icon: 'mdi:calendar-check-outline',
                iconColor: 'text-amber-500',
                iconBg: 'bg-amber-50',
                borderColor: 'border-l-amber-500',
                badgeBg: 'bg-amber-100',
                badgeColor: 'text-amber-700'
            }
        }[type] || {
            icon: 'mdi:bell-outline',
            iconColor: 'text-fg-secondary',
            iconBg: 'bg-bg',
            borderColor: 'border-l-bg-border',
            badgeBg: 'bg-bg',
            badgeColor: 'text-fg-secondary'
        };

        var now = new Date();
        var hh = String(now.getHours()).padStart(2, '0');
        var mm = String(now.getMinutes()).padStart(2, '0');

        _dynamics.unshift({
            id: Date.now(),
            type: type,
            title: title,
            desc: caseName ? caseName + ' · ' + (desc || '无附加描述') : desc || '无附加描述',
            time: '今天 ' + hh + ':' + mm,
            user: '当前用户',
            icon: typeMeta.icon,
            iconColor: typeMeta.iconColor,
            iconBg: typeMeta.iconBg,
            borderColor: typeMeta.borderColor,
            badgeBg: typeMeta.badgeBg,
            badgeColor: typeMeta.badgeColor,
            action: '查看'
        });

        closeNewDynamicModal();
        renderDynamics();

        if (typeof showToast === 'function') showToast('动态已发布', 'success');
    }

    function initCaseDynamics() {
        var searchInput = document.getElementById('dynamics-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', searchDynamics);
        }

        var typeSelect = document.getElementById('dynamics-type-filter');
        if (typeSelect) {
            typeSelect.addEventListener('change', function () {
                var val = this.value;
                if (val === '全部类型') val = 'all';
                _currentFilter = val;
                renderDynamics();
            });
        }

        renderDynamics();
    }

    globalThis.filterDynamics = filterDynamics;
    globalThis.searchDynamics = searchDynamics;
    globalThis.switchDynamicsView = switchDynamicsView;
    globalThis.openCaseDynamicDetail = openCaseDynamicDetail;
    globalThis.closeDynamicDetail = closeDynamicDetail;
    globalThis.openNewDynamicModal = openNewDynamicModal;
    globalThis.closeNewDynamicModal = closeNewDynamicModal;
    globalThis.submitNewDynamic = submitNewDynamic;
    globalThis.initCaseDynamics = initCaseDynamics;
})();
