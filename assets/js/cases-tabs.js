/**
 * 案件 - 9 个 tab 内容 + AI 面板 + 案件分析模块
 * 拆分自 cases.js (2026-06-28 IIFE 拆分计划)
 *
 * 包含: 证据目录 CRUD + 时间线 CRUD + 证件 CRUD + 委托合同 CRUD + 证据材料 CRUD +
 *       文书 CRUD (授权委托书/判决书/其他) + AI 智能目录 + AI 面板切换 + 案件分析入口
 * 依赖: showToast (script.js), loadView (router.js),
 *       catalogSelectedFiles/editingCatalogRow/currentDocumentType/documentTypeMap
 *       (与 script.js 共享, 显式挂 globalThis 跨模块同步)
 *
 * 加载顺序: 在 cases-list.js / cases-detail.js 之后
 */

(function() {
    'use strict';

    // ===== 跨模块共享状态 (与 script.js 互通, 显式挂 globalThis) =====
    // 注: 之前 cases.js 无 IIFE 包裹, 引用未声明变量会创建 globalThis
    // 现在 cases-tabs.js 用 IIFE, 必须显式挂 globalThis 与 script.js 同步
    if (!globalThis.catalogSelectedFiles) globalThis.catalogSelectedFiles = [];
    if (!globalThis.editingCatalogRow) globalThis.editingCatalogRow = null;
    if (!globalThis.currentDocumentType) globalThis.currentDocumentType = '';
    if (!globalThis.documentTypeMap) globalThis.documentTypeMap = {
        'power-attorney': { title: '上传授权委托书', listId: 'power-attorney-list', toast: '授权委托书已上传', deleteToast: '授权委托书已删除', subText: '' },
        'judgment': { title: '上传判决书/调解书', listId: 'judgment-list', toast: '文书已上传', deleteToast: '文书已删除', subText: '判决文书' },
        'other': { title: '上传其他文书', listId: 'other-doc-list', toast: '文书已上传', deleteToast: '文书已删除', subText: '其他' }
    };
    if (typeof globalThis.currentCaseIndex === 'undefined') globalThis.currentCaseIndex = -1;

    // local alias 指向同一引用 (避免函数内 `X = []` 重新赋值丢失 globalThis 引用)
    var catalogSelectedFiles = globalThis.catalogSelectedFiles;
    var editingCatalogRow = globalThis.editingCatalogRow;
    var currentDocumentType = globalThis.currentDocumentType;
    var documentTypeMap = globalThis.documentTypeMap;

    // ===== 证据目录 =====
    function addEvidenceCatalogItem() {
        var modal = document.getElementById('add-evidence-catalog-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.getElementById('catalog-number').value = '';
            document.getElementById('catalog-name').value = '';
            document.getElementById('catalog-pages').value = '';
            document.getElementById('catalog-description').value = '';
            var radios = document.getElementsByName('catalog-type');
            if (radios.length > 0) radios[0].checked = true;
            var tbody = document.getElementById('evidence-catalog-list');
            if (tbody) {
                var rows = tbody.querySelectorAll('tr');
                document.getElementById('catalog-number').value = rows.length + 1;
            }
            loadCatalogFileList();
            catalogSelectedFiles.length = 0;  // 清空数组内容 (保留引用)
            updateCatalogSelectedCount();
        }
    }

    function loadCatalogFileList() {
        var listContainer = document.getElementById('catalog-file-select-list');
        if (!listContainer) return;

        var materialsList = document.getElementById('materials-list');
        if (!materialsList) {
            listContainer.innerHTML = '<div class="px-3 py-4 text-center text-[11px] text-gray-400">暂无上传的证据材料</div>';
            return;
        }

        var rows = materialsList.querySelectorAll('tr');
        if (rows.length === 0) {
            listContainer.innerHTML = '<div class="px-3 py-4 text-center text-[11px] text-gray-400">暂无上传的证据材料</div>';
            return;
        }

        var html = '';
        rows.forEach(function(row, index) {
            var cells = row.querySelectorAll('td');
            var fileName = cells[0]?.textContent?.trim() || '';
            var fileType = cells[1]?.textContent?.trim() || '';
            var fileId = 'catalog-file-' + index;

            html +=
                '<label class="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer border-b border-gray-50 last:border-b-0">' +
                '<input class="accent-[#165DFF] catalog-file-checkbox" type="checkbox" id="' + fileId + '" data-name="' + fileName + '" data-type="' + fileType + '" onchange="toggleCatalogFileSelect(this)">' +
                '<iconify-icon class="text-gray-400 text-base flex-shrink-0" icon="mdi:file-document-outline"></iconify-icon>' +
                '<div class="flex-1 min-w-0">' +
                '<p class="text-[11px] text-gray-700 truncate">' + fileName + '</p>' +
                '<p class="text-[10px] text-gray-400">' + fileType + '</p>' +
                '</div>' +
                '</label>';
        });

        listContainer.innerHTML = html;
    }

    function toggleCatalogFileSelect(checkbox) {
        var fileName = checkbox.getAttribute('data-name');
        var fileType = checkbox.getAttribute('data-type');

        if (checkbox.checked) {
            catalogSelectedFiles.push({ name: fileName, type: fileType });
        } else {
            var idx = catalogSelectedFiles.findIndex(function(f) { return f.name === fileName; });
            if (idx >= 0) catalogSelectedFiles.splice(idx, 1);
        }

        updateCatalogSelectedCount();
    }

    function updateCatalogSelectedCount() {
        var countEl = document.getElementById('catalog-selected-count');
        var selectedEl = document.getElementById('catalog-selected-files');
        if (countEl) countEl.textContent = '已选 ' + catalogSelectedFiles.length + ' 个';
        if (selectedEl) {
            if (catalogSelectedFiles.length > 0) {
                selectedEl.textContent = '已选择：' + catalogSelectedFiles.map(function(f) { return f.name; }).join('、');
            } else {
                selectedEl.textContent = '';
            }
        }
    }

    function closeAddEvidenceCatalogModal() {
        var modal = document.getElementById('add-evidence-catalog-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    function submitEvidenceCatalog() {
        var number = document.getElementById('catalog-number').value.trim();
        var name = document.getElementById('catalog-name').value.trim();
        var pages = document.getElementById('catalog-pages').value.trim();
        var description = document.getElementById('catalog-description').value.trim();

        var typeRadios = document.getElementsByName('catalog-type');
        var type = '书证';
        for (var i = 0; i < typeRadios.length; i++) {
            if (typeRadios[i].checked) {
                type = typeRadios[i].value;
                break;
            }
        }

        if (!name) {
            showToast('请输入证据材料名称');
            return;
        }

        var tbody = document.getElementById('evidence-catalog-list');
        if (!tbody) return;

        var typeClass = '';
        if (type === '书证') {
            typeClass = 'bg-blue-100 text-blue-700';
        } else if (type === '电子数据') {
            typeClass = 'bg-purple-100 text-purple-700';
        } else if (type === '视听资料') {
            typeClass = 'bg-orange-100 text-orange-700';
        } else {
            typeClass = 'bg-gray-100 text-gray-700';
        }

        var newRow = document.createElement('tr');
        newRow.className = 'hover:bg-gray-50 group';
        if (catalogSelectedFiles.length > 0) {
            newRow.setAttribute('data-linked-files', JSON.stringify(catalogSelectedFiles));
        }

        var linkedFilesHtml = '';
        if (catalogSelectedFiles.length > 0) {
            linkedFilesHtml = '<p class="text-[10px] text-gray-400 mt-0.5">关联：' + catalogSelectedFiles.map(function(f) { return f.name; }).join('、') + '</p>';
        }

        newRow.innerHTML =
            '<td class="text-center py-3 px-4 text-xs text-gray-700">' + (number || '') + '</td>' +
            '<td class="text-center py-3 px-4"><span class="text-[10px] ' + typeClass + ' px-2 py-0.5 rounded">' + type + '</span></td>' +
            '<td class="py-3 px-4 text-xs text-gray-800">' + name + linkedFilesHtml + '</td>' +
            '<td class="py-3 px-4 text-[11px] text-gray-500 max-w-[300px] truncate" title="' + description + '">' + (description || '-') + '</td>' +
            '<td class="text-center py-3 px-4 text-xs text-gray-500">' + (pages || '-') + '</td>' +
            '<td class="text-center py-3 px-4">' +
            '<div class="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">' +
            '<button class="text-[10px] text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded" onclick="editCatalogItem(this)">编辑</button>' +
            '<button class="text-[10px] text-red-500 hover:bg-red-50 px-2 py-1 rounded" onclick="deleteCatalogItem(this)">删除</button>' +
            '</div>' +
            '</td>';

        tbody.appendChild(newRow);
        closeAddEvidenceCatalogModal();
        showToast('证据目录已添加');
    }

    function editCatalogItem(btn) {
        var card = btn.closest('[data-catalog-item]');
        if (!card) return;

        editingCatalogRow = card;

        var number = card.dataset.number || '';
        var type = card.dataset.type || '书证';
        var name = card.dataset.name || '';
        var description = card.dataset.description || '';
        var pages = card.dataset.pages || '';

        var linkedFiles = card.getAttribute('data-linked-files');
        if (linkedFiles) {
            try {
                catalogSelectedFiles.length = 0;
                var parsed = JSON.parse(linkedFiles);
                parsed.forEach(function(f) { catalogSelectedFiles.push(f); });
            } catch(e) {
                catalogSelectedFiles.length = 0;
            }
        } else {
            catalogSelectedFiles.length = 0;
        }

        var modal = document.getElementById('add-evidence-catalog-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.getElementById('catalog-number').value = number;
            document.getElementById('catalog-name').value = name;
            document.getElementById('catalog-pages').value = pages === '-' ? '' : pages;
            document.getElementById('catalog-description').value = description === '-' ? '' : description;

            var typeRadios = document.getElementsByName('catalog-type');
            for (var i = 0; i < typeRadios.length; i++) {
                typeRadios[i].checked = (typeRadios[i].value === type);
            }

            var modalTitle = modal.querySelector('h3');
            if (modalTitle) modalTitle.textContent = '编辑证据目录';
            var submitBtn = modal.querySelector('[onclick="submitEvidenceCatalog()"]');
            if (submitBtn) submitBtn.textContent = '保存';

            loadCatalogFileList();
            setTimeout(function() {
                var checkboxes = document.querySelectorAll('.catalog-file-checkbox');
                checkboxes.forEach(function(cb) {
                    var fileName = cb.getAttribute('data-name');
                    var isSelected = catalogSelectedFiles.some(function(f) { return f.name === fileName; });
                    cb.checked = isSelected;
                });
                updateCatalogSelectedCount();
            }, 50);
        }
    }

    function deleteCatalogItem(btn) {
        if (!confirm('确定要删除该证据目录项吗？')) return;
        var row = btn.closest('tr');
        if (row) {
            row.remove();
            showToast('证据目录已删除');
            var tbody = document.getElementById('evidence-catalog-list');
            if (tbody) {
                var rows = tbody.querySelectorAll('tr');
                rows.forEach(function(r, index) {
                    var numCell = r.querySelector('td:first-child');
                    if (numCell) numCell.textContent = index + 1;
                });
            }
        }
    }

    function aiCreateEvidenceCatalog() {
        showToast('AI正在分析证据材料，生成证据目录...');

        setTimeout(function() {
            var tbody = document.getElementById('evidence-catalog-list');
            if (!tbody) return;

            var aiItems = [
                { number: 14, type: '书证', typeClass: 'bg-blue-100 text-blue-700', name: 'AI分析报告', description: 'AI自动分析生成的证据关联性分析报告', pages: '见附件' },
                { number: 15, type: '电子数据', typeClass: 'bg-purple-100 text-purple-700', name: '银行流水记录', description: '银行账户资金往来明细，证明资金流向', pages: '56-60' },
                { number: 16, type: '视听资料', typeClass: 'bg-orange-100 text-orange-700', name: '现场勘查视频', description: '第三方机构现场勘查记录视频', pages: '见光盘' }
            ];

            aiItems.forEach(function(item) {
                var newRow = document.createElement('tr');
                newRow.className = 'hover:bg-gray-50 group';
                newRow.innerHTML =
                    '<td class="text-center py-3 px-4 text-xs text-gray-700">' + item.number + '</td>' +
                    '<td class="text-center py-3 px-4"><span class="text-[10px] ' + item.typeClass + ' px-2 py-0.5 rounded">' + item.type + '</span></td>' +
                    '<td class="py-3 px-4 text-xs text-gray-800">' + item.name + '</td>' +
                    '<td class="py-3 px-4 text-[11px] text-gray-500 max-w-[300px] truncate" title="' + item.description + '">' + item.description + '</td>' +
                    '<td class="text-center py-3 px-4 text-xs text-gray-500">' + item.pages + '</td>' +
                    '<td class="text-center py-3 px-4">' +
                    '<div class="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">' +
                    '<button class="text-[10px] text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded" onclick="editCatalogItem(this)">编辑</button>' +
                    '<button class="text-[10px] text-red-500 hover:bg-red-50 px-2 py-1 rounded" onclick="deleteCatalogItem(this)">删除</button>' +
                    '</div>' +
                    '</td>';
                tbody.appendChild(newRow);
            });

            showToast('AI已成功生成证据目录（共3项）');
        }, 1500);
    }

    // ===== 时间线 =====
    function openAddTimelineModal() {
        var modal = document.getElementById('add-timeline-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.getElementById('timeline-title').value = '';
            document.getElementById('timeline-date').value = '';
            document.getElementById('timeline-color').value = '#165DFF';
            document.getElementById('timeline-desc').value = '';
            document.getElementById('timeline-tag').value = '';
        }
    }

    function closeAddTimelineModal() {
        var modal = document.getElementById('add-timeline-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    function submitTimeline() {
        var title = document.getElementById('timeline-title').value.trim();
        var date = document.getElementById('timeline-date').value;
        var color = document.getElementById('timeline-color').value;
        var desc = document.getElementById('timeline-desc').value.trim();
        var tag = document.getElementById('timeline-tag').value.trim();

        if (!title) {
            showToast('请输入事件标题');
            return;
        }
        if (!date) {
            showToast('请选择事件日期');
            return;
        }

        var container = document.getElementById('timeline-container');
        if (!container) {
            showToast('时间线容器未找到');
            return;
        }

        var tagHtml = '';
        if (tag) {
            tagHtml = '<span class="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full mt-1 inline-block">' + tag + '</span>';
        }

        var iconClass = 'mdi:calendar';
        if (color === '#165DFF') iconClass = 'mdi:file-document';
        else if (color === 'orange-500') iconClass = 'mdi:file-document-outline';
        else if (color === 'green-500') iconClass = 'mdi:gavel';
        else if (color === 'purple-500') iconClass = 'mdi:calendar';
        else if (color === 'red-500') iconClass = 'mdi:alert-circle';
        else iconClass = 'mdi:clock';

        var newItem = document.createElement('div');
        newItem.className = 'relative';
        newItem.innerHTML = '<div class="absolute -left-10 top-0 w-7 h-7 rounded-full bg-' + color.split('-')[0] + (color.includes('-') ? '-' + color.split('-')[1] : '') + ' flex items-center justify-center text-white shadow">' +
            '<iconify-icon class="text-xs" icon="' + iconClass + '"></iconify-icon>' +
            '</div>' +
            '<div class="bg-white rounded-xl border border-[#E5E6EB] p-4 ml-4 group">' +
            '<div class="flex items-center justify-between mb-1">' +
            '<span class="text-sm font-medium">' + title + '</span>' +
            '<div class="flex items-center gap-2">' +
            '<span class="text-[10px] text-gray-400">' + date + '</span>' +
            '<button class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity" onclick="deleteTimeline(this)">' +
            '<iconify-icon class="text-sm" icon="mdi:delete-outline"></iconify-icon>' +
            '</button>' +
            '</div>' +
            '</div>' +
            (desc ? '<p class="text-xs text-gray-500">' + desc + '</p>' : '') +
            (tagHtml ? tagHtml : '') +
            '</div>' +
            '</div>';

        container.appendChild(newItem);
        closeAddTimelineModal();
        showToast('时间线已添加');
    }

    function deleteTimeline(btn) {
        if (!confirm('确定要删除这条时间线吗？')) return;
        var item = btn.closest('.relative');
        if (item) {
            item.remove();
            showToast('时间线已删除');
        }
    }

    // ===== 证件 =====
    function openUploadEvidenceModal() {
        var modal = document.getElementById('upload-evidence-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.getElementById('evidence-name').value = '';
            document.getElementById('evidence-type').value = '企业证件';
        }
    }

    function closeUploadEvidenceModal() {
        var modal = document.getElementById('upload-evidence-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    function submitEvidence() {
        var name = document.getElementById('evidence-name').value.trim();
        var type = document.getElementById('evidence-type').value;

        if (!name) {
            showToast('请输入证件名称');
            return;
        }

        var list = document.getElementById('evidence-list');
        if (!list) {
            showToast('证件列表未找到');
            return;
        }

        var today = new Date();
        var dateStr = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');

        var newItem = document.createElement('div');
        newItem.className = 'flex items-center justify-between p-3 bg-gray-50 rounded-lg';
        newItem.innerHTML = '<div class="flex items-center gap-3">' +
            '<iconify-icon class="text-xl text-[#165DFF]" icon="mdi:card-account-details"></iconify-icon>' +
            '<div>' +
            '<p class="text-sm font-medium">' + name + '</p>' +
            '<p class="text-xs text-gray-400">' + type + ' · ' + dateStr + '</p>' +
            '</div>' +
            '</div>' +
            '<div class="flex gap-2">' +
            '<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-3 py-1.5 rounded border border-[#E5E6EB]">预览</button>' +
            '<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-3 py-1.5 rounded border border-[#E5E6EB]">下载</button>' +
            '<button class="text-xs text-gray-500 hover:bg-red-50 hover:text-red-500 px-3 py-1.5 rounded border border-[#E5E6EB]" onclick="deleteEvidence(this)">删除</button>' +
            '</div>';

        list.appendChild(newItem);
        closeUploadEvidenceModal();
        showToast('证件已上传');
    }

    function deleteEvidence(btn) {
        if (!confirm('确定要删除该证件吗？')) return;
        var item = btn.closest('.flex.items-center.justify-between');
        if (item) {
            item.remove();
            showToast('证件已删除');
        }
    }

    // ===== 委托合同 =====
    function openUploadContractModal() {
        var modal = document.getElementById('upload-contract-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.getElementById('contract-name').value = '';
        }
    }

    function closeUploadContractModal() {
        var modal = document.getElementById('upload-contract-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    function submitContract() {
        var name = document.getElementById('contract-name').value.trim();

        if (!name) {
            showToast('请输入合同名称');
            return;
        }

        var list = document.getElementById('contract-list');
        if (!list) {
            showToast('合同列表未找到');
            return;
        }

        var today = new Date();
        var dateStr = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');

        var newItem = document.createElement('div');
        newItem.className = 'flex items-center justify-between p-3 bg-gray-50 rounded-lg';
        newItem.innerHTML = '<div class="flex items-center gap-3">' +
            '<iconify-icon class="text-xl text-[#165DFF]" icon="mdi:file-pdf-box"></iconify-icon>' +
            '<div>' +
            '<p class="text-sm font-medium">' + name + '</p>' +
            '<p class="text-xs text-gray-400">' + dateStr + ' 上传</p>' +
            '</div>' +
            '</div>' +
            '<div class="flex gap-2">' +
            '<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-3 py-1.5 rounded border border-[#E5E6EB]">预览</button>' +
            '<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-3 py-1.5 rounded border border-[#E5E6EB]">下载</button>' +
            '<button class="text-xs text-gray-500 hover:bg-red-50 hover:text-red-500 px-3 py-1.5 rounded border border-[#E5E6EB]" onclick="deleteContract(this)">删除</button>' +
            '</div>';

        list.appendChild(newItem);
        closeUploadContractModal();
        showToast('委托合同已上传');
    }

    function deleteContract(btn) {
        var confirmed = confirm('确定要删除该委托合同吗？');
        if (confirmed) {
            var item = btn.closest('.flex.items-center.justify-between');
            if (item) {
                item.remove();
                showToast('委托合同已删除');
            }
        }
    }

    // ===== 证据材料 =====
    function openUploadMaterialModal() {
        var modal = document.getElementById('upload-material-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.getElementById('material-name').value = '';
            document.getElementById('material-type').value = '合同';
        }
    }

    function closeUploadMaterialModal() {
        var modal = document.getElementById('upload-material-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    function submitMaterial() {
        var name = document.getElementById('material-name').value.trim();
        var type = document.getElementById('material-type').value;

        if (!name) {
            showToast('请输入文件名称');
            return;
        }

        var list = document.getElementById('materials-list');
        if (!list) {
            showToast('材料列表未找到');
            return;
        }

        var now = new Date();
        var dateStr = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0') + '-' + String(now.getDate()).padStart(2, '0') + ' ' + String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');

        var newRow = document.createElement('tr');
        newRow.className = 'hover:bg-gray-50';
        newRow.innerHTML = '<td class="py-2.5 px-4 text-sm text-[#165DFF] cursor-pointer">' + name + '</td>' +
            '<td class="py-2.5 px-4 text-xs text-gray-500">' + type + '</td>' +
            '<td class="py-2.5 px-4 text-xs text-gray-500">' + dateStr + '</td>' +
            '<td class="text-center py-2.5 px-4">' +
            '<div class="flex items-center justify-center gap-2">' +
            '<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded border border-[#E5E6EB]">预览</button>' +
            '<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded border border-[#E5E6EB]">下载</button>' +
            '<button class="text-xs text-gray-500 hover:bg-red-50 hover:text-red-500 px-2 py-1 rounded border border-[#E5E6EB]" onclick="deleteMaterial(this)">删除</button>' +
            '</div>' +
            '</td>';

        list.appendChild(newRow);
        closeUploadMaterialModal();
        showToast('证据材料已上传');
    }

    function deleteMaterial(btn) {
        var confirmed = confirm('确定要删除该证据材料吗？');
        if (confirmed) {
            var row = btn.closest('tr');
            if (row) {
                row.remove();
                showToast('证据材料已删除');
            }
        }
    }

    // ===== 文书 (授权委托书/判决书/其他) =====
    function openUploadDocumentModal(type) {
        currentDocumentType = type;
        var modal = document.getElementById('upload-document-modal');
        var config = documentTypeMap[type];
        if (modal && config) {
            document.getElementById('upload-document-title').textContent = config.title;
            document.getElementById('document-name').value = '';
            modal.classList.remove('hidden');
        }
    }

    function closeUploadDocumentModal() {
        var modal = document.getElementById('upload-document-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    function submitDocument() {
        var name = document.getElementById('document-name').value.trim();
        var config = documentTypeMap[currentDocumentType];

        if (!name) {
            showToast('请输入文件名称');
            return;
        }

        if (!config) {
            showToast('未知文书类型');
            return;
        }

        var list = document.getElementById(config.listId);
        if (!list) {
            showToast('文书列表未找到');
            return;
        }

        var today = new Date();
        var dateStr = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');

        var subInfo = config.subText ? config.subText + ' · ' + dateStr : dateStr + ' 上传';

        var newItem = document.createElement('div');
        newItem.className = 'flex items-center justify-between p-3 bg-gray-50 rounded-lg';
        newItem.innerHTML = '<div class="flex items-center gap-3">' +
            '<iconify-icon class="text-xl text-[#165DFF]" icon="mdi:file-pdf-box"></iconify-icon>' +
            '<div>' +
            '<p class="text-sm font-medium">' + name + '</p>' +
            '<p class="text-xs text-gray-400">' + subInfo + '</p>' +
            '</div>' +
            '</div>' +
            '<div class="flex gap-2">' +
            '<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-3 py-1.5 rounded border border-[#E5E6EB]">预览</button>' +
            '<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-3 py-1.5 rounded border border-[#E5E6EB]">下载</button>' +
            '<button class="text-xs text-gray-500 hover:bg-red-50 hover:text-red-500 px-3 py-1.5 rounded border border-[#E5E6EB]" onclick="deleteDocument(this, \'' + currentDocumentType + '\')">删除</button>' +
            '</div>';

        list.appendChild(newItem);
        closeUploadDocumentModal();
        showToast(config.toast);
    }

    function deleteDocument(btn, type) {
        var config = documentTypeMap[type];
        var confirmed = confirm('确定要删除该文书吗？');
        if (confirmed) {
            var item = btn.closest('.flex.items-center.justify-between');
            if (item) {
                item.remove();
                showToast(config ? config.deleteToast : '文书已删除');
            }
        }
    }

    // ===== AI 面板 =====
    function switchAIPanel(btn, panelName) {
        var container = btn.closest('.w-80') || btn.closest('[class*="w-80"]');
        if (!container) return;
        var tabs = container.querySelectorAll('.flex.border-b.border-gray-100 button');
        tabs.forEach(function(b) {
            b.className = 'flex-1 py-3 text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700';
        });
        btn.className = 'flex-1 py-3 text-sm font-medium border-b-2 border-[#165DFF] text-[#165DFF]';
        ['mapping', 'advice', 'laws'].forEach(function(name) {
            var panel = container.querySelector('#ai-panel-' + name);
            if (panel) panel.classList.add('hidden');
        });
        var activePanel = container.querySelector('#ai-panel-' + panelName);
        if (activePanel) activePanel.classList.remove('hidden');
    }

    function switchEvidenceAIPanel(btn, panelName) {
        var container = btn.closest('.w-72') || document;
        var tabs = container.querySelectorAll('[data-evidence-panel]');
        tabs.forEach(function(b) {
            b.classList.remove('border-b-2', 'border-[#165DFF]', 'text-[#165DFF]');
            b.classList.add('text-gray-500', 'hover:text-gray-700');
        });
        btn.classList.add('border-b-2', 'border-[#165DFF]', 'text-[#165DFF]');
        btn.classList.remove('text-gray-500', 'hover:text-gray-700');
        ['check', 'object', 'laws'].forEach(function(name) {
            var panel = document.getElementById('evidence-ai-' + name);
            if (panel) panel.classList.add('hidden');
        });
        var active = document.getElementById('evidence-ai-' + panelName);
        if (active) active.classList.remove('hidden');
    }

    // ===== 案件分析 + 返回 =====
    function openCaseAnalysis() {
        document.querySelectorAll('.view-content').forEach(function(v) {
            v.classList.add('hidden');
        });
        var analysisView = document.getElementById('view-case-analysis');
        if (analysisView) analysisView.classList.remove('hidden');
    }

    function backToCaseList() {
        document.querySelectorAll('.view-content').forEach(function(v) {
            v.classList.add('hidden');
        });
        var listView = document.getElementById('view-case-list');
        if (listView) listView.classList.remove('hidden');
    }

    // ===== 双绑定 =====
    globalThis.addEvidenceCatalogItem = addEvidenceCatalogItem;
    globalThis.loadCatalogFileList = loadCatalogFileList;
    globalThis.toggleCatalogFileSelect = toggleCatalogFileSelect;
    globalThis.updateCatalogSelectedCount = updateCatalogSelectedCount;
    globalThis.closeAddEvidenceCatalogModal = closeAddEvidenceCatalogModal;
    globalThis.submitEvidenceCatalog = submitEvidenceCatalog;
    globalThis.editCatalogItem = editCatalogItem;
    globalThis.deleteCatalogItem = deleteCatalogItem;
    globalThis.aiCreateEvidenceCatalog = aiCreateEvidenceCatalog;
    globalThis.openAddTimelineModal = openAddTimelineModal;
    globalThis.closeAddTimelineModal = closeAddTimelineModal;
    globalThis.submitTimeline = submitTimeline;
    globalThis.deleteTimeline = deleteTimeline;
    globalThis.openUploadEvidenceModal = openUploadEvidenceModal;
    globalThis.closeUploadEvidenceModal = closeUploadEvidenceModal;
    globalThis.submitEvidence = submitEvidence;
    globalThis.deleteEvidence = deleteEvidence;
    globalThis.openUploadContractModal = openUploadContractModal;
    globalThis.closeUploadContractModal = closeUploadContractModal;
    globalThis.submitContract = submitContract;
    globalThis.deleteContract = deleteContract;
    globalThis.openUploadMaterialModal = openUploadMaterialModal;
    globalThis.closeUploadMaterialModal = closeUploadMaterialModal;
    globalThis.submitMaterial = submitMaterial;
    globalThis.deleteMaterial = deleteMaterial;
    globalThis.openUploadDocumentModal = openUploadDocumentModal;
    globalThis.closeUploadDocumentModal = closeUploadDocumentModal;
    globalThis.submitDocument = submitDocument;
    globalThis.deleteDocument = deleteDocument;
    globalThis.switchAIPanel = switchAIPanel;
    globalThis.switchEvidenceAIPanel = switchEvidenceAIPanel;
    globalThis.openCaseAnalysis = openCaseAnalysis;
    globalThis.backToCaseList = backToCaseList;
})();