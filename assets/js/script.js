        // ===== 全局应用状态 =====
        var AppState = {
            isYearly: false,
            selectedPayment: 'alipay',
            selectedDynamicType: '紧急',
            selectedExtractSource: 'case',
            batchFiles: [],
            dynamicsViewData: [],
            autoSaveTimer: null,
            dynamicAttachments: []
        };

        // ===== 视图缓存管理 =====
        var viewCache = {};

        // 视图文件名映射
        var viewFileMap = {
            'workstation': 'workstation.html',
            'schedule-list': 'schedule-list.html',
            'attention-list': 'attention-list.html',
            'case-list': 'case-list.html',
            'case-analysis': 'case-analysis.html',
            'schedule-calendar': 'schedule-calendar.html',
            'case-dynamics': 'case-dynamics.html',
            'attachment-list': 'attachment-list.html',
            'case': 'case-detail.html',
            'client': 'client.html',
            'client-detail': 'client-detail.html',
            'template': 'template.html',
            'knowledge': 'knowledge.html',
            'ai': 'ai.html',
            'subscription': 'subscription.html',
            'payment': 'payment.html',
            'payment-success': 'payment-success.html',
            'orders': 'orders.html',
            'member-center': 'member-center.html',
            'account-settings': 'account-settings.html',
            'archive': 'archive.html'
        };

        // 动态加载视图
        // 开发模式: URL 含 ?dev=1 时跳过 viewCache, 每次重新拉取最新 HTML
        var isDevMode = window.location.search.indexOf('dev=1') !== -1 ||
                         window.location.search.indexOf('dev=') !== -1 && /dev=(\d+)/.test(window.location.search) && RegExp.$1 !== '0';

        function loadView(viewId, callback) {
            // 开发模式下跳过缓存
            if (!isDevMode && viewCache[viewId]) {
                // 已缓存，直接使用
                if (callback) callback(viewCache[viewId]);
                return;
            }
            var fileName = viewFileMap[viewId];
            if (!fileName) {
                console.error('未知的视图ID:', viewId);
                return;
            }
            // 加时间戳绕过 HTTP 缓存
            var url = 'templates/views/' + fileName + '?_t=' + Date.now();
            fetch(url)
                .then(function(response) { return response.text(); })
                .then(function(html) {
                    viewCache[viewId] = html;
                    if (callback) callback(html);
                })
                .catch(function(err) { console.error('加载视图失败:', viewId, err); });
        }

        // ===== 案件列表筛选 =====
        var caseCurrentPage = 1;

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

        // ===== 案件归档 =====
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

        // ===== 案件详情页操作 =====
        function shareCase() {
            showToast('分享案件功能开发中');
        }

        var currentEditSection = null;
        var sectionConfigs = {
            basic: {
                title: '编辑案件基本信息',
                fields: [
                    { key: 'caseNumber', label: '案号', type: 'text', colSpan: 1 },
                    { key: 'caseType', label: '案由', type: 'text', colSpan: 1 },
                    { key: 'status', label: '案件状态', type: 'select', options: ['进行中', '已结案', '已归档', '中止审理'], colSpan: 1 },
                    { key: 'claimAmount', label: '标的金额', type: 'text', colSpan: 1 },
                    { key: 'contractAmount', label: '合同金额', type: 'text', colSpan: 1 },
                    { key: 'signDate', label: '签约日期', type: 'date', colSpan: 1 },
                    { key: 'stage', label: '代理阶段', type: 'select', options: ['一审', '二审', '再审', '执行', '仲裁'], colSpan: 1 },
                    { key: 'preservation', label: '是否保全', type: 'select', options: ['已保全', '未保全', '保全中'], colSpan: 1 },
                    { key: 'paymentStatus', label: '缴费情况', type: 'select', options: ['已缴费', '未缴费', '部分缴费'], colSpan: 1 },
                    { key: 'specialTerms', label: '特殊约定', type: 'textarea', colSpan: 3 }
                ]
            },
            client: {
                title: '编辑客户信息',
                fields: [
                    { key: 'name', label: '客户姓名', type: 'text', colSpan: 1 },
                    { key: 'phone', label: '客户电话', type: 'text', colSpan: 1 },
                    { key: 'idNumber', label: '客户证件号', type: 'text', colSpan: 1 },
                    { key: 'legalRep', label: '法定代表人', type: 'text', colSpan: 1 },
                    { key: 'address', label: '客户地址', type: 'textarea', colSpan: 2 }
                ]
            },
            opponent: {
                title: '编辑对方信息',
                fields: [
                    { key: 'name', label: '对方姓名', type: 'text', colSpan: 1 },
                    { key: 'phone', label: '对方电话', type: 'text', colSpan: 1 },
                    { key: 'idNumber', label: '对方证件号', type: 'text', colSpan: 1 },
                    { key: 'legalRep', label: '法定代表人', type: 'text', colSpan: 1 },
                    { key: 'address', label: '对方地址', type: 'textarea', colSpan: 2 }
                ]
            },
            claims: {
                title: '编辑客户诉求',
                fields: [
                    { key: 'content', label: '客户诉求内容', type: 'textarea', rows: 6, colSpan: 2 }
                ]
            },
            strategy: {
                title: '编辑办案思路',
                fields: [
                    { key: 'content', label: '办案思路', type: 'textarea', rows: 6, colSpan: 2 }
                ]
            },
            summary: {
                title: '编辑案情简述',
                fields: [
                    { key: 'content', label: '案情简述', type: 'textarea', rows: 6, colSpan: 2 }
                ]
            }
        };

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

        // 视图切换逻辑
        function switchView(viewId, el) {
            var target = document.getElementById('view-' + viewId);
            if (target) {
                // 视图已存在，直接显示
                document.querySelectorAll('.view-content').forEach(view => view.classList.add('hidden'));
                target.classList.remove('hidden');
                if (viewId === 'schedule-list' || viewId === 'attention-list') {
                    target.classList.add('flex-col');
                }
                // 修复 template 视图: 浏览器重组 DOM 后把卡片视图和孤儿卡片放到主体 div 直接子级
                if (viewId === 'template') {
                    fixTemplateViewDOM();
                }
            } else {
                // 视图未加载，动态加载
                loadView(viewId, function(html) {
                    document.getElementById('main-content').insertAdjacentHTML('beforeend', html);
                    var newTarget = document.getElementById('view-' + viewId);
                    if (newTarget) {
                        document.querySelectorAll('.view-content').forEach(view => view.classList.add('hidden'));
                        newTarget.classList.remove('hidden');
                        if (viewId === 'schedule-list' || viewId === 'attention-list') {
                            newTarget.classList.add('flex-col');
                        }
                        if (viewId === 'template') {
                            // 延迟修复, 等 DOM 稳定
                            setTimeout(fixTemplateViewDOM, 100);
                            setTimeout(fixTemplateViewDOM, 500);
                        }
                    }
                });
            }

            // 更新侧边栏状态
            if (el) {
                document.querySelectorAll('.sidebar-item').forEach(function(item) { item.classList.remove('active'); });
                el.classList.add('active');
            }

            // 切换 workstation 时刷新今日日程角标
            if (viewId === 'workstation') {
                setTimeout(updateTodayScheduleBadge, 50);
            }
        }

        // 侧边栏标签页切换
        function switchSidebarTab(tab) {
            var tabWork = document.getElementById('sidebarTabWork');
            var tabAI = document.getElementById('sidebarTabAI');
            var btns = document.querySelectorAll('.sidebar-tab-btn');
            
            btns.forEach(function(btn) { btn.classList.remove('active'); });
            
            if (tab === 'work') {
                if (tabWork) tabWork.classList.remove('hidden');
                if (tabAI) tabAI.classList.add('hidden');
                if (btns[0]) btns[0].classList.add('active');
                
                // 隐藏AI视图，显示当前激活的工作视图
                var viewAI = document.getElementById('view-ai');
                if (viewAI) viewAI.classList.add('hidden');
                // 默认显示工作台
                var ws = document.getElementById('view-workstation');
                if (ws) ws.classList.remove('hidden');
            } else {
                if (tabWork) tabWork.classList.add('hidden');
                if (tabAI) tabAI.classList.remove('hidden');
                if (btns[1]) btns[1].classList.add('active');
                
                // 清除侧边栏菜单项高亮（AI模式下无对应工作菜单项）
                document.querySelectorAll('.sidebar-item').forEach(function(item) {
                    item.classList.remove('active');
                });
                
                // 隐藏所有工作视图，显示AI视图
                document.querySelectorAll('.view-content').forEach(function(v) { v.classList.add('hidden'); });
                
                // 动态加载AI视图（如果尚未加载）
                var viewAI = document.getElementById('view-ai');
                if (!viewAI) {
                    loadView('ai', function(html) {
                        document.getElementById('main-content').insertAdjacentHTML('beforeend', html);
                        var newViewAI = document.getElementById('view-ai');
                        if (newViewAI) newViewAI.classList.remove('hidden');
                        // 显示AI新对话子视图
                        var aiViewChat = document.getElementById('aiViewChat');
                        if (aiViewChat) aiViewChat.classList.remove('hidden');
                    });
                } else {
                    viewAI.classList.remove('hidden');
                    // 显示AI新对话子视图
                    var aiViewChat = document.getElementById('aiViewChat');
                    if (aiViewChat) aiViewChat.classList.remove('hidden');
                    var aiViewSkills = document.getElementById('aiViewSkills');
                    if (aiViewSkills) aiViewSkills.classList.add('hidden');
                    var aiViewHistory = document.getElementById('aiViewHistory');
                    if (aiViewHistory) aiViewHistory.classList.add('hidden');
                }
            }
        }

        // AI 子标签页切换
        function switchAITab(tab) {
            // 切换按钮高亮
            document.querySelectorAll('.ai-subtab-btn').forEach(function(btn) {
                btn.classList.remove('active');
            });
            var activeBtn = document.querySelector('.ai-subtab-btn[data-ai-tab="' + tab + '"]');
            if (activeBtn) activeBtn.classList.add('active');

            // 切换内容区
            document.getElementById('aiTabNew').classList.add('hidden');
            document.getElementById('aiTabSkills').classList.add('hidden');
            document.getElementById('aiTabHistory').classList.add('hidden');

            if (tab === 'new') {
                document.getElementById('aiTabNew').classList.remove('hidden');
                document.getElementById('aiChatInput').classList.remove('hidden');
            } else if (tab === 'skills') {
                document.getElementById('aiTabSkills').classList.remove('hidden');
                document.getElementById('aiChatInput').classList.add('hidden');
            } else if (tab === 'history') {
                document.getElementById('aiTabHistory').classList.remove('hidden');
                document.getElementById('aiChatInput').classList.add('hidden');
            }

            // 重置滚动
            document.getElementById('aiSubContent').scrollTop = 0;
        }

        // 新建对话（合并版：同时清空侧边栏和主视图消息）
        function startNewChat() {
            // 清空侧边栏聊天消息
            var chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {
                chatMessages.innerHTML = '';
            }
            // 清空右侧主视图聊天消息
            var aiViewMessages = document.getElementById('aiViewMessages');
            if (aiViewMessages) {
                aiViewMessages.innerHTML = '';
            }
            // 添加系统欢迎消息到侧边栏
            var welcomeHtml = '<div class="flex items-start gap-2 mb-3"><div class="w-7 h-7 rounded-lg bg-gradient-to-br from-[#165DFF] to-[#5B8FF9] flex items-center justify-center flex-shrink-0"><iconify-icon icon="mdi:robot" class="text-white text-sm"></iconify-icon></div><div class="bg-[#F2F3F5] rounded-xl px-3 py-2 text-xs text-gray-700"><p>您好！我是 LexPrime AI 助手，可以帮您：</p><ul class="list-disc pl-4 mt-1 space-y-0.5"><li>起草法律文书</li><li>检索类案与法条</li><li>分析案件策略</li><li>审查合同风险</li></ul><p class="mt-1">请问有什么可以帮您的？</p></div></div>';
            
            var chatArea = document.querySelector('#chatPanel .flex-1.overflow-y-auto');
            if (chatArea) chatArea.innerHTML = welcomeHtml;
            
            if (aiViewMessages) {
                aiViewMessages.innerHTML = '<div class="flex items-start gap-2.5 px-4 py-3">' +
                    '<div class="w-8 h-8 rounded-xl bg-gradient-to-br from-[#165DFF] to-[#5B8FF9] flex items-center justify-center flex-shrink-0 shadow-sm">' +
                        '<iconify-icon icon="mdi:robot" class="text-white text-base"></iconify-icon>' +
                    '</div>' +
                    '<div class="bg-white rounded-xl px-3.5 py-2.5 text-xs text-gray-700 shadow-sm max-w-[80%]">' +
                        '<p>您好！我是 LexPrime AI 助手，可以帮您起草文书、检索类案、分析策略、审查合同。请问有什么可以帮您的？</p>' +
                    '</div>' +
                '</div>';
            }
        }

        // 选择历史对话
        function selectHistory(el) {
            var title = el.getAttribute('data-title') || '历史对话';
            // 切换到新对话标签页
            switchAITab('new');

            // 清空消息列表，显示新欢迎语+用户模拟消息
            var msgList = document.getElementById('chatMessages');
            msgList.innerHTML = '' +
                '<div class="flex gap-2.5 chat-message-ai">' +
                  '<div class="w-7 h-7 rounded-full bg-gradient-to-br from-[#165DFF] to-[#6C5CE7] flex items-center justify-center text-white flex-shrink-0 mt-0.5">' +
                    '<iconify-icon class="text-[10px]" icon="mdi:robot"></iconify-icon>' +
                  '</div>' +
                  '<div class="chat-bubble-ai max-w-[85%]">' +
                    '<p class="text-xs leading-relaxed text-[#4E5969]">已切换到对话：「<span class="font-medium text-[#165DFF]">' + title + '</span>」</p>' +
                    '<div class="flex items-center gap-2 mt-1.5">' +
                      '<span class="text-[10px] text-[#86909C]">刚刚</span>' +
                    '</div>' +
                  '</div>' +
                '</div>';

            document.getElementById('aiSubContent').scrollTop = 0;
        }

        // 历史对话搜索过滤
        function filterHistory() {
            var keyword = document.getElementById('historySearch').value.toLowerCase().trim();
            var items = document.querySelectorAll('#historyList .history-item');
            items.forEach(function(item) {
                var title = item.getAttribute('data-title') || '';
                if (!keyword || title.toLowerCase().indexOf(keyword) !== -1) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }

        // AI视图切换（左侧菜单点击 -> 右侧内容切换）
        function switchAIView(viewId, el) {
            // 更新侧边栏菜单高亮
            document.querySelectorAll('#sidebarTabAI .sidebar-item').forEach(function(item) { item.classList.remove('active'); });
            if (el) el.classList.add('active');
            
            // 获取AI子视图元素
            var aiViewChat = document.getElementById('aiViewChat');
            var aiViewSkills = document.getElementById('aiViewSkills');
            var aiViewHistory = document.getElementById('aiViewHistory');
            
            // 如果AI视图尚未加载，先加载它
            var viewAI = document.getElementById('view-ai');
            if (!viewAI) {
                loadView('ai', function(html) {
                    document.getElementById('main-content').insertAdjacentHTML('beforeend', html);
                    // 加载完成后切换子视图
                    switchAIViewSubView(viewId);
                });
                return;
            }
            
            // 隐藏所有AI子视图
            if (aiViewChat) aiViewChat.classList.add('hidden');
            if (aiViewSkills) aiViewSkills.classList.add('hidden');
            if (aiViewHistory) aiViewHistory.classList.add('hidden');
            
            // 显示目标视图
            switchAIViewSubView(viewId);
        }
        
        // AI子视图切换辅助函数
        function switchAIViewSubView(viewId) {
            var aiViewChat = document.getElementById('aiViewChat');
            var aiViewSkills = document.getElementById('aiViewSkills');
            var aiViewHistory = document.getElementById('aiViewHistory');
            
            if (viewId === 'chat' && aiViewChat) {
                aiViewChat.classList.remove('hidden');
            } else if (viewId === 'skills' && aiViewSkills) {
                aiViewSkills.classList.remove('hidden');
            } else if (viewId === 'history' && aiViewHistory) {
                aiViewHistory.classList.remove('hidden');
            }
        }

        // 选择历史对话
        function selectAIHistory(el) {
            var title = el.getAttribute('data-title') || '历史对话';
            // 切换到新对话视图
            document.querySelectorAll('#sidebarTabAI .sidebar-item').forEach(item => item.classList.remove('active'));
            document.querySelector('#sidebarTabAI .sidebar-item').classList.add('active');
            
            document.getElementById('aiViewChat').classList.remove('hidden');
            document.getElementById('aiViewSkills').classList.add('hidden');
            document.getElementById('aiViewHistory').classList.add('hidden');
            
            var msgList = document.getElementById('aiViewMessages');
            if (msgList) {
                msgList.innerHTML = '' +
                    '<div class="flex gap-3">' +
                      '<div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#165DFF] to-[#6C5CE7] flex items-center justify-center text-white flex-shrink-0">' +
                        '<iconify-icon class="text-sm" icon="mdi:robot"></iconify-icon>' +
                      '</div>' +
                      '<div class="max-w-[70%] bg-white rounded-xl p-4 shadow-sm border border-[#E5E6EB]">' +
                        '<p class="text-sm leading-relaxed text-[#4E5969]">已切换到对话：<span class="font-semibold text-[#165DFF]">' + title + '</span></p>' +
                        '<span class="text-[11px] text-[#86909C] mt-2 block">刚刚</span>' +
                      '</div>' +
                    '</div>';
            }
        }

        // 过滤历史记录
        function filterAIHistory(input) {
            var keyword = input.value.toLowerCase().trim();
            var items = document.querySelectorAll('#aiHistoryList > div');
            items.forEach(function(item) {
                var title = item.getAttribute('data-title') || '';
                if (!keyword || title.toLowerCase().indexOf(keyword) !== -1) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }

        // 更多菜单切换（每个标签各自独立菜单）
        function toggleMoreMenu(tab) {
            var menuId = tab === 'work' ? 'moreMenuWork' : 'moreMenuAI';
            var menu = document.getElementById(menuId);
            // 关闭另一个菜单（如果有打开的）
            var otherId = tab === 'work' ? 'moreMenuAI' : 'moreMenuWork';
            var otherMenu = document.getElementById(otherId);
            if (otherMenu) otherMenu.classList.add('hidden');
            // 切换当前菜单
            menu.classList.toggle('hidden');
        }

        // 点击页面其他位置关闭所有菜单
        document.addEventListener('click', function(e) {
            var menuWork = document.getElementById('moreMenuWork');
            var menuAI = document.getElementById('moreMenuAI');

            // 检查点击是否在任意「更多」按钮或菜单内部
            var isClickInBtn = e.target.closest('[onclick*="toggleMoreMenu"]');

            if (!isClickInBtn) {
                if (menuWork) menuWork.classList.add('hidden');
                if (menuAI) menuAI.classList.add('hidden');
            }

            // 点击外部关闭通知面板
            var panel = document.getElementById('notificationPanel');
            var notifBtn = document.querySelector('[onclick*="toggleNotifications"]');
            if (panel && notifBtn && !panel.contains(e.target) && !notifBtn.contains(e.target)) {
                panel.classList.add('hidden');
            }
        });

        // 更多菜单操作
        function handleMoreAction(action) {
            document.getElementById('moreMenuWork').classList.add('hidden');
            document.getElementById('moreMenuAI').classList.add('hidden');
            if (action === 'settings') {
                switchSidebarTab('work');
                alert('设置功能开发中');
            } else if (action === 'upgrade') {
                alert('升级功能开发中');
            } else if (action === 'feedback') {
                alert('问题反馈功能开发中');
            } else if (action === 'guide') {
                alert('用户指南功能开发中');
            } else if (action === 'contact') {
                alert('联系我们功能开发中');
            } else if (action === 'logout') {
                if (confirm('确认退出登录？')) {
                    showToast('已退出登录');
                }
            }
        }

        // 待办事项切换
        function toggleTodo(el) {
            var cb = el.querySelector('input[type="checkbox"]');
            if (cb) {
                cb.checked = !cb.checked;
                el.querySelectorAll('.text-gray-800').forEach(function(t) {
                    t.classList.toggle('line-through');
                    t.classList.toggle('text-gray-300');
                });
                el.querySelectorAll('.text-gray-400').forEach(function(t) {
                    t.classList.toggle('line-through');
                    t.classList.toggle('text-gray-300');
                });
            }
        }

        // 修改日程
        function editSchedule(btn) {
            var item = btn.closest('[onclick*="toggleTodo"]') || btn.parentElement.parentElement;
            var timeEl = item.querySelector('.text-sm.font-bold');
            var titleEl = item.querySelector('.text-sm.font-medium');
            var descEl = item.querySelector('.text-xs.text-gray-400');
            
            if (titleEl) {
                var currentTitle = titleEl.textContent;
                var newTitle = prompt('修改日程事项：', currentTitle);
                if (newTitle && newTitle.trim() !== '') {
                    titleEl.textContent = newTitle.trim();
                }
            }
            if (descEl) {
                var currentDesc = descEl.textContent;
                var newDesc = prompt('修改案件/描述：', currentDesc);
                if (newDesc && newDesc.trim() !== '') {
                    descEl.textContent = newDesc.trim();
                }
            }
        }

        // 删除日程
        function deleteSchedule(btn) {
            if (confirm('确定删除此日程吗？')) {
                var item = btn.closest('[onclick*="toggleTodo"]');
                if (item) {
                    item.remove();
                }
            }
        }

        // 通知面板切换
        function toggleNotifications(event) {
            if (event) event.stopPropagation();
            var panel = document.getElementById('notificationPanel');
            panel.classList.toggle('hidden');
        }

        // 全部已读
        function markAllNotifications() {
            var dots = document.querySelectorAll('#notificationPanel span.rounded-full.bg-\\[\\#165DFF\\]');
            dots.forEach(function(dot) {
                dot.classList.remove('bg-[#165DFF]');
                dot.classList.add('bg-transparent');
            });
            // 隐藏小红点
            var badge = document.querySelector('button[onclick*="toggleNotifications"] .w-2.h-2');
            if (badge) badge.classList.add('hidden');
        }

        // 用户菜单切换
        function toggleUserMenu(event) {
            if (event) event.stopPropagation();
            var menu = document.getElementById('userMenu');
            menu.classList.toggle('hidden');
        }

        // 初始加载
        window.onload = function() {
            // 页面加载完毕
        };

        // 跳转到会员订阅页面
        function switchToSubscription() {
            var userMenu = document.getElementById('userMenu');
            if (userMenu) userMenu.classList.add('hidden');
            
            switchSidebarTab('work');
            
            document.querySelectorAll('.sidebar-item').forEach(function(item) {
                item.classList.remove('active');
            });

            var target = document.getElementById('view-subscription');
            if (target) {
                document.querySelectorAll('.view-content').forEach(function(v) {
                    v.classList.add('hidden');
                });
                target.classList.remove('hidden');
            } else {
                loadView('subscription', function(html) {
                    document.getElementById('main-content').insertAdjacentHTML('beforeend', html);
                    var newTarget = document.getElementById('view-subscription');
                    if (newTarget) {
                        document.querySelectorAll('.view-content').forEach(function(v) {
                            v.classList.add('hidden');
                        });
                        newTarget.classList.remove('hidden');
                    }
                });
            }
        }

        // 年月付切换
        // var isYearly = false; // → AppState.isYearly

        function toggleBilling() {
            AppState.isYearly = !AppState.isYearly;
            var toggle = document.getElementById('billing-toggle');
            var knob = document.getElementById('billing-knob');
            var monthlyLabel = document.getElementById('monthly-label');
            var yearlyLabel = document.getElementById('yearly-label');
            
            if (AppState.isYearly) {
                toggle.style.backgroundColor = '#165DFF';
                knob.style.transform = 'translateX(24px)';
                monthlyLabel.style.color = '#86909C';
                yearlyLabel.style.color = '#1D2129';
                
                // 专业版：¥299/月 → ¥2399/年（省 ¥1199）
                document.getElementById('pro-price').textContent = '¥2,399';
                document.getElementById('pro-period').textContent = '/年';
                document.getElementById('pro-tip').textContent = '年付省 ¥1,189';
                
                // 企业版：¥899/月 → ¥7,199/年
                document.getElementById('enterprise-price').textContent = '¥7,199';
                document.getElementById('enterprise-period').textContent = '/年';
                document.getElementById('enterprise-tip').textContent = '年付省 ¥3,589';
            } else {
                toggle.style.backgroundColor = '#165DFF';
                knob.style.transform = 'translateX(0)';
                monthlyLabel.style.color = '#1D2129';
                yearlyLabel.style.color = '#86909C';
                
                document.getElementById('pro-price').textContent = '¥299';
                document.getElementById('pro-period').textContent = '/月';
                document.getElementById('pro-tip').textContent = '最适合个人律师';
                
                document.getElementById('enterprise-price').textContent = '¥899';
                document.getElementById('enterprise-period').textContent = '/月';
                document.getElementById('enterprise-tip').textContent = '适合律所及团队';
            }
        }

        // 跳转到支付页面
        function showPayment(plan) {
            var planNames = {
                'free': '免费版',
                'professional': '专业版',
                'enterprise': '企业版'
            };
            var planDesc = {
                'free': '基础功能体验',
                'professional': '最适合个人律师',
                'enterprise': '适合律所及团队'
            };
            var planPrice = {
                'free': '¥0',
                'professional': AppState.isYearly ? '¥2,399' : '¥299',
                'enterprise': AppState.isYearly ? '¥7,199' : '¥899'
            };
            
            if (plan === 'free') {
                // 免费版直接提示
                alert('免费版无需支付，可直接使用。如需要更多功能，请选择专业版或企业版。');
                return;
            }
            
            var billingText = AppState.isYearly ? '年付' : '月付';
            document.getElementById('payment-plan-name').textContent = planNames[plan] + ' · ' + billingText;
            document.getElementById('payment-plan-desc').textContent = planDesc[plan];
            document.getElementById('payment-amount').textContent = planPrice[plan];
            document.getElementById('payment-subtotal').textContent = planPrice[plan];
            document.getElementById('payment-total').textContent = planPrice[plan];
            document.getElementById('pay-button-amount').textContent = planPrice[plan];
            
            // 切换视图
            document.querySelectorAll('.view-content').forEach(function(v) {
                v.classList.add('hidden');
            });
            document.getElementById('view-payment').classList.remove('hidden');
        }

        // 返回订阅页面
        function backToSubscription() {
            document.querySelectorAll('.view-content').forEach(function(v) {
                v.classList.add('hidden');
            });
            document.getElementById('view-subscription').classList.remove('hidden');
        }

        // 支付方式选择
        // var selectedPayment = 'alipay'; // → AppState.selectedPayment

        function selectPaymentMethod(el, method) {
            AppState.selectedPayment = method;
            document.querySelectorAll('.payment-method').forEach(function(btn) {
                btn.classList.remove('border-[#165DFF]', 'bg-[#F2F7FF]');
                btn.classList.add('border-[#E5E6EB]');
                var dot = btn.querySelector('.w-5.h-5');
                if (dot) {
                    dot.classList.remove('border-[#165DFF]');
                    dot.classList.add('border-[#E5E6EB]');
                    var inner = dot.querySelector('.w-2\\.5');
                    if (inner) inner.remove();
                }
            });
            el.classList.remove('border-[#E5E6EB]');
            el.classList.add('border-[#165DFF]', 'bg-[#F2F7FF]');
            var dot = el.querySelector('.w-5.h-5');
            if (dot) {
                dot.classList.remove('border-[#E5E6EB]');
                dot.classList.add('border-[#165DFF]');
                var inner = document.createElement('div');
                inner.className = 'w-2.5 h-2.5 rounded-full bg-[#165DFF]';
                dot.appendChild(inner);
            }
        }

        // 支付成功
        function paySuccess() {
            // 获取当前支付信息
            var planEl = document.getElementById('payment-plan-name');
            var amountEl = document.getElementById('payment-total');
            var planName = planEl ? planEl.textContent : '专业版 · 月付';
            var amount = amountEl ? amountEl.textContent : '¥299';
            
            var methodNames = {'alipay': '支付宝', 'wechat': '微信支付', 'unionpay': '银联支付'};
            var methodName = methodNames[AppState.selectedPayment] || '支付宝';
            
            // 填充成功页信息
            document.getElementById('success-plan-info').textContent = planName + ' 已生效';
            document.getElementById('success-plan').textContent = planName;
            document.getElementById('success-amount').textContent = amount;
            document.getElementById('success-payment-method').textContent = methodName;
            
            // 生成订单号和到期时间
            var now = new Date();
            var orderNo = 'LP' + now.getFullYear() + 
                String(now.getMonth()+1).padStart(2,'0') + 
                String(now.getDate()).padStart(2,'0') + '001';
            document.getElementById('success-order-no').textContent = orderNo;
            
            var expiry = new Date(now);
            expiry.setMonth(expiry.getMonth() + 1);
            document.getElementById('success-expiry').textContent = 
                expiry.getFullYear() + '-' + 
                String(expiry.getMonth()+1).padStart(2,'0') + '-' + 
                String(expiry.getDate()).padStart(2,'0');
            
            // 切换视图
            document.querySelectorAll('.view-content').forEach(function(v) {
                v.classList.add('hidden');
            });
            document.getElementById('view-payment-success').classList.remove('hidden');
        }

        // 从支付成功页跳转
        function goToSubscription() {
            switchView('subscription');
        }

        function goToWorkstation() {
            switchView('workstation');
        }

        // 跳转到订单记录
        function switchToOrders() {
            var userMenu = document.getElementById('userMenu');
            if (userMenu) userMenu.classList.add('hidden');
            switchView('orders');
        }

        // 跳转到会员中心
        function switchToMemberCenter() {
            var userMenu = document.getElementById('userMenu');
            if (userMenu) userMenu.classList.add('hidden');
            switchView('member-center');
        }

        function goToMemberCenter() {
            switchView('member-center');
        }

        // 跳转到账号设置
        function switchToAccountSettings() {
            var userMenu = document.getElementById('userMenu');
            if (userMenu) userMenu.classList.add('hidden');
            switchView('account-settings');
        }
    // 切换个人资料编辑模式
    // 切换个人资料编辑模式
    function toggleProfileEdit() {
        var display = document.getElementById('profile-display');
        var edit = document.getElementById('profile-edit');
        var btn = document.getElementById('edit-profile-btn');
        
        if (display && edit && btn) {
            var isEditing = !edit.classList.contains('hidden');
            if (isEditing) {
                // 当前是编辑模式 → 切回只读
                cancelProfileEdit();
            } else {
                // 当前是只读模式 → 切到编辑
                display.classList.add('hidden');
                edit.classList.remove('hidden');
                // 隐藏右上角按钮
                btn.classList.add('hidden');
            }
        }
    }

    // 取消编辑，切回只读（不保存更改）
    function cancelProfileEdit() {
        var display = document.getElementById('profile-display');
        var edit = document.getElementById('profile-edit');
        var btn = document.getElementById('edit-profile-btn');
        if (display && edit && btn) {
            edit.classList.add('hidden');
            display.classList.remove('hidden');
            // 显示「修改」按钮
            btn.classList.remove('hidden');
            btn.textContent = '修改';
            btn.className = 'px-5 py-2 text-xs font-semibold rounded-lg border border-[#165DFF] text-[#165DFF] hover:bg-[#E8F3FF] transition-colors';
        }
    }

    // 保存个人资料
    function saveProfile() {
        var name = document.getElementById('profile-name');
        var phone = document.getElementById('profile-phone');
        var email = document.getElementById('profile-email');
        var firm = document.getElementById('profile-firm');
        var license = document.getElementById('profile-license');
        var bio = document.getElementById('profile-bio');
        
        // 校验必填
        if (!name || !name.value.trim()) {
            alert('请输入姓名');
            if (name) name.focus();
            return;
        }
        if (!phone || !phone.value.trim()) {
            alert('请输入手机号');
            if (phone) phone.focus();
            return;
        }
        
        // 手机号格式校验
        var phoneVal = phone.value.trim();
        if (!/^1\d{10}$/.test(phoneVal) && !/^\d{3,4}\*{4}\d{4}$/.test(phoneVal)) {
            if (!confirm('手机号格式异常，是否仍要保存？')) return;
        }
        
        // 邮箱格式校验
        var emailVal = email ? email.value.trim() : '';
        if (emailVal && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailVal)) {
            if (!confirm('邮箱格式不正确，是否仍要保存？')) return;
        }
        
        // 更新只读区域的显示内容
        var displayGrid = document.querySelector('#profile-display .grid.grid-cols-2');
        if (displayGrid) {
            var displayItems = displayGrid.querySelectorAll('div');
            if (displayItems.length >= 6) {
                // 姓名
                var nameP = displayItems[0].querySelector('p.text-sm');
                if (nameP) nameP.textContent = name.value.trim();
                
                // 手机号
                var phoneP = displayItems[1].querySelector('p.text-sm');
                if (phoneP) phoneP.textContent = phone.value.trim();
                
                // 邮箱
                var emailP = displayItems[2].querySelector('p.text-sm');
                if (emailP) emailP.textContent = email.value.trim() || '未设置';
                
                // 律所
                var firmP = displayItems[3].querySelector('p.text-sm');
                if (firmP) firmP.textContent = firm.value.trim() || '未设置';
                
                // 执业证号
                var licenseP = displayItems[4].querySelector('p.text-sm');
                if (licenseP) licenseP.textContent = license.value.trim() || '未设置';
                
                // 专业领域（从编辑区同步标签到只读区）
                var editTags = document.querySelectorAll('#edit-skill-tags .inline-flex');
                var displayTagsContainer = displayItems[5].querySelector('.flex.flex-wrap');
                if (displayTagsContainer && editTags.length > 0) {
                    displayTagsContainer.innerHTML = '';
                    editTags.forEach(function(tag) {
                        var tagText = tag.textContent.replace('×', '').replace('+ 添加', '').trim();
                        if (tagText) {
                            var span = document.createElement('span');
                            span.className = 'inline-flex px-2.5 py-1 rounded-full bg-[#E8F3FF] text-[#165DFF] text-[10px] font-medium';
                            span.textContent = tagText;
                            displayTagsContainer.appendChild(span);
                        }
                    });
                }
            }
        }
        
        // 更新个人简介
        var displayBio = document.querySelector('#profile-display .border-t p.text-sm');
        if (displayBio && bio) {
            displayBio.textContent = bio.value.trim() || '未填写';
        }
        
        // 更新左侧头像下方的名称
        var avatarName = document.querySelector('#profile-display + .flex-shrink-0 p.text-xs, #profile-display').closest('.flex').querySelector('.flex-shrink-0 p.text-xs');
        // 更靠谱：找父级 flex 容器中的左侧 p
        var profileContainer = document.querySelector('#profile-display')?.closest('.flex');
        if (profileContainer) {
            var nameUnderAvatar = profileContainer.querySelector('.flex-shrink-0 p.text-xs');
            if (nameUnderAvatar) nameUnderAvatar.textContent = name.value.trim();
        }
        
        // 显示保存成功提示
        showSaveSuccess('个人资料已保存成功');
        
        // 切回只读模式
        cancelProfileEdit();
    }
    
    // 保存成功提示
    function showSaveSuccess(msg) {
        var existing = document.getElementById('save-toast');
        if (existing) existing.remove();
        
        var toast = document.createElement('div');
        toast.id = 'save-toast';
        toast.className = 'fixed top-4 right-4 z-[999] bg-green-50 border border-green-200 text-green-700 text-sm px-5 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-slide-in';
        toast.innerHTML = '<iconify-icon icon="mdi:check-circle" class="text-green-600 text-lg"></iconify-icon><span>' + msg + '</span><button onclick="this.parentElement.remove()" class="ml-2 text-green-400 hover:text-green-600"><iconify-icon icon="mdi:close" class="text-sm"></iconify-icon></button>';
        document.body.appendChild(toast);
        
        setTimeout(function() {
            if (toast.parentElement) {
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.3s';
                setTimeout(function() { if (toast.parentElement) toast.remove(); }, 300);
            }
        }, 3000);
    }

    // 添加专业领域标签
    function addTagInput(el) {
        var tag = prompt('请输入专业领域名称：');
        if (tag && tag.trim()) {
            var span = document.createElement('span');
            span.className = 'inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#E8F3FF] text-[#165DFF] text-[10px] font-medium';
            span.innerHTML = tag.trim() + ' <button onclick="removeTag(this); autoSaveProfile()" class="hover:text-red-500"><iconify-icon icon="mdi:close" class="text-xs"></iconify-icon></button>';
            el.parentNode.insertBefore(span, el);
        }
    }

    // 头像预览
    // 头像上传处理
    function handleAvatarUpload(event) {
        var file = event.target.files[0];
        if (!file) return;
        
        // 校验文件大小（5MB）
        if (file.size > 5 * 1024 * 1024) {
            showSaveSuccess('头像文件大小不能超过 5MB');
            return;
        }
        
        // 校验文件类型
        var allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            showSaveSuccess('仅支持 JPG、PNG、WebP 格式的图片');
            return;
        }
        
        // 显示上传中状态
        var progress = document.getElementById('avatar-progress-display');
        var success = document.getElementById('avatar-success-display');
        if (progress) progress.classList.remove('hidden');
        if (success) success.classList.add('hidden');
        
        // 模拟上传延迟后显示预览
        setTimeout(function() {
            var reader = new FileReader();
            reader.onload = function(e) {
                var img = document.getElementById('avatar-image-display');
                var icon = document.getElementById('avatar-icon-display');
                var preview = document.getElementById('avatar-preview-display');
                
                if (img && icon && preview) {
                    img.src = e.target.result;
                    img.classList.remove('hidden');
                    icon.style.display = 'none';
                    preview.style.backgroundImage = 'none';
                }
                
                // 显示成功状态
                if (progress) progress.classList.add('hidden');
                if (success) success.classList.remove('hidden');
                
                // 显示保存成功提示
                showSaveSuccess('头像上传成功');
                
                // 3秒后隐藏成功标识
                setTimeout(function() {
                    if (success) success.classList.add('hidden');
                }, 3000);
            };
            reader.readAsDataURL(file);
        }, 800);
    }

    // 删除专业领域标签
    function removeTag(btn) {
        var tag = btn.closest('span');
        if (tag) {
            tag.remove();
        }
    }

    // 添加专业领域标签（增强版）
    function showAddTagDialog(el) {
        var tag = prompt('请输入专业领域名称：\n（如：知识产权、刑事辩护、婚姻家事等）');
        if (tag && tag.trim()) {
            var span = document.createElement('span');
            span.className = 'inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-[#E8F3FF] text-[#165DFF] text-xs font-medium';
            span.innerHTML = tag.trim() + ' <button onclick="removeTag(this); autoSaveProfile()" class="hover:text-red-500 transition-colors"><iconify-icon icon="mdi:close" class="text-xs"></iconify-icon></button>';
            el.parentNode.insertBefore(span, el);
        }
    }

    // 职业认证 - 证件文件上传
    function handleCertUpload(event) {
        var file = event.target.files[0];
        if (!file) return;
        
        if (file.size > 10 * 1024 * 1024) {
            alert('证件文件大小不能超过 10MB');
            return;
        }
        
        var preview = document.getElementById('cert-file-preview');
        var nameEl = document.getElementById('cert-file-name');
        var sizeEl = document.getElementById('cert-file-size');
        
        if (preview && nameEl && sizeEl) {
            nameEl.textContent = file.name;
            var sizeKB = (file.size / 1024).toFixed(1);
            sizeEl.textContent = sizeKB + ' KB';
            preview.classList.remove('hidden');
        }
    }

    // 职业认证 - 移除已上传文件
    function removeCertFile() {
        var preview = document.getElementById('cert-file-preview');
        var upload = document.getElementById('cert-upload');
        if (preview) preview.classList.add('hidden');
        if (upload) upload.value = '';
    }

    // 职业认证 - 提交审核
    function submitCertification() {
        alert('您的律师执业认证申请已提交！\n我们将在 1-3 个工作日内完成审核。\n审核结果将以消息通知您。');
    }

    // 双因素认证切换
    function toggle2FA(checkbox) {
        var status = document.getElementById('2fa-status');
        if (checkbox.checked) {
            if (confirm('开启双因素认证将提高账号安全性。\n\n建议使用 Authenticator App（如 Google Authenticator、Microsoft Authenticator）或短信验证码。\n\n是否继续开启？')) {
                status.textContent = '已开启';
                status.className = 'text-[10px] text-green-600 font-medium';
            } else {
                checkbox.checked = false;
            }
        } else {
            if (confirm('关闭双因素认证将降低账号安全等级，确定要关闭吗？')) {
                status.textContent = '未开启';
                status.className = 'text-[10px] text-[#C9CDD4]';
            } else {
                checkbox.checked = true;
            }
        }
    }

    // 设备管理
    function showDeviceManager() {
        var deviceInfo = 
            '📱 当前登录设备\n' +
            '━━━━━━━━━━━━━━━━━━\n' +
            '1️⃣ Windows PC\n' +
            '   浏览器：Chrome 120.0\n' +
            '   IP：192.168.1.100\n' +
            '   最近活动：现在\n' +
            '   [当前设备]\n\n' +
            '2️⃣ iPhone 15\n' +
            '   系统：iOS 18.0\n' +
            '   IP：192.168.1.101\n' +
            '   最近活动：2 小时前\n' +
            '   [点击移除此设备]';
        alert(deviceInfo);
    }

    // 账号注销确认
    function confirmAccountDeletion() {
        var step1 = confirm('⚠️ 确认要注销账号吗？\n\n注销后：\n· 所有案件数据将被永久清除\n· 所有文书和材料将无法恢复\n· 您的会员权益将立即终止\n\n此操作不可撤销！');
        if (step1) {
            var step2 = prompt('请输入「确认注销」以继续操作：');
            if (step2 === '确认注销') {
                alert('您的账号注销申请已提交。\n系统将在 7 天冷静期后执行注销。\n在此期间重新登录可取消注销。');
            } else {
                alert('输入不正确，注销操作已取消。');
            }
        }
    }

    // ========== 客户管理增强功能 ==========
    // 客户分类切换
    function switchClientTab(el, tab) {
        document.querySelectorAll('#view-client .bg-white.rounded-xl.border.border-\\[\\#E5E6EB\\] .flex.items-center.gap-1 button').forEach(function(btn) {
            if (btn.closest('.flex.items-center.gap-1')) {
                btn.classList.remove('bg-[#165DFF]', 'text-white');
                btn.classList.add('text-[#4E5969]', 'hover:bg-[#F7F8FA]');
            }
        });
        el.classList.remove('text-[#4E5969]', 'hover:bg-[#F7F8FA]');
        el.classList.add('bg-[#165DFF]', 'text-white');
        // 显示对应客户（实际项目中筛选数据）
    }

    // 知识库管理 - 分类切换
    function switchKnowledgeTab(el, type) {
        document.querySelectorAll('#view-knowledge .flex.items-center.gap-1.flex-wrap button').forEach(function(btn) {
            btn.classList.remove('bg-[#165DFF]', 'text-white');
            btn.classList.add('text-[#4E5969]', 'hover:bg-[#F7F8FA]');
        });
        el.classList.remove('text-[#4E5969]', 'hover:bg-[#F7F8FA]');
        el.classList.add('bg-[#165DFF]', 'text-white');
        // 筛选表格行
        var rows = document.querySelectorAll('#view-knowledge tbody tr[data-knowledge-type]');
        var visibleCount = 0;
        rows.forEach(function(tr) {
            var t = tr.getAttribute('data-knowledge-type');
            var match = (type === 'all') || (t === type);
            tr.style.display = match ? '' : 'none';
            if (match) visibleCount++;
        });
    }

    // 打开客户详情
    function openClientDetail(index) {
        var clients = [
            { name: '李明', avatar: '李', grade: 'A 级', gradeClass: '#FFF1F0 text-[#F53F3F]', status: '活跃', phone: '138****1234', cases: '3' },
            { name: '王华', avatar: '王', grade: 'B 级', gradeClass: '#FFF7E6 text-[#FAAD14]', status: '活跃', phone: '139****5678', cases: '2' },
            { name: '某科技有限公司', avatar: '某', grade: 'A 级', gradeClass: '#FFF1F0 text-[#F53F3F]', status: '活跃', phone: '010-8888****', cases: '5' },
            { name: '赵六', avatar: '赵', grade: 'C 级', gradeClass: '#F7F8FA text-[#86909C]', status: '待回访', phone: '136****9012', cases: '1' },
            { name: '张三', avatar: '张', grade: 'C 级', gradeClass: '#F7F8FA text-[#86909C]', status: '静默', phone: '137****3456', cases: '1' }
        ];
        
        var c = clients[index] || clients[0];
        
        document.querySelectorAll('.view-content').forEach(function(v) {
            v.classList.add('hidden');
        });
        
        document.getElementById('view-client-detail').classList.remove('hidden');
        
        // 填充数据
        document.getElementById('client-detail-name').textContent = c.name;
        document.getElementById('client-detail-name-text').textContent = c.name;
        document.getElementById('client-detail-avatar').textContent = c.avatar;
        document.getElementById('client-detail-grade').textContent = c.grade;
        document.getElementById('client-detail-grade').className = 'text-[10px] font-medium px-2 py-0.5 rounded';
        var gradeParts = c.gradeClass.split(' ');
        gradeParts.forEach(function(cls) { if (cls) document.getElementById('client-detail-grade').classList.add(cls); });
        document.getElementById('client-detail-status').textContent = c.status;
        document.getElementById('client-detail-phone').textContent = c.phone;
        document.getElementById('client-detail-cases').textContent = c.cases;
    }

    // 返回客户列表
    function backToClientList() {
        document.querySelectorAll('.view-content').forEach(function(v) {
            v.classList.add('hidden');
        });
        document.getElementById('view-client').classList.remove('hidden');
    }

    // 新建客户弹窗
    function showNewClientModal() {
        document.getElementById('new-client-modal').classList.remove('hidden');
    }

    function closeNewClientModal() {
        document.getElementById('new-client-modal').classList.add('hidden');
    }

    function submitNewClient() {
        showSaveSuccess('客户信息已保存，请完善案件信息');
        closeNewClientModal();
    }

    // 新建客户时利益冲突检索
    function runNewClientConflictCheck() {
        var result = document.getElementById('new-client-conflict-result');
        if (result) {
            result.classList.remove('hidden');
        }
        showSaveSuccess('利益冲突检索完成，未发现冲突');
    }

    // 客户详情页利益冲突审查
    function runConflictCheck() {
        var result = document.getElementById('conflict-result');
        if (result) {
            result.classList.remove('hidden');
        }
        showSaveSuccess('利益冲突审查完成');
    }
    // 跳转到案件列表主页
    function switchToList(viewName, el) {
        // 更新侧边栏选中状态
        document.querySelectorAll('.sidebar-item').forEach(function(item) {
            item.classList.remove('active');
        });
        if (el) el.classList.add('active');

        var targetId = 'view-' + viewName;
        var target = document.getElementById(targetId);
        if (target && !isDevMode) {
            // 视图已存在，直接显示
            document.querySelectorAll('.view-content').forEach(function(v) {
                v.classList.add('hidden');
            });
            target.classList.remove('hidden');
        } else {
            // 视图未加载 / dev 模式下强制刷新: 移除旧 target 后重新 fetch
            if (target) target.remove();
            // 视图未加载，动态加载
            loadView(viewName, function(html) {
                document.getElementById('main-content').insertAdjacentHTML('beforeend', html);
                var newTarget = document.getElementById(targetId);
                if (newTarget) {
                    document.querySelectorAll('.view-content').forEach(function(v) {
                        v.classList.add('hidden');
                    });
                    newTarget.classList.remove('hidden');
                }
            });
        }
    }

    // 打开案件详情（跳转到案件详情页，默认显示案件概览 Tab）
    var currentCaseIndex = -1;
    
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

    // Tab 切换 - 案件详情
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

    // 证据材料标签页切换
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

    // 模板管理 - 标签页切换
    function switchTemplateTab(tabName, btn) {
        document.getElementById('template-tab-personal').classList.add('hidden');
        document.getElementById('template-tab-official').classList.add('hidden');
        document.getElementById('template-tab-' + tabName).classList.remove('hidden');
        document.querySelectorAll('.template-tab').forEach(function(tab) {
            tab.classList.remove('text-[#165DFF]', 'border-[#165DFF]');
            tab.classList.add('text-gray-500', 'border-transparent');
        });
        if (btn) {
            btn.classList.remove('text-gray-500', 'border-transparent');
            btn.classList.add('text-[#165DFF]', 'border-[#165DFF]');
        }
    }

    // 修复 template 视图 DOM 重组: 浏览器把 official tab 内的卡片视图和孤儿卡片飘到主体 div 直接子级
    function fixTemplateViewDOM() {
        var main = document.querySelector('.max-w-7xl.mx-auto.space-y-4');
        if (!main) return;
        var personal = document.getElementById('template-tab-personal');
        var official = document.getElementById('template-tab-official');
        if (!personal || !official) return;
        var personalCardView = personal.querySelector('.template-view-card');
        var officialCardView = official.querySelector('.template-view-card');
        // 备用: official tab 内 template-view-card 飘出时, 找 main 中第一个非 personal 的 template-view-card
        if (!officialCardView) {
            var allCards = document.querySelectorAll('.template-view-card');
            for (var j = 0; j < allCards.length; j++) {
                if (allCards[j] !== personalCardView) {
                    officialCardView = allCards[j];
                    break;
                }
            }
        }
        var orphans = [];
        for (var i = 0; i < main.children.length; i++) {
            var c = main.children[i];
            if (c === personal || c === official) continue;
            if (c.classList && c.classList.contains('fixed')) continue;
            if (c.className && (c.className.indexOf('rounded-xl') !== -1 || c.className.indexOf('template-view-card') !== -1)) {
                orphans.push(c);
            }
        }
        if (!orphans.length) return;
        orphans.forEach(function(el) {
            if (el.classList.contains('template-view-card')) {
                var cards = el.querySelectorAll('[data-template-category]');
                var firstCat = cards[0] ? cards[0].getAttribute('data-template-category') : '';
                if (firstCat === '诉状类' || firstCat === '答辩类' || firstCat === '合同类') {
                    if (personalCardView && el !== personalCardView) {
                        while (el.firstChild) personalCardView.appendChild(el.firstChild);
                        el.parentNode.removeChild(el);
                    }
                } else {
                    if (officialCardView && el !== officialCardView) {
                        while (el.firstChild) officialCardView.appendChild(el.firstChild);
                        el.parentNode.removeChild(el);
                    }
                }
                return;
            }
            var cat = el.getAttribute('data-template-category');
            if (!cat) return;
            if (cat === '诉状类' || cat === '答辩类' || cat === '合同类') {
                if (personalCardView) personalCardView.appendChild(el);
            } else {
                if (officialCardView) officialCardView.appendChild(el);
            }
        });
    }

    // 模板管理 - 列表/卡片视图切换
    function switchTemplateView(viewName, btn) {
        document.querySelectorAll('.template-view-btn').forEach(function(b) {
            b.classList.remove('bg-blue-50', 'text-[#165DFF]');
            b.classList.add('text-gray-500', 'hover:text-gray-700');
        });
        if (btn) {
            btn.classList.add('bg-blue-50', 'text-[#165DFF]');
            btn.classList.remove('text-gray-500', 'hover:text-gray-700');
        }
        // 切换 personal + official 两个 tab 内的视图
        ['personal', 'official'].forEach(function(tab) {
            var listView = document.querySelector('#template-tab-' + tab + ' .template-view-list');
            var cardView = document.querySelector('#template-tab-' + tab + ' .template-view-card');
            if (viewName === 'list') {
                if (listView) listView.classList.remove('hidden');
                if (cardView) cardView.classList.add('hidden');
            } else {
                if (listView) listView.classList.add('hidden');
                if (cardView) cardView.classList.remove('hidden');
            }
        });
        // 切到卡片视图时同步调用官方模板 filter, 让 grid 列数按可见卡片数适配
        if (viewName === 'card' && typeof applyOfficialFilter === 'function') {
            applyOfficialFilter();
        }
    }

    // 上传模板弹窗 (占位)
    function openUploadTemplateModal() {
        var modal = document.getElementById('upload-template-modal');
        if (!modal) return;
        // 同步分类下拉
        var sel = document.getElementById('upload-template-category');
        if (sel) {
            sel.innerHTML = '<option value="">请选择分类</option>';
            var cats = document.querySelectorAll('.category-item');
            cats.forEach(function(item) {
                var name = item.getAttribute('data-category');
                var opt = document.createElement('option');
                opt.value = name;
                opt.textContent = name;
                sel.appendChild(opt);
            });
        }
        // 重置表单
        var nameInput = document.getElementById('upload-template-name');
        if (nameInput) nameInput.value = '';
        var fileInput = document.getElementById('upload-template-file');
        if (fileInput) fileInput.value = '';
        var filename = document.getElementById('upload-template-filename');
        if (filename) filename.textContent = '点击或拖拽文件到此处';
        modal.classList.remove('hidden');
    }

    function closeUploadTemplateModal() {
        var modal = document.getElementById('upload-template-modal');
        if (modal) modal.classList.add('hidden');
    }

    function submitUploadTemplate() {
        var name = (document.getElementById('upload-template-name').value || '').trim();
        var category = document.getElementById('upload-template-category').value;
        var fileInput = document.getElementById('upload-template-file');
        var file = fileInput.files[0];
        if (!name) { showToast('请输入模板名称'); return; }
        if (!category) { showToast('请选择分类'); return; }
        if (!file) { showToast('请选择文件'); return; }
        // 格式校验
        var ext = file.name.split('.').pop().toLowerCase();
        if (['docx', 'pdf', 'txt'].indexOf(ext) < 0) {
            showToast('仅支持 .docx / .pdf / .txt 格式');
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            showToast('文件大小不能超过 10MB');
            return;
        }
        // 取文件大小
        var sizeKb = Math.round(file.size / 1024);
        var sizeText = sizeKb < 1024 ? sizeKb + ' KB' : (sizeKb / 1024).toFixed(1) + ' MB';
        // 选中的格式 radio
        var fmtRadio = document.querySelector('input[name="upload-template-format"]:checked');
        var fmt = fmtRadio ? fmtRadio.value : ext;
        // 类型徽章颜色 (按分类)
        var colorCls = {
            '诉状类': 'bg-blue-100 text-blue-700',
            '答辩类': 'bg-purple-100 text-purple-700',
            '合同类': 'bg-orange-100 text-orange-700',
            '申请类': 'bg-green-100 text-green-700'
        };
        var cls = colorCls[category] || 'bg-gray-100 text-gray-600';
        // 当前用户 (mock 张律师)
        var creator = '张律师';
        var now = new Date();
        var pad = function(n) { return n < 10 ? '0' + n : '' + n; };
        var timeStr = now.getFullYear() + '-' + pad(now.getMonth()+1) + '-' + pad(now.getDate()) + ' ' + pad(now.getHours()) + ':' + pad(now.getMinutes());
        // 创建新行, 插到 tbody 顶部
        var tbody = document.querySelector('#template-tab-personal tbody');
        if (!tbody) { showToast('模板列表不存在'); return; }
        var tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-50 group';
        tr.setAttribute('data-template-category', category);
        tr.innerHTML = '<td class="py-3 px-5">' +
            '<div class="flex items-center gap-2">' +
            '<iconify-icon class="text-base text-[#165DFF]" icon="mdi:file-document-outline"></iconify-icon>' +
            '<span class="text-sm text-gray-800 font-medium">' + name.replace(/</g, '&lt;') + '</span>' +
            '<span class="text-[10px] text-gray-400">(' + sizeText + ')</span>' +
            '</div>' +
            '</td>' +
            '<td class="py-3 px-5"><span class="text-[10px] ' + cls + ' px-1.5 py-0.5 rounded font-medium">' + category + '</span></td>' +
            '<td class="py-3 px-5 text-xs text-gray-600">' + creator + '</td>' +
            '<td class="py-3 px-5 text-xs text-gray-500">' + timeStr + '</td>' +
            '<td class="py-3 px-5 text-center">' +
            '<div class="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">' +
            '<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded">使用</button>' +
            '<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded">编辑</button>' +
            '<button class="text-xs text-red-500 hover:bg-red-50 px-2 py-1 rounded" onclick="deletePersonalTemplate(this)">删除</button>' +
            '</div>' +
            '</td>';
        tbody.insertBefore(tr, tbody.firstChild);
        // 同时添加到卡片视图
        var cardContainer = document.querySelector('#template-tab-personal .template-view-card');
        if (cardContainer) {
            var card = document.createElement('div');
            card.className = 'bg-white border border-[#E5E6EB] rounded-xl p-4 hover:shadow-md hover:border-[#165DFF] transition-all cursor-pointer group';
            card.setAttribute('data-template-category', category);
            card.innerHTML = '<div class="flex items-start justify-between mb-3">' +
                '<iconify-icon class="text-2xl text-[#165DFF]" icon="mdi:file-document-outline"></iconify-icon>' +
                '<span class="text-[10px] ' + cls + ' px-1.5 py-0.5 rounded font-medium">' + category + '</span>' +
                '</div>' +
                '<h4 class="text-sm font-bold text-gray-800 mb-2 group-hover:text-[#165DFF]">' + name.replace(/</g, '&lt;') + '</h4>' +
                '<div class="flex items-center justify-between text-[10px] text-gray-400 pt-3 border-t border-gray-100">' +
                '<span class="flex items-center gap-1"><iconify-icon icon="mdi:account-outline"></iconify-icon>' + creator + '</span>' +
                '<span>' + timeStr + '</span>' +
                '</div>';
            cardContainer.insertBefore(card, cardContainer.firstChild);
        }
        // 更新"全部"标签数字
        if (typeof updateAllCategoryCount === 'function') updateAllCategoryCount();
        // 更新对应分类标签数字
        var tabBtn = document.querySelector('.personal-category-tab[data-category="' + category + '"]');
        if (tabBtn) {
            var m = tabBtn.textContent.match(/\((\d+)\)/);
            if (m) tabBtn.textContent = category + ' (' + (parseInt(m[1]) + 1) + ')';
        }
        // 更新弹窗内分类数
        var item = document.querySelector('.category-item[data-category="' + category + '"]');
        if (item) {
            var countSpan = item.querySelector('span.text-\\[10px\\]');
            if (countSpan) {
                var cm = countSpan.textContent.match(/\d+/);
                if (cm) countSpan.textContent = '(' + (parseInt(cm[0]) + 1) + ' 个模板)';
            }
        }
        // 更新标题栏"共 N 个"数字
        var headerCount = document.querySelector('.template-view-header-count');
        if (headerCount) {
            var hm = headerCount.textContent.match(/\d+/);
            if (hm) headerCount.textContent = '共 ' + (parseInt(hm[0]) + 1) + ' 个';
        }
        closeUploadTemplateModal();
        showToast('模板「' + name + '」已上传');
    }

    // 删除个人模板 (客户端模拟)
    function deletePersonalTemplate(btn) {
        if (!confirm('确定删除该模板?')) return;
        var tr = btn.closest('tr');
        if (!tr) return;
        var category = tr.getAttribute('data-template-category');
        var rowName = tr.querySelector('td:first-child span') ? tr.querySelector('td:first-child span').textContent.trim() : '';
        tr.remove();
        // 同步删除卡片视图中的对应卡片
        document.querySelectorAll('#template-tab-personal .template-view-card > div[data-template-category]').forEach(function(card) {
            var cardName = card.querySelector('h4') ? card.querySelector('h4').textContent.trim() : '';
            if (card.getAttribute('data-template-category') === category && (rowName === '' || cardName === rowName || cardName.indexOf(rowName.split(' (')[0]) === 0)) {
                card.remove();
            }
        });
        if (typeof updateAllCategoryCount === 'function') updateAllCategoryCount();
        if (category) {
            var tabBtn = document.querySelector('.personal-category-tab[data-category="' + category + '"]');
            if (tabBtn) {
                var m = tabBtn.textContent.match(/\((\d+)\)/);
                if (m) {
                    var n = Math.max(0, parseInt(m[1]) - 1);
                    tabBtn.textContent = category + ' (' + n + ')';
                }
            }
        }
        showToast('已删除');
    }

    // 分类管理 - 弹窗控制
    function openCategoryManageModal() {
        var modal = document.getElementById('category-manage-modal');
        if (modal) modal.classList.remove('hidden');
    }
    function closeCategoryManageModal() {
        var modal = document.getElementById('category-manage-modal');
        if (modal) modal.classList.add('hidden');
    }

    // 分类管理 - 新增/删除 (客户端模拟, 不持久化)
    function addCategory() {
        var input = document.getElementById('new-category-input');
        var name = (input.value || '').trim();
        if (!name) {
            showToast('请输入分类名称');
            return;
        }
        if (name.length > 20) {
            showToast('分类名称不能超过 20 个字符');
            return;
        }
        // 检查重名
        var exists = Array.from(document.querySelectorAll('.category-item')).some(function(el) {
            return el.getAttribute('data-category') === name;
        });
        if (exists) {
            showToast('该分类已存在');
            return;
        }
        // 创建新分类项 (弹窗内)
        var list = document.getElementById('category-list');
        var countEl = document.getElementById('category-list-count');
        var div = document.createElement('div');
        div.className = 'category-item flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100';
        div.setAttribute('data-category', name);
        div.innerHTML = '<div class="flex items-center gap-3">' +
            '<iconify-icon class="text-base text-[#165DFF]" icon="mdi:folder-outline"></iconify-icon>' +
            '<span class="text-sm text-gray-800 font-medium">' + name + '</span>' +
            '<span class="text-[10px] text-gray-400">(0 个模板)</span>' +
            '</div>' +
            '<button class="text-xs text-red-500 hover:bg-red-50 px-2 py-1 rounded delete-category-btn" onclick="deleteCategory(\'' + name.replace(/'/g, "\\'") + '\')">' +
            '<iconify-icon icon="mdi:trash-can-outline"></iconify-icon>删除</button>';
        list.appendChild(div);
        // 同步添加到个人模板标签栏
        var tabs = document.getElementById('personal-category-tabs');
        if (tabs) {
            var tabBtn = document.createElement('button');
            tabBtn.className = 'personal-category-tab text-xs px-3 py-1 rounded-full bg-white border border-gray-200 text-gray-600 hover:border-[#165DFF] hover:text-[#165DFF]';
            tabBtn.setAttribute('data-category', name);
            tabBtn.setAttribute('onclick', "filterPersonalByCategory('" + name.replace(/'/g, "\\'") + "', this)");
            tabBtn.textContent = name + ' (0)';
            tabs.appendChild(tabBtn);
        }
        // 同步更新"全部"标签的数字
        updateAllCategoryCount();
        input.value = '';
        // 更新计数
        var total = list.querySelectorAll('.category-item').length;
        if (countEl) countEl.textContent = '共 ' + total + ' 个分类';
        showToast('分类「' + name + '」已添加');
    }

    // 按时间排序个人模板 (desc/asc 切换)
    var _personalSortOrder = null; // null = 默认顺序, 'desc' = 最新的在前面, 'asc' = 最旧的在前
    function sortPersonalTemplates(btn) {
        // 切换顺序
        if (_personalSortOrder === 'desc') {
            _personalSortOrder = 'asc';
        } else {
            _personalSortOrder = 'desc';
        }
        var order = _personalSortOrder;
        // 解析行的时间字符串 (第 4 列 td)
        function parseTime(tr) {
            var tds = tr.querySelectorAll('td');
            var timeStr = tds.length >= 4 ? (tds[3].textContent || '').trim() : '';
            var d = new Date(timeStr.replace(/-/g, '/'));
            return isNaN(d.getTime()) ? 0 : d.getTime();
        }
        // 排序 tbody
        var tbody = document.querySelector('#template-tab-personal tbody');
        if (tbody) {
            var rows = Array.from(tbody.querySelectorAll('tr[data-template-category]'));
            rows.sort(function(a, b) {
                var ta = parseTime(a), tb = parseTime(b);
                return order === 'desc' ? (tb - ta) : (ta - tb);
            });
            rows.forEach(function(r) { tbody.appendChild(r); });
        }
        // 同步排序卡片视图 (按卡片底部时间排序)
        var cardContainer = document.querySelector('#template-tab-personal .template-view-card');
        if (cardContainer) {
            var cards = Array.from(cardContainer.querySelectorAll('div[data-template-category]'));
            cards.sort(function(a, b) {
                var ta = 0, tb = 0;
                var timeSpans = a.querySelectorAll('span');
                var taStr = timeSpans.length ? timeSpans[timeSpans.length - 1].textContent.trim() : '';
                var dA = new Date(taStr.replace(/-/g, '/'));
                ta = isNaN(dA.getTime()) ? 0 : dA.getTime();
                timeSpans = b.querySelectorAll('span');
                var tbStr = timeSpans.length ? timeSpans[timeSpans.length - 1].textContent.trim() : '';
                var dB = new Date(tbStr.replace(/-/g, '/'));
                tb = isNaN(dB.getTime()) ? 0 : dB.getTime();
                return order === 'desc' ? (tb - ta) : (ta - tb);
            });
            cards.forEach(function(c) { cardContainer.appendChild(c); });
        }
        // 按钮视觉反馈
        if (btn) {
            document.querySelectorAll('.sort-btn').forEach(function(b) {
                b.classList.remove('bg-[#165DFF]', 'text-white');
                b.classList.add('text-[#165DFF]', 'bg-[#EEF3FF]');
            });
            btn.classList.add('bg-[#165DFF]', 'text-white');
            btn.classList.remove('text-[#165DFF]', 'bg-[#EEF3FF]');
            // 更新图标方向
            var icon = btn.querySelector('iconify-icon');
            if (icon) {
                icon.setAttribute('icon', order === 'desc' ? 'mdi:sort-variant' : 'mdi:sort-reverse-variant');
            }
        }
        // 重新应用当前分类筛选 (排序后保持筛选)
        var activeTab = document.querySelector('.personal-category-tab.bg-\\[\\#165DFF\\]');
        if (activeTab) {
            var cat = activeTab.getAttribute('data-category');
            filterPersonalByCategory(cat, activeTab);
        }
        showToast(order === 'desc' ? '已按时间降序排列' : '已按时间升序排列');
    }

    // 同步更新"全部"标签的数字
    function updateAllCategoryCount() {
        var allTab = document.querySelector('.personal-category-tab[data-category="all"]');
        if (allTab) {
            var total = document.querySelectorAll('#template-tab-personal tbody tr[data-template-category]').length;
            allTab.textContent = '全部 (' + total + ')';
        }
    }

    // 按分类筛选个人模板
    function filterPersonalByCategory(category, btn) {
        // 更新 active 样式
        document.querySelectorAll('.personal-category-tab').forEach(function(b) {
            b.classList.remove('bg-[#165DFF]', 'text-white', 'font-medium');
            b.classList.add('bg-white', 'border', 'border-gray-200', 'text-gray-600');
        });
        if (btn) {
            btn.classList.add('bg-[#165DFF]', 'text-white', 'font-medium');
            btn.classList.remove('bg-white', 'border', 'border-gray-200', 'text-gray-600');
        }
        // 筛选列表行
        document.querySelectorAll('#template-tab-personal tbody tr[data-template-category]').forEach(function(tr) {
            if (category === 'all' || tr.getAttribute('data-template-category') === category) {
                tr.style.display = '';
            } else {
                tr.style.display = 'none';
            }
        });
        // 筛选卡片
        document.querySelectorAll('#template-tab-personal .template-view-card > div[data-template-category]').forEach(function(card) {
            if (category === 'all' || card.getAttribute('data-template-category') === category) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    }

    // 官方模板: 一级分类筛选 + 二级文书类型筛选 + 搜索
    var _officialCategory = 'all';
    var _officialType = 'all';
    var _officialSearch = '';

    function filterOfficialByCategory(category, btn) {
        _officialCategory = category;
        // 更新一级 active 样式
        var officialTabs = document.querySelectorAll('.official-category-tab');
        officialTabs.forEach(function(b) {
            b.classList.remove('bg-[#165DFF]', 'text-white', 'border-[#165DFF]', 'hover:bg-[#0E4AD8]');
            b.classList.add('bg-white', 'border-gray-200', 'text-gray-600', 'hover:bg-gray-50');
        });
        if (btn) {
            btn.classList.add('bg-[#165DFF]', 'text-white', 'border-[#165DFF]', 'hover:bg-[#0E4AD8]');
            btn.classList.remove('bg-white', 'border-gray-200', 'text-gray-600', 'hover:bg-gray-50');
        }
        // 二级筛选: 执行/其他 不显示起诉/答辩类型
        var typeFilter = document.getElementById('official-type-filter');
        if (typeFilter) {
            if (category === '执行' || category === '其他') {
                typeFilter.classList.add('hidden');
            } else {
                typeFilter.classList.remove('hidden');
            }
        }
        // 切到「执行/其他」时强制 type 回到 all
        if (category === '执行' || category === '其他') {
            _officialType = 'all';
            filterOfficialByType('all', document.querySelector('.official-type-tab[data-type="all"]'));
            return;
        }
        applyOfficialFilter();
    }

    function filterOfficialByType(type, btn) {
        _officialType = type;
        // 更新二级 active 样式
        document.querySelectorAll('.official-type-tab').forEach(function(b) {
            b.classList.remove('bg-[#165DFF]', 'text-white', 'border-[#165DFF]', 'hover:bg-[#0E4AD8]');
            b.classList.add('bg-white', 'border-gray-200', 'text-gray-600', 'hover:bg-gray-50');
        });
        if (btn) {
            btn.classList.add('bg-[#165DFF]', 'text-white', 'border-[#165DFF]', 'hover:bg-[#0E4AD8]');
            btn.classList.remove('bg-white', 'border-gray-200', 'text-gray-600', 'hover:bg-gray-50');
        }
        applyOfficialFilter();
    }

    function applyOfficialFilter() {
        // 读取搜索词
        var searchEl = document.getElementById('official-search');
        if (searchEl) _officialSearch = searchEl.value.trim().toLowerCase();
        // 清除按钮显隐
        var clearEl = document.getElementById('official-search-clear');
        if (clearEl) {
            if (_officialSearch) { clearEl.classList.remove('hidden'); }
            else { clearEl.classList.add('hidden'); }
        }
        // 双重过滤: cat + type + search
        var rows = document.querySelectorAll('#template-tab-official tbody tr[data-template-category]');
        rows.forEach(function(tr) {
            var cat = tr.getAttribute('data-template-category');
            var typ = tr.getAttribute('data-template-type');
            var title = (tr.querySelector('td:first-child') ? tr.querySelector('td:first-child').textContent : '').toLowerCase();
            var catMatch = _officialCategory === 'all' || cat === _officialCategory;
            var typeMatch = _officialType === 'all' || typ === _officialType;
            var searchMatch = !_officialSearch || title.indexOf(_officialSearch) > -1;
            tr.style.display = (catMatch && typeMatch && searchMatch) ? '' : 'none';
        });
        var cards = document.querySelectorAll('#template-tab-official .template-view-card > div[data-template-category]');
        var visibleCount = 0;
        cards.forEach(function(card) {
            var cat = card.getAttribute('data-template-category');
            var typ = card.getAttribute('data-template-type');
            var titleEl = card.querySelector('h4');
            var title = titleEl ? titleEl.textContent.toLowerCase() : '';
            var catMatch = _officialCategory === 'all' || cat === _officialCategory;
            var typeMatch = _officialType === 'all' || typ === _officialType;
            var searchMatch = !_officialSearch || title.indexOf(_officialSearch) > -1;
            var visible = catMatch && typeMatch && searchMatch;
            card.style.display = visible ? '' : 'none';
            if (visible) visibleCount++;
        });
        // 动态调整 grid 列数: 1-2 张用 2 列, 3-4 张用 3 列, 5+ 张用 4 列
        var grid = document.getElementById('official-card-grid');
        if (grid) {
            var cols = visibleCount === 0 ? 4 : visibleCount <= 2 ? 2 : visibleCount <= 4 ? 3 : 4;
            grid.style.gridTemplateColumns = 'repeat(' + cols + ', minmax(0, 1fr))';
        }
        // 0 张时显示空状态
        var emptyEl = document.getElementById('official-card-empty');
        if (emptyEl) {
            if (visibleCount === 0) {
                emptyEl.classList.remove('hidden');
                emptyEl.style.display = 'block';
            } else {
                emptyEl.classList.add('hidden');
                emptyEl.style.display = 'none';
            }
        }
        // 底部统计: 当前命中数
        var countEl = document.getElementById('official-card-count');
        if (countEl) countEl.textContent = visibleCount;
        var totalEl = document.getElementById('official-card-total');
        if (totalEl) totalEl.textContent = cards.length;
    }

    // 清除搜索
    function clearOfficialSearch() {
        var searchEl = document.getElementById('official-search');
        if (searchEl) searchEl.value = '';
        applyOfficialFilter();
    }

    // 官方模板卡片预览 (占位)
    function previewOfficialTemplate(cardEl) {
        var titleEl = cardEl.querySelector('h4');
        var title = titleEl ? titleEl.textContent.trim() : '未命名模板';
        var cat = cardEl.dataset.templateCategory || '';
        var typ = cardEl.dataset.templateType || '';
        if (typeof showToast === 'function') {
            showToast('预览「' + title + '」(分类: ' + cat + ' · 类型: ' + typ + ')');
        } else {
            alert('预览「' + title + '」(分类: ' + cat + ' · 类型: ' + typ + ')');
        }
    }

    function deleteCategory(name) {
        // 检查该分类下是否还有模板 (在个人模板表格中)
        var rows = document.querySelectorAll('#template-tab-personal tbody tr');
        var hasTemplate = Array.from(rows).some(function(tr) {
            var badge = tr.querySelector('td:nth-child(2) span');
            return badge && badge.textContent.trim() === name;
        });
        if (hasTemplate) {
            showToast('该分类下还有模板, 请先删除模板');
            return;
        }
        if (!confirm('确定删除分类「' + name + '」?')) return;
        var item = document.querySelector('.category-item[data-category="' + name + '"]');
        if (item) item.remove();
        // 同步移除个人模板标签栏按钮
        var tabBtn = document.querySelector('.personal-category-tab[data-category="' + name + '"]');
        if (tabBtn) tabBtn.remove();
        var countEl = document.getElementById('category-list-count');
        var list = document.getElementById('category-list');
        if (countEl && list) {
            var total = list.querySelectorAll('.category-item').length;
            countEl.textContent = '共 ' + total + ' 个分类';
        }
        showToast('分类「' + name + '」已删除');
    }

    // 手动创建证据目录 - 打开模态框
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

    // 加载证据概览文件列表供选择
    var catalogSelectedFiles = [];
    
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

    // 切换文件选择状态
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

    // 更新已选文件数量显示
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

    // 关闭证据目录模态框
    function closeAddEvidenceCatalogModal() {
        var modal = document.getElementById('add-evidence-catalog-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    // 提交证据目录
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

    // 编辑证据目录项
    var editingCatalogRow = null;
    
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

    // 覆盖提交函数以支持编辑模式
    var originalSubmitEvidenceCatalog = submitEvidenceCatalog;
    submitEvidenceCatalog = function() {
        if (editingCatalogRow) {
            // 编辑模式
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
            
            // 更新 data-* 属性
            editingCatalogRow.dataset.number = number || '';
            editingCatalogRow.dataset.type = type;
            editingCatalogRow.dataset.name = name;
            editingCatalogRow.dataset.description = description || '';
            editingCatalogRow.dataset.pages = pages || '';
            
            // 更新可视内容
            var numDiv = editingCatalogRow.querySelector('[data-catalog-number]');
            if (numDiv) numDiv.textContent = number || '';
            
            var typeSpan = editingCatalogRow.querySelector('[data-catalog-type]');
            if (typeSpan) {
                typeSpan.className = 'text-[10px] ' + typeClass + ' px-1.5 py-0.5 rounded';
                typeSpan.textContent = type;
            }
            
            var nameSpan = editingCatalogRow.querySelector('[data-catalog-name]');
            if (nameSpan) {
                nameSpan.textContent = name;
                nameSpan.setAttribute('title', name);
            }
            
            var descEl = editingCatalogRow.querySelector('[data-catalog-description]');
            if (descEl) descEl.textContent = description || '-';
            
            var pagesEl = editingCatalogRow.querySelector('[data-catalog-pages]');
            if (pagesEl) pagesEl.textContent = pages || '-';
            
            // 保存关联文件到data属性
            if (catalogSelectedFiles.length > 0) {
                editingCatalogRow.setAttribute('data-linked-files', JSON.stringify(catalogSelectedFiles));
            } else {
                editingCatalogRow.removeAttribute('data-linked-files');
            }
            
            editingCatalogRow = null;
            closeAddEvidenceCatalogModal();
            showToast('证据目录已更新');
        } else {
            // 新增模式 - 调用原函数
            originalSubmitEvidenceCatalog();
        }
    };

    // 关闭模态框时重置编辑状态
    var originalCloseAddEvidenceCatalogModal = closeAddEvidenceCatalogModal;
    closeAddEvidenceCatalogModal = function() {
        editingCatalogRow = null;
        var modal = document.getElementById('add-evidence-catalog-modal');
        if (modal) {
            var modalTitle = modal.querySelector('h3');
            if (modalTitle) modalTitle.textContent = '手动创建证据目录';
            var submitBtn = modal.querySelector('[onclick="submitEvidenceCatalog()"]');
            if (submitBtn) submitBtn.textContent = '添加';
        }
        originalCloseAddEvidenceCatalogModal();
    };

    // 删除证据目录项
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

    // AI创建证据目录
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

    // 时间线相关函数
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

    // 证件管理相关函数
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

    // 委托合同相关函数
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

    // 证据材料相关函数
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

    // 文书管理相关函数（授权委托书、判决书/调解书、其他文书通用）
    var currentDocumentType = '';

    var documentTypeMap = {
        'power-attorney': { title: '上传授权委托书', listId: 'power-attorney-list', toast: '授权委托书已上传', deleteToast: '授权委托书已删除', subText: '' },
        'judgment': { title: '上传判决书/调解书', listId: 'judgment-list', toast: '文书已上传', deleteToast: '文书已删除', subText: '判决文书' },
        'other': { title: '上传其他文书', listId: 'other-doc-list', toast: '文书已上传', deleteToast: '文书已删除', subText: '其他' }
    };

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

    // AI 侧边面板子标签切换
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

    // 证据目录 AI 面板切换 (3 tab: 完整性/证明对象/法条)
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


    // 打开智能卷宗分析
    function openCaseAnalysis() {
        document.querySelectorAll('.view-content').forEach(function(v) {
            v.classList.add('hidden');
        });
        var analysisView = document.getElementById('view-case-analysis');
        if (analysisView) analysisView.classList.remove('hidden');
    }

    // 从卷宗分析/日程管理返回案件列表
    function backToCaseList() {
        document.querySelectorAll('.view-content').forEach(function(v) {
            v.classList.add('hidden');
        });
        var listView = document.getElementById('view-case-list');
        if (listView) listView.classList.remove('hidden');
    }

    // 打开日程管理
    function openScheduleCalendar() {
        document.querySelectorAll('.view-content').forEach(function(v) {
            v.classList.add('hidden');
        });
        var calView = document.getElementById('view-schedule-calendar');
        if (calView) calView.classList.remove('hidden');
        // 标记日程冲突
        setTimeout(function() { markCalendarConflicts(); checkCourtConflicts(); }, 50);
    }

    // 标记日历中的冲突日程
    function markCalendarConflicts() {
        var calDates = document.querySelectorAll('#view-schedule-calendar .grid.grid-cols-7 .py-3');
        calDates.forEach(function(cell) {
            // 清除旧的标记
            var oldConflict = cell.querySelector('.schedule-conflict-marker');
            if (oldConflict) oldConflict.remove();
            var oldRedDot = cell.querySelector('.schedule-conflict-red');
            if (oldRedDot) oldRedDot.remove();
            var oldCourt = cell.querySelector('.court-schedule-marker');
            if (oldCourt) oldCourt.remove();
        });

        // 按日期分组日程
        var dateGroups = {};
        scheduleData.forEach(function(item) {
            if (!dateGroups[item.date]) dateGroups[item.date] = [];
            dateGroups[item.date].push(item);
        });

        // 为开庭日程添加特殊标记（红色外边框）
        scheduleData.forEach(function(item) {
            if (item.type !== '开庭') return;
            var dayNum = parseInt(item.date.split('-')[2]);
            calDates.forEach(function(cell) {
                var cellText = cell.textContent.trim();
                var cellDay = parseInt(cellText);
                if (cellDay === dayNum) {
                    // 添加开庭标记：红色小徽章
                    if (!cell.querySelector('.court-schedule-marker')) {
                        var courtMarker = document.createElement('span');
                        courtMarker.className = 'court-schedule-marker text-[8px] text-red-600 font-medium block leading-none mt-0.5';
                        courtMarker.textContent = '开庭';
                        cell.appendChild(courtMarker);
                    }
                }
            });
        });

        // 对每组的日程检查时间重叠
        Object.keys(dateGroups).forEach(function(dateKey) {
            var items = dateGroups[dateKey];
            var hasConflict = false;
            for (var i = 0; i < items.length && !hasConflict; i++) {
                for (var j = i + 1; j < items.length && !hasConflict; j++) {
                    if (items[i].time < items[j].endTime && items[j].time < items[i].endTime) {
                        hasConflict = true;
                    }
                }
            }
            if (!hasConflict) return;

            // 对应到日历单元格：从日期字符串提取日数
            var dayNum = parseInt(dateKey.split('-')[2]);
            calDates.forEach(function(cell) {
                var cellText = cell.textContent.trim();
                var cellDay = parseInt(cellText);
                if (cellDay === dayNum) {
                    var conflictMarker = document.createElement('span');
                    conflictMarker.className = 'schedule-conflict-red w-1.5 h-1.5 rounded-full bg-red-500 inline-block mx-auto mt-0.5';
                    // 移除原有指示点（蓝色/红色），只标记冲突
                    var existingDots = cell.querySelectorAll('.rounded-full');
                    existingDots.forEach(function(d) {
                        if (!d.classList.contains('schedule-conflict-red')) {
                            d.style.display = 'none';
                        }
                    });
                    cell.appendChild(conflictMarker);
                }
            });
        });
    }

    // 字段校验（必填）
    function validateField(el, msg) {
        if (!el.value.trim()) {
            el.classList.add('border-red-400', 'bg-[#FFF0F0]');
            el.classList.remove('border-[#E5E6EB]');
            var errorEl = el.parentNode.querySelector('.field-error');
            if (!errorEl) {
                errorEl = document.createElement('p');
                errorEl.className = 'field-error text-[10px] text-red-400 mt-1';
                errorEl.textContent = msg;
                el.parentNode.appendChild(errorEl);
            }
        } else {
            el.classList.remove('border-red-400', 'bg-[#FFF0F0]');
            el.classList.add('border-[#E5E6EB]');
            var errorEl = el.parentNode.querySelector('.field-error');
            if (errorEl) errorEl.remove();
        }
    }

    // 邮箱格式校验
    function validateEmail(el) {
        var val = el.value.trim();
        if (val && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
            el.classList.add('border-[#FAAD14]', 'bg-[#FFF7E6]');
            el.classList.remove('border-[#E5E6EB]');
            var errorEl = el.parentNode.querySelector('.field-error');
            if (!errorEl) {
                errorEl = document.createElement('p');
                errorEl.className = 'field-error text-[10px] text-[#FAAD14] mt-1';
                errorEl.textContent = '邮箱格式不正确';
                el.parentNode.appendChild(errorEl);
            }
        } else {
            el.classList.remove('border-[#FAAD14]', 'bg-[#FFF7E6]');
            el.classList.add('border-[#E5E6EB]');
            var errorEl = el.parentNode.querySelector('.field-error');
            if (errorEl) errorEl.remove();
        }
    }

    // 自动保存（防抖）
    // var autoSaveTimer = null;

    function autoSaveProfile() {
        if (AppState.autoSaveTimer) clearTimeout(AppState.autoSaveTimer);

        var saveBtn = document.getElementById('profile-save-btn');
        var saveText = document.getElementById('save-btn-text');
        var saveSpinner = document.getElementById('save-btn-spinner');
        if (saveBtn) {
            saveBtn.classList.remove('bg-[#165DFF]');
            saveBtn.classList.add('bg-[#4080FF]', 'cursor-default', 'opacity-80');
        }
        if (saveText) saveText.textContent = '保存中...';
        if (saveSpinner) saveSpinner.classList.remove('hidden');

        AppState.autoSaveTimer = setTimeout(function() {
            if (saveBtn) {
                saveBtn.classList.remove('bg-[#4080FF]', 'cursor-default', 'opacity-80');
                saveBtn.classList.add('bg-[#165DFF]');
            }
            if (saveText) saveText.textContent = '已保存';
            if (saveSpinner) saveSpinner.classList.add('hidden');

            setTimeout(function() {
                if (saveText && saveText.textContent === '已保存') {
                    saveText.textContent = '保存';
                }
            }, 2000);
        }, 1500);
    }

    // 保存通知设置
    function saveNotificationSettings() {
        var toggles = document.querySelectorAll('.notif-toggle');
        var enabled = [];
        var disabled = [];
        toggles.forEach(function(t, i) {
            if (t.checked) enabled.push(i);
            else disabled.push(i);
        });
        showSaveSuccess('通知设置已保存');
    }

    // 绑定第三方账号
    function bindAccount(name) {
        showSaveSuccess('正在跳转至' + name + '授权页面...');
    }

    // 解绑第三方账号
    function unbindAccount(name) {
        if (confirm('确定要解绑' + name + '吗？解绑后可能影响相关功能使用。')) {
            showSaveSuccess(name + '已解绑');
        }
    }

    // ===== 日程冲突检测（模拟数据） =====
    const scheduleData = [
        { id: 1, title: '李明诉XX公司买卖合同纠纷开庭', date: getTodayDate(), time: '09:00', endTime: '11:00', type: '开庭', location: '朝阳区人民法院 第3法庭' },
        { id: 2, title: '王华借贷纠纷 - 策略讨论', date: getTodayDate(), time: '14:00', endTime: '15:30', type: '会议', location: '线上会议' },
        { id: 3, title: '提交张三合同纠纷补充证据', date: getTodayDate(), time: '16:00', endTime: '16:30', type: '待办', location: '' },
        { id: 4, title: '律所月度合伙人会议', date: getTodayDate(), time: '10:30', endTime: '11:30', type: '其他', location: '大会议室' },
        { id: 5, title: '某科技公司股权纠纷二审开庭', date: getTodayDate(), time: '15:00', endTime: '17:00', type: '开庭', location: '北京市高级人民法院 第8法庭' },
        { id: 6, title: '赵六劳动争议仲裁开庭', date: getFutureDate(1), time: '09:00', endTime: '12:00', type: '开庭', location: '朝阳区劳动仲裁委' },
        { id: 7, title: '张三合同纠纷证据交换', date: getFutureDate(2), time: '14:00', endTime: '16:00', type: '开庭', location: '海淀区人民法院' },
    ];

    function getTodayDate() {
        const d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
    }

    function getFutureDate(days) {
        const d = new Date();
        d.setDate(d.getDate() + days);
        return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
    }

    function checkScheduleConflict(date, time) {
        if (!date || !time) return null;
        const conflicts = scheduleData.filter(item => {
            if (item.date !== date) return false;
            if (time >= item.time && time < item.endTime) return true;
            return false;
        });
        return conflicts.length > 0 ? conflicts : null;
    }

    function checkAndShowConflict() {
        const date = document.getElementById('sched-date').value;
        const time = document.getElementById('sched-time').value;
        const warningEl = document.getElementById('schedule-conflict-warning');
        const detailEl = document.getElementById('schedule-conflict-detail');
        if (!warningEl || !detailEl) return;
        const conflicts = checkScheduleConflict(date, time);
        if (conflicts && conflicts.length > 0) {
            detailEl.innerHTML = conflicts.map(c =>
                '• <span class="font-medium">' + c.title + '</span><br><span class="text-amber-600">' + c.time + ' - ' + c.endTime + '</span>'
            ).join('<br>');
            warningEl.classList.remove('hidden');
        } else {
            warningEl.classList.add('hidden');
        }
    }

    function bindScheduleConflictCheck() {
        const dateInput = document.getElementById('sched-date');
        const timeInput = document.getElementById('sched-time');
        if (dateInput) dateInput.addEventListener('change', checkAndShowConflict);
        if (timeInput) timeInput.addEventListener('change', checkAndShowConflict);
    }

    // ===== 新建日程弹窗 =====
    function openScheduleModal() {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('sched-date').value = today;
        document.getElementById('sched-time').value = '09:00';
        document.getElementById('schedule-modal').classList.remove('hidden');
        // 检查当天冲突并绑定监听
        setTimeout(function() {
            checkAndShowConflict();
            bindScheduleConflictCheck();
        }, 100);
    }

    function closeScheduleModal() {
        document.getElementById('schedule-modal').classList.add('hidden');
    }

    function saveSchedule() {
        const title = document.getElementById('sched-title').value.trim();
        const date = document.getElementById('sched-date').value;
        const time = document.getElementById('sched-time').value;
        if (!title) {
            alert('请输入日程标题');
            return;
        }
        if (!date) {
            alert('请选择日期');
            return;
        }
        if (!time) {
            alert('请选择时间');
            return;
        }
        const type = document.querySelector('input[name="sched-type"]:checked')?.value || '其他';
        const caseVal = document.getElementById('sched-case').value;
        const note = document.getElementById('sched-note').value.trim();
        const remind = document.querySelector('input[name="sched-remind"]:checked')?.value || '60';
        
        // 冲突检测
        const conflicts = checkScheduleConflict(date, time);
        if (conflicts && conflicts.length > 0) {
            // 暂存待保存日程
            const endHour = parseInt(time.split(':')[0]) + 1;
            const endTime = String(endHour).padStart(2,'0') + ':' + time.split(':')[1];
            const caseSelect = document.getElementById('sched-case');
            const caseName = caseSelect.options[caseSelect.selectedIndex]?.text || '';
            pendingSchedule = {
                id: scheduleData.length + 1,
                title: title,
                date: date,
                time: time,
                endTime: endTime,
                type: type,
                caseName: caseName,
                location: note || '',
                note: '',
                remind: remind
            };
            showConflictResolve(conflicts);
            return; // 等待用户选择
        }
        
        const sched = { title, date, time, type, case: caseVal, note, remind };
        
        // 保存到日程数据
        const endHour = parseInt(time.split(':')[0]) + 1;
        const endTime = String(endHour).padStart(2,'0') + ':' + time.split(':')[1];
        scheduleData.push({
            id: scheduleData.length + 1,
            title: title,
            date: date,
            time: time,
            endTime: endTime,
            type: type,
            location: note || ''
        });
        
        closeScheduleModal();
        alert('日程已创建！');
        updateTodayScheduleBadge();
    }

    // ===== 更新今日日程角标 =====
    function updateTodayScheduleBadge() {
        const badge = document.getElementById('today-schedule-badge');
        if (!badge) return;
        const today = getTodayDate();
        const count = scheduleData.filter(s => s.date === today).length;
        badge.textContent = count;
    }

    // ===== 今日日程筛选 =====
    function filterSchedule(type, btn) {
        document.querySelectorAll('#view-schedule-list .filter-btn').forEach(b => {
            b.className = 'filter-btn text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200';
        });
        btn.className = 'filter-btn text-xs px-3 py-1.5 rounded-full bg-[#165DFF] text-white';
        document.querySelectorAll('#view-schedule-list .arco-card').forEach(card => {
            try {
                var tagEl = card.querySelector('.rounded-full:first-child');
                var tag = tagEl ? tagEl.textContent.trim() : '';
                if (type === 'all' || tag === type) {
                    card.classList.remove('hidden');
                } else {
                    card.classList.add('hidden');
                }
            } catch(e) {
                // 防御性：如果提取失败，跳过该卡片
                card.classList.remove('hidden');
            }
        });
    }

    // ===== 需要关注筛选 =====
    function filterAttention(type, btn) {
        document.querySelectorAll('#view-attention-list .att-filter-btn').forEach(b => {
            b.className = 'att-filter-btn text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200';
        });
        btn.className = 'att-filter-btn text-xs px-3 py-1.5 rounded-full bg-[#165DFF] text-white';
        document.querySelectorAll('#view-attention-list .bg-white.rounded-xl').forEach(card => {
            var tagEl = card.querySelector('.rounded-full:first-child');
            var tag = tagEl ? tagEl.textContent.trim() : '';
            if (type === 'all' || tag === type) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
    }

    // ===== 案件动态筛选 =====
    function filterDynamics(type, btn) {
        document.querySelectorAll('#view-case-dynamics .dyn-filter-btn').forEach(b => {
            b.className = 'dyn-filter-btn text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200';
        });
        btn.className = 'dyn-filter-btn text-xs px-3 py-1.5 rounded-full bg-[#165DFF] text-white';
        document.querySelectorAll('#view-case-dynamics .bg-white.rounded-xl').forEach(card => {
            const tag = card.querySelector('.rounded-full:first-child')?.textContent.trim();
            if (type === 'all' || tag === type) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
        searchDynamics(); // 结合搜索关键词
    }

    // ===== 图表初始化（已移除） =====
    // 统计模块已删除，Chart.js 引用及 initCharts 函数已移除

    // ===== 日程详情弹窗 =====
    let currentDetailScheduleId = null;

    function openScheduleDetail(id) {
        const item = scheduleData.find(s => s.id === id);
        if (!item) return;
        currentDetailScheduleId = id;
        
        document.getElementById('sdetail-title').textContent = item.title;
        document.getElementById('sdetail-date').textContent = item.date;
        document.getElementById('sdetail-time').textContent = item.time + ' - ' + (item.endTime || '');
        document.getElementById('sdetail-location').textContent = item.location || '未设置';
        document.getElementById('sdetail-case').textContent = item.caseName || '未关联案件';
        document.getElementById('sdetail-note').textContent = item.note || '无';
        
        // 类型徽章
        const badge = document.getElementById('sdetail-type-badge');
        const typeColors = { '开庭': ['bg-purple-100', 'text-purple-700'], '会议': ['bg-blue-100', 'text-blue-700'], '待办': ['bg-green-100', 'text-green-700'], '其他': ['bg-amber-100', 'text-amber-700'] };
        const colors = typeColors[item.type] || ['bg-gray-100', 'text-gray-700'];
        badge.className = 'text-xs px-2 py-0.5 rounded-full ' + colors.join(' ');
        badge.textContent = item.type;
        
        // 头部左边框颜色
        const header = document.getElementById('sdetail-header');
        const borderColors = { '开庭': '#7c3aed', '会议': '#3b82f6', '待办': '#22c55e', '其他': '#f59e0b' };
        header.style.borderLeftColor = borderColors[item.type] || '#165DFF';
        
        // 提醒文本
        const remindMap = { '0': '不提醒', '15': '提前 15 分钟', '60': '提前 1 小时', '1440': '提前 1 天' };
        document.getElementById('sdetail-remind').textContent = remindMap[item.remind] || '不提醒';
        
        // 检查冲突
        checkDetailConflict(item);
        
        document.getElementById('sdetail-note-row').classList.toggle('hidden', !item.note);
        document.getElementById('schedule-detail-modal').classList.remove('hidden');
    }

    function closeScheduleDetail() {
        document.getElementById('schedule-detail-modal').classList.add('hidden');
        currentDetailScheduleId = null;
    }

    function checkDetailConflict(item) {
        const warningEl = document.getElementById('sdetail-conflict');
        const detailEl = document.getElementById('sdetail-conflict-detail');
        
        const conflicts = scheduleData.filter(s => 
            s.id !== item.id && s.date === item.date &&
            item.time < s.endTime && item.endTime > s.time
        );
        
        if (conflicts.length > 0) {
            detailEl.innerHTML = conflicts.map(c => 
                '• <span class="font-medium">' + c.title + '</span> (' + c.time + '-' + (c.endTime||'') + ')'
            ).join('<br>');
            warningEl.classList.remove('hidden');
        } else {
            warningEl.classList.add('hidden');
        }
    }

    function editScheduleFromDetail() {
        closeScheduleDetail();
        openScheduleModal();
    }

    function deleteScheduleFromDetail() {
        if (!currentDetailScheduleId) return;
        if (confirm('确定要删除该日程吗？')) {
            const idx = scheduleData.findIndex(s => s.id === currentDetailScheduleId);
            if (idx > -1) scheduleData.splice(idx, 1);
            closeScheduleDetail();
            alert('日程已删除');
            if (typeof openScheduleCalendar === 'function') openScheduleCalendar();
        }
    }

    // ===== 冲突自动处理 =====
    let pendingSchedule = null;

    function showConflictResolve(conflicts) {
        const listEl = document.getElementById('conflict-list');
        listEl.innerHTML = conflicts.map(c => 
            '<div class="flex items-center gap-3 bg-red-50 rounded-lg p-3">' +
                '<iconify-icon icon="mdi:calendar-remove-outline" class="text-red-400 text-lg"></iconify-icon>' +
                '<div class="flex-1">' +
                    '<div class="text-sm font-medium text-red-700">' + c.title + '</div>' +
                    '<div class="text-xs text-red-500">' + c.time + ' - ' + (c.endTime||'') + '</div>' +
                '</div>' +
            '</div>'
        ).join('');
        
        // 推荐空闲时段
        const slotsEl = document.getElementById('suggested-slots');
        const date = pendingSchedule.date;
        const busyPeriods = conflicts.map(c => ({ start: c.time, end: c.endTime }));
        const suggestions = suggestFreeSlots(date, busyPeriods);
        slotsEl.innerHTML = suggestions.map(s => 
            '<button onclick="selectSuggestedSlot(\'' + s.start + '\',\'' + s.end + '\')" class="text-xs px-3 py-1.5 rounded-full border border-[#165DFF] text-[#165DFF] hover:bg-blue-50 transition-colors">' + s.start + ' - ' + s.end + '</button>'
        ).join('');
        
        document.getElementById('conflict-resolve-modal').classList.remove('hidden');
    }

    function closeConflictResolve() {
        document.getElementById('conflict-resolve-modal').classList.add('hidden');
        pendingSchedule = null;
    }

    function conflictResolveAction(action) {
        if (action === 'cancel') {
            closeConflictResolve();
            return;
        }
        if (action === 'ignore') {
            closeConflictResolve();
            if (pendingSchedule) {
                scheduleData.push(pendingSchedule);
                pendingSchedule = null;
                alert('日程已创建（含冲突）');
            }
            return;
        }
        if (action === 'reschedule') {
            closeConflictResolve();
            if (pendingSchedule) {
                scheduleData.push(pendingSchedule);
                pendingSchedule = null;
                alert('日程已调整至推荐时段');
            }
            return;
        }
    }

    function selectSuggestedSlot(start, end) {
        if (pendingSchedule) {
            pendingSchedule.time = start;
            pendingSchedule.endTime = end;
        }
        document.getElementById('sched-time').value = start;
    }

    function suggestFreeSlots(date, busyPeriods) {
        const allSlots = [];
        for (let h = 8; h < 20; h++) {
            allSlots.push({ start: String(h).padStart(2,'0') + ':00', end: String(h+1).padStart(2,'0') + ':00' });
        }
        return allSlots.filter(slot => 
            !busyPeriods.some(busy => slot.start < busy.end && slot.end > busy.start)
        ).slice(0, 4);
    }

    // ===== 庭审冲突预警 =====
    function checkCourtConflicts() {
        const courtSchedules = scheduleData.filter(s => s.type === '开庭');
        const conflicts = [];
        
        for (let i = 0; i < courtSchedules.length; i++) {
            for (let j = i + 1; j < courtSchedules.length; j++) {
                const a = courtSchedules[i], b = courtSchedules[j];
                if (a.date === b.date && a.time < b.endTime && a.endTime > b.time) {
                    conflicts.push({ a, b });
                }
            }
        }
        
        const bar = document.getElementById('court-conflict-bar');
        const detail = document.getElementById('court-conflict-detail');
        
        if (conflicts.length > 0) {
            detail.innerHTML = conflicts.map(c => 
                '• <span class="font-medium">' + c.a.title + '</span> 与 <span class="font-medium">' + c.b.title + '</span> 时间重叠（' + c.a.date + ' ' + c.a.time + '-' + c.b.endTime + '）'
            ).join('<br>');
            bar.classList.remove('hidden');
        } else {
            bar.classList.add('hidden');
        }
        
        return conflicts;
    }

    function dismissCourtConflict() {
        document.getElementById('court-conflict-bar').classList.add('hidden');
    }

    // ===== 动态详情弹窗 =====
    function openCaseDynamicDetail(index) {
        var dynamics = [
            { type: '紧急', typeClass: 'bg-red-100 text-red-700', title: '举证期限即将截止', caseName: '张三合同纠纷', time: '2026-06-10 14:30', handler: '李明', description: '张三合同纠纷一案的举证期限将于2026年6月23日截止，请尽快整理并提交相关证据材料，避免因逾期导致证据失权。', files: ['证据目录_v3.xlsx (256KB)', '举证期限告知书.pdf (1.2MB)'], note: '请务必在截止日前完成证据交换，已通知对方代理人。', action: '去处理' },
            { type: '文书', typeClass: 'bg-blue-100 text-blue-700', title: '起诉状已完成', caseName: '李四借贷纠纷', time: '2026-06-09 16:20', handler: '王芳', description: '李四借贷纠纷案的民事起诉状已完成最终审核，经合伙人确认无误，可安排打印盖章后提交法院立案。', files: ['民事起诉状_终稿.docx (45KB)'], note: '已安排下周一早提交立案庭。', action: '查看文书' },
            { type: '文书', typeClass: 'bg-blue-100 text-blue-700', title: '证据目录已更新', caseName: '王五股权转让纠纷', time: '2026-06-08 11:00', handler: '赵磊', description: '根据最新补充的银行流水和股权变更登记材料，已更新证据目录，新增证据5-8号，请确认是否完整。', files: ['证据目录_更新版.xlsx (128KB)', '补充材料_银行流水.pdf (3.5MB)'], note: '', action: '查看详情' },
            { type: '开庭', typeClass: 'bg-purple-100 text-purple-700', title: '开庭日期已确定', caseName: '赵六劳动争议', time: '2026-06-07 09:00', handler: '陈静', description: '赵六诉某科技公司劳动争议案，经与法院沟通，开庭时间定于2026年7月15日上午9:00，在市劳动争议仲裁委员会第一仲裁庭。', files: ['开庭传票.pdf (0.5MB)'], note: '请提前30分钟到达，带齐证据原件。', action: '查看详情' },
            { type: '开庭', typeClass: 'bg-purple-100 text-purple-700', title: '合议庭组成已确定', caseName: '孙七建设工程合同纠纷', time: '2026-06-06 15:00', handler: '刘强', description: '孙七建设工程合同纠纷案合议庭成员已确定，审判长：张明法官，审判员：李华、王丽。当事人对合议庭成员如申请回避，需在5日内提出。', files: ['合议庭组成通知书.pdf (0.3MB)'], note: '已与当事人确认无回避申请。', action: '查看详情' },
            { type: '归档', typeClass: 'bg-green-100 text-green-700', title: '案件已归档', caseName: '周八借款纠纷', time: '2026-06-05 17:00', handler: '李明', description: '周八借款纠纷案已结案归档。判决已生效，案卷材料已按档案管理规定整理完毕，存放于档案室第3柜第12号。', files: ['结案报告.docx (32KB)', '判决书.pdf (0.8MB)'], note: '归档编号：2026-0312', action: '查看归档' },
            { type: '归档', typeClass: 'bg-green-100 text-green-700', title: '判决书已上传', caseName: '吴九房屋租赁合同纠纷', time: '2026-06-04 14:00', handler: '王芳', description: '吴九房屋租赁合同纠纷案一审判决书已收到并上传系统。判决结果：被告支付租金及违约金合计￥45,600。双方是否上诉待确认。', files: ['一审判决书.pdf (1.1MB)'], note: '已通知当事人查收判决书，上诉期限15天。', action: '查看判决书' },
            { type: '提醒', typeClass: 'bg-amber-100 text-amber-700', title: '续约提醒', caseName: '常年法律顾问 - 某科技公司', time: '2026-06-03 10:00', handler: '系统自动', description: '某科技公司常年法律顾问服务合同将于2026年7月1日到期，如需续约请提前30天联系客户沟通续约事宜。', files: ['顾问合同_2025.pdf (0.6MB)'], note: '客户满意度较高，建议主动联系续约。', action: '查看详情' }
        ];
        var d = dynamics[index] || dynamics[0];
        document.getElementById('detail-type-badge').textContent = d.type;
        document.getElementById('detail-type-badge').className = 'text-[10px] font-medium px-1.5 py-0.5 rounded-full ' + d.typeClass;
        document.getElementById('detail-title').textContent = d.title;
        document.getElementById('detail-case-name').textContent = d.caseName;
        document.getElementById('detail-time').textContent = d.time;
        document.getElementById('detail-handler').textContent = d.handler;
        document.getElementById('detail-description').textContent = d.description;
        document.getElementById('detail-note').textContent = d.note || '暂无备注';
        document.getElementById('detail-action-btn').textContent = d.action;
        
        // 动态渲染关联文件
        var filesContainer = document.getElementById('detail-files-list');
        if (filesContainer) {
            var filesHtml = '';
            var fileIcons = {
                'xlsx': 'mdi:file-excel-outline',
                'xls': 'mdi:file-excel-outline',
                'pdf': 'mdi:file-pdf-outline',
                'doc': 'mdi:file-word-outline',
                'docx': 'mdi:file-word-outline',
                'jpg': 'mdi:file-image-outline',
                'png': 'mdi:file-image-outline',
                'gif': 'mdi:file-image-outline'
            };
            var fileColors = {
                'xlsx': 'bg-green-100 text-green-500',
                'xls': 'bg-green-100 text-green-500',
                'pdf': 'bg-red-100 text-red-500',
                'doc': 'bg-blue-100 text-blue-500',
                'docx': 'bg-blue-100 text-blue-500',
                'jpg': 'bg-purple-100 text-purple-500',
                'png': 'bg-purple-100 text-purple-500',
                'gif': 'bg-purple-100 text-purple-500'
            };
            
            (d.files || []).forEach(function(f) {
                var ext = f.split('(')[0].split('.').pop().trim().toLowerCase();
                var icon = fileIcons[ext] || 'mdi:file-document-outline';
                var color = fileColors[ext] || 'bg-gray-100 text-gray-500';
                var name = f.split('(')[0].trim();
                var sizeMatch = f.match(/\(([^)]+)\)/);
                var sizeStr = sizeMatch ? sizeMatch[1] : '';
                filesHtml += '<div class="flex items-center gap-3 bg-gray-50 rounded-lg px-3 py-2.5 hover:bg-gray-100 transition-colors cursor-pointer">' +
                    '<div class="w-8 h-8 rounded-lg ' + color.split(' ')[0] + ' flex items-center justify-center flex-shrink-0">' +
                        '<iconify-icon icon="' + icon + '" class="' + color.split(' ')[1] + ' text-base"></iconify-icon>' +
                    '</div>' +
                    '<div class="flex-1 min-w-0">' +
                        '<p class="text-xs font-medium text-gray-700 truncate">' + name + '</p>' +
                        '<p class="text-[10px] text-gray-400">' + sizeStr + '</p>' +
                    '</div>' +
                    '<button class="text-[11px] text-[#165DFF] hover:underline flex-shrink-0">预览</button>' +
                '</div>';
            });
            filesContainer.innerHTML = filesHtml;
        }
        
        document.getElementById('case-dynamic-detail-modal').classList.remove('hidden');
    }
    function closeCaseDynamicDetail() {
        document.getElementById('case-dynamic-detail-modal').classList.add('hidden');
    }

    // ===== 动态搜索筛选 =====
    function searchDynamics() {
        var keyword = document.getElementById('dynamics-search-input').value.trim().toLowerCase();
        document.querySelectorAll('#view-case-dynamics .bg-white.rounded-xl').forEach(function(card) {
            var text = card.textContent.toLowerCase();
            if (keyword === '' || text.indexOf(keyword) !== -1) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
        var visibleCount = document.querySelectorAll('#view-case-dynamics .bg-white.rounded-xl:not(.hidden)').length;
        var totalCount = document.querySelectorAll('#view-case-dynamics .bg-white.rounded-xl').length;
        var countEl = document.querySelector('#view-case-dynamics h2 + span');
        if (countEl) countEl.textContent = '共 ' + visibleCount + ' / ' + totalCount + ' 条';
        
        // 显示/隐藏空状态
        var emptyState = document.getElementById('dynamics-empty-state');
        if (emptyState) {
            if (visibleCount === 0) {
                emptyState.classList.remove('hidden');
            } else {
                emptyState.classList.add('hidden');
            }
        }
    }

    // ===== 发布动态 =====
    // var selectedDynamicType = '紧急'; // → AppState.selectedDynamicType
    function selectDynamicType(btn, type) {
        document.querySelectorAll('.dyn-type-option').forEach(function(b) {
            b.className = 'dyn-type-option text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200';
        });
        btn.className = 'dyn-type-option text-xs px-3 py-1.5 rounded-full bg-[#165DFF] text-white';
        AppState.selectedDynamicType = type;
    }
    function openNewDynamicModal() {
        document.getElementById('new-dynamic-modal').classList.remove('hidden');
    }
    function closeNewDynamicModal() {
        document.getElementById('new-dynamic-modal').classList.add('hidden');
    }
    
    // 动态发布 - 附件上传
    // var dynamicAttachments = []; // → AppState.dynamicAttachments

    function handleDynamicFileSelect(input) {
        var files = input.files;
        for (var i = 0; i < files.length; i++) {
            addDynamicFile(files[i]);
        }
        input.value = '';
    }

    function handleDynamicFileDrop(event) {
        var files = event.dataTransfer.files;
        for (var i = 0; i < files.length; i++) {
            addDynamicFile(files[i]);
        }
    }

    function addDynamicFile(file) {
        var size = file.size;
        var sizeStr = '';
        if (size < 1024) sizeStr = size + 'B';
        else if (size < 1024 * 1024) sizeStr = (size / 1024).toFixed(1) + 'KB';
        else sizeStr = (size / 1024 / 1024).toFixed(1) + 'MB';
        
        var icon = 'mdi:file-document-outline';
        var ext = file.name.split('.').pop().toLowerCase();
        if (['png','jpg','jpeg','gif','webp'].indexOf(ext) !== -1) icon = 'mdi:file-image-outline';
        else if (['pdf'].indexOf(ext) !== -1) icon = 'mdi:file-pdf-outline';
        else if (['doc','docx'].indexOf(ext) !== -1) icon = 'mdi:file-word-outline';
        else if (['xls','xlsx'].indexOf(ext) !== -1) icon = 'mdi:file-excel-outline';
        
        var fileId = 'dyn_file_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
        
        AppState.dynamicAttachments.push({
            id: fileId,
            name: file.name,
            size: sizeStr,
            icon: icon,
            file: file
        });
        
        renderDynamicFilePreview();
    }

    function removeDynamicFile(fileId) {
        AppState.dynamicAttachments = AppState.dynamicAttachments.filter(function(f) { return f.id !== fileId; });
        renderDynamicFilePreview();
    }

    function renderDynamicFilePreview() {
        var container = document.getElementById('dynamic-file-preview-list');
        if (!container) return;
        
        if (AppState.dynamicAttachments.length === 0) {
            container.classList.add('hidden');
            return;
        }
        container.classList.remove('hidden');
        
        var html = '';
        AppState.dynamicAttachments.forEach(function(f) {
            html += '<div class="flex items-center gap-2 bg-white rounded-lg border border-[#E5E6EB] px-3 py-2">' +
                '<iconify-icon icon="' + f.icon + '" class="text-base text-[#165DFF] flex-shrink-0"></iconify-icon>' +
                '<div class="flex-1 min-w-0">' +
                    '<p class="text-xs text-gray-700 truncate">' + f.name + '</p>' +
                    '<p class="text-[10px] text-gray-400">' + f.size + '</p>' +
                '</div>' +
                '<button onclick="removeDynamicFile(\'' + f.id + '\')" class="text-gray-400 hover:text-red-500 flex-shrink-0">' +
                    '<iconify-icon icon="mdi:close-circle"></iconify-icon>' +
                '</button>' +
            '</div>';
        });
        container.innerHTML = html;
    }
    
    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');
    }
    
    function submitNewDynamic() {
        var title = document.getElementById('new-dynamic-title').value.trim();
        if (!title) { alert('请填写动态标题'); return; }
        var desc = document.getElementById('new-dynamic-desc').value.trim();
        var caseName = document.getElementById('new-dynamic-case').value || '未关联案件';
        var isUrgent = document.getElementById('new-dynamic-urgent').checked;
        var now = new Date();
        var timeStr = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0') + '-' + String(now.getDate()).padStart(2,'0') + ' ' + String(now.getHours()).padStart(2,'0') + ':' + String(now.getMinutes()).padStart(2,'0');
        var typeColorMap = {
            '紧急': { border: 'border-l-red-500', bg: 'bg-red-50', icon: 'mdi:alert-circle-outline', iconColor: 'text-red-500', tagBg: 'bg-red-100', tagText: 'text-red-700' },
            '文书': { border: 'border-l-blue-500', bg: 'bg-blue-50', icon: 'mdi:file-document-outline', iconColor: 'text-blue-500', tagBg: 'bg-blue-100', tagText: 'text-blue-700' },
            '开庭': { border: 'border-l-purple-500', bg: 'bg-purple-50', icon: 'mdi:gavel', iconColor: 'text-purple-500', tagBg: 'bg-purple-100', tagText: 'text-purple-700' },
            '归档': { border: 'border-l-green-500', bg: 'bg-green-50', icon: 'mdi:archive-outline', iconColor: 'text-green-500', tagBg: 'bg-green-100', tagText: 'text-green-700' },
            '提醒': { border: 'border-l-amber-500', bg: 'bg-amber-50', icon: 'mdi:bell-outline', iconColor: 'text-amber-500', tagBg: 'bg-amber-100', tagText: 'text-amber-700' }
        };
        var colors = typeColorMap[AppState.selectedDynamicType] || typeColorMap['提醒'];
        // 构建附件标签行
        var attachHtml = '';
        if (AppState.dynamicAttachments.length > 0) {
            attachHtml = '<div class="flex items-center gap-2 mt-1.5">' +
                AppState.dynamicAttachments.map(function(a) {
                    return '<span class="inline-flex items-center gap-1 text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full"><iconify-icon icon="' + a.icon + '" class="text-xs"></iconify-icon>' + escapeHtml(a.name) + '</span>';
                }).join('') +
            '</div>';
        }
        var cardHtml = '<div class="bg-white rounded-xl border border-[#E5E6EB] p-4 hover:shadow-sm transition-shadow ' + colors.border + '">' +
            '<div class="flex items-start gap-3">' +
                '<div class="w-9 h-9 rounded-lg ' + colors.bg + ' flex items-center justify-center flex-shrink-0">' +
                    '<iconify-icon icon="' + colors.icon + '" class="' + colors.iconColor + ' text-lg"></iconify-icon>' +
                '</div>' +
                '<div class="flex-1 min-w-0">' +
                    '<div class="flex items-center gap-2 mb-1">' +
                        '<span class="text-[10px] ' + colors.tagBg + ' ' + colors.tagText + ' font-medium px-1.5 py-0.5 rounded-full">' + (isUrgent ? '紧急' : AppState.selectedDynamicType) + '</span>' +
                        '<span class="font-medium text-sm text-gray-800">' + escapeHtml(title) + '</span>' +
                    '</div>' +
                    '<p class="text-xs text-gray-500">案件：' + escapeHtml(caseName) + ' · ' + (escapeHtml(desc.substring(0,30)) || '暂无详细描述') + '</p>' +
                    attachHtml +
                    '<div class="flex items-center gap-3 mt-2">' +
                        '<span class="text-[10px] text-gray-400"><iconify-icon icon="mdi:clock-outline" class="mr-0.5"></iconify-icon>' + timeStr + '</span>' +
                        '<span class="text-[10px] text-gray-400"><iconify-icon icon="mdi:account-outline" class="mr-0.5"></iconify-icon>我</span>' +
                    '</div>' +
                '</div>' +
                '<button class="text-[11px] text-[#165DFF] hover:underline flex-shrink-0 mt-1" onclick="alert(\'' + escapeHtml(title) + '\\n\\n案件：' + escapeHtml(caseName) + '\\n' + (escapeHtml(desc.substring(0,50)) || '') + '\\n\\n附件：' + (AppState.dynamicAttachments.length > 0 ? AppState.dynamicAttachments.map(function(a){return escapeHtml(a.name)}).join(', ') : '无') + '\')">查看</button>' +
            '</div>' +
        '</div>';
        var listContainer = document.querySelector('#dynamics-list-view');
        if (listContainer) {
            var tempDiv = document.createElement('div');
            tempDiv.innerHTML = cardHtml;
            listContainer.insertBefore(tempDiv.firstElementChild, listContainer.firstElementChild);
        }
        var totalCards = document.querySelectorAll('#view-case-dynamics .bg-white.rounded-xl').length;
        var countEl = document.querySelector('#view-case-dynamics h2 + span');
        if (countEl) countEl.textContent = '共 ' + totalCards + ' 条';
        closeNewDynamicModal();
        document.getElementById('new-dynamic-title').value = '';
        document.getElementById('new-dynamic-desc').value = '';
        document.getElementById('new-dynamic-case').value = '';
        document.getElementById('new-dynamic-urgent').checked = false;
        AppState.selectedDynamicType = '紧急';
        document.querySelectorAll('.dyn-type-option').forEach(function(b, i) {
            b.className = 'dyn-type-option text-xs px-3 py-1.5 rounded-full ' + (i === 0 ? 'bg-[#165DFF] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200');
        });
        // 重置附件
        AppState.dynamicAttachments = [];
        renderDynamicFilePreview();
    }

    // ===== 案件动态 - 视图切换 =====
    // var dynamicsViewData = [...] // → AppState.dynamicsViewData
    AppState.dynamicsViewData = [
        { type: '紧急', typeClass: 'bg-red-100 text-red-700', icon: 'mdi:alert-circle-outline', iconColor: 'text-red-500', title: '举证期限即将截止', caseName: '张三合同纠纷', time: '2026-06-10', desc: '举证期限将于2026年6月23日截止' },
        { type: '文书', typeClass: 'bg-blue-100 text-blue-700', icon: 'mdi:file-document-outline', iconColor: 'text-blue-500', title: '起诉状已完成', caseName: '李四借贷纠纷', time: '2026-06-09', desc: '民事起诉状已完成最终审核' },
        { type: '文书', typeClass: 'bg-blue-100 text-blue-700', icon: 'mdi:file-document-outline', iconColor: 'text-blue-500', title: '证据目录已更新', caseName: '王五股权转让纠纷', time: '2026-06-08', desc: '新增证据5-8号' },
        { type: '开庭', typeClass: 'bg-purple-100 text-purple-700', icon: 'mdi:gavel', iconColor: 'text-purple-500', title: '开庭日期已确定', caseName: '赵六劳动争议', time: '2026-06-07', desc: '2026年7月15日上午9:00开庭' },
        { type: '开庭', typeClass: 'bg-purple-100 text-purple-700', icon: 'mdi:gavel', iconColor: 'text-purple-500', title: '合议庭组成已确定', caseName: '孙七建设工程合同纠纷', time: '2026-06-06', desc: '审判长：张明法官' },
        { type: '归档', typeClass: 'bg-green-100 text-green-700', icon: 'mdi:archive-outline', iconColor: 'text-green-500', title: '案件已归档', caseName: '周八借款纠纷', time: '2026-06-05', desc: '已结案归档，档案第3柜12号' },
        { type: '归档', typeClass: 'bg-green-100 text-green-700', icon: 'mdi:archive-outline', iconColor: 'text-green-500', title: '判决书已上传', caseName: '吴九房屋租赁合同纠纷', time: '2026-06-04', desc: '一审判决书已收到并上传' },
        { type: '提醒', typeClass: 'bg-amber-100 text-amber-700', icon: 'mdi:bell-outline', iconColor: 'text-amber-500', title: '续约提醒', caseName: '某科技公司', time: '2026-06-03', desc: '顾问合同将于2026年7月1日到期' }
    ];

    function switchDynamicsView(view) {
        var listBtn = document.getElementById('dyn-view-list');
        var tlBtn = document.getElementById('dyn-view-timeline');
        var listView = document.getElementById('dynamics-list-view');
        var tlView = document.getElementById('dynamics-timeline-view');
        
        if (view === 'timeline') {
            listBtn.className = 'flex items-center gap-1 h-8 px-2.5 text-xs bg-white text-gray-600 hover:bg-gray-50 transition-colors';
            tlBtn.className = 'flex items-center gap-1 h-8 px-2.5 text-xs bg-[#165DFF] text-white transition-colors';
            listView.classList.add('hidden');
            tlView.classList.remove('hidden');
            renderDynamicsTimeline();
        } else {
            tlBtn.className = 'flex items-center gap-1 h-8 px-2.5 text-xs bg-white text-gray-600 hover:bg-gray-50 transition-colors';
            listBtn.className = 'flex items-center gap-1 h-8 px-2.5 text-xs bg-[#165DFF] text-white transition-colors';
            tlView.classList.add('hidden');
            listView.classList.remove('hidden');
        }
    }

    function renderDynamicsTimeline() {
        var container = document.querySelector('#dynamics-timeline-view .relative.pl-8');
        if (!container) return;
        if (container.querySelectorAll('.dyn-tl-item').length > 0) return;
        
        var htmlStr = '';
        AppState.dynamicsViewData.forEach(function(d, i) {
            var dotColor = d.iconColor.replace('text-', 'border-');
            htmlStr += '<div class="dyn-tl-item relative pb-6">' +
                '<div class="absolute left-[-22px] top-1 w-3 h-3 rounded-full border-2 bg-white ' + (dotColor || 'border-blue-500') + '"></div>' +
                '<div class="bg-white rounded-xl border border-[#E5E6EB] p-4 hover:shadow-sm transition-shadow cursor-pointer" onclick="openCaseDynamicDetail(' + i + ')">' +
                    '<div class="flex items-start gap-3">' +
                        '<div class="w-8 h-8 rounded-lg ' + d.typeClass.split(' ')[0].replace('text-', 'bg-').replace('-700', '-50') + ' flex items-center justify-center flex-shrink-0">' +
                            '<iconify-icon icon="' + d.icon + '" class="' + d.iconColor + ' text-base"></iconify-icon>' +
                        '</div>' +
                        '<div class="flex-1 min-w-0">' +
                            '<div class="flex items-center gap-2 mb-0.5">' +
                                '<span class="text-[10px] ' + d.typeClass + ' font-medium px-1.5 py-0.5 rounded-full">' + d.type + '</span>' +
                                '<span class="font-medium text-sm text-gray-800">' + d.title + '</span>' +
                            '</div>' +
                            '<p class="text-xs text-gray-500">' + d.caseName + ' · ' + d.desc + '</p>' +
                            '<span class="text-[10px] text-gray-400 mt-1 inline-block">' + d.time + '</span>' +
                        '</div>' +
                    '</div>' +
                '</div>' +
            '</div>';
        });
        container.insertAdjacentHTML('beforeend', htmlStr);
    }
    
    // ===== AI一键提取要点 =====
    // var selectedExtractSource = 'case';
    function selectExtractSource(btn, source) {
        document.querySelectorAll('.extract-source-btn').forEach(function(b) {
            b.className = 'extract-source-btn text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200';
        });
        btn.className = 'extract-source-btn text-xs px-3 py-1.5 rounded-full bg-[#165DFF] text-white';
        AppState.selectedExtractSource = source;
    }
    function openAIExtractModal() {
        document.getElementById('extract-result-area').classList.add('hidden');
        document.getElementById('extract-loading').classList.add('hidden');
        document.getElementById('ai-extract-modal').classList.remove('hidden');
    }
    function closeAIExtractModal() {
        document.getElementById('ai-extract-modal').classList.add('hidden');
    }
    function startAIExtract() {
        document.getElementById('extract-loading').classList.remove('hidden');
        document.getElementById('extract-result-area').classList.add('hidden');
        setTimeout(function() {
            document.getElementById('extract-loading').classList.add('hidden');
            document.getElementById('extract-result-area').classList.remove('hidden');
        }, 2000);
    }
    function copyExtractResult() {
        showToast('提取结果已复制到剪贴板');
    }
    function exportExtractResult() {
        alert('报告已导出为Markdown格式（演示功能）');
    }
    
    // ===== 批量上传 =====
    // var batchFiles = []; // → AppState.batchFiles
    function openBatchUploadModal() {
        document.getElementById('batch-upload-modal').classList.remove('hidden');
    }
    function closeBatchUploadModal() {
        document.getElementById('batch-upload-modal').classList.add('hidden');
    }
    function handleBatchSelect(input) {
        for (var i = 0; i < input.files.length; i++) {
            addBatchFile(input.files[i]);
        }
        input.value = '';
        renderBatchFiles();
    }
    function handleBatchDrop(event) {
        for (var i = 0; i < event.dataTransfer.files.length; i++) {
            addBatchFile(event.dataTransfer.files[i]);
        }
        renderBatchFiles();
    }
    function addBatchFile(file) {
        if (AppState.batchFiles.length >= 20) { alert('最多上传 20 个文件'); return; }
        var icon = 'mdi:file-document-outline';
        var ext = file.name.split('.').pop().toLowerCase();
        if (['png','jpg','jpeg','gif','webp'].indexOf(ext) !== -1) icon = 'mdi:file-image-outline';
        else if (['pdf'].indexOf(ext) !== -1) icon = 'mdi:file-pdf-outline';
        else if (['doc','docx'].indexOf(ext) !== -1) icon = 'mdi:file-word-outline';
        else if (['xls','xlsx'].indexOf(ext) !== -1) icon = 'mdi:file-excel-outline';
        var size = file.size;
        var sizeStr = size < 1024 ? size + 'B' : size < 1048576 ? (size/1024).toFixed(1)+'KB' : (size/1048576).toFixed(1)+'MB';
        AppState.batchFiles.push({ id: 'batch_'+Date.now()+'_'+Math.random().toString(36).substr(2,5), name: file.name, size: sizeStr, icon: icon, file: file });
    }
    function renderBatchFiles() {
        var area = document.getElementById('batch-progress-area');
        var list = document.getElementById('batch-file-list');
        var count = document.getElementById('batch-file-count');
        var uploadBtn = document.getElementById('batch-upload-count');
        if (AppState.batchFiles.length === 0) {
            area.classList.add('hidden');
            return;
        }
        area.classList.remove('hidden');
        count.textContent = AppState.batchFiles.length;
        uploadBtn.textContent = AppState.batchFiles.length;
        var html = '';
        AppState.batchFiles.forEach(function(f) {
            html += '<div class="flex items-center gap-2 bg-white rounded-lg border border-[#E5E6EB] px-3 py-2">' +
                '<iconify-icon icon="' + f.icon + '" class="text-base text-[#165DFF] flex-shrink-0"></iconify-icon>' +
                '<div class="flex-1 min-w-0"><p class="text-xs text-gray-700 truncate">' + f.name + '</p><p class="text-[10px] text-gray-400">' + f.size + '</p></div>' +
                '<button onclick="removeBatchFile(\'' + f.id + '\')" class="text-gray-400 hover:text-red-500 flex-shrink-0"><iconify-icon icon="mdi:close-circle"></iconify-icon></button>' +
            '</div>';
        });
        list.innerHTML = html;
    }
    function removeBatchFile(id) {
        AppState.batchFiles = AppState.batchFiles.filter(function(f) { return f.id !== id; });
        renderBatchFiles();
    }
    function clearBatchFiles() {
        AppState.batchFiles = [];
        renderBatchFiles();
    }
    function confirmBatchUpload() {
        if (AppState.batchFiles.length === 0) { alert('请先选择文件'); return; }
        var count = AppState.batchFiles.length;
        AppState.batchFiles.forEach(function(f) {
            addDynamicFile(f.file);
        });
        AppState.batchFiles = [];
        renderBatchFiles();
        closeBatchUploadModal();
        setTimeout(function() { alert('成功上传 ' + count + ' 个文件到附件列表'); }, 100);
    }

    // 全局 Toast 提示
    function showToast(message) {
        var existing = document.querySelector('.custom-toast');
        if (existing) existing.remove();
        var toast = document.createElement('div');
        toast.className = 'custom-toast fixed top-4 right-4 z-[9999] bg-green-50 border border-green-200 text-green-700 text-xs px-4 py-2.5 rounded-lg shadow-lg flex items-center gap-2 transform transition-all duration-300';
        toast.innerHTML = '<iconify-icon icon="mdi:check-circle-outline" class="text-green-500"></iconify-icon><span>' + (message || '操作成功') + '</span>';
        document.body.appendChild(toast);
        setTimeout(function() { toast.style.opacity = '0'; setTimeout(function() { toast.remove(); }, 300); }, 2500);
    }



    // 页面加载时检查 template 视图是否需要修复 DOM 重组
    (function() {
        function tryFix() {
            if (document.getElementById('view-template') && typeof fixTemplateViewDOM === 'function') {
                fixTemplateViewDOM();
            }
        }
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            setTimeout(tryFix, 50);
            setTimeout(tryFix, 300);
        } else {
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(tryFix, 50);
                setTimeout(tryFix, 300);
            });
        }
        // 兜底: 监听 main-content 变化, view-template 出现时立即修
        var main = document.getElementById('main-content');
        if (main) {
            var obs = new MutationObserver(function() {
                if (document.getElementById('view-template')) {
                    setTimeout(tryFix, 30);
                }
            });
            obs.observe(main, { childList: true });
        }
    })();
