/**
 * 案件 - 列表/归档/新建模块
 * 拆分自 cases.js (2026-06-28 IIFE 拆分计划)
 *
 * 包含: 案件列表筛选/分页 + 案件标题编辑 + 案件删除 + 新建案件 modal +
 *       归档列表/恢复/删除/筛选
 * 依赖: caseCurrentPage (script.js), AppState (app-state.js),
 *       showToast (script.js), openCaseDetail (cases-detail.js)
 *
 * 加载顺序: 在 cases-detail.js 之前 (因 openCaseDetail 由 cases-detail.js 暴露)
 */

(function () {
    'use strict';

    // ===== 跨模块共享状态 (script.js 在 IIFE 内 var, 需显式桥接 globalThis) =====
    if (typeof globalThis.caseCurrentPage === 'undefined') globalThis.caseCurrentPage = 1;

    // 案件列表筛选 + 分页
    function filterCaseList() {
        // 隐藏已归档的 row
        try {
            var archived = JSON.parse(localStorage.getItem('lexprime_archived') || '[]');
            if (archived.length > 0) {
                var allRows = document.querySelectorAll('#caseTableBody tr[data-row-idx]');
                allRows.forEach(function (row) {
                    var idx = parseInt(row.getAttribute('data-row-idx'));
                    if (archived.indexOf(idx) >= 0) row.style.display = 'none';
                });
            }
        } catch (e) {
            /* ignore */
        }
        var searchInput = document.getElementById('caseSearchInput');
        var statusFilter = document.getElementById('caseStatusFilter');
        var typeFilter = document.getElementById('caseTypeFilter');
        var tbody = document.getElementById('caseTableBody');
        var resultCount = document.getElementById('caseResultCount');
        var pageSizeSelect = document.getElementById('casePageSize');
        var paginationInfo = document.getElementById('casePaginationInfo');
        var paginationBtns = document.getElementById('casePaginationBtns');

        if (!searchInput || !statusFilter || !typeFilter || !tbody) return;

        var searchText = searchInput.value.trim().toLowerCase();
        var statusValue = statusFilter.value;
        var typeValue = typeFilter.value;
        var pageSize = pageSizeSelect ? parseInt(pageSizeSelect.value) : 10;

        var rows = tbody.querySelectorAll('tr');
        var filteredRows = [];

        rows.forEach(function (row) {
            var caseNum = row.querySelector('td:nth-child(1)')?.textContent.toLowerCase() || '';
            var caseType = row.querySelector('td:nth-child(2)')?.textContent.toLowerCase() || '';
            var party = row.querySelector('td:nth-child(3)')?.textContent.toLowerCase() || '';
            var lawyer = row.querySelector('td:nth-child(4)')?.textContent.toLowerCase() || '';
            var rowStatus = row.getAttribute('data-status') || '';
            var rowType = row.getAttribute('data-type') || '';

            var matchSearch =
                !searchText ||
                caseNum.includes(searchText) ||
                caseType.includes(searchText) ||
                party.includes(searchText) ||
                lawyer.includes(searchText);

            var matchStatus = !statusValue || rowStatus === statusValue;
            var matchType = !typeValue || rowType.includes(typeValue) || caseType.includes(typeValue);

            if (matchSearch && matchStatus && matchType) {
                filteredRows.push(row);
            }
        });

        globalThis.caseCurrentPage = 1;

        if (resultCount) {
            resultCount.textContent = '共 ' + filteredRows.length + ' 条';
        }

        var totalPages = Math.ceil(filteredRows.length / pageSize) || 1;
        if (globalThis.caseCurrentPage > totalPages) globalThis.caseCurrentPage = totalPages;

        var startIdx = (globalThis.caseCurrentPage - 1) * pageSize;
        var endIdx = startIdx + pageSize;

        rows.forEach(function (row) {
            row.style.display = 'none';
        });
        filteredRows.forEach(function (row, idx) {
            if (idx >= startIdx && idx < endIdx) {
                row.style.display = '';
            }
        });

        if (paginationInfo) {
            paginationInfo.textContent =
                '共 ' + filteredRows.length + ' 条，第 ' + globalThis.caseCurrentPage + '/' + totalPages + ' 页';
        }

        if (paginationBtns) {
            paginationBtns.innerHTML = '';
            for (var i = 1; i <= totalPages; i++) {
                var btn = document.createElement('button');
                btn.className =
                    'w-7 h-7 rounded text-xs flex items-center justify-center ' +
                    (i === caseCurrentPage
                        ? 'bg-[#165DFF] text-white'
                        : 'bg-white hover:bg-[#F7F8FA] text-[#4E5969] border border-[#E5E6EB]');
                btn.textContent = i;
                btn.onclick = (function (page) {
                    return function () {
                        goToCasePage(page, pageSize);
                    };
                })(i);
                paginationBtns.appendChild(btn);
            }
        }
    }

    function goToCasePage(page, pageSize) {
        globalThis.caseCurrentPage = page;
        filterCaseList();
    }

    async function archiveCase(idx) {
        if (idx === undefined || idx === null) {
            // 兼容无参调用: 从 currentCaseIndex 读
            idx = globalThis.currentCaseIndex;
        }
        if (idx === undefined || idx < 0) {
            showToast('请先点击案件"详情"再归档', 'warning');
            return;
        }
        var confirmed = await Utils.showConfirm('确定归档当前案件？归档后会从案件列表移除，可在"归档管理"中查看/恢复。');
        if (!confirmed) return;
        var archived = JSON.parse(localStorage.getItem('lexprime_archived') || '[]');
        if (archived.indexOf(idx) === -1) archived.push(idx);
        localStorage.setItem('lexprime_archived', JSON.stringify(archived));
        showToast('案件已归档', 'success');
        if (typeof filterCaseList === 'function') filterCaseList();
    }

    function editCaseTitle() {
        var el = document.getElementById('case-detail-title');
        if (!el) return;
        var currentText = el.textContent.trim();
        var input = document.createElement('input');
        input.type = 'text';
        input.value = currentText;
        input.className =
            'text-sm font-medium text-gray-800 bg-transparent border border-[#165DFF] rounded px-2 py-0.5 outline-none focus:border-[#165DFF] w-auto min-w-[200px]';

        function finishEdit() {
            var newText = input.value.trim();
            if (newText && newText !== currentText) {
                el.textContent = newText;
                if (typeof globalThis.currentCaseIndex !== 'undefined' && globalThis.currentCaseIndex >= 0) {
                    var tbody = document.getElementById('caseTableBody');
                    if (tbody) {
                        var rows = tbody.querySelectorAll('tr');
                        if (rows[globalThis.currentCaseIndex]) {
                            var firstTd = rows[globalThis.currentCaseIndex].querySelector('td:first-child');
                            if (firstTd) {
                                firstTd.textContent = newText;
                            }
                        }
                    }
                }
                showToast('案件名已更新');
            }
            el.style.display = '';
            input.remove();
            var editBtn = document.getElementById('case-title-edit-btn');
            if (editBtn) editBtn.style.display = '';
        }

        input.addEventListener('blur', finishEdit);
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                input.blur();
            } else if (e.key === 'Escape') {
                input.value = currentText;
                input.blur();
            }
        });

        el.style.display = 'none';
        var editBtn = el.nextElementSibling;
        if (editBtn) editBtn.style.display = 'none';
        el.parentNode.insertBefore(input, el.nextSibling);
        input.focus();
        input.select();
    }

    async function deleteCase(index) {
        var confirmed = await Utils.showConfirm('确定要删除该案件吗？删除后不可恢复。');
        if (!confirmed) return;
        var tbody = document.getElementById('caseTableBody');
        if (!tbody) return;
        var rows = tbody.querySelectorAll('tr');
        if (rows[index]) {
            rows[index].remove();
            showToast('案件已删除');
            filterCaseList();
        }
    }

    var _closeNewCaseModal = null;

    function openNewCaseModal() {
        var content =
            '' +
            '<div class="space-y-5">' +
            '<div>' +
            '<h5 class="text-sm font-semibold text-fg-primary mb-3 flex items-center gap-2">' +
            '<iconify-icon class="text-brand" icon="mdi:file-document-outline"></iconify-icon>' +
            '案件基本信息' +
            '</h5>' +
            '<div class="grid grid-cols-3 gap-4">' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">案件名 <span class="text-red-400">*</span></label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-case-name" placeholder="请输入案件名" type="text"/>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">案号</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-case-number" placeholder="请输入案号" type="text"/>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">案由</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-case-type" placeholder="请输入案由" type="text"/>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">案件状态</label>' +
            '<select class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand appearance-none bg-white" id="new-case-status">' +
            '<option value="进行中">进行中</option>' +
            '<option value="待开庭">待开庭</option>' +
            '<option value="已结案">已结案</option>' +
            '<option value="已归档">已归档</option>' +
            '<option value="中止审理">中止审理</option>' +
            '</select>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">标的金额</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-case-claim" placeholder="请输入标的金额" type="text"/>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">合同金额</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-case-contract" placeholder="请输入合同金额" type="text"/>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">签约日期</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-case-signDate" type="date"/>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">代理阶段</label>' +
            '<select class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand appearance-none bg-white" id="new-case-stage">' +
            '<option value="一审">一审</option>' +
            '<option value="二审">二审</option>' +
            '<option value="再审">再审</option>' +
            '<option value="执行">执行</option>' +
            '<option value="仲裁">仲裁</option>' +
            '</select>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">是否保全</label>' +
            '<select class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand appearance-none bg-white" id="new-case-preservation">' +
            '<option value="未保全">未保全</option>' +
            '<option value="已保全">已保全</option>' +
            '<option value="保全中">保全中</option>' +
            '</select>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">缴费情况</label>' +
            '<select class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand appearance-none bg-white" id="new-case-payment">' +
            '<option value="已缴费">已缴费</option>' +
            '<option value="未缴费">未缴费</option>' +
            '<option value="部分缴费">部分缴费</option>' +
            '</select>' +
            '</div>' +
            '<div class="col-span-2">' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">特殊约定</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-case-special" placeholder="请输入特殊约定" type="text"/>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '<div>' +
            '<h5 class="text-sm font-semibold text-fg-primary mb-3 flex items-center gap-2">' +
            '<iconify-icon class="text-green-500" icon="mdi:account"></iconify-icon>' +
            '客户信息' +
            '</h5>' +
            '<div class="grid grid-cols-2 gap-4">' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">客户姓名</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-client-name" placeholder="请输入客户姓名" type="text"/>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">客户电话</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-client-phone" placeholder="请输入客户电话" type="text"/>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">客户证件号</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-client-id" placeholder="请输入客户证件号" type="text"/>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">法定代表人</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-client-legalRep" placeholder="请输入法定代表人" type="text"/>' +
            '</div>' +
            '<div class="col-span-2">' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">客户地址</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-client-address" placeholder="请输入客户地址" type="text"/>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '<div>' +
            '<h5 class="text-sm font-semibold text-fg-primary mb-3 flex items-center gap-2">' +
            '<iconify-icon class="text-red-500" icon="mdi:account"></iconify-icon>' +
            '对方信息' +
            '</h5>' +
            '<div class="grid grid-cols-2 gap-4">' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">对方姓名</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-opponent-name" placeholder="请输入对方姓名" type="text"/>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">对方电话</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-opponent-phone" placeholder="请输入对方电话" type="text"/>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">对方证件号</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-opponent-id" placeholder="请输入对方证件号" type="text"/>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">法定代表人</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-opponent-legalRep" placeholder="请输入法定代表人" type="text"/>' +
            '</div>' +
            '<div class="col-span-2">' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">对方地址</label>' +
            '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" id="new-opponent-address" placeholder="请输入对方地址" type="text"/>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '<div>' +
            '<h5 class="text-sm font-semibold text-fg-primary mb-3 flex items-center gap-2">' +
            '<iconify-icon class="text-brand" icon="mdi:format-list-checks"></iconify-icon>' +
            '客户诉求' +
            '</h5>' +
            '<textarea class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand resize-none" id="new-case-claims" placeholder="请输入客户诉求，每行一项" rows="4"></textarea>' +
            '</div>' +
            '<div>' +
            '<h5 class="text-sm font-semibold text-fg-primary mb-3 flex items-center gap-2">' +
            '<iconify-icon class="text-brand" icon="mdi:lightbulb-outline"></iconify-icon>' +
            '办案思路' +
            '</h5>' +
            '<textarea class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand resize-none" id="new-case-strategy" placeholder="请输入办案思路" rows="4"></textarea>' +
            '</div>' +
            '<div>' +
            '<h5 class="text-sm font-semibold text-fg-primary mb-3 flex items-center gap-2">' +
            '<iconify-icon class="text-brand" icon="mdi:text-subject"></iconify-icon>' +
            '案情简述' +
            '</h5>' +
            '<textarea class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand resize-none" id="new-case-summary" placeholder="请输入案情简述" rows="4"></textarea>' +
            '</div>' +
            '</div>';

        var footer =
            '' +
            '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg transition-colors" onclick="closeNewCaseModal()">取消</button>' +
            '<button class="h-9 px-4 text-xs font-medium text-white bg-brand hover:bg-blue-600 rounded-lg transition-colors" onclick="submitNewCase()">立即创建</button>';

        if (_closeNewCaseModal) _closeNewCaseModal();
        _closeNewCaseModal = Utils.showModal({
            id: 'new-case-modal',
            title: '新建案件',
            content: content,
            footer: footer,
            size: 'xl'
        });
    }

    function closeNewCaseModal() {
        if (_closeNewCaseModal) {
            _closeNewCaseModal();
            _closeNewCaseModal = null;
        }
    }

    function submitNewCase() {
        var caseName = document.getElementById('new-case-name').value.trim();
        if (!caseName) {
            showToast('请输入案件名');
            return;
        }

        var caseNumber = document.getElementById('new-case-number').value.trim() || '待分配案号';
        var caseType = document.getElementById('new-case-type').value.trim() || '暂无';
        var status = document.getElementById('new-case-status').value;
        var claim = document.getElementById('new-case-claim').value.trim() || '-';
        var clientName = document.getElementById('new-client-name').value.trim() || '待补充';
        var opponentName = document.getElementById('new-opponent-name').value.trim() || '待补充';

        var statusClass = '';
        if (status === '进行中') {
            statusClass = 'bg-[#E8F3FF] text-[#165DFF]';
        } else if (status === '待开庭') {
            statusClass = 'bg-amber-100 text-amber-700';
        } else if (status === '已结案') {
            statusClass = 'bg-green-100 text-green-700';
        } else if (status === '已归档') {
            statusClass = 'bg-gray-100 text-gray-600';
        } else {
            statusClass = 'bg-[#E8F3FF] text-[#165DFF]';
        }

        var tbody = document.getElementById('caseTableBody');
        if (tbody) {
            var index = tbody.querySelectorAll('tr').length;
            var tr = document.createElement('tr');
            tr.className = 'hover:bg-[#F7F8FA] transition-colors';
            tr.setAttribute('data-status', status);
            tr.setAttribute('data-type', caseType);
            tr.innerHTML = `
                    <td class="py-3 px-4 text-xs font-medium text-[#1D2129] truncate" title="${caseName}">${caseName}</td>
                    <td class="py-3 px-4 text-xs text-[#4E5969] truncate" title="${caseNumber}">${caseNumber}</td>
                    <td class="py-3 px-4 text-xs text-[#4E5969] truncate" title="${caseType}">${caseType}</td>
                    <td class="py-3 px-4 text-xs text-[#4E5969] truncate" title="${clientName}">${clientName}</td>
                    <td class="py-3 px-4 text-xs text-[#4E5969] truncate" title="${opponentName}">${opponentName}</td>
                    <td class="text-center py-3 px-4 whitespace-nowrap"><span class="text-[10px] ${statusClass} font-medium px-2 py-0.5 rounded inline-block">${status}</span></td>
                    <td class="text-center py-3 px-4 text-xs text-[#4E5969] truncate" title="待安排">待安排</td>
                    <td class="text-center py-3 px-4 whitespace-nowrap">
                        <div class="flex items-center justify-center gap-2">
                            <button class="text-xs text-[#165DFF] hover:underline flex-shrink-0" onclick="openCaseDetail(${index})">详情</button>
                            <span class="text-[#E5E6EB] flex-shrink-0">|</span>
                            <button class="text-xs text-[#165DFF] hover:underline flex-shrink-0" onclick="archiveCase()">归档</button>
                            <span class="text-[#E5E6EB] flex-shrink-0">|</span>
                            <button class="text-xs text-red-500 hover:underline flex-shrink-0" onclick="deleteCase(${index})">删除</button>
                        </div>
                    </td>
                `;
            tbody.appendChild(tr);
            filterCaseList();
        }

        closeNewCaseModal();
        showToast('案件创建成功');
    }

    function openArchiveDetail(id) {
        // 归档案件 ID 即 caseMeta 数组的 index (0-4)
        if (typeof openCaseDetail === 'function') {
            openCaseDetail(id);
        } else {
            switchView('case');
        }
    }

    async function restoreArchive() {
        var id = typeof globalThis.currentArchiveId !== 'undefined' ? globalThis.currentArchiveId : null;
        if (id === null || id === undefined) {
            showToast('请先选择要恢复的归档', 'warning');
            return;
        }
        var confirmed = await Utils.showConfirm('确定要恢复此归档案件？恢复后会重新出现在案件列表中。');
        if (!confirmed) return;
        var archived = JSON.parse(localStorage.getItem('lexprime_archived') || '[]');
        archived = archived.filter(function (x) {
            return x !== id;
        });
        localStorage.setItem('lexprime_archived', JSON.stringify(archived));
        showToast('归档已恢复', 'success');
        if (typeof renderArchiveTable === 'function') renderArchiveTable();
        else filterArchiveList();
    }

    async function deleteArchive() {
        var id = typeof globalThis.currentArchiveId !== 'undefined' ? globalThis.currentArchiveId : null;
        if (id === null || id === undefined) {
            showToast('请先选择要删除的归档', 'warning');
            return;
        }
        var confirmed = await Utils.showConfirm('确定要永久删除此归档？此操作不可恢复。');
        if (!confirmed) return;
        var archived = JSON.parse(localStorage.getItem('lexprime_archived') || '[]');
        archived = archived.filter(function (x) {
            return x !== id;
        });
        localStorage.setItem('lexprime_archived', JSON.stringify(archived));
        showToast('归档已删除', 'success');
        if (typeof renderArchiveTable === 'function') renderArchiveTable();
        else filterArchiveList();
    }

    function filterArchiveList() {
        if (typeof renderArchiveTable === 'function') {
            renderArchiveTable();
        } else {
            var tbody = document.getElementById('archiveTableBody');
            if (!tbody) return;
            var search = (document.getElementById('archiveSearchInput')?.value || '').toLowerCase();
            var year = document.getElementById('archiveYearFilter')?.value || '';
            var type = document.getElementById('archiveTypeFilter')?.value || '';
            tbody.querySelectorAll('tr').forEach(function (tr) {
                var haystack = tr.textContent.toLowerCase();
                var show =
                    (!search || haystack.indexOf(search) > -1) &&
                    (!year || haystack.indexOf(year) > -1) &&
                    (!type || tr.getAttribute('data-archive-type') === type);
                tr.style.display = show ? '' : 'none';
            });
        }
    }

    function toggleAllArchive(masterCb) {
        var tbody = document.getElementById('archiveTableBody');
        if (!tbody) return;
        tbody.querySelectorAll('input[type="checkbox"]').forEach(function (cb) {
            cb.checked = masterCb.checked;
        });
    }

    // ===== 双绑定 =====
    globalThis.filterCaseList = filterCaseList;
    globalThis.goToCasePage = goToCasePage;
    globalThis.archiveCase = archiveCase;
    globalThis.editCaseTitle = editCaseTitle;
    globalThis.deleteCase = deleteCase;
    globalThis.openNewCaseModal = openNewCaseModal;
    globalThis.closeNewCaseModal = closeNewCaseModal;
    globalThis.submitNewCase = submitNewCase;
    globalThis.openArchiveDetail = openArchiveDetail;
    globalThis.restoreArchive = restoreArchive;
    globalThis.deleteArchive = deleteArchive;
    globalThis.filterArchiveList = filterArchiveList;
    globalThis.toggleAllArchive = toggleAllArchive;
})();
