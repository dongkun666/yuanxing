/**
 * 案件归档模块
 * 包含: 归档列表动态渲染、筛选分页、查看详情、还原案件、删除归档、批量导出
 */
(function() {
    'use strict';

    // ===== 归档数据 =====
    var archiveData = [];

    function initArchiveData() {
        try {
            var saved = localStorage.getItem('lexprime_archive');
            if (saved) {
                var data = JSON.parse(saved);
                if (Array.isArray(data) && data.length > 0) return data;
            }
        } catch (e) { /* fall through */ }

        return [
            { id: 'arc-1', caseNo: '(2025)京01民终456号', type: '房屋买卖合同纠纷', typeCategory: '民事', plaintiff: '陈某某', defendant: '某某房地产公司', archiveDate: '2025-12-15', closeDate: '2025-11-20', court: '北京市第一中级人民法院', result: '调解结案', amount: 3200000, materials: 18 },
            { id: 'arc-2', caseNo: '(2025)京02民终789号', type: '借款合同纠纷', typeCategory: '商事', plaintiff: '赵某某', defendant: '王某某', archiveDate: '2025-11-20', closeDate: '2025-10-15', court: '北京市第二中级人民法院', result: '判决胜诉', amount: 500000, materials: 12 },
            { id: 'arc-3', caseNo: '(2024)京01民终123号', type: '劳动争议', typeCategory: '劳动争议', plaintiff: '孙某某', defendant: '某某科技公司', archiveDate: '2024-12-01', closeDate: '2024-11-10', court: '北京市第一中级人民法院', result: '仲裁调解', amount: 180000, materials: 15 },
            { id: 'arc-4', caseNo: '(2024)京03民终456号', type: '买卖合同纠纷', typeCategory: '商事', plaintiff: '某某贸易公司', defendant: '某制造公司', archiveDate: '2024-10-20', closeDate: '2024-09-28', court: '北京市第三中级人民法院', result: '部分胜诉', amount: 1200000, materials: 22 },
            { id: 'arc-5', caseNo: '(2025)京01民初789号', type: '民间借贷纠纷', typeCategory: '民事', plaintiff: '李某', defendant: '张某', archiveDate: '2025-09-10', closeDate: '2025-08-25', court: '北京市朝阳区人民法院', result: '撤诉', amount: 200000, materials: 8 },
            { id: 'arc-6', caseNo: '(2026)京02民初100号', type: '股权转让纠纷', typeCategory: '商事', plaintiff: '某某投资公司', defendant: '某科技公司', archiveDate: '2026-01-15', closeDate: '2026-01-10', court: '北京市海淀区人民法院', result: '判决胜诉', amount: 5000000, materials: 30 },
            { id: 'arc-7', caseNo: '(2025)京03民初234号', type: '劳动合同纠纷', typeCategory: '劳动争议', plaintiff: '刘某', defendant: '某咨询公司', archiveDate: '2025-07-08', closeDate: '2025-06-20', court: '北京市丰台区人民法院', result: '仲裁胜诉', amount: 95000, materials: 10 }
        ];
    }

    var currentPage = 1;
    var pageSize = 10;
    var selectedIds = [];

    function initArchive() {
        archiveData = initArchiveData();
        currentPage = 1;
        selectedIds = [];
        renderArchiveList();
    }

    function persistArchive() {
        try { localStorage.setItem('lexprime_archive', JSON.stringify(archiveData)); } catch (e) {}
    }

    // ===== 筛选 =====
    function getFilteredArchives() {
        var searchInput = document.getElementById('archiveSearchInput');
        var yearFilter = document.getElementById('archiveYearFilter');
        var typeFilter = document.getElementById('archiveTypeFilter');
        var pageSizeSelect = document.getElementById('archivePageSize');

        var searchText = searchInput ? searchInput.value.trim().toLowerCase() : '';
        var yearValue = yearFilter ? yearFilter.value : '';
        var typeValue = typeFilter ? typeFilter.value : '';
        if (pageSizeSelect) pageSize = parseInt(pageSizeSelect.value) || 10;

        return archiveData.filter(function(item) {
            var year = item.archiveDate ? item.archiveDate.substring(0, 4) : '';
            var matchSearch = !searchText ||
                (item.caseNo || '').toLowerCase().indexOf(searchText) >= 0 ||
                (item.type || '').toLowerCase().indexOf(searchText) >= 0 ||
                (item.plaintiff || '').toLowerCase().indexOf(searchText) >= 0 ||
                (item.defendant || '').toLowerCase().indexOf(searchText) >= 0;
            var matchYear = !yearValue || year === yearValue;
            var matchType = !typeValue || item.typeCategory === typeValue;
            return matchSearch && matchYear && matchType;
        });
    }

    // ===== 渲染 =====
    function renderArchiveList() {
        var tbody = document.getElementById('archiveTableBody');
        var resultCount = document.getElementById('archiveResultCount');
        var paginationInfo = document.getElementById('archivePaginationInfo');
        var paginationBtns = document.getElementById('archivePaginationBtns');
        if (!tbody) return;

        var filtered = getFilteredArchives();
        var totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
        if (currentPage > totalPages) currentPage = totalPages;
        var start = (currentPage - 1) * pageSize;
        var pageItems = filtered.slice(start, start + pageSize);

        if (resultCount) resultCount.textContent = '共 ' + filtered.length + ' 条';

        if (pageItems.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="py-10 text-center text-xs text-fg-tertiary"><iconify-icon icon="mdi:archive-outline" class="text-3xl mb-2 block"></iconify-icon>暂无归档记录</td></tr>';
            if (paginationInfo) paginationInfo.textContent = '';
            if (paginationBtns) paginationBtns.innerHTML = '';
            return;
        }

        var html = '';
        pageItems.forEach(function(item, idx) {
            var realIndex = archiveData.indexOf(item);
            var isChecked = selectedIds.indexOf(item.id) >= 0;
            html += '<tr class="hover:bg-bg-subtle transition-colors" data-index="' + realIndex + '">' +
                '<td class="py-3 px-4"><input type="checkbox" class="archive-checkbox w-4 h-4 rounded border-bg-border cursor-pointer" data-id="' + item.id + '" ' + (isChecked ? 'checked' : '') + '/></td>' +
                '<td class="py-3 px-4"><span class="text-xs font-medium text-brand cursor-pointer hover:underline" onclick="openArchiveDetail(' + realIndex + ')">' + escapeHtml(item.caseNo) + '</span></td>' +
                '<td class="py-3 px-4 text-xs text-fg-secondary">' + escapeHtml(item.type) + '</td>' +
                '<td class="py-3 px-4 text-xs text-fg-secondary">' + escapeHtml(item.plaintiff) + '</td>' +
                '<td class="py-3 px-4 text-xs text-fg-secondary">' + escapeHtml(item.defendant) + '</td>' +
                '<td class="text-center py-3 px-4 text-xs text-fg-tertiary">' + escapeHtml(item.archiveDate) + '</td>' +
                '<td class="text-center py-3 px-4">' +
                    '<div class="flex items-center justify-center gap-2">' +
                        '<button class="text-xs text-brand hover:underline" onclick="openArchiveDetail(' + realIndex + ')">查看</button>' +
                        '<span class="text-bg-border">|</span>' +
                        '<button class="text-xs text-brand hover:underline" onclick="restoreArchive(' + realIndex + ')">还原</button>' +
                        '<span class="text-bg-border">|</span>' +
                        '<button class="text-xs text-red-500 hover:underline" onclick="deleteArchive(' + realIndex + ')">删除</button>' +
                    '</div>' +
                '</td>' +
            '</tr>';
        });
        tbody.innerHTML = html;

        // 绑定 checkbox
        tbody.querySelectorAll('.archive-checkbox').forEach(function(cb) {
            cb.addEventListener('change', function() {
                var id = this.getAttribute('data-id');
                if (this.checked) {
                    if (selectedIds.indexOf(id) < 0) selectedIds.push(id);
                } else {
                    selectedIds = selectedIds.filter(function(sid) { return sid !== id; });
                }
            });
        });

        // 分页
        if (paginationInfo) {
            paginationInfo.textContent = '共 ' + filtered.length + ' 条，第 ' + currentPage + '/' + totalPages + ' 页';
        }
        if (paginationBtns) {
            var btnsHtml = '';
            btnsHtml += '<button class="w-7 h-7 rounded text-xs flex items-center justify-center ' + (currentPage <= 1 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-bg-subtle text-fg-secondary') + '" onclick="' + (currentPage > 1 ? 'archiveGoPage(' + (currentPage - 1) + ')' : '') + '"><iconify-icon icon="mdi:chevron-left"></iconify-icon></button>';
            for (var i = 1; i <= totalPages; i++) {
                if (i === currentPage) {
                    btnsHtml += '<button class="w-7 h-7 rounded text-xs flex items-center justify-center bg-brand text-white">' + i + '</button>';
                } else {
                    btnsHtml += '<button class="w-7 h-7 rounded text-xs flex items-center justify-center hover:bg-bg-subtle text-fg-secondary border border-bg-border" onclick="archiveGoPage(' + i + ')">' + i + '</button>';
                }
            }
            btnsHtml += '<button class="w-7 h-7 rounded text-xs flex items-center justify-center ' + (currentPage >= totalPages ? 'opacity-50 cursor-not-allowed' : 'hover:bg-bg-subtle text-fg-secondary') + '" onclick="' + (currentPage < totalPages ? 'archiveGoPage(' + (currentPage + 1) + ')' : '') + '"><iconify-icon icon="mdi:chevron-right"></iconify-icon></button>';
            paginationBtns.innerHTML = btnsHtml;
        }
    }

    // ===== 全选 =====
    window.toggleAllArchive = function(checkbox) {
        var tbody = document.getElementById('archiveTableBody');
        if (!tbody) return;
        var cbs = tbody.querySelectorAll('.archive-checkbox');
        selectedIds = [];
        cbs.forEach(function(cb) {
            cb.checked = checkbox.checked;
            if (checkbox.checked) {
                var id = cb.getAttribute('data-id');
                if (id) selectedIds.push(id);
            }
        });
    };

    // ===== 分页 =====
    window.archiveGoPage = function(page) {
        var filtered = getFilteredArchives();
        var totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
        if (page < 1 || page > totalPages) return;
        currentPage = page;
        renderArchiveList();
    };

    // ===== 筛选回调 =====
    window.filterArchiveList = function() {
        currentPage = 1;
        renderArchiveList();
    };

    // ===== 查看详情 =====
    window.openArchiveDetail = function(index) {
        var item = archiveData[index];
        if (!item) return;

        var modal = document.getElementById('archive-detail-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'archive-detail-modal';
            modal.className = 'hidden fixed inset-0 z-[1000] bg-black/40 flex items-center justify-center p-4';
            modal.onclick = function(e) { if (e.target === modal) modal.classList.add('hidden'); };
            document.body.appendChild(modal);
        }

        var resultColor = item.result.indexOf('胜诉') >= 0 || item.result.indexOf('调解') >= 0 ? 'bg-green-50 text-success' : (item.result.indexOf('撤诉') >= 0 ? 'bg-bg text-fg-tertiary' : 'bg-amber-50 text-warning');

        modal.innerHTML =
            '<div class="bg-white rounded-xl w-[560px] max-w-full max-h-[85vh] flex flex-col shadow-2xl" onclick="event.stopPropagation()">' +
                '<div class="flex items-center justify-between p-5 border-b border-bg-border">' +
                    '<h3 class="text-base font-semibold text-fg-primary">归档详情</h3>' +
                    '<button class="text-fg-tertiary hover:text-fg-secondary" onclick="closeArchiveDetail()"><iconify-icon icon="mdi:close" class="text-xl"></iconify-icon></button>' +
                '</div>' +
                '<div class="p-5 overflow-y-auto flex-1 space-y-4">' +
                    '<div class="flex items-center justify-between p-3 rounded-lg bg-bg-subtle">' +
                        '<div>' +
                            '<p class="text-sm font-semibold text-fg-primary">' + escapeHtml(item.caseNo) + '</p>' +
                            '<p class="text-xs text-fg-tertiary mt-0.5">' + escapeHtml(item.type) + '</p>' +
                        '</div>' +
                        '<span class="text-xs font-medium px-2 py-0.5 rounded ' + resultColor + '">' + escapeHtml(item.result) + '</span>' +
                    '</div>' +
                    '<div class="grid grid-cols-2 gap-3">' +
                        detailRow('原告', item.plaintiff) +
                        detailRow('被告', item.defendant) +
                        detailRow('审理法院', item.court) +
                        detailRow('标的金额', formatAmount(item.amount)) +
                        detailRow('结案日期', item.closeDate) +
                        detailRow('归档日期', item.archiveDate) +
                        detailRow('材料数量', item.materials + ' 份') +
                    '</div>' +
                '</div>' +
                '<div class="p-4 border-t border-bg-border flex justify-end gap-2">' +
                    '<button class="px-3 py-2 text-xs text-fg-secondary hover:bg-bg-subtle rounded-lg" onclick="closeArchiveDetail()">关闭</button>' +
                    '<button class="px-3 py-2 text-xs text-brand hover:bg-brand-tint3 rounded-lg" onclick="restoreArchive(' + index + '); closeArchiveDetail();">还原到案件列表</button>' +
                '</div>' +
            '</div>';

        modal.classList.remove('hidden');
    };

    function detailRow(label, value) {
        return '<div class="flex justify-between text-xs p-2 rounded bg-bg-subtle"><span class="text-fg-tertiary">' + escapeHtml(label) + '</span><span class="text-fg-primary font-medium">' + escapeHtml(value) + '</span></div>';
    }

    window.closeArchiveDetail = function() {
        var modal = document.getElementById('archive-detail-modal');
        if (modal) modal.classList.add('hidden');
    };

    // ===== 还原 =====
    window.restoreArchive = function(index) {
        var item = archiveData[index];
        if (!item) return;
        if (!confirm('确定将案件「' + item.caseNo + '」还原到案件列表吗？')) return;

        // 从归档中移除
        archiveData.splice(index, 1);
        persistArchive();
        showToast('案件已还原到案件列表');
        renderArchiveList();
    };

    // ===== 删除 =====
    window.deleteArchive = function(index) {
        var item = archiveData[index];
        if (!item) return;
        if (!confirm('确定永久删除归档「' + item.caseNo + '」吗？删除后不可恢复。')) return;

        archiveData.splice(index, 1);
        persistArchive();
        showToast('归档已永久删除');
        renderArchiveList();
    };

    // ===== 批量导出 =====
    window.exportArchiveBatch = function() {
        var tbody = document.getElementById('archiveTableBody');
        if (!tbody) return;
        var checkedRows = tbody.querySelectorAll('.archive-checkbox:checked');
        if (checkedRows.length === 0) {
            showToast('请先选择要导出的归档');
            return;
        }

        // 生成CSV
        var csv = '\uFEFF案号,案由,原告,被告,归档时间,审理法院,结果,标的金额\n';
        checkedRows.forEach(function(cb) {
            var row = cb.closest('tr');
            var cells = row.querySelectorAll('td');
            var caseNo = cells[1] ? cells[1].textContent.trim() : '';
            var type = cells[2] ? cells[2].textContent.trim() : '';
            var plaintiff = cells[3] ? cells[3].textContent.trim() : '';
            var defendant = cells[4] ? cells[4].textContent.trim() : '';
            var archiveDate = cells[5] ? cells[5].textContent.trim() : '';

            var tr = row;
            var idx = parseInt(tr.getAttribute('data-index'));
            var item = archiveData[idx] || {};

            csv += '"' + caseNo + '","' + type + '","' + plaintiff + '","' + defendant + '","' + archiveDate + '","' + (item.court || '') + '","' + (item.result || '') + '","' + (item.amount || '') + '"\n';
        });

        var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = '归档案件导出_' + new Date().toISOString().slice(0, 10) + '.csv';
        a.click();
        URL.revokeObjectURL(url);
        showToast('已导出 ' + checkedRows.length + ' 条归档');
    };

    // ===== 工具函数 =====
    function formatAmount(amount) {
        if (!amount) return '-';
        return '¥' + Number(amount).toLocaleString('zh-CN');
    }

    function escapeHtml(str) {
        return String(str || '').replace(/[&<>"']/g, function(m) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
        });
    }

    // ===== 视图加载监听 =====
    function watchArchiveView() {
        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(m) {
                if (m.target.id === 'view-archive' && !m.target.classList.contains('hidden')) {
                    initArchive();
                    // 绑定批量导出按钮
                    var exportBtn = document.querySelector('#view-archive button.bg-brand');
                    if (exportBtn && !exportBtn.dataset.bound) {
                        exportBtn.onclick = exportArchiveBatch;
                        exportBtn.dataset.bound = '1';
                    }
                }
            });
        });
        var viewEl = document.getElementById('view-archive');
        if (viewEl) {
            observer.observe(viewEl, { attributes: true, attributeFilter: ['class'] });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', watchArchiveView);
    } else {
        watchArchiveView();
    }

    window.initArchive = initArchive;
})();
