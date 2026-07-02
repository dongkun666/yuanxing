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
            tbody.innerHTML = '<tr><td colspan="7" class="py-12 text-center">' +
                '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:archive-search-outline"></iconify-icon>' +
                '<p class="text-sm text-fg-tertiary mt-3">未找到匹配的归档案件</p>' +
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

    function openArchiveDetail(id) {
        var item = _archiveData.find(function(x) { return x.id === id; });
        if (!item) {
            if (typeof showToast === 'function') showToast('未找到归档案件 #' + id);
            return;
        }

        var modal = document.getElementById('archive-detail-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'archive-detail-modal';
            modal.className = 'hidden fixed inset-0 z-[1000] bg-black/40 flex items-center justify-center p-4';
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-modal', 'true');
            modal.addEventListener('click', function(e) {
                if (e.target === modal) closeArchiveDetail();
            });
            document.body.appendChild(modal);
        }

        modal.innerHTML = '<div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">' +
            '<div class="flex items-center justify-between px-5 py-4 border-b border-bg-border">' +
            '<h3 class="text-base font-semibold text-fg-primary flex items-center gap-2">' +
            '<iconify-icon icon="mdi:archive-search-outline" class="text-brand text-lg"></iconify-icon>' +
            '归档详情' +
            '</h3>' +
            '<button class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-bg text-fg-tertiary" onclick="closeArchiveDetail()" aria-label="关闭">' +
            '<iconify-icon icon="mdi:close" class="text-lg"></iconify-icon>' +
            '</button>' +
            '</div>' +
            '<div class="px-5 py-4 space-y-4">' +
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
            '</div>' +
            '<div class="flex items-center justify-end gap-2 px-5 py-4 bg-bg-subtle border-t border-bg-border">' +
            '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeArchiveDetail()">关闭</button>' +
            '<button class="h-9 px-4 text-xs text-brand hover:text-brand-hover bg-brand-tint border border-brand/20 rounded-lg" onclick="closeArchiveDetail(); restoreArchive(' + item.id + ')">还原案件</button>' +
            '<button class="h-9 px-4 text-xs text-danger hover:text-danger/80 bg-danger-tint border border-danger/20 rounded-lg" onclick="closeArchiveDetail(); deleteArchive(' + item.id + ')">删除归档</button>' +
            '</div>' +
            '</div>';

        modal.classList.remove('hidden');
    }

    function closeArchiveDetail() {
        var modal = document.getElementById('archive-detail-modal');
        if (modal) modal.classList.add('hidden');
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
