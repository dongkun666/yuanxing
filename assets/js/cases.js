/**
 * 案件管理模块 - 案件列表/详情/归档 + 9 个 case tab
 * 包含: 案件 CRUD + 字段编辑 + 案件详情 tab 切换 + 证据目录/时间线/证据/合同/委托/文书
 * 加载: 在 script.js 之前同步加载
 */



        function filterCaseList() {
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

            rows.forEach(function(row) {
                var caseNum = row.querySelector('td:nth-child(1)')?.textContent.toLowerCase() || '';
                var caseType = row.querySelector('td:nth-child(2)')?.textContent.toLowerCase() || '';
                var party = row.querySelector('td:nth-child(3)')?.textContent.toLowerCase() || '';
                var lawyer = row.querySelector('td:nth-child(4)')?.textContent.toLowerCase() || '';
                var rowStatus = row.getAttribute('data-status') || '';
                var rowType = row.getAttribute('data-type') || '';

                var matchSearch = !searchText ||
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

            // 重置到第一页
            caseCurrentPage = 1;

            // 显示结果计数
            if (resultCount) {
                resultCount.textContent = '共 ' + filteredRows.length + ' 条';
            }

            // 计算总页数
            var totalPages = Math.ceil(filteredRows.length / pageSize) || 1;
            if (caseCurrentPage > totalPages) caseCurrentPage = totalPages;

            // 显示/隐藏行
            var startIdx = (caseCurrentPage - 1) * pageSize;
            var endIdx = startIdx + pageSize;

            rows.forEach(function(row) { row.style.display = 'none'; });
            filteredRows.forEach(function(row, idx) {
                if (idx >= startIdx && idx < endIdx) {
                    row.style.display = '';
                }
            });

            // 更新分页信息
            if (paginationInfo) {
                paginationInfo.textContent = '共 ' + filteredRows.length + ' 条，第 ' + caseCurrentPage + '/' + totalPages + ' 页';
            }

            // 生成分页按钮
            if (paginationBtns) {
                paginationBtns.innerHTML = '';
                for (var i = 1; i <= totalPages; i++) {
                    var btn = document.createElement('button');
                    btn.className = 'w-7 h-7 rounded text-xs flex items-center justify-center ' +
                        (i === caseCurrentPage ? 'bg-[#165DFF] text-white' : 'bg-white hover:bg-[#F7F8FA] text-[#4E5969] border border-[#E5E6EB]');
                    btn.textContent = i;
                    btn.onclick = (function(page) {
                        return function() {
                            goToCasePage(page, pageSize);
                        };
                    })(i);
                    paginationBtns.appendChild(btn);
                }
            }
        }


        function goToCasePage(page, pageSize) {
            caseCurrentPage = page;
            filterCaseList();
        }

        function archiveCase() {
            showToast('案件归档功能开发中');
        }


        function editCaseTitle() {
            var el = document.getElementById('case-detail-title');
            if (!el) return;
            var currentText = el.textContent.trim();
            var input = document.createElement('input');
            input.type = 'text';
            input.value = currentText;
            input.className = 'text-sm font-medium text-gray-800 bg-transparent border border-[#165DFF] rounded px-2 py-0.5 outline-none focus:border-[#165DFF] w-auto min-w-[200px]';
            
            function finishEdit() {
                var newText = input.value.trim();
                if (newText && newText !== currentText) {
                    el.textContent = newText;
                    if (currentCaseIndex >= 0) {
                        var tbody = document.getElementById('caseTableBody');
                        if (tbody) {
                            var rows = tbody.querySelectorAll('tr');
                            if (rows[currentCaseIndex]) {
                                var firstTd = rows[currentCaseIndex].querySelector('td:first-child');
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
            input.addEventListener('keydown', function(e) {
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

            
            function finishEdit() {
                var newText = input.value.trim();
                if (newText && newText !== currentText) {
                    el.textContent = newText;
                    if (currentCaseIndex >= 0) {
                        var tbody = document.getElementById('caseTableBody');
                        if (tbody) {
                            var rows = tbody.querySelectorAll('tr');
                            if (rows[currentCaseIndex]) {
                                var firstTd = rows[currentCaseIndex].querySelector('td:first-child');
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


        function deleteCase(index) {
            if (!confirm('确定要删除该案件吗？删除后不可恢复。')) return;
            var tbody = document.getElementById('caseTableBody');
            if (!tbody) return;
            var rows = tbody.querySelectorAll('tr');
            if (rows[index]) {
                rows[index].remove();
                showToast('案件已删除');
                filterCaseList();
            }
        }


        function openNewCaseModal() {
            var modal = document.getElementById('new-case-modal');
            if (modal) {
                modal.classList.remove('hidden');
            }
        }


        function closeNewCaseModal() {
            var modal = document.getElementById('new-case-modal');
            if (modal) {
                modal.classList.add('hidden');
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
            showToast('打开归档详情 #' + id + ' (功能开发中)');
        }

        function restoreArchive() {
            if (confirm('确定要恢复此归档案件？恢复后会重新出现在案件列表中。')) {
                showToast('归档已恢复', 'success');
            }
        }

        function deleteArchive() {
            if (confirm('确定要永久删除此归档？此操作不可恢复。')) {
                showToast('归档已删除', 'success');
            }
        }

        // 归档列表筛选 (归档视图搜索/年份/类型)
        function filterArchiveList() {
            // 触发归档表的重新筛选 - 占位实现, 真实表格行筛选由 renderArchiveTable 读取 input 值
            if (typeof renderArchiveTable === 'function') {
                renderArchiveTable();
            } else {
                // 退化为本地筛选: 按搜索词 hide/show tbody tr
                var tbody = document.getElementById('archiveTableBody');
                if (!tbody) return;
                var search = (document.getElementById('archiveSearchInput')?.value || '').toLowerCase();
                var year = document.getElementById('archiveYearFilter')?.value || '';
                var type = document.getElementById('archiveTypeFilter')?.value || '';
                tbody.querySelectorAll('tr').forEach(function(tr) {
                    var haystack = tr.textContent.toLowerCase();
                    var show = (!search || haystack.indexOf(search) > -1)
                            && (!year || haystack.indexOf(year) > -1)
                            && (!type || tr.getAttribute('data-archive-type') === type);
                    tr.style.display = show ? '' : 'none';
                });
            }
        }

        // 全选/取消全选 归档 checkbox
        function toggleAllArchive(masterCb) {
            var tbody = document.getElementById('archiveTableBody');
            if (!tbody) return;
            tbody.querySelectorAll('input[type="checkbox"]').forEach(function(cb) {
                cb.checked = masterCb.checked;
            });
        }


        function getFieldValue(section, key) {
            var el = document.getElementById('field-' + section + '-' + key);
            if (!el) return '';
            if (section === 'claims' || section === 'strategy' || section === 'summary') {
                return el.innerText.trim();
            }
            return el.innerText.trim();
        }


        function setFieldValue(section, key, value) {
            var el = document.getElementById('field-' + section + '-' + key);
            if (!el) return;
            if (section === 'claims') {
                var lines = value.split('\n').filter(function(l) { return l.trim(); });
                el.innerHTML = lines.map(function(line, i) {
                    return '<p>' + (i + 1) + '. ' + line.replace(/^\d+\.\s*/, '') + '</p>';
                }).join('');
            } else if (section === 'strategy' || section === 'summary') {
                el.innerText = value;
            } else if (key === 'status') {
                el.innerText = value;
                el.className = 'text-[11px] font-medium px-2 py-0.5 rounded-full ' + 
                    (value === '进行中' ? 'bg-blue-100 text-blue-700' :
                     value === '已结案' ? 'bg-green-100 text-green-700' :
                     value === '已归档' ? 'bg-gray-100 text-gray-700' :
                     'bg-orange-100 text-orange-700');
            } else if (key === 'preservation') {
                el.innerText = value;
                el.className = 'text-[11px] font-medium px-2 py-0.5 rounded-full ' + 
                    (value === '已保全' ? 'bg-green-100 text-green-700' :
                     value === '未保全' ? 'bg-gray-100 text-gray-700' :
                     'bg-orange-100 text-orange-700');
            } else if (section === 'opponent' && key === 'legalRep') {
                el.innerText = value;
                if (!value || value === '未提供 · 请补充') {
                    el.className = 'text-sm text-red-500';
                } else {
                    el.className = 'text-sm text-gray-800';
                }
            } else {
                el.innerText = value;
            }
        }


        function renderEditForm(section) {
            var config = sectionConfigs[section];
            if (!config) return;
            document.getElementById('edit-modal-title').innerText = config.title;
            var formBody = document.getElementById('edit-form-body');
            var html = '';
            var fields = config.fields;
            for (var i = 0; i < fields.length; i += 2) {
                var field1 = fields[i];
                var field2 = fields[i + 1];
                var rowColSpan = (field1.colSpan || 1) + (field2 ? (field2.colSpan || 1) : 0);
                if (field1.colSpan === 2 || (field1.colSpan === 3 && !field2)) {
                    html += '<div class="space-y-1">';
                    html += '<label class="block text-xs font-medium text-gray-700">' + field1.label + '</label>';
                    html += renderFieldInput(section, field1);
                    html += '</div>';
                } else {
                    html += '<div class="grid grid-cols-2 gap-4">';
                    html += '<div class="space-y-1">';
                    html += '<label class="block text-xs font-medium text-gray-700">' + field1.label + '</label>';
                    html += renderFieldInput(section, field1);
                    html += '</div>';
                    if (field2) {
                        html += '<div class="space-y-1">';
                        html += '<label class="block text-xs font-medium text-gray-700">' + field2.label + '</label>';
                        html += renderFieldInput(section, field2);
                        html += '</div>';
                    }
                    html += '</div>';
                }
            }
            formBody.innerHTML = html;
        }


        function renderFieldInput(section, field) {
            var value = getFieldValue(section, field.key);
            var inputClass = 'w-full border border-[#E5E6EB] rounded-lg px-3 py-2 text-sm text-[#1D2129] focus:outline-none focus:border-[#165DFF] transition-colors';
            if (field.type === 'textarea') {
                var rows = field.rows || 4;
                return '<textarea class="' + inputClass + ' resize-none" data-field="' + field.key + '" rows="' + rows + '">' + value + '</textarea>';
            } else if (field.type === 'select') {
                var options = field.options || [];
                var optionsHtml = options.map(function(opt) {
                    return '<option value="' + opt + '"' + (opt === value ? ' selected' : '') + '>' + opt + '</option>';
                }).join('');
                return '<select class="' + inputClass + ' appearance-none bg-white" data-field="' + field.key + '">' + optionsHtml + '</select>';
            } else if (field.type === 'date') {
                return '<input type="date" class="' + inputClass + '" data-field="' + field.key + '" value="' + value + '"/>';
            } else {
                return '<input type="text" class="' + inputClass + '" data-field="' + field.key + '" value="' + value + '"/>';
            }
        }


        function editSection(section) {
            currentEditSection = section;
            renderEditForm(section);
            document.getElementById('edit-section-modal').classList.remove('hidden');
        }


        function closeEditSectionModal() {
            document.getElementById('edit-section-modal').classList.add('hidden');
            currentEditSection = null;
        }


        function saveEditSection() {
            if (!currentEditSection) return;
            var config = sectionConfigs[currentEditSection];
            if (!config) return;
            var formBody = document.getElementById('edit-form-body');
            var inputs = formBody.querySelectorAll('[data-field]');
            for (var i = 0; i < inputs.length; i++) {
                var input = inputs[i];
                var fieldKey = input.getAttribute('data-field');
                var value = input.value;
                setFieldValue(currentEditSection, fieldKey, value);
            }
            closeEditSectionModal();
            showToast('保存成功');
        }

    
    function openCaseDetail(index) {
        var caseMeta = [
            { caseName: '李明诉XX公司买卖合同纠纷', caseNumber: '(2026)京01民初128号', type: '民间借贷纠纷', status: '进行中' },
            { caseName: '赵六劳动争议仲裁案', caseNumber: '(2026)京02民初256号', type: '劳动争议仲裁', status: '进行中' },
            { caseName: '张三合同纠纷案', caseNumber: '(2026)京03民初789号', type: '合同纠纷', status: '待开庭' },
            { caseName: '某科技公司股权纠纷案', caseNumber: '(2026)京04民初345号', type: '知识产权侵权', status: '已立案' },
            { caseName: '王华借贷纠纷案', caseNumber: '(2026)京05民初567号', type: '离婚纠纷', status: '进行中' }
        ];
        
        currentCaseIndex = index;
        
        document.querySelectorAll('.view-content').forEach(function(v) {
            v.classList.add('hidden');
        });
        
        var caseView = document.getElementById('view-case');
        if (caseView) {
            caseView.classList.remove('hidden');
            // 更新案件元数据
            if (caseMeta[index]) {
                var meta = caseMeta[index];
                var titleEl = document.getElementById('case-detail-title');
                if (titleEl) titleEl.textContent = meta.caseName;
            }
            // 切换回案件概览 Tab
            var tab = document.querySelector('.case-tab[data-tab="overview"]');
            if (tab) switchCaseTab('overview', tab);
        } else {
            // 视图未加载，动态加载
            loadView('case', function(html) {
                document.getElementById('main-content').insertAdjacentHTML('beforeend', html);
                var newCaseView = document.getElementById('view-case');
                if (newCaseView) {
                    newCaseView.classList.remove('hidden');
                    // 更新案件元数据
                    if (caseMeta[index]) {
                        var meta = caseMeta[index];
                        var titleEl = document.getElementById('case-detail-title');
                        if (titleEl) titleEl.textContent = meta.caseName;
                    }
                    // 自动切换到案件概览 Tab
                    var tab = document.querySelector('.case-tab[data-tab="overview"]');
                    if (tab) switchCaseTab('overview', tab);
                }
            });
        }
    }

    function switchCaseTab(tabName, btn) {
        document.querySelectorAll('[id^="case-tab-"]').forEach(function(el) {
            el.classList.add('hidden');
            el.classList.remove('flex', 'flex-row', 'flex-col');
        });
        var target = document.getElementById('case-tab-' + tabName);
        if (target) {
            target.classList.remove('hidden');
            target.classList.add('flex');
            if (tabName === 'documents') {
                target.classList.add('flex-row');
            } else {
                target.classList.add('flex-col');
            }
        }
        document.querySelectorAll('.case-tab').forEach(function(b) {
            b.classList.remove('border-[#165DFF]', 'text-[#165DFF]');
            b.classList.add('border-transparent', 'text-gray-500');
        });
        if (btn) {
            btn.classList.remove('border-transparent', 'text-gray-500');
            btn.classList.add('border-[#165DFF]', 'text-[#165DFF]');
        }
    }

    function switchMaterialsTab(tabName, btn) {
        document.getElementById('materials-tab-overview').classList.add('hidden');
        document.getElementById('materials-tab-catalog').classList.add('hidden');
        document.getElementById('materials-tab-' + tabName).classList.remove('hidden');
        document.querySelectorAll('.materials-tab').forEach(function(tab) {
            tab.classList.remove('text-[#165DFF]', 'border-[#165DFF]');
            tab.classList.add('text-gray-500', 'border-transparent');
        });
        if (btn) {
            btn.classList.remove('text-gray-500', 'border-transparent');
            btn.classList.add('text-[#165DFF]', 'border-[#165DFF]');
        }
    }

    function addEvidenceCatalogItem() {
        var modal = document.getElementById('add-evidence-catalog-modal');
        if (modal) {
            modal.classList.remove('hidden');
            // 重置表单
            document.getElementById('catalog-number').value = '';
            document.getElementById('catalog-name').value = '';
            document.getElementById('catalog-pages').value = '';
            document.getElementById('catalog-description').value = '';
            // 设置默认证据种类
            var radios = document.getElementsByName('catalog-type');
            if (radios.length > 0) radios[0].checked = true;
            // 自动计算下一个编号
            var tbody = document.getElementById('evidence-catalog-list');
            if (tbody) {
                var rows = tbody.querySelectorAll('tr');
                document.getElementById('catalog-number').value = rows.length + 1;
            }
            // 加载证据概览文件列表
            loadCatalogFileList();
            // 重置已选文件
            catalogSelectedFiles = [];
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
            catalogSelectedFiles = catalogSelectedFiles.filter(function(f) { return f.name !== fileName; });
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
        
        // 获取选中的证据种类
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
        
        // 获取证据种类的颜色样式
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
        // 保存关联文件到data属性
        if (catalogSelectedFiles.length > 0) {
            newRow.setAttribute('data-linked-files', JSON.stringify(catalogSelectedFiles));
        }
        
        // 生成关联文件显示
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
        
        // 从 data-* 属性读取
        var number = card.dataset.number || '';
        var type = card.dataset.type || '书证';
        var name = card.dataset.name || '';
        var description = card.dataset.description || '';
        var pages = card.dataset.pages || '';
        
        // 获取已关联文件（从data属性获取）
        var linkedFiles = card.getAttribute('data-linked-files');
        if (linkedFiles) {
            try {
                catalogSelectedFiles = JSON.parse(linkedFiles);
            } catch(e) {
                catalogSelectedFiles = [];
            }
        } else {
            catalogSelectedFiles = [];
        }
        
        // 填充模态框
        var modal = document.getElementById('add-evidence-catalog-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.getElementById('catalog-number').value = number;
            document.getElementById('catalog-name').value = name;
            document.getElementById('catalog-pages').value = pages === '-' ? '' : pages;
            document.getElementById('catalog-description').value = description === '-' ? '' : description;
            
            // 设置证据种类选中状态
            var typeRadios = document.getElementsByName('catalog-type');
            for (var i = 0; i < typeRadios.length; i++) {
                typeRadios[i].checked = (typeRadios[i].value === type);
            }
            
            // 修改标题和按钮文字
            var modalTitle = modal.querySelector('h3');
            if (modalTitle) modalTitle.textContent = '编辑证据目录';
            var submitBtn = modal.querySelector('[onclick="submitEvidenceCatalog()"]');
            if (submitBtn) submitBtn.textContent = '保存';
            
            // 加载文件列表并回显已选
            loadCatalogFileList();
            // 延迟一点设置选中状态，确保DOM已渲染
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
            // 重新编号
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
        
        // 模拟AI生成目录结构
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
