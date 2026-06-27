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
                switchView('account-settings');
            } else if (action === 'upgrade') {
                switchView('subscription');
            } else if (action === 'feedback') {
                showToast('问题反馈功能开发中');
            } else if (action === 'guide') {
                showToast('用户指南功能开发中');
            } else if (action === 'contact') {
                showToast('联系我们功能开发中');
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

    // ===== AI 对话流式输出 =====

    // Enter 发送 / Shift+Enter 换行
    function handleAIInputKeydown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendAIMessage();
        }
    }

    // Mock AI 回复生成器 (按用户输入关键词分支)
    function generateMockAIReply(userInput) {
        var input = (userInput || '').trim().toLowerCase();
        if (!input) return '您好！请问有什么可以帮您的？';
        // 关键词路由
        if (input.indexOf('起诉状') >= 0 || input.indexOf('起诉') >= 0 || input.indexOf('诉状') >= 0) {
            return '好的！我来帮您起草起诉状。\n\n为了确保起诉状内容准确, 我需要了解以下信息:\n\n1. **原被告基本信息**: 姓名/名称、住所地、统一社会信用代码 (法人)\n2. **诉讼请求**: 例如要求被告支付货款 XX 元及利息\n3. **事实与理由**: 合同签订时间、主要条款、履行情况、违约事实\n4. **证据清单**: 合同、付款凭证、对账单、催款函等\n\n您可以分条告诉我, 也可以直接描述案件情况, 我会按《民事诉讼法》第 122 条规定的起诉条件为您起草。';
        }
        if (input.indexOf('答辩') >= 0 || input.indexOf('应诉') >= 0) {
            return '收到答辩状起草请求。答辩状一般包含以下结构:\n\n1. **答辩人基本信息**\n2. **案由**: 表明对原告诉讼请求的态度 (承认/反驳)\n3. **答辩理由**: 针对原告的诉求逐条回应, 并提出自己的主张\n4. **证据目录**\n5. **此致**: 写明受诉法院\n\n请告诉我:\n- 案件类型 (合同/侵权/婚姻家庭等)\n- 原告诉求的核心是什么\n- 您方的事实和理由\n- 您希望达到什么答辩目标';
        }
        if (input.indexOf('合同') >= 0 || input.indexOf('审查') >= 0 || input.indexOf('风险') >= 0) {
            return '合同审查要点如下:\n\n1. **主体资格**: 核对对方营业执照、资质、法定代表人\n2. **标的与数量**: 是否明确具体, 避免歧义\n3. **价款与支付**: 金额、币种、支付方式、账期、违约金\n4. **履行期限、地点、方式**: 明确可量化的时间节点\n5. **违约责任**: 逾期违约金比例、损失赔偿计算方式\n6. **争议解决**: 仲裁 vs 诉讼, 管辖法院约定是否有效\n7. **不可抗力 / 情势变更**: 是否覆盖疫情、政策变化\n8. **合同生效、解除、终止条件**\n\n您可以把合同关键条款贴给我, 我帮您逐条扫描风险点。';
        }
        if (input.indexOf('证据') >= 0 || input.indexOf('举证') >= 0) {
            return '证据准备要点:\n\n**三类核心证据**:\n1. **当事人主体证据**: 身份证 / 营业执照 / 法定代表人身份证明\n2. **法律关系证据**: 合同 / 协议 / 章程 / 决议\n3. **履行/侵权证据**: 履行凭证 / 损失凭证 / 现场照片 / 鉴定报告\n\n**提交注意**:\n- 证据清单 + 证明目的\n- 复印件与原件核对\n- 对方持有的证据可申请法院调取\n- 涉及商业秘密可申请不公开质证\n\n告诉我您的案件类型, 我可以列出针对性的证据清单模板。';
        }
        if (input.indexOf('类案') >= 0 || input.indexOf('判例') >= 0 || input.indexOf('检索') >= 0) {
            return '类案检索思路:\n\n1. **确定案由**: 案由关键词 (如"买卖合同纠纷")\n2. **筛选维度**: 法院层级、审理程序、裁判年份、争议焦点\n3. **关键词组合**: 主体 + 行为 + 法律关系 + 诉求\n4. **重点关注**: 最高人民法院指导案例、公报案例、典型案例\n\n我可以帮您:\n- 总结某类案件近 3 年的裁判趋势\n- 提炼特定法院的裁判口径\n- 检索您手头案件最相似的 5-10 个判例\n\n请告诉我您想研究的法律问题或争议焦点。';
        }
        if (input.indexOf('你好') >= 0 || input.indexOf('您好') >= 0 || input.indexOf('hi') >= 0) {
            return '您好！我是 LexPrime AI 助手, 可以帮您:\n\n- 起草法律文书 (起诉状 / 答辩状 / 合同 / 律师函等)\n- 审查合同风险\n- 检索类案与法条\n- 整理证据清单\n- 分析案件策略\n\n请问今天想处理什么法律事务?';
        }
        // 通用回复
        return '我已收到您的问题:「' + userInput + '」\n\n针对您的提问, 我建议按以下思路处理:\n\n1. **明确问题核心**: 先把争议焦点拆成 1-2 个核心法律问题\n2. **查找法律依据**: 检索相关法条 + 类案裁判口径\n3. **整理事实与证据**: 按时间线梳理, 区分主张与反驳\n4. **形成方案**: 文书 / 谈判 / 调解 / 诉讼 多种路径组合\n\n您可以补充更多案件细节, 例如:\n- 案件类型 (合同 / 侵权 / 婚姻 / 劳动 / 知识产权 等)\n- 当事人诉求\n- 当前所处阶段 (协商 / 起诉前 / 已立案 / 审理中)\n\n我可以进一步帮您出具针对性的方案。';
    }

    // 发送 AI 消息: 用户消息立即 append, AI 消息流式 chunk by chunk 输出
    var aiStreamingTimer = null;
    function sendAIMessage() {
        var input = document.getElementById('aiChatInput');
        var msgList = document.getElementById('aiViewMessages');
        var sendBtn = document.getElementById('aiSendBtn');
        var sendIcon = document.getElementById('aiSendIcon');
        if (!input || !msgList) return;
        var text = (input.value || '').trim();
        if (!text) { input.focus(); return; }
        if (aiStreamingTimer) {
            // 已有流在跑: 忽略, 等流完
            return;
        }
        // 1. 追加用户消息
        var userHtml = '<div class="flex gap-3 justify-end chat-message-user">' +
            '<div class="max-w-[70%] bg-brand rounded-xl p-4 shadow-sm">' +
                '<p class="text-sm leading-relaxed text-white whitespace-pre-wrap">' + escapeHtml(text) + '</p>' +
                '<span class="text-[10px] text-white/70 mt-2 block text-right">刚刚</span>' +
            '</div>' +
            '<div class="w-8 h-8 rounded-full bg-brand flex items-center justify-center text-white flex-shrink-0">' +
                '<iconify-icon class="text-sm" icon="mdi:account"></iconify-icon>' +
            '</div>' +
        '</div>';
        msgList.insertAdjacentHTML('beforeend', userHtml);
        // 2. 清空输入框 + 禁用发送按钮
        input.value = '';
        input.style.height = 'auto';
        if (sendBtn) { sendBtn.disabled = true; sendBtn.classList.add('opacity-50', 'cursor-not-allowed'); }
        if (sendIcon) sendIcon.setAttribute('icon', 'mdi:loading');
        // 3. 创建 AI 消息占位 (思考中...)
        var aiMsgId = 'ai-msg-' + Date.now();
        var aiHtml = '<div class="flex gap-3 chat-message-ai" id="' + aiMsgId + '">' +
            '<div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#165DFF] to-[#6C5CE7] flex items-center justify-center text-white flex-shrink-0">' +
                '<iconify-icon class="text-sm" icon="mdi:robot"></iconify-icon>' +
            '</div>' +
            '<div class="max-w-[70%] bg-white rounded-xl p-4 shadow-sm border border-bg-border">' +
                '<p class="text-sm leading-relaxed text-fg-secondary whitespace-pre-wrap ai-msg-content">思考中<span class="dot-flash">.</span><span class="dot-flash">.</span><span class="dot-flash">.</span></p>' +
                '<span class="text-[10px] text-fg-tertiary mt-2 block ai-msg-time">刚刚</span>' +
            '</div>' +
        '</div>';
        msgList.insertAdjacentHTML('beforeend', aiHtml);
        // 4. 滚动到底部
        msgList.scrollTop = msgList.scrollHeight;
        // 5. 生成回复 + 流式输出
        var fullReply = generateMockAIReply(text);
        streamAIMessage(aiMsgId, fullReply, function() {
            // 流完恢复发送按钮
            if (sendBtn) { sendBtn.disabled = false; sendBtn.classList.remove('opacity-50', 'cursor-not-allowed'); }
            if (sendIcon) sendIcon.setAttribute('icon', 'mdi:send');
        });
    }

    // 流式输出: 把 fullReply 按字符/词 chunk-by-chunk append 到 ai-msg-content
    function streamAIMessage(msgId, fullText, onComplete) {
        var msgEl = document.getElementById(msgId);
        if (!msgEl) { if (onComplete) onComplete(); return; }
        var contentEl = msgEl.querySelector('.ai-msg-content');
        var msgList = document.getElementById('aiViewMessages');
        if (!contentEl) { if (onComplete) onComplete(); return; }
        contentEl.textContent = ''; // 清掉 "思考中..."
        // 拆 chunk (中文按字, 英文按词, 标点独立)
        var chunks = tokenizeForStream(fullText);
        var idx = 0;
        // chunk 输出节奏: 25-45ms 一个 chunk (模拟真实流速)
        var intervalMs = 30;
        aiStreamingTimer = setInterval(function() {
            if (idx >= chunks.length) {
                clearInterval(aiStreamingTimer);
                aiStreamingTimer = null;
                if (onComplete) onComplete();
                return;
            }
            contentEl.textContent += chunks[idx];
            idx++;
            // 滚动到底
            if (msgList) msgList.scrollTop = msgList.scrollHeight;
        }, intervalMs);
    }

    // 简易分词器: 中文按字 (含标点独立), 英文按空格分词
    function tokenizeForStream(text) {
        var tokens = [];
        var i = 0;
        while (i < text.length) {
            var c = text[i];
            // 中文字符 (含 CJK 标点)
            if (/[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]/.test(c)) {
                tokens.push(c);
                i++;
            } else if (c === ' ') {
                tokens.push(' ');
                i++;
            } else if (/\s/.test(c)) {
                tokens.push(c);
                i++;
            } else {
                // 连续 ASCII 字符作为整体
                var j = i;
                while (j < text.length && !/[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\s]/.test(text[j])) {
                    j++;
                }
                tokens.push(text.substring(i, j));
                i = j;
            }
        }
        return tokens;
    }

    // 简易 escapeHtml (避免 AI 回复里 < > 破坏 DOM)
    function escapeHtml(str) {
        if (str == null) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
