        // ===== 全局应用状态 =====
        var AppState = {
            isYearly: false,
            selectedPayment: 'alipay',
            selectedDynamicType: '紧急',
            selectedExtractSource: 'case',
            currentPDFPage: 1,
            currentZoom: 1.0,
            currentAnnotateColor: 'bg-yellow-300',
            annotateHistory: [],
            historyIndex: -1,
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
            'archive': 'archive.html',
            'contract-list': 'contract-list.html'
        };

        // 动态加载视图
        function loadView(viewId, callback) {
            if (viewCache[viewId]) {
                // 已缓存，直接使用
                if (callback) callback(viewCache[viewId]);
                return;
            }
            var fileName = viewFileMap[viewId];
            if (!fileName) {
                console.error('未知的视图ID:', viewId);
                return;
            }
            fetch('templates/views/' + fileName)
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

        // ===== 案件详情页操作 =====
        function editCase() {
            showToast('编辑案件功能开发中');
        }

        function shareCase() {
            showToast('分享案件功能开发中');
        }

        function archiveCurrentCase() {
            showToast('案件归档功能开发中');
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

        // 新建对话（已合并到上方，此处保留注释占位）
        /* function startNewChat() {
            var msgList = document.getElementById('aiViewMessages');
            if (msgList) {
                msgList.innerHTML = '' +
                    '<div class="flex gap-3">' +
                      '<div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#165DFF] to-[#6C5CE7] flex items-center justify-center text-white flex-shrink-0">' +
                        '<iconify-icon class="text-sm" icon="mdi:robot"></iconify-icon>' +
                      '</div>' +
                      '<div class="max-w-[70%] bg-white rounded-xl p-4 shadow-sm border border-[#E5E6EB]">' +
                        '<p class="text-sm leading-relaxed text-[#4E5969]">您好！我是 <span class="font-semibold text-[#165DFF]">LexPrime AI</span> 助手。请问有什么可以帮您的？</p>' +
                        '<span class="text-[11px] text-[#86909C] mt-2 block">刚刚</span>' +
                      '</div>' +
                    '</div>';
            }
        } */

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
            // 关闭用户菜单
            var userMenu = document.getElementById('userMenu');
            if (userMenu) userMenu.classList.add('hidden');
            
            // 切换到工作标签
            switchSidebarTab('work');
            
            // 隐藏所有视图，显示订阅页面
            document.querySelectorAll('.view-content').forEach(function(v) {
                v.classList.add('hidden');
            });
            document.getElementById('view-subscription').classList.remove('hidden');
            
            // 取消所有侧边栏菜单的高亮
            document.querySelectorAll('.sidebar-item').forEach(function(item) {
                item.classList.remove('active');
            });
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
            document.querySelectorAll('.view-content').forEach(function(v) {
                v.classList.add('hidden');
            });
            document.getElementById('view-subscription').classList.remove('hidden');
        }

        function goToWorkstation() {
            document.querySelectorAll('.view-content').forEach(function(v) {
                v.classList.add('hidden');
            });
            document.getElementById('view-workstation').classList.remove('hidden');
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
            document.querySelectorAll('.view-content').forEach(function(v) {
                v.classList.add('hidden');
            });
            document.getElementById('view-member-center').classList.remove('hidden');
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
        if (target) {
            // 视图已存在，直接显示
            document.querySelectorAll('.view-content').forEach(function(v) {
                v.classList.add('hidden');
            });
            target.classList.remove('hidden');
        } else {
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
    function openCaseDetail(index) {
        var caseMeta = [
            { title: '(2026)京01民初128号', type: '民间借贷纠纷', status: '进行中' },
            { title: '(2026)京02民初256号', type: '劳动争议仲裁', status: '进行中' },
            { title: '(2026)京03民初789号', type: '合同纠纷', status: '待开庭' },
            { title: '(2026)京04民初345号', type: '知识产权侵权', status: '已立案' },
            { title: '(2026)京05民初567号', type: '离婚纠纷', status: '进行中' }
        ];
        
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
                var typeEl = document.getElementById('case-detail-type');
                var statusEl = document.getElementById('case-detail-status');
                if (titleEl) titleEl.textContent = meta.title;
                if (typeEl) typeEl.textContent = meta.type;
                if (statusEl) {
                    statusEl.textContent = meta.status;
                    statusEl.className = 'text-[10px] bg-blue-100 text-blue-700 font-medium px-2 py-0.5 rounded-full';
                }
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
                        var typeEl = document.getElementById('case-detail-type');
                        var statusEl = document.getElementById('case-detail-status');
                        if (titleEl) titleEl.textContent = meta.title;
                        if (typeEl) typeEl.textContent = meta.type;
                        if (statusEl) {
                            statusEl.textContent = meta.status;
                            statusEl.className = 'text-[10px] bg-blue-100 text-blue-700 font-medium px-2 py-0.5 rounded-full';
                        }
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
        });
        var target = document.getElementById('case-tab-' + tabName);
        if (target) {
            target.classList.remove('hidden');
            target.classList.add('flex'); // 确保所有标签都有 flex 类
            // 只对需要 flex-col 的标签添加
            if (tabName === 'overview' || tabName === 'timeline' || tabName === 'materials') {
                target.classList.add('flex-col');
            }
            // documents 需要 flex-row
            if (tabName === 'documents') {
                target.classList.add('flex-row');
            }
            // 其他标签（evidence, contract, authorization, judgment, other）已有 flex-row，只需确保有 flex
        }
        document.querySelectorAll('.case-tab').forEach(function(b) {
            b.className = 'case-tab px-4 py-2.5 text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700 transition-colors';
        });
        if (btn) {
            btn.className = 'case-tab px-4 py-2.5 text-sm font-medium border-b-2 border-[#165DFF] text-[#165DFF] transition-colors';
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
    
    // ===== PDF在线批注 - 完整功能 =====
    // var currentPDFPage = 1; // → AppState.currentPDFPage
    // var currentZoom = 1.0; // → AppState.currentZoom
    // var currentAnnotateColor = 'bg-yellow-300'; // → AppState.currentAnnotateColor
    // var annotateHistory = []; // → AppState.annotateHistory
    // var historyIndex = -1; // → AppState.historyIndex
    
    function openPDFAnnotateModal() {
        document.getElementById('pdf-annotate-modal').classList.remove('hidden');
    }
    function closePDFAnnotateModal() {
        document.getElementById('pdf-annotate-modal').classList.add('hidden');
    }
    
    // 工具选择
    function setAnnotateTool(tool, btn) {
        document.querySelectorAll('.annotate-tool-btn').forEach(function(b) {
            b.className = 'annotate-tool-btn flex items-center gap-1 px-2.5 py-1.5 text-[11px] text-gray-600 hover:bg-gray-200 rounded-md';
        });
        if (btn) btn.className = 'annotate-tool-btn flex items-center gap-1 px-2.5 py-1.5 text-[11px] rounded-md bg-[#165DFF] text-white';
        var labels = { pan: '选择', highlight: '高亮', underline: '下划线', strikethrough: '删除线', comment: '批注', draw: '画笔', shape: '形状' };
        var label = document.getElementById('current-tool-label');
        if (label) label.textContent = labels[tool] || '选择';
    }
    
    // 颜色选择
    function selectAnnotateColor(btn, color) {
        document.querySelectorAll('.annotate-color-btn').forEach(function(b) {
            b.className = 'annotate-color-btn w-5 h-5 rounded-full border border-gray-200 ' + b.getAttribute('data-color');
        });
        btn.className = 'annotate-color-btn w-5 h-5 rounded-full border-2 border-[#165DFF] ' + color;
        AppState.currentAnnotateColor = color;
    }
    
    // 翻页
    function changePDFPage(delta) {
        AppState.currentPDFPage = Math.max(1, Math.min(8, AppState.currentPDFPage + delta));
        var el = document.getElementById('pdf-current-page');
        if (el) el.textContent = AppState.currentPDFPage;
    }
    
    // 缩放
    function zoomPDF(delta) {
        AppState.currentZoom = Math.max(0.5, Math.min(2.0, AppState.currentZoom + delta));
        var content = document.getElementById('pdf-page-content');
        if (content) {
            content.style.transform = 'scale(' + AppState.currentZoom + ')';
            content.style.transformOrigin = 'top center';
        }
        var zoomEl = document.getElementById('pdf-zoom-level');
        if (zoomEl) zoomEl.textContent = Math.round(AppState.currentZoom * 100) + '%';
        var zoomBar = document.getElementById('zoom-level-bar');
        if (zoomBar) zoomBar.textContent = Math.round(AppState.currentZoom * 100) + '%';
    }
    
    // 批注高亮定位
    function focusAnnotation(id) {
        // 高亮侧边栏对应项
        document.querySelectorAll('.annotation-item').forEach(function(item) {
            item.classList.remove('bg-blue-50', 'border-l-2', 'border-l-[#165DFF]');
        });
        var targetItem = document.querySelector('.annotation-item[data-annotation-id="' + id + '"]');
        if (targetItem) {
            targetItem.classList.add('bg-blue-50', 'border-l-2', 'border-l-[#165DFF]');
            targetItem.scrollIntoView({ block: 'nearest' });
        }
        // 高亮页面标注
        document.querySelectorAll('.annotate-marker, .annotate-comment').forEach(function(el) {
            el.style.outline = 'none';
        });
        var targetMarker = document.querySelector('[data-annotation-id="' + id + '"]');
        if (targetMarker) {
            targetMarker.style.outline = '2px solid #165DFF';
            targetMarker.style.outlineOffset = '2px';
            targetMarker.scrollIntoView({ behavior: 'smooth', block: 'center' });
            setTimeout(function() {
                targetMarker.style.outline = 'none';
            }, 2000);
        }
    }
    
    // 批注筛选
    function filterAnnotations(filter, btn) {
        document.querySelectorAll('.ann-filter-btn').forEach(function(b) {
            b.className = 'ann-filter-btn text-[10px] px-2 py-1 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200';
        });
        btn.className = 'ann-filter-btn text-[10px] px-2 py-1 rounded-full bg-[#165DFF] text-white';
        
        document.querySelectorAll('.annotation-item').forEach(function(item) {
            if (filter === 'all') {
                item.classList.remove('hidden');
            } else if (filter === 'unsolved') {
                var status = item.getAttribute('data-status');
                if (status === 'unsolved' || status === 'processing') {
                    item.classList.remove('hidden');
                } else {
                    item.classList.add('hidden');
                }
            } else if (filter === 'solved') {
                if (item.getAttribute('data-status') === 'solved') {
                    item.classList.remove('hidden');
                } else {
                    item.classList.add('hidden');
                }
            }
        });
    }
    
    // 撤销/重做
    function undoAnnotation() {
        if (AppState.historyIndex > 0) {
            AppState.historyIndex--;
            alert('撤销：回退到上一步操作（演示功能）');
        } else {
            alert('没有可撤销的操作');
        }
    }
    function redoAnnotation() {
        if (AppState.historyIndex < AppState.annotateHistory.length - 1) {
            AppState.historyIndex++;
            alert('重做：恢复已撤销操作（演示功能）');
        } else {
            alert('没有可重做的操作');
        }
    }
    
    // 新增批注（从侧边栏底部按钮触发）
    function addNewAnnotation() {
        // 选中批注工具
        var commentBtn = document.querySelector('.annotate-tool-btn[data-tool="comment"]');
        if (commentBtn) setAnnotateTool('comment', commentBtn);
        // 打开编辑弹窗
        document.getElementById('annotation-edit-content').value = '';
        document.getElementById('annotation-edit-status').value = 'unsolved';
        document.getElementById('annotation-edit-modal').classList.remove('hidden');
    }
    
    // 批注编辑弹窗
    function closeAnnotationEdit() {
        document.getElementById('annotation-edit-modal').classList.add('hidden');
    }
    function saveAnnotationEdit() {
        var content = document.getElementById('annotation-edit-content').value.trim();
        if (!content) { alert('请输入批注内容'); return; }
        var status = document.getElementById('annotation-edit-status').value;
        var statusLabels = { unsolved: '未解决', processing: '处理中', solved: '已解决' };
        var statusColors = { unsolved: 'text-yellow-600 bg-yellow-50', processing: 'text-blue-600 bg-blue-50', solved: 'text-green-600 bg-green-50' };
        
        // 添加新批注到 PDF 页面
        var container = document.querySelector('#pdf-text-content');
        if (container) {
            var newComment = document.createElement('div');
            newComment.className = 'annotate-comment bg-yellow-50 border-l-4 border-yellow-400 pl-3 py-2 pr-2 rounded-r text-xs relative mt-2';
            newComment.setAttribute('data-annotation-id', 'ann-new-' + Date.now());
            newComment.innerHTML = '<div class="flex items-center gap-1 text-yellow-600 font-medium"><iconify-icon icon="mdi:comment-text-outline" class="text-sm"></iconify-icon><span class="text-[10px]">我 · ' + new Date().toISOString().slice(0,10) + '</span><span class="text-[10px] ml-auto ' + statusColors[status].split(' ')[0] + '">' + statusLabels[status] + '</span></div><p class="text-[11px] text-gray-700 mt-0.5">' + content + '</p>';
            container.parentNode.insertBefore(newComment, container.nextSibling);
        }
        
        // 添加新批注到侧边栏
        var panelList = document.getElementById('annotations-panel-list');
        if (panelList) {
            var newItem = document.createElement('div');
            newItem.className = 'annotation-item px-4 py-3 border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition-colors';
            newItem.setAttribute('data-annotation-id', 'ann-new-' + Date.now());
            newItem.setAttribute('data-status', status);
            newItem.setAttribute('onclick', "focusAnnotation('ann-new-" + Date.now() + "')");
            newItem.innerHTML = '<div class="flex items-center gap-1.5 mb-1"><span class="w-2 h-2 rounded-full bg-yellow-400"></span><span class="text-[10px] font-medium text-gray-600">批注</span><span class="text-[10px] text-gray-400 ml-auto">我</span></div><p class="text-[11px] text-gray-700 truncate">' + content + '</p><div class="mt-1"><span class="text-[10px] ' + statusColors[status] + ' px-1 py-0.5 rounded leading-none inline-block">' + statusLabels[status] + '</span></div>';
            panelList.insertBefore(newItem, panelList.firstElementChild);
        }
        
        updateAnnotationStats();
        // 记录历史，关闭弹窗
        AppState.annotateHistory.push('new');
        AppState.historyIndex = AppState.annotateHistory.length - 1;
        closeAnnotationEdit();
    }
    
    function deleteAnnotation() {
        if (confirm('确定删除此批注？')) {
            closeAnnotationEdit();
            alert('批注已删除（演示功能）');
        }
    }
    
    // 保存所有批注
    function saveAnnotations() {
        var count = document.querySelectorAll('.annotation-item').length;
        alert('已保存 ' + count + ' 条批注（演示功能）\n批注数据已关联到案件：张三合同纠纷');
    }
    
    // 更新统计数据
    function updateAnnotationStats() {
        var total = document.querySelectorAll('.annotation-item').length;
        var unsolved = document.querySelectorAll('.annotation-item[data-status="unsolved"], .annotation-item[data-status="processing"]').length;
        var countEl = document.getElementById('annotations-count');
        if (countEl) countEl.textContent = total + ' 条';
        var countBar = document.getElementById('annotations-count-bar');
        if (countBar) countBar.textContent = total;
        var unsolvedBar = document.getElementById('unsolved-count-bar');
        if (unsolvedBar) unsolvedBar.textContent = unsolved;
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
