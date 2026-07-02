(function () {
    'use strict';

    var _archiveData = [
        {
            id: 0,
            caseNum: '(2025)京01民终456号',
            cause: '房屋买卖合同纠纷',
            plaintiff: '陈某某',
            defendant: '某某房地产公司',
            archiveDate: '2025-12-15',
            year: '2025',
            type: '民事'
        },
        {
            id: 1,
            caseNum: '(2025)京02民终789号',
            cause: '借款合同纠纷',
            plaintiff: '赵某某',
            defendant: '王某某',
            archiveDate: '2025-11-20',
            year: '2025',
            type: '商事'
        },
        {
            id: 2,
            caseNum: '(2024)京01民终123号',
            cause: '劳动争议',
            plaintiff: '孙某某',
            defendant: '某某科技公司',
            archiveDate: '2024-12-01',
            year: '2024',
            type: '劳动争议'
        },
        {
            id: 3,
            caseNum: '(2024)京03民初567号',
            cause: '股权转让纠纷',
            plaintiff: '李某某',
            defendant: '某某投资公司',
            archiveDate: '2024-10-15',
            year: '2024',
            type: '商事'
        },
        {
            id: 4,
            caseNum: '(2026)京01民初100号',
            cause: '建设工程合同纠纷',
            plaintiff: '某某建筑公司',
            defendant: '某某房地产公司',
            archiveDate: '2026-01-20',
            year: '2026',
            type: '民事'
        }
    ];

    var _currentPage = 1;
    var _pageSize = 10;
    var _searchTimer = null;
    var _currentYearFilter = '';

    function getFilteredData() {
        var searchInput = document.getElementById('archiveSearchInput');
        var yearFilter = document.getElementById('archiveYearFilter');
        var typeFilter = document.getElementById('archiveTypeFilter');

        var searchText = searchInput ? searchInput.value.trim().toLowerCase() : '';
        var yearValue = yearFilter ? yearFilter.value : (_currentYearFilter === 'all' ? '' : _currentYearFilter);
        var typeValue = typeFilter ? typeFilter.value : '';

        return _archiveData.filter(function (item) {
            var matchSearch =
                !searchText ||
                item.caseNum.toLowerCase().indexOf(searchText) > -1 ||
                item.cause.toLowerCase().indexOf(searchText) > -1 ||
                item.plaintiff.toLowerCase().indexOf(searchText) > -1 ||
                item.defendant.toLowerCase().indexOf(searchText) > -1;
            var matchYear = !yearValue || item.year === yearValue;
            var matchType = !typeValue || item.type.indexOf(typeValue) > -1;
            return matchSearch && matchYear && matchType;
        });
    }

    function getTypeBadgeClass(type) {
        if (type === '民事') return 'archive-type-civil';
        if (type === '商事') return 'archive-type-commercial';
        if (type === '劳动争议') return 'archive-type-labor';
        return 'archive-type-other';
    }

    function renderTableRow(item, index) {
        var staggerIndex = index !== undefined ? index : 0;
        return (
            '<tr class="archive-table-row hover:bg-brand-tint3/40 transition-all duration-200 cursor-default group" data-year="' +
            item.year +
            '" data-animate="fade-in-up" data-stagger-group="archive-rows" data-stagger-index="' + staggerIndex + '" data-delay="0.05">' +
            '<td class="py-4 px-5">' +
            '<input type="checkbox" class="archive-checkbox w-4 h-4 rounded border-bg-border cursor-pointer"/>' +
            '</td>' +
            '<td class="py-4 px-5">' +
            '<div class="flex items-center gap-3">' +
            '<div class="w-9 h-9 rounded-xl bg-gradient-to-br from-wiki-tint to-purple-100 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">' +
            '<iconify-icon icon="mdi:archive-outline" class="text-wiki text-base"></iconify-icon>' +
            '</div>' +
            '<span class="text-sm font-medium text-brand truncate font-mono cursor-pointer hover:underline" title="' + escapeHtml(item.caseNum) + '" onclick="openArchiveDetail(' +
            item.id +
            ')">' +
            escapeHtml(item.caseNum) +
            '</span>' +
            '</div>' +
            '</td>' +
            '<td class="py-4 px-5 text-sm text-fg-secondary truncate" title="' + escapeHtml(item.cause) + '">' +
            escapeHtml(item.cause) +
            '</td>' +
            '<td class="py-4 px-5 text-sm text-fg-secondary truncate" title="' + escapeHtml(item.plaintiff) + '">' +
            escapeHtml(item.plaintiff) +
            '</td>' +
            '<td class="py-4 px-5 text-sm text-fg-secondary truncate" title="' + escapeHtml(item.defendant) + '">' +
            escapeHtml(item.defendant) +
            '</td>' +
            '<td class="text-center py-4 px-5 whitespace-nowrap">' +
            '<div class="inline-flex items-center gap-1.5 text-xs text-fg-tertiary">' +
            '<iconify-icon icon="mdi:calendar-check-outline" class="text-base text-success"></iconify-icon>' +
            '<span>' + item.archiveDate + '</span>' +
            '</div>' +
            '</td>' +
            '<td class="text-center py-4 px-5 whitespace-nowrap">' +
            '<div class="flex items-center justify-center gap-1">' +
            '<button class="table-action-btn table-action-btn-primary" onclick="openArchiveDetail(' + item.id + ')">' +
            '<iconify-icon icon="mdi:eye-outline" class="text-xs"></iconify-icon>查看' +
            '</button>' +
            '<button class="table-action-btn table-action-btn-default" onclick="restoreArchive(' + item.id + ')">' +
            '<iconify-icon icon="mdi:restore" class="text-xs"></iconify-icon>还原' +
            '</button>' +
            '<button class="table-action-btn table-action-btn-danger" onclick="deleteArchive(' + item.id + ')">' +
            '<iconify-icon icon="mdi:trash-outline" class="text-xs"></iconify-icon>删除' +
            '</button>' +
            '</div>' +
            '</td>' +
            '</tr>'
        );
    }

    function updateStatsCards() {
        var statsContainer = document.getElementById('archive-stats-cards');
        if (!statsContainer) return;

        var yearCounts = { all: _archiveData.length, '2026': 0, '2025': 0, '2024': 0 };
        _archiveData.forEach(function (item) {
            if (yearCounts[item.year] !== undefined) {
                yearCounts[item.year]++;
            }
        });

        var cards = statsContainer.querySelectorAll('.archive-stat-card');
        cards.forEach(function (card) {
            var onClickAttr = card.getAttribute('onclick') || '';
            var match = onClickAttr.match(/filterByArchiveYear\('([^']+)'\)/);
            if (match) {
                var year = match[1];
                var countEl = card.querySelector('.text-2xl');
                if (countEl && yearCounts[year] !== undefined) {
                    countEl.textContent = yearCounts[year];
                }
            }
        });
    }

    function renderArchiveTable() {
        var tbody = document.getElementById('archiveTableBody');
        var resultCount = document.getElementById('archiveResultCount');
        var pageSizeSelect = document.getElementById('archivePageSize');
        var paginationInfo = document.getElementById('archivePaginationInfo');
        var paginationBtns = document.getElementById('archivePaginationBtns');
        var emptyState = document.getElementById('archiveEmptyState');
        var table = document.getElementById('archiveTable');

        if (!tbody) return;

        var filtered = getFilteredData();
        _pageSize = pageSizeSelect ? parseInt(pageSizeSelect.value) : 10;

        var totalPages = Math.ceil(filtered.length / _pageSize) || 1;
        if (_currentPage > totalPages) _currentPage = totalPages;

        var startIdx = (_currentPage - 1) * _pageSize;
        var endIdx = startIdx + _pageSize;
        var pageData = filtered.slice(startIdx, endIdx);

        if (filtered.length === 0) {
            if (table) table.classList.add('hidden');
            if (emptyState) {
                emptyState.classList.remove('hidden');
                emptyState.classList.add('flex');
                var searchInput = document.getElementById('archiveSearchInput');
                var hasSearch = searchInput && searchInput.value.trim() !== '';
                Utils.createEmptyState({
                    preset: hasSearch ? 'no-result' : 'empty-list',
                    icon: 'mdi:archive-search-outline',
                    title: hasSearch ? '没有找到匹配的归档案件' : '暂无归档案件',
                    description: hasSearch ? '没有匹配的归档案件，请尝试其他关键词' : '归档已完成或关闭的案件，方便以后查阅',
                    actionText: hasSearch ? '重置筛选' : '查看案件列表',
                    actionHandler: hasSearch ? resetArchiveFilters : function () { switchToList('case-list', null); },
                    container: emptyState
                });
            }
        } else {
            if (table) table.classList.remove('hidden');
            if (emptyState) {
                emptyState.classList.add('hidden');
                emptyState.classList.remove('flex');
            }
            tbody.innerHTML = pageData
                .map(function (item, idx) {
                    return renderTableRow(item, idx);
                })
                .join('');

            setTimeout(function () {
                if (typeof Animations !== 'undefined' && Animations.initPageAnimations) {
                    Animations.initPageAnimations(tbody);
                }
            }, 50);
        }

        if (resultCount) resultCount.textContent = '共 ' + filtered.length + ' 条';
        if (paginationInfo)
            paginationInfo.textContent = '共 ' + filtered.length + ' 条，第 ' + _currentPage + '/' + totalPages + ' 页';

        if (paginationBtns) {
            paginationBtns.innerHTML = '';
            if (_currentPage > 1) {
                var prevBtn = document.createElement('button');
                prevBtn.className = 'w-8 h-8 rounded-xl hover:bg-bg-subtle flex items-center justify-center text-xs text-fg-tertiary hover:text-brand transition-all hover:-translate-y-0.5';
                prevBtn.innerHTML = '<iconify-icon icon="mdi:chevron-left"></iconify-icon>';
                prevBtn.onclick = function () {
                    _currentPage--;
                    renderArchiveTable();
                };
                paginationBtns.appendChild(prevBtn);
            }
            for (var i = 1; i <= totalPages; i++) {
                var btn = document.createElement('button');
                btn.className =
                    'min-w-[32px] h-8 rounded-xl text-xs font-medium flex items-center justify-center transition-all ' +
                    (i === _currentPage
                        ? 'bg-gradient-to-r from-brand to-brand-hover text-white shadow-md shadow-brand/20'
                        : 'bg-white hover:bg-bg-subtle text-fg-secondary border border-bg-border hover:border-brand hover:text-brand hover:-translate-y-0.5');
                btn.textContent = i;
                btn.onclick = (function (page) {
                    return function () {
                        _currentPage = page;
                        renderArchiveTable();
                    };
                })(i);
                paginationBtns.appendChild(btn);
            }
            if (_currentPage < totalPages) {
                var nextBtn = document.createElement('button');
                nextBtn.className = 'w-8 h-8 rounded-xl hover:bg-bg-subtle flex items-center justify-center text-xs text-fg-tertiary hover:text-brand transition-all hover:-translate-y-0.5';
                nextBtn.innerHTML = '<iconify-icon icon="mdi:chevron-right"></iconify-icon>';
                nextBtn.onclick = function () {
                    _currentPage++;
                    renderArchiveTable();
                };
                paginationBtns.appendChild(nextBtn);
            }
        }
    }

    function filterArchiveList() {
        clearTimeout(_searchTimer);
        _searchTimer = setTimeout(function () {
            _currentPage = 1;
            renderArchiveTable();
        }, 300);
    }

    function filterByArchiveYear(year) {
        _currentYearFilter = year;
        var yearFilter = document.getElementById('archiveYearFilter');
        if (yearFilter) {
            yearFilter.value = year === 'all' ? '' : year;
        }
        _currentPage = 1;
        renderArchiveTable();
    }

    function resetArchiveFilters() {
        var searchInput = document.getElementById('archiveSearchInput');
        var yearFilter = document.getElementById('archiveYearFilter');
        var typeFilter = document.getElementById('archiveTypeFilter');

        if (searchInput) searchInput.value = '';
        if (yearFilter) yearFilter.value = '';
        if (typeFilter) typeFilter.value = '';

        _currentYearFilter = '';
        _currentPage = 1;
        renderArchiveTable();
    }

    function toggleAllArchive(checkbox) {
        var checkboxes = document.querySelectorAll('.archive-checkbox');
        checkboxes.forEach(function (cb) {
            cb.checked = checkbox.checked;
        });
    }

    var _closeArchiveDetail = null;

    function openArchiveDetail(id) {
        var item = _archiveData.find(function (x) {
            return x.id === id;
        });
        if (!item) {
            if (typeof showToast === 'function') showToast('未找到归档案件 #' + id);
            return;
        }

        var content =
            '<div class="space-y-4">' +
            '<div class="flex items-center gap-3 p-4 bg-gradient-to-r from-wiki-tint to-purple-50 rounded-2xl border border-purple-100">' +
            '<div class="w-14 h-14 rounded-xl bg-gradient-to-br from-wiki to-purple-600 text-white flex items-center justify-center flex-shrink-0 shadow-lg shadow-wiki/20">' +
            '<iconify-icon icon="mdi:archive" class="text-2xl"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<p class="font-semibold text-sm text-fg-primary font-mono">' +
            escapeHtml(item.caseNum) +
            '</p>' +
            '<p class="text-xs text-fg-tertiary mt-0.5">' +
            escapeHtml(item.cause) +
            '</p>' +
            '<span class="inline-block mt-1.5 archive-type-badge ' + getTypeBadgeClass(item.type) + '">' +
            escapeHtml(item.type) +
            '</span>' +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-xl hover:border-brand/30 transition-colors">' +
            '<p class="text-[11px] text-fg-tertiary mb-1 flex items-center gap-1">' +
            '<iconify-icon icon="mdi:gavel" class="text-[10px]"></iconify-icon>案件类型' +
            '</p>' +
            '<p class="text-sm font-medium text-fg-primary">' +
            escapeHtml(item.type) +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-xl hover:border-brand/30 transition-colors">' +
            '<p class="text-[11px] text-fg-tertiary mb-1 flex items-center gap-1">' +
            '<iconify-icon icon="mdi:calendar-outline" class="text-[10px]"></iconify-icon>归档年份' +
            '</p>' +
            '<p class="text-sm font-medium text-fg-primary">' +
            escapeHtml(item.year) +
            ' 年</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-xl hover:border-brand/30 transition-colors">' +
            '<p class="text-[11px] text-fg-tertiary mb-1 flex items-center gap-1">' +
            '<iconify-icon icon="mdi:account-outline" class="text-[10px]"></iconify-icon>原告' +
            '</p>' +
            '<p class="text-sm font-medium text-fg-primary">' +
            escapeHtml(item.plaintiff) +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-xl hover:border-brand/30 transition-colors">' +
            '<p class="text-[11px] text-fg-tertiary mb-1 flex items-center gap-1">' +
            '<iconify-icon icon="mdi:account-outline" class="text-[10px]"></iconify-icon>被告' +
            '</p>' +
            '<p class="text-sm font-medium text-fg-primary">' +
            escapeHtml(item.defendant) +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="p-4 bg-gradient-to-r from-success-tint/50 to-green-50 rounded-2xl border border-green-100">' +
            '<div class="flex items-center gap-2 mb-1">' +
            '<iconify-icon icon="mdi:calendar-check-outline" class="text-success text-base"></iconify-icon>' +
            '<p class="text-[11px] text-success font-semibold">归档日期</p>' +
            '</div>' +
            '<p class="text-base font-bold text-fg-primary">' +
            escapeHtml(item.archiveDate) +
            '</p>' +
            '</div>' +
            '<div class="text-[11px] text-fg-tertiary flex items-center gap-1 p-3 bg-bg-subtle rounded-xl">' +
            '<iconify-icon icon="mdi:information-outline" class="text-brand"></iconify-icon>' +
            '<span>案件已归档，如需恢复可点击下方"还原案件"按钮</span>' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="h-9 px-4 text-xs font-medium text-fg-secondary bg-white border border-bg-border rounded-xl hover:bg-bg transition-all" onclick="closeArchiveDetail()">关闭</button>' +
            '<button class="h-9 px-4 text-xs font-medium text-brand hover:text-brand-hover bg-brand-tint border border-brand/20 rounded-xl hover:bg-brand-tint2 transition-all flex items-center gap-1.5" onclick="closeArchiveDetail(); restoreArchive(' +
            item.id +
            ')">' +
            '<iconify-icon icon="mdi:restore" class="text-sm"></iconify-icon>还原案件' +
            '</button>' +
            '<button class="h-9 px-4 text-xs font-medium text-danger hover:text-danger/80 bg-danger-tint border border-danger/20 rounded-xl hover:bg-red-100 transition-all flex items-center gap-1.5" onclick="closeArchiveDetail(); deleteArchive(' +
            item.id +
            ')">' +
            '<iconify-icon icon="mdi:trash-outline" class="text-sm"></iconify-icon>删除归档' +
            '</button>';

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

    async function restoreArchive(id) {
        var item = _archiveData.find(function (x) {
            return x.id === id;
        });
        if (!item) return;
        var confirmed = await Utils.showConfirm('确定要将案件 "' + item.caseNum + '" 从归档中还原吗？');
        if (confirmed) {
            _archiveData = _archiveData.filter(function (x) {
                return x.id !== id;
            });
            renderArchiveTable();
            updateStatsCards();
            Utils.showToast('success', '案件已还原');
        }
    }

    async function deleteArchive(id) {
        var item = _archiveData.find(function (x) {
            return x.id === id;
        });
        if (!item) return;
        var confirmed = await Utils.showConfirm('确定要永久删除归档案件 "' + item.caseNum + '" 吗？此操作不可撤销。');
        if (confirmed) {
            _archiveData = _archiveData.filter(function (x) {
                return x.id !== id;
            });
            renderArchiveTable();
            updateStatsCards();
            Utils.showToast('success', '案件已删除');
        }
    }

    function batchExportArchive() {
        if (typeof showToast === 'function') {
            showToast('批量导出功能开发中...');
        }
    }

    function initArchive() {
        var pageSizeSelect = document.getElementById('archivePageSize');
        if (pageSizeSelect) {
            pageSizeSelect.addEventListener('change', filterArchiveList);
        }
        updateStatsCards();
        renderArchiveTable();
    }

    globalThis.filterArchiveList = filterArchiveList;
    globalThis.toggleAllArchive = toggleAllArchive;
    globalThis.openArchiveDetail = openArchiveDetail;
    globalThis.closeArchiveDetail = closeArchiveDetail;
    globalThis.restoreArchive = restoreArchive;
    globalThis.deleteArchive = deleteArchive;
    globalThis.initArchive = initArchive;
    globalThis.filterByArchiveYear = filterByArchiveYear;
    globalThis.resetArchiveFilters = resetArchiveFilters;
    globalThis.batchExportArchive = batchExportArchive;
})();
