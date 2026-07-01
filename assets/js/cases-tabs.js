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
            var modalTitle = modal.querySelector('h3');
            if (modalTitle) modalTitle.textContent = '手动创建证据目录';
            var submitBtn = modal.querySelector('[onclick="saveCatalogEdit()"]');
            if (!submitBtn) submitBtn = modal.querySelector('[onclick="submitEvidenceCatalog()"]');
            if (submitBtn) {
                submitBtn.textContent = '添加';
                submitBtn.setAttribute('onclick', 'submitEvidenceCatalog()');
            }
            editingCatalogRow = null;
        }
    }

    function getTypeClass(type) {
        if (type === '书证') {
            return 'bg-brand-tint text-brand';
        } else if (type === '电子数据') {
            return 'bg-wiki-tint text-wiki';
        } else if (type === '视听资料') {
            return 'bg-warning-tint text-orange-700';
        } else {
            return 'bg-gray-100 text-gray-700';
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

        var typeClass = getTypeClass(type);

        var newRow = document.createElement('tr');
        newRow.className = 'hover:bg-gray-50 group';
        newRow.setAttribute('data-catalog-item', '');
        newRow.setAttribute('data-number', number || '');
        newRow.setAttribute('data-type', type);
        newRow.setAttribute('data-name', name);
        newRow.setAttribute('data-description', description || '');
        newRow.setAttribute('data-pages', pages || '');
        if (catalogSelectedFiles.length > 0) {
            newRow.setAttribute('data-linked-files', JSON.stringify(catalogSelectedFiles));
        }

        var linkedFilesHtml = '';
        if (catalogSelectedFiles.length > 0) {
            linkedFilesHtml = '<p class="text-[10px] text-fg-tertiary mt-0.5">关联：' + catalogSelectedFiles.map(function(f) { return f.name; }).join('、') + '</p>';
        }

        newRow.innerHTML =
            '<td class="py-3 px-5 text-center"><span class="inline-flex w-7 h-7 bg-brand-tint3 text-brand rounded items-center justify-center text-xs font-bold">' + (number || '') + '</span></td>' +
            '<td class="py-3 px-5">' +
            '<div class="flex items-center gap-2 mb-0.5">' +
            '<span class="text-[10px] ' + typeClass + ' px-1.5 py-0.5 rounded font-medium">' + type + '</span>' +
            '<span class="text-sm text-fg-primary font-medium">' + name + '</span>' +
            '</div>' +
            '<p class="text-[10px] text-fg-tertiary truncate max-w-2xl">' + (description || '') + '</p>' +
            linkedFilesHtml +
            '</td>' +
            '<td class="py-3 px-5 text-center text-xs text-fg-secondary">' + (pages || '-') + ' 页</td>' +
            '<td class="py-3 px-5 text-center">' +
            '<div class="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">' +
            '<button class="text-xs text-brand hover:bg-brand-tint3 px-2 py-1 rounded" onclick="editCatalogItem(this)">编辑</button>' +
            '<button class="text-xs text-red-500 hover:bg-red-50 px-2 py-1 rounded" onclick="deleteCatalogItem(this)">删除</button>' +
            '</div>' +
            '</td>';

        tbody.appendChild(newRow);
        renumberCatalogItems();
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
            if (submitBtn) {
                submitBtn.textContent = '保存';
                submitBtn.setAttribute('onclick', 'saveCatalogEdit()');
            }

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

    function saveCatalogEdit() {
        if (!editingCatalogRow) return;

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

        var typeClass = getTypeClass(type);

        editingCatalogRow.setAttribute('data-number', number || '');
        editingCatalogRow.setAttribute('data-type', type);
        editingCatalogRow.setAttribute('data-name', name);
        editingCatalogRow.setAttribute('data-description', description || '');
        editingCatalogRow.setAttribute('data-pages', pages || '');
        if (catalogSelectedFiles.length > 0) {
            editingCatalogRow.setAttribute('data-linked-files', JSON.stringify(catalogSelectedFiles));
        } else {
            editingCatalogRow.removeAttribute('data-linked-files');
        }

        var linkedFilesHtml = '';
        if (catalogSelectedFiles.length > 0) {
            linkedFilesHtml = '<p class="text-[10px] text-fg-tertiary mt-0.5">关联：' + catalogSelectedFiles.map(function(f) { return f.name; }).join('、') + '</p>';
        }

        var cells = editingCatalogRow.querySelectorAll('td');
        if (cells.length >= 4) {
            cells[0].innerHTML = '<span class="inline-flex w-7 h-7 bg-brand-tint3 text-brand rounded items-center justify-center text-xs font-bold">' + (number || '') + '</span>';
            cells[1].innerHTML =
                '<div class="flex items-center gap-2 mb-0.5">' +
                '<span class="text-[10px] ' + typeClass + ' px-1.5 py-0.5 rounded font-medium">' + type + '</span>' +
                '<span class="text-sm text-fg-primary font-medium">' + name + '</span>' +
                '</div>' +
                '<p class="text-[10px] text-fg-tertiary truncate max-w-2xl">' + (description || '') + '</p>' +
                linkedFilesHtml;
            cells[2].textContent = (pages || '-') + ' 页';
        }

        renumberCatalogItems();
        closeAddEvidenceCatalogModal();

        var submitBtn = document.querySelector('#add-evidence-catalog-modal [onclick="saveCatalogEdit()"]');
        if (submitBtn) {
            submitBtn.textContent = '添加';
            submitBtn.setAttribute('onclick', 'submitEvidenceCatalog()');
        }

        editingCatalogRow = null;
        showToast('证据目录已更新');
    }

    function renumberCatalogItems() {
        var tbody = document.getElementById('evidence-catalog-list');
        if (!tbody) return;
        var rows = tbody.querySelectorAll('tr[data-catalog-item]');
        rows.forEach(function(r, index) {
            var newNum = index + 1;
            r.setAttribute('data-number', newNum);
            var numCell = r.querySelector('td:first-child span');
            if (numCell) numCell.textContent = newNum;
        });
    }

    function deleteCatalogItem(btn) {
        if (!confirm('确定要删除该证据目录项吗？')) return;
        var row = btn.closest('tr');
        if (row) {
            row.remove();
            showToast('证据目录已删除');
            renumberCatalogItems();
        }
    }

    function aiCreateEvidenceCatalog() {
        showToast('AI正在分析证据材料，生成证据目录...');

        setTimeout(function() {
            var tbody = document.getElementById('evidence-catalog-list');
            if (!tbody) return;

            var aiItems = [
                { type: '书证', name: 'AI分析报告', description: 'AI自动分析生成的证据关联性分析报告', pages: '见附件' },
                { type: '电子数据', name: '银行流水记录', description: '银行账户资金往来明细，证明资金流向', pages: '56-60' },
                { type: '视听资料', name: '现场勘查视频', description: '第三方机构现场勘查记录视频', pages: '见光盘' }
            ];

            aiItems.forEach(function(item) {
                var typeClass = getTypeClass(item.type);
                var newRow = document.createElement('tr');
                newRow.className = 'hover:bg-gray-50 group';
                newRow.setAttribute('data-catalog-item', '');
                newRow.setAttribute('data-type', item.type);
                newRow.setAttribute('data-name', item.name);
                newRow.setAttribute('data-description', item.description);
                newRow.setAttribute('data-pages', item.pages);

                var currentCount = tbody.querySelectorAll('tr[data-catalog-item]').length + 1;
                newRow.setAttribute('data-number', currentCount);

                newRow.innerHTML =
                    '<td class="py-3 px-5 text-center"><span class="inline-flex w-7 h-7 bg-brand-tint3 text-brand rounded items-center justify-center text-xs font-bold">' + currentCount + '</span></td>' +
                    '<td class="py-3 px-5">' +
                    '<div class="flex items-center gap-2 mb-0.5">' +
                    '<span class="text-[10px] ' + typeClass + ' px-1.5 py-0.5 rounded font-medium">' + item.type + '</span>' +
                    '<span class="text-sm text-fg-primary font-medium">' + item.name + '</span>' +
                    '</div>' +
                    '<p class="text-[10px] text-fg-tertiary truncate max-w-2xl">' + item.description + '</p>' +
                    '</td>' +
                    '<td class="py-3 px-5 text-center text-xs text-fg-secondary">' + item.pages + ' 页</td>' +
                    '<td class="py-3 px-5 text-center">' +
                    '<div class="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">' +
                    '<button class="text-xs text-brand hover:bg-brand-tint3 px-2 py-1 rounded" onclick="editCatalogItem(this)">编辑</button>' +
                    '<button class="text-xs text-red-500 hover:bg-red-50 px-2 py-1 rounded" onclick="deleteCatalogItem(this)">删除</button>' +
                    '</div>' +
                    '</td>';
                tbody.appendChild(newRow);
            });

            renumberCatalogItems();
            showToast('AI已成功生成证据目录（共3项）');
        }, 1500);
    }

    // ===== 时间线 =====
    var editingTimelineItem = null;

    function getTimelineStatusColor(status) {
        var colorMap = {
            'completed': { node: 'green-500', bar: 'green-500', tagBg: 'bg-green-50', tagText: 'text-green-700', icon: 'mdi:check' },
            'current': { node: 'brand', bar: 'brand', tagBg: 'bg-brand', tagText: 'text-white', icon: 'mdi:pencil-ruler' },
            'upcoming': { node: 'purple-500', bar: 'purple-500', tagBg: 'bg-purple-50', tagText: 'text-purple-700', icon: 'mdi:calendar-clock' }
        };
        return colorMap[status] || colorMap['completed'];
    }

    function openAddTimelineModal() {
        var modal = document.getElementById('add-timeline-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.getElementById('timeline-title').value = '';
            document.getElementById('timeline-date').value = '';
            document.getElementById('timeline-color').value = 'completed';
            document.getElementById('timeline-desc').value = '';
            document.getElementById('timeline-tag').value = '';
            document.getElementById('timeline-status') && (document.getElementById('timeline-status').value = 'completed');
            editingTimelineItem = null;

            var modalTitle = modal.querySelector('h3');
            if (modalTitle) modalTitle.textContent = '添加时间线';
            var submitBtn = modal.querySelector('[onclick="submitTimeline()"]');
            if (submitBtn) submitBtn.textContent = '添加';
        }
    }

    function closeAddTimelineModal() {
        var modal = document.getElementById('add-timeline-modal');
        if (modal) {
            modal.classList.add('hidden');
            editingTimelineItem = null;
        }
    }

    function editTimeline(btn) {
        var item = btn.closest('.timeline-item');
        if (!item) return;

        editingTimelineItem = item;

        var title = item.querySelector('.timeline-title')?.textContent?.trim() || '';
        var date = item.getAttribute('data-date') || '';
        var status = item.getAttribute('data-status') || 'completed';
        var desc = item.querySelector('.timeline-desc')?.textContent?.trim() || '';
        var tag = item.querySelector('.timeline-tag')?.textContent?.trim() || '';

        var modal = document.getElementById('add-timeline-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.getElementById('timeline-title').value = title;
            document.getElementById('timeline-date').value = date;
            document.getElementById('timeline-color').value = status;
            document.getElementById('timeline-desc').value = desc;
            document.getElementById('timeline-tag').value = tag;

            var modalTitle = modal.querySelector('h3');
            if (modalTitle) modalTitle.textContent = '编辑时间线';
            var submitBtn = modal.querySelector('[onclick="submitTimeline()"]');
            if (submitBtn) submitBtn.textContent = '保存';
        }
    }

    function submitTimeline() {
        var title = document.getElementById('timeline-title').value.trim();
        var date = document.getElementById('timeline-date').value;
        var status = document.getElementById('timeline-color').value;
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

        if (editingTimelineItem) {
            updateTimelineItem(editingTimelineItem, title, date, status, desc, tag);
            showToast('时间线已更新');
        } else {
            var container = document.getElementById('timeline-container');
            if (!container) {
                showToast('时间线容器未找到');
                return;
            }
            var newItem = createTimelineElement(title, date, status, desc, tag);
            container.appendChild(newItem);
            showToast('时间线已添加');
        }

        closeAddTimelineModal();
        sortTimeline();
    }

    function createTimelineElement(title, date, status, desc, tag) {
        var colors = getTimelineStatusColor(status);
        var item = document.createElement('div');
        item.className = 'grid grid-cols-[48px_1fr] gap-x-3 timeline-item';
        item.setAttribute('data-status', status);
        item.setAttribute('data-date', date);

        var isCurrent = status === 'current';
        var nodeClass = isCurrent
            ? 'w-10 h-10 rounded-full bg-brand flex items-center justify-center text-white shadow-lg ring-4 ring-brand-tint animate-pulse z-10'
            : 'w-9 h-9 rounded-full bg-white border-2 border-' + colors.node + ' flex items-center justify-center shadow-sm z-10';
        var iconColor = isCurrent ? 'text-white' : 'text-' + colors.node;
        var borderClass = isCurrent ? 'border-2 border-brand shadow-lg' : 'border border-bg-border hover:border-brand/40 hover:shadow-md';

        var tagHtml = '';
        if (tag) {
            tagHtml = '<span class="timeline-tag text-[10px] ' + colors.tagBg + ' ' + colors.tagText + ' px-1.5 py-0.5 rounded-full font-medium">' + tag + '</span>';
        }

        item.innerHTML =
            '<div class="relative flex flex-col items-center">' +
            '<div class="' + nodeClass + '">' +
            '<iconify-icon class="' + (isCurrent ? 'text-lg' : 'text-base') + ' ' + iconColor + '" icon="' + colors.icon + '"></iconify-icon>' +
            '</div>' +
            '</div>' +
            '<div class="relative bg-white rounded-xl ' + borderClass + ' transition-all group overflow-hidden mb-3">' +
            '<div class="absolute left-0 top-0 bottom-0 w-1 bg-' + colors.bar + '"></div>' +
            '<div class="p-4 pl-5">' +
            '<div class="flex items-start justify-between mb-1.5">' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-center gap-2 mb-1 flex-wrap">' +
            '<span class="timeline-title text-sm font-semibold text-fg-primary">' + title + '</span>' +
            tagHtml +
            '</div>' +
            '<p class="timeline-desc text-xs text-fg-tertiary leading-relaxed">' + (desc || '') + '</p>' +
            '</div>' +
            '<div class="flex items-center gap-1.5 flex-none ml-3">' +
            '<span class="text-[11px] text-fg-tertiary">' + date + '</span>' +
            '<button class="opacity-0 group-hover:opacity-100 text-fg-tertiary hover:text-brand transition-opacity p-1" onclick="editTimeline(this)" title="编辑">' +
            '<iconify-icon class="text-base" icon="mdi:pencil-outline"></iconify-icon>' +
            '</button>' +
            '<button class="opacity-0 group-hover:opacity-100 text-fg-tertiary hover:text-red-500 transition-opacity p-1" onclick="deleteTimeline(this)" title="删除">' +
            '<iconify-icon class="text-base" icon="mdi:delete-outline"></iconify-icon>' +
            '</button>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>';

        return item;
    }

    function updateTimelineItem(item, title, date, status, desc, tag) {
        var colors = getTimelineStatusColor(status);
        var isCurrent = status === 'current';

        item.setAttribute('data-status', status);
        item.setAttribute('data-date', date);

        var titleEl = item.querySelector('.timeline-title');
        if (titleEl) titleEl.textContent = title;

        var descEl = item.querySelector('.timeline-desc');
        if (descEl) descEl.textContent = desc || '';

        var dateEl = item.querySelector('.flex.items-center.gap-1\.5 span');
        if (dateEl) dateEl.textContent = date;

        var tagContainer = item.querySelector('.flex.items-center.gap-2.mb-1');
        if (tagContainer) {
            var existingTag = tagContainer.querySelector('.timeline-tag');
            if (tag) {
                if (existingTag) {
                    existingTag.textContent = tag;
                    existingTag.className = 'timeline-tag text-[10px] ' + colors.tagBg + ' ' + colors.tagText + ' px-1.5 py-0.5 rounded-full font-medium';
                } else {
                    var newTag = document.createElement('span');
                    newTag.className = 'timeline-tag text-[10px] ' + colors.tagBg + ' ' + colors.tagText + ' px-1.5 py-0.5 rounded-full font-medium';
                    newTag.textContent = tag;
                    titleEl && titleEl.parentNode.insertBefore(newTag, titleEl.nextSibling);
                }
            } else if (existingTag) {
                existingTag.remove();
            }
        }

        var card = item.querySelector('.relative.bg-white.rounded-xl');
        if (card) {
            var bar = card.querySelector('.absolute.left-0');
            if (bar) {
                bar.className = 'absolute left-0 top-0 bottom-0 w-1 bg-' + colors.bar;
            }
            if (isCurrent) {
                card.className = 'relative bg-white rounded-xl border-2 border-brand shadow-lg group overflow-hidden';
            } else {
                card.className = 'relative bg-white rounded-xl border border-bg-border hover:border-brand/40 hover:shadow-md transition-all group overflow-hidden mb-3';
            }
        }

        var node = item.querySelector('.relative.flex.flex-col.items-center > div');
        if (node) {
            var icon = node.querySelector('iconify-icon');
            if (isCurrent) {
                node.className = 'w-10 h-10 rounded-full bg-brand flex items-center justify-center text-white shadow-lg ring-4 ring-brand-tint animate-pulse z-10';
                if (icon) {
                    icon.className = 'text-lg text-white';
                    icon.setAttribute('icon', colors.icon);
                }
            } else {
                node.className = 'w-9 h-9 rounded-full bg-white border-2 border-' + colors.node + ' flex items-center justify-center shadow-sm z-10';
                if (icon) {
                    icon.className = 'text-base text-' + colors.node;
                    icon.setAttribute('icon', colors.icon);
                }
            }
        }
    }

    function sortTimeline() {
        var container = document.getElementById('timeline-container');
        if (!container) return;
        var items = Array.from(container.querySelectorAll('.timeline-item'));
        items.sort(function(a, b) {
            var dateA = new Date(a.getAttribute('data-date') || '');
            var dateB = new Date(b.getAttribute('data-date') || '');
            return dateA - dateB;
        });
        items.forEach(function(item) {
            container.appendChild(item);
        });
    }

    function deleteTimeline(btn) {
        if (!confirm('确定要删除这条时间线吗？')) return;
        var item = btn.closest('.timeline-item');
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

    // ===== 初始化 =====
    function initTimelineItems() {
        var container = document.getElementById('timeline-container');
        if (!container) return;

        var items = container.querySelectorAll('.timeline-item');
        items.forEach(function(item) {
            if (!item.getAttribute('data-date')) {
                var dateSpan = item.querySelector('.flex.items-center.gap-1\\.5 > span');
                if (dateSpan) {
                    item.setAttribute('data-date', dateSpan.textContent.trim());
                }
            }

            var titleEl = item.querySelector('.text-sm.font-semibold, .text-sm.font-bold');
            if (titleEl && !titleEl.classList.contains('timeline-title')) {
                titleEl.classList.add('timeline-title');
            }

            var tagEl = item.querySelector('.rounded-full.font-medium:not(.timeline-tag)');
            if (tagEl && !tagEl.classList.contains('timeline-tag') && tagEl.textContent.trim() !== '' && tagEl.textContent.trim().length < 10) {
                tagEl.classList.add('timeline-tag');
            }

            var descEl = item.querySelector('.text-xs.leading-relaxed');
            if (descEl && !descEl.classList.contains('timeline-desc')) {
                descEl.classList.add('timeline-desc');
            }

            var actionGroup = item.querySelector('.flex.items-center.gap-1\\.5.flex-none');
            if (actionGroup && !actionGroup.querySelector('[onclick="editTimeline(this)"]')) {
                var dateSpan = actionGroup.querySelector('span');
                var editBtn = document.createElement('button');
                editBtn.className = 'opacity-0 group-hover:opacity-100 text-fg-tertiary hover:text-brand transition-opacity p-1';
                editBtn.setAttribute('onclick', 'editTimeline(this)');
                editBtn.setAttribute('title', '编辑');
                editBtn.innerHTML = '<iconify-icon class="text-base" icon="mdi:pencil-outline"></iconify-icon>';
                if (dateSpan) {
                    dateSpan.parentNode.insertBefore(editBtn, dateSpan.nextSibling);
                }
            }
        });
    }

    // ===== 双绑定 =====
    globalThis.addEvidenceCatalogItem = addEvidenceCatalogItem;
    globalThis.loadCatalogFileList = loadCatalogFileList;
    globalThis.toggleCatalogFileSelect = toggleCatalogFileSelect;
    globalThis.updateCatalogSelectedCount = updateCatalogSelectedCount;
    globalThis.closeAddEvidenceCatalogModal = closeAddEvidenceCatalogModal;
    globalThis.submitEvidenceCatalog = submitEvidenceCatalog;
    globalThis.editCatalogItem = editCatalogItem;
    globalThis.saveCatalogEdit = saveCatalogEdit;
    globalThis.deleteCatalogItem = deleteCatalogItem;
    globalThis.renumberCatalogItems = renumberCatalogItems;
    globalThis.aiCreateEvidenceCatalog = aiCreateEvidenceCatalog;
    globalThis.openAddTimelineModal = openAddTimelineModal;
    globalThis.closeAddTimelineModal = closeAddTimelineModal;
    globalThis.submitTimeline = submitTimeline;
    globalThis.editTimeline = editTimeline;
    globalThis.deleteTimeline = deleteTimeline;
    globalThis.initTimelineItems = initTimelineItems;
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