(function() {
    'use strict';

    var _archiveData = [
        { id: 0, caseNum: '(2025)京01民终456号', cause: '房屋买卖合同纠纷', plaintiff: '陈某某', defendant: '某某房地产公司', archiveDate: '2025-12-15', year: '2025', type: '民事' },
        { id: 1, caseNum: '(2025)京02民终789号', cause: '借款合同纠纷', plaintiff: '赵某某', defendant: '王某某', archiveDate: '2025-11-20', year: '2025', type: '商事' },
        { id: 2, caseNum: '(2024)京01民终123号', cause: '劳动争议', plaintiff: '孙某某', defendant: '某某科技公司', archiveDate: '2024-12-01', year: '2024', type: '劳动争议' },
        { id: 3, caseNum: '(2024)京03民初567号', cause: '股权转让纠纷', plaintiff: '李某某', defendant: '某某投资公司', archiveDate: '2024-10-15', year: '2024', type: '商事' },
        { id: 4, caseNum: '(2026)京01民初100号', cause: '建设工程合同纠纷', plaintiff: '某某建筑公司', defendant: '某某房地产公司', archiveDate: '2026-01-20', year: '2026', type: '民事' }
    ];

    var _currentPage = 1;
    var _pageSize = 10;
    var _searchTimer = null;

    function getFilteredData() {
        var searchInput = document.getElementById('archiveSearchInput');
        var yearFilter = document.getElementById('archiveYearFilter');
        var typeFilter = document.getElementById('archiveTypeFilter');

        var searchText = searchInput ? searchInput.value.trim().toLowerCase() : '';
        var yearValue = yearFilter ? yearFilter.value : '';
        var typeValue = typeFilter ? typeFilter.value : '';

        return _archiveData.filter(function(item) {
            var matchSearch = !searchText ||
                item.caseNum.toLowerCase().indexOf(searchText) > -1 ||
                item.cause.toLowerCase().indexOf(searchText) > -1 ||
                item.plaintiff.toLowerCase().indexOf(searchText) > -1 ||
                item.defendant.toLowerCase().indexOf(searchText) > -1;
            var matchYear = !yearValue || item.year === yearValue;
            var matchType = !typeValue || item.type.indexOf(typeValue) > -1;
            return matchSearch && matchYear && matchType;
        });
    }

    function renderArchiveTable() {
        var tbody = document.getElementById('archiveTableBody');
        var resultCount = document.getElementById('archiveResultCount');
        var pageSizeSelect = document.getElementById('archivePageSize');
        var paginationInfo = document.getElementById('archivePaginationInfo');
        var paginationBtns = document.getElementById('archivePaginationBtns');

        if (!tbody) return;

        var filtered = getFilteredData();
        _pageSize = pageSizeSelect ? parseInt(pageSizeSelect.value) : 10;

        var totalPages = Math.ceil(filtered.length / _pageSize) || 1;
        if (_currentPage > totalPages) _currentPage = totalPages;

        var startIdx = (_currentPage - 1) * _pageSize;
        var endIdx = startIdx + _pageSize;
        var pageData = filtered.slice(startIdx, endIdx);

        if (filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="py-16 text-center">' +
                '<div class="flex flex-col items-center">' +
                '<div class="w-16 h-16 bg-bg-subtle rounded-full flex items-center justify-center mb-3">' +
                '<iconify-icon class="text-3xl text-fg-disabled" icon="mdi:archive-search-outline"></iconify-icon>' +
                '</div>' +
                '<p class="text-sm font-medium text-fg-primary mb-1">暂无归档案件</p>' +
                '<p class="text-xs text-fg-tertiary mb-4">归档已完成或关闭的案件，方便以后查阅</p>' +
                '<div class="flex items-center justify-center gap-2">' +
                '<button class="h-8 px-3 text-xs text-brand bg-brand-tint rounded-lg hover:bg-brand-tint/70" onclick="switchToList(\'case-list\')">查看案件列表</button>' +
                '<button class="h-8 px-3 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="switchView(\'deadline\')">期限计算</button>' +
                '</div>' +
                '</div>' +
                '</td></tr>';
        } else {
            tbody.innerHTML = pageData.map(function(item) {
                return '<tr class="hover:bg-bg-subtle transition-colors" data-year="' + item.year + '">' +
                '<td class="py-3 px-4"><input type="checkbox" class="archive-checkbox w-4 h-4 rounded border-bg-border cursor-pointer"/></td>' +
                '<td class="py-3 px-4"><span class="text-xs font-medium text-brand cursor-pointer hover:underline" onclick="openArchiveDetail(' + item.id + ')">' + escapeHtml(item.caseNum) + '</span></td>' +
                '<td class="py-3 px-4 text-xs text-fg-secondary">' + escapeHtml(item.cause) + '</td>' +
                '<td class="py-3 px-4 text-xs text-fg-secondary">' + escapeHtml(item.plaintiff) + '</td>' +
                '<td class="py-3 px-4 text-xs text-fg-secondary">' + escapeHtml(item.defendant) + '</td>' +
                '<td class="text-center py-3 px-4 text-xs text-fg-tertiary">' + item.archiveDate + '</td>' +
                '<td class="text-center py-3 px-4">' +
                '<div class="flex items-center justify-center gap-2">' +
                '<button class="text-xs text-brand hover:underline" onclick="openArchiveDetail(' + item.id + ')">查看</button>' +
                '<span class="text-bg-border">|</span>' +
                '<button class="text-xs text-brand hover:underline" onclick="restoreArchive(' + item.id + ')">还原</button>' +
                '<span class="text-bg-border">|</span>' +
                '<button class="text-xs text-danger hover:underline" onclick="deleteArchive(' + item.id + ')">删除</button>' +
                '</div>' +
                '</td>' +
                '</tr>';
            }).join('');
        }

        if (resultCount) resultCount.textContent = '共 ' + filtered.length + ' 条';
        if (paginationInfo) paginationInfo.textContent = '共 ' + filtered.length + ' 条，第 ' + _currentPage + '/' + totalPages + ' 页';

        if (paginationBtns) {
            paginationBtns.innerHTML = '';
            for (var i = 1; i <= totalPages; i++) {
                var btn = document.createElement('button');
                btn.className = 'w-7 h-7 rounded text-xs flex items-center justify-center ' +
                    (i === _currentPage ? 'bg-brand text-white' : 'bg-white hover:bg-bg-subtle text-fg-secondary border border-bg-border');
                btn.textContent = i;
                btn.onclick = (function(page) {
                    return function() {
                        _currentPage = page;
                        renderArchiveTable();
                    };
                })(i);
                paginationBtns.appendChild(btn);
            }
        }
    }

    function filterArchiveList() {
        clearTimeout(_searchTimer);
        _searchTimer = setTimeout(function() {
            _currentPage = 1;
            renderArchiveTable();
        }, 300);
    }

    function toggleAllArchive(checkbox) {
        var checkboxes = document.querySelectorAll('.archive-checkbox');
        checkboxes.forEach(function(cb) { cb.checked = checkbox.checked; });
    }

    var _closeArchiveDetail = null;

    function openArchiveDetail(id) {
        var item = _archiveData.find(function(x) { return x.id === id; });
        if (!item) {
            if (typeof showToast === 'function') showToast('未找到归档案件 #' + id);
            return;
        }

        var content = '<div class="space-y-4">' +
            '<div class="flex items-center gap-3 p-3 bg-bg-subtle rounded-xl">' +
            '<div class="w-12 h-12 rounded-lg bg-wiki-tint text-wiki flex items-center justify-center flex-shrink-0">' +
            '<iconify-icon icon="mdi:archive" class="text-xl"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<p class="font-medium text-sm text-fg-primary font-mono">' + escapeHtml(item.caseNum) + '</p>' +
            '<p class="text-xs text-fg-tertiary">' + escapeHtml(item.cause) + '</p>' +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">案件类型</p>' +
            '<p class="text-sm text-fg-primary">' + escapeHtml(item.type) + '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">归档年份</p>' +
            '<p class="text-sm text-fg-primary">' + escapeHtml(item.year) + ' 年</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">原告</p>' +
            '<p class="text-sm text-fg-primary">' + escapeHtml(item.plaintiff) + '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">被告</p>' +
            '<p class="text-sm text-fg-primary">' + escapeHtml(item.defendant) + '</p>' +
            '</div>' +
            '</div>' +
            '<div class="p-3 bg-bg-subtle rounded-xl">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">归档日期</p>' +
            '<p class="text-sm text-fg-primary">' + escapeHtml(item.archiveDate) + '</p>' +
            '</div>' +
            '<div class="text-[11px] text-fg-tertiary flex items-center gap-1">' +
            '<iconify-icon icon="mdi:information-outline"></iconify-icon>' +
            '案件已归档, 如需恢复可点击下方按钮' +
            '</div>' +
            '</div>';

        var footer = '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeArchiveDetail()">关闭</button>' +
            '<button class="h-9 px-4 text-xs text-brand hover:text-brand-hover bg-brand-tint border border-brand/20 rounded-lg" onclick="closeArchiveDetail(); restoreArchive(' + item.id + ')">还原案件</button>' +
            '<button class="h-9 px-4 text-xs text-danger hover:text-danger/80 bg-danger-tint border border-danger/20 rounded-lg" onclick="closeArchiveDetail(); deleteArchive(' + item.id + ')">删除归档</button>';

        if (_closeArchiveDetail) _closeArchiveDetail();
        _closeArchiveDetail = Utils.showModal({
            id: 'archive-detail-modal',
            title: '归档详情',
            icon: 'mdi:archive-search-outline',
            content: content,
            footer: footer,
            size: 'md'
        });
    }

    function closeArchiveDetail() {
        if (_closeArchiveDetail) {
            _closeArchiveDetail();
            _closeArchiveDetail = null;
        }
    }

    function restoreArchive(id) {
        var item = _archiveData.find(function(x) { return x.id === id; });
        if (!item) return;
        if (confirm('确定要将案件 "' + item.caseNum + '" 从归档中还原吗？')) {
            _archiveData = _archiveData.filter(function(x) { return x.id !== id; });
            renderArchiveTable();
            if (typeof showToast === 'function') showToast('案件已还原');
        }
    }

    function deleteArchive(id) {
        var item = _archiveData.find(function(x) { return x.id === id; });
        if (!item) return;
        if (confirm('确定要永久删除归档案件 "' + item.caseNum + '" 吗？此操作不可撤销。')) {
            _archiveData = _archiveData.filter(function(x) { return x.id !== id; });
            renderArchiveTable();
            if (typeof showToast === 'function') showToast('案件已删除');
        }
    }

    function initArchive() {
        var pageSizeSelect = document.getElementById('archivePageSize');
        if (pageSizeSelect) {
            pageSizeSelect.addEventListener('change', filterArchiveList);
        }
        renderArchiveTable();
    }

    globalThis.filterArchiveList = filterArchiveList;
    globalThis.toggleAllArchive = toggleAllArchive;
    globalThis.openArchiveDetail = openArchiveDetail;
    globalThis.closeArchiveDetail = closeArchiveDetail;
    globalThis.restoreArchive = restoreArchive;
    globalThis.deleteArchive = deleteArchive;
    globalThis.initArchive = initArchive;
})();
