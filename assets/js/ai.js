/**
 * AI 对话模块 - AI 助手 + 历史 + AI 一键提取
 * 包含: AI 标签切换 + 新建对话 + 历史搜索 + 提取要素
 * 加载: 在 script.js 之前同步加载
 */


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

        function selectAIHistory(el) {
            var title = el.getAttribute('data-title') || '历史对话';
            // 切换到新对话视图
            var aiTabs = document.querySelectorAll('#sidebarTabAI .sidebar-item');
            aiTabs.forEach(item => item.classList.remove('active'));
            if (aiTabs[0]) aiTabs[0].classList.add('active');
            
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
                    if (typeof Auth !== 'undefined' && Auth.logout) {
                        Auth.logout();
                    }
                    showToast('已退出登录');
                }
            }
        }

    function selectExtractSource(btn, source) {
        document.querySelectorAll('.extract-source-btn').forEach(function(b) {
            b.className = 'extract-source-btn text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200';
        });
        btn.className = 'extract-source-btn text-xs px-3 py-1.5 rounded-full bg-[#165DFF] text-white';
        AppState.selectedExtractSource = source;
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
