(function () {
    'use strict';

    function switchAITab(tab) {
        document.querySelectorAll('.ai-subtab-btn').forEach(function (btn) {
            btn.classList.remove('active');
        });
        var activeBtn = document.querySelector('.ai-subtab-btn[data-ai-tab="' + tab + '"]');
        if (activeBtn) activeBtn.classList.add('active');

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

        document.getElementById('aiSubContent').scrollTop = 0;
    }

    function startNewChat() {
        var chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
        var aiViewMessages = document.getElementById('aiViewMessages');
        if (aiViewMessages) {
            aiViewMessages.innerHTML = '';
        }
        var welcomeHtml =
            '<div class="flex items-start gap-2 mb-3"><div class="w-7 h-7 rounded-lg bg-gradient-to-br from-[#165DFF] to-[#5B8FF9] flex items-center justify-center flex-shrink-0"><iconify-icon icon="mdi:robot" class="text-white text-sm"></iconify-icon></div><div class="bg-[#F2F3F5] rounded-xl px-3 py-2 text-xs text-gray-700"><p>您好！我是 LexPrime AI 助手，可以帮您：</p><ul class="list-disc pl-4 mt-1 space-y-0.5"><li>起草法律文书</li><li>检索类案与法条</li><li>分析案件策略</li><li>审查合同风险</li></ul><p class="mt-1">请问有什么可以帮您的？</p></div></div>';

        var chatArea = document.querySelector('#chatPanel .flex-1.overflow-y-auto');
        if (chatArea) chatArea.innerHTML = welcomeHtml;

        if (aiViewMessages) {
            aiViewMessages.innerHTML =
                '<div class="flex items-start gap-2.5 px-4 py-3">' +
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
        switchAITab('new');

        var msgList = document.getElementById('chatMessages');
        msgList.innerHTML =
            '' +
            '<div class="flex gap-2.5 chat-message-ai">' +
            '<div class="w-7 h-7 rounded-full bg-gradient-to-br from-[#165DFF] to-[#6C5CE7] flex items-center justify-center text-white flex-shrink-0 mt-0.5">' +
            '<iconify-icon class="text-[10px]" icon="mdi:robot"></iconify-icon>' +
            '</div>' +
            '<div class="chat-bubble-ai max-w-[85%]">' +
            '<p class="text-xs leading-relaxed text-[#4E5969]">已切换到对话：「<span class="font-medium text-[#165DFF]">' +
            title +
            '</span>」</p>' +
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
        items.forEach(function (item) {
            var title = item.getAttribute('data-title') || '';
            if (!keyword || title.toLowerCase().indexOf(keyword) !== -1) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }

    function switchAIView(viewId, el) {
        document.querySelectorAll('#sidebarTabAI .sidebar-item').forEach(function (item) {
            item.classList.remove('active');
        });
        if (el) el.classList.add('active');

        var aiViewChat = document.getElementById('aiViewChat');
        var aiViewSkills = document.getElementById('aiViewSkills');
        var aiViewHistory = document.getElementById('aiViewHistory');

        var viewAI = document.getElementById('view-ai');
        if (!viewAI) {
            loadView('ai', function (html) {
                document.getElementById('main-content').insertAdjacentHTML('beforeend', html);
                switchAIViewSubView(viewId);
            });
            return;
        }

        if (aiViewChat) aiViewChat.classList.add('hidden');
        if (aiViewSkills) aiViewSkills.classList.add('hidden');
        if (aiViewHistory) aiViewHistory.classList.add('hidden');

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
        var aiTabs = document.querySelectorAll('#sidebarTabAI .sidebar-item');
        aiTabs.forEach(function (item) {
            item.classList.remove('active');
        });
        if (aiTabs[0]) aiTabs[0].classList.add('active');

        document.getElementById('aiViewChat').classList.remove('hidden');
        document.getElementById('aiViewSkills').classList.add('hidden');
        document.getElementById('aiViewHistory').classList.add('hidden');

        var msgList = document.getElementById('aiViewMessages');
        if (msgList) {
            msgList.innerHTML =
                '' +
                '<div class="flex gap-3">' +
                '<div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#165DFF] to-[#6C5CE7] flex items-center justify-center text-white flex-shrink-0">' +
                '<iconify-icon class="text-sm" icon="mdi:robot"></iconify-icon>' +
                '</div>' +
                '<div class="max-w-[70%] bg-white rounded-xl p-4 shadow-sm border border-[#E5E6EB]">' +
                '<p class="text-sm leading-relaxed text-[#4E5969]">已切换到对话：<span class="font-semibold text-[#165DFF]">' +
                title +
                '</span></p>' +
                '<span class="text-[11px] text-[#86909C] mt-2 block">刚刚</span>' +
                '</div>' +
                '</div>';
        }
    }

    function filterAIHistory(input) {
        var keyword = input.value.toLowerCase().trim();
        var items = document.querySelectorAll('#aiHistoryList > div');
        items.forEach(function (item) {
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
        var otherId = tab === 'work' ? 'moreMenuAI' : 'moreMenuWork';
        var otherMenu = document.getElementById(otherId);
        if (otherMenu) otherMenu.classList.add('hidden');
        menu.classList.toggle('hidden');
    }

    async function handleMoreAction(action) {
        document.getElementById('moreMenuWork').classList.add('hidden');
        document.getElementById('moreMenuAI').classList.add('hidden');
        if (action === 'settings') {
            switchSidebarTab('work');
            switchView('account-settings');
        } else if (action === 'check-update') {
            var current = window.APP_VERSION || '0.7.0';
            Utils.showToast('info', '当前版本: v' + current + ' · 已是最新版本');
        } else if (action === 'feedback') {
            openFeedbackModal();
        } else if (action === 'guide') {
            openUserGuideModal();
        } else if (action === 'contact') {
            openContactModal();
        } else if (action === 'logout') {
            var logoutConfirm = await Utils.showConfirm('确认退出登录？');
            if (logoutConfirm) {
                if (typeof Auth !== 'undefined' && Auth.logout) {
                    Auth.logout();
                }
                Utils.showToast('success', '已退出登录');
            }
        }
    }

    var _closeAIExtractModal = null;

    function buildAIExtractContent() {
        return (
            '<div class="space-y-5">' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-primary mb-2">提取来源</label>' +
            '<div class="flex gap-2 flex-wrap">' +
            '<button class="extract-source-btn text-xs px-3 py-1.5 rounded-full bg-brand text-white" data-source="case" onclick="selectExtractSource(this, \'case\')" type="button">案件材料</button>' +
            '<button class="extract-source-btn text-xs px-3 py-1.5 rounded-full bg-bg text-fg-secondary hover:bg-bg-border" data-source="document" onclick="selectExtractSource(this, \'document\')" type="button">当前文书</button>' +
            '<button class="extract-source-btn text-xs px-3 py-1.5 rounded-full bg-bg text-fg-secondary hover:bg-bg-border" data-source="evidence" onclick="selectExtractSource(this, \'evidence\')" type="button">证据材料</button>' +
            '<button class="extract-source-btn text-xs px-3 py-1.5 rounded-full bg-bg text-fg-secondary hover:bg-bg-border" data-source="timeline" onclick="selectExtractSource(this, \'timeline\')" type="button">时间线记录</button>' +
            '</div>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-primary mb-2">提取维度</label>' +
            '<div class="grid grid-cols-2 gap-2">' +
            '<label class="flex items-center gap-2 text-xs text-fg-secondary bg-gray-50 rounded-lg px-3 py-2 cursor-pointer hover:bg-brand-tint3/50">' +
            '<input checked class="rounded border-bg-border text-brand focus:ring-brand" type="checkbox"/> 关键事实' +
            '</label>' +
            '<label class="flex items-center gap-2 text-xs text-fg-secondary bg-gray-50 rounded-lg px-3 py-2 cursor-pointer hover:bg-brand-tint3/50">' +
            '<input checked class="rounded border-bg-border text-brand focus:ring-brand" type="checkbox"/> 争议焦点' +
            '</label>' +
            '<label class="flex items-center gap-2 text-xs text-fg-secondary bg-gray-50 rounded-lg px-3 py-2 cursor-pointer hover:bg-brand-tint3/50">' +
            '<input checked class="rounded border-bg-border text-brand focus:ring-brand" type="checkbox"/> 法律依据' +
            '</label>' +
            '<label class="flex items-center gap-2 text-xs text-fg-secondary bg-gray-50 rounded-lg px-3 py-2 cursor-pointer hover:bg-brand-tint3/50">' +
            '<input class="rounded border-bg-border text-brand focus:ring-brand" type="checkbox"/> 风险提示' +
            '</label>' +
            '<label class="flex items-center gap-2 text-xs text-fg-secondary bg-gray-50 rounded-lg px-3 py-2 cursor-pointer hover:bg-brand-tint3/50">' +
            '<input class="rounded border-bg-border text-brand focus:ring-brand" type="checkbox"/> 时间节点' +
            '</label>' +
            '<label class="flex items-center gap-2 text-xs text-fg-secondary bg-gray-50 rounded-lg px-3 py-2 cursor-pointer hover:bg-brand-tint3/50">' +
            '<input class="rounded border-bg-border text-brand focus:ring-brand" type="checkbox"/> 证据摘要' +
            '</label>' +
            '</div>' +
            '</div>' +
            '<div class="hidden space-y-3" id="extract-result-area">' +
            '<div class="flex items-center justify-between">' +
            '<h4 class="text-xs font-semibold text-fg-secondary">提取结果</h4>' +
            '<div class="flex items-center gap-2">' +
            '<button class="text-[10px] text-brand hover:underline" onclick="copyExtractResult()">复制结果</button>' +
            '<button class="text-[10px] text-brand hover:underline" onclick="exportExtractResult()">导出报告</button>' +
            '</div>' +
            '</div>' +
            '<div class="bg-brand-tint3/50 rounded-lg border border-blue-100 p-3">' +
            '<div class="flex items-center gap-1.5 mb-2">' +
            '<iconify-icon class="text-brand text-sm" icon="mdi:lightbulb-outline"></iconify-icon>' +
            '<span class="text-xs font-semibold text-brand">关键事实</span>' +
            '</div>' +
            '<ul class="space-y-1">' +
            '<li class="text-xs text-fg-primary flex items-start gap-1.5"><span class="text-brand mt-0.5">•</span>张三于2025年3月与李四签订《借款合同》，约定借款金额50万元</li>' +
            '<li class="text-xs text-fg-primary flex items-start gap-1.5"><span class="text-brand mt-0.5">•</span>借款期限12个月，年利率12%，按月付息</li>' +
            '<li class="text-xs text-fg-primary flex items-start gap-1.5"><span class="text-brand mt-0.5">•</span>张三已支付利息至2026年2月，本金未归还</li>' +
            '<li class="text-xs text-fg-primary flex items-start gap-1.5"><span class="text-brand mt-0.5">•</span>李四于2026年4月发出催收函，张三未回应</li>' +
            '</ul>' +
            '</div>' +
            '<div class="bg-purple-50/50 rounded-lg border border-purple-100 p-3">' +
            '<div class="flex items-center gap-1.5 mb-2">' +
            '<iconify-icon class="text-purple-500 text-sm" icon="mdi:scale-balance"></iconify-icon>' +
            '<span class="text-xs font-semibold text-wiki">争议焦点</span>' +
            '</div>' +
            '<ul class="space-y-1">' +
            '<li class="text-xs text-fg-primary flex items-start gap-1.5"><span class="text-purple-500 mt-0.5">•</span>借款利率是否超过法定上限（LPR的4倍）</li>' +
            '<li class="text-xs text-fg-primary flex items-start gap-1.5"><span class="text-purple-500 mt-0.5">•</span>张三主张已通过现金方式部分还款是否成立</li>' +
            '</ul>' +
            '</div>' +
            '<div class="bg-green-50/50 rounded-lg border border-green-100 p-3">' +
            '<div class="flex items-center gap-1.5 mb-2">' +
            '<iconify-icon class="text-green-500 text-sm" icon="mdi:book-open-page-variant-outline"></iconify-icon>' +
            '<span class="text-xs font-semibold text-success">法律依据</span>' +
            '</div>' +
            '<ul class="space-y-1">' +
            '<li class="text-xs text-fg-primary flex items-start gap-1.5"><span class="text-green-500 mt-0.5">•</span>《中华人民共和国民法典》第六百六十七条：借款合同定义</li>' +
            '<li class="text-xs text-fg-primary flex items-start gap-1.5"><span class="text-green-500 mt-0.5">•</span>《最高人民法院关于审理民间借贷案件适用法律若干问题的规定》第二十五条</li>' +
            '</ul>' +
            '</div>' +
            '<div class="text-[10px] text-fg-tertiary italic border-t border-gray-100 pt-2">AI辅助生成，仅供参考。建议律师结合案件实际核查。</div>' +
            '</div>' +
            '<div class="hidden flex items-center justify-center gap-2 py-8" id="extract-loading">' +
            '<div class="w-5 h-5 border-2 border-brand border-t-transparent rounded-full animate-spin"></div>' +
            '<span class="text-xs text-fg-tertiary">AI 正在分析案件材料...</span>' +
            '</div>' +
            '</div>'
        );
    }

    function openAIExtractModal() {
        var content = buildAIExtractContent();
        var footer =
            '' +
            '<button class="px-4 py-2 text-sm text-fg-secondary hover:bg-bg rounded-lg transition-colors" onclick="closeAIExtractModal()">关闭</button>' +
            '<button class="px-4 py-2 text-sm text-white bg-brand hover:bg-brand/90 rounded-lg transition-colors flex items-center gap-1.5" onclick="startAIExtract()">' +
            '<iconify-icon class="text-sm" icon="mdi:robot-outline"></iconify-icon> 开始提取' +
            '</button>';

        if (_closeAIExtractModal) _closeAIExtractModal();

        _closeAIExtractModal = Utils.showModal({
            id: 'ai-extract-modal',
            title: 'AI 一键提取要点',
            icon: 'mdi:robot',
            content: content,
            footer: footer,
            size: 'lg',
            onClose: function () {
                _closeAIExtractModal = null;
            }
        });

        setTimeout(function () {
            var extractResultArea = document.getElementById('extract-result-area');
            var extractLoading = document.getElementById('extract-loading');
            if (extractResultArea) extractResultArea.classList.add('hidden');
            if (extractLoading) extractLoading.classList.add('hidden');
            if (typeof AppState !== 'undefined') AppState.selectedExtractSource = 'case';
        }, 50);
    }

    function selectExtractSource(btn, source) {
        document.querySelectorAll('.extract-source-btn').forEach(function (b) {
            b.className =
                'extract-source-btn text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200';
        });
        btn.className = 'extract-source-btn text-xs px-3 py-1.5 rounded-full bg-[#165DFF] text-white';
        AppState.selectedExtractSource = source;
    }

    function closeAIExtractModal() {
        if (_closeAIExtractModal) {
            _closeAIExtractModal();
            _closeAIExtractModal = null;
        }
    }

    function startAIExtract() {
        document.getElementById('extract-loading').classList.remove('hidden');
        document.getElementById('extract-result-area').classList.add('hidden');
        setTimeout(function () {
            document.getElementById('extract-loading').classList.add('hidden');
            document.getElementById('extract-result-area').classList.remove('hidden');
        }, 2000);
    }

    function copyExtractResult() {
        showToast('提取结果已复制到剪贴板');
    }

    function exportExtractResult() {
        Utils.showToast('success', '报告已导出为Markdown格式（演示功能）');
    }

    function toggleAISidebar() {
        var sidebar = document.querySelector('#view-ai > div > div:first-child');
        if (sidebar) {
            sidebar.classList.toggle('hidden');
            sidebar.classList.toggle('lg:flex');
            sidebar.classList.toggle('fixed');
            sidebar.classList.toggle('inset-y-0');
            sidebar.classList.toggle('left-0');
            sidebar.classList.toggle('z-50');
        }
    }

    function quickAsk(question) {
        var input = document.getElementById('aiChatInput');
        if (input) {
            input.value = question;
            input.focus();
        }
        sendAIMessage();
    }

    function handleAIInputKeydown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendAIMessage();
        }
    }

    function generateMockAIReply(userInput) {
        var input = (userInput || '').trim().toLowerCase();
        if (!input) return '您好！请问有什么可以帮您的？';
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
        return (
            '我已收到您的问题:「' +
            userInput +
            '」\n\n针对您的提问, 我建议按以下思路处理:\n\n1. **明确问题核心**: 先把争议焦点拆成 1-2 个核心法律问题\n2. **查找法律依据**: 检索相关法条 + 类案裁判口径\n3. **整理事实与证据**: 按时间线梳理, 区分主张与反驳\n4. **形成方案**: 文书 / 谈判 / 调解 / 诉讼 多种路径组合\n\n您可以补充更多案件细节, 例如:\n- 案件类型 (合同 / 侵权 / 婚姻 / 劳动 / 知识产权 等)\n- 当事人诉求\n- 当前所处阶段 (协商 / 起诉前 / 已立案 / 审理中)\n\n我可以进一步帮您出具针对性的方案。'
        );
    }

    var aiStreamingTimer = null;
    var _aiConversationId = null;

    async function sendAIMessage() {
        var input = document.getElementById('aiChatInput');
        var msgList = document.getElementById('aiViewMessages');
        var sendBtn = document.getElementById('aiSendBtn');
        var sendIcon = document.getElementById('aiSendIcon');
        if (!input || !msgList) return;
        var text = (input.value || '').trim();
        if (!text) {
            input.focus();
            return;
        }
        if (aiStreamingTimer) {
            return;
        }

        var userHtml =
            '<div class="flex gap-3 justify-end chat-message-user">' +
            '<div class="max-w-[70%] bg-brand rounded-xl p-4 shadow-sm">' +
            '<p class="text-sm leading-relaxed text-white whitespace-pre-wrap">' +
            escapeHtml(text) +
            '</p>' +
            '<span class="text-[10px] text-white/70 mt-2 block text-right">刚刚</span>' +
            '</div>' +
            '<div class="w-8 h-8 rounded-full bg-brand flex items-center justify-center text-white flex-shrink-0">' +
            '<iconify-icon class="text-sm" icon="mdi:account"></iconify-icon>' +
            '</div>' +
            '</div>';
        msgList.insertAdjacentHTML('beforeend', userHtml);
        input.value = '';
        input.style.height = 'auto';
        if (sendBtn) {
            sendBtn.disabled = true;
            sendBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }
        if (sendIcon) sendIcon.setAttribute('icon', 'mdi:loading');

        var aiMsgId = 'ai-msg-' + Date.now();
        var aiHtml =
            '<div class="flex gap-3 chat-message-ai" id="' +
            aiMsgId +
            '">' +
            '<div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#165DFF] to-[#6C5CE7] flex items-center justify-center text-white flex-shrink-0">' +
            '<iconify-icon class="text-sm" icon="mdi:robot"></iconify-icon>' +
            '</div>' +
            '<div class="max-w-[70%] bg-white rounded-xl p-4 shadow-sm border border-bg-border">' +
            '<p class="text-sm leading-relaxed text-fg-secondary whitespace-pre-wrap ai-msg-content"><span class="ai-thinking-text">AI 思考中<span class="dot-flash">.</span><span class="dot-flash">.</span><span class="dot-flash">.</span></span></p>' +
            '<span class="text-[10px] text-fg-tertiary mt-2 block ai-msg-time">刚刚</span>' +
            '<div class="ai-error-area hidden mt-2 text-xs text-danger bg-danger-tint/30 rounded-lg p-2 border border-danger/20"></div>' +
            '<div class="ai-retry-area hidden mt-2">' +
            '<button class="text-xs text-brand hover:underline" onclick="retryAIMessage(\'' + aiMsgId + '\', \'' + escapeHtml(text).replace(/'/g, '\\\'') + '\')">重试</button>' +
            '</div>' +
            '</div>' +
            '</div>';
        msgList.insertAdjacentHTML('beforeend', aiHtml);
        msgList.scrollTop = msgList.scrollHeight;

        try {
            var result = await callAIChat(text);
            streamAIMessage(aiMsgId, result.reply, function () {
                if (sendBtn) {
                    sendBtn.disabled = false;
                    sendBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                }
                if (sendIcon) sendIcon.setAttribute('icon', 'mdi:send');
            });
            if (result.conversation_id) {
                _aiConversationId = result.conversation_id;
            }
        } catch (err) {
            showAIError(aiMsgId, err.message || 'AI 服务暂时不可用，请稍后重试');
            if (sendBtn) {
                sendBtn.disabled = false;
                sendBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            }
            if (sendIcon) sendIcon.setAttribute('icon', 'mdi:send');
        }
    }

    async function callAIChat(message) {
        if (typeof API !== 'undefined' && API.ai && API.ai.chat) {
            try {
                var res = await API.ai.chat(message, {
                    conversationId: _aiConversationId
                });
                if (res && res.ok && res.data) {
                    return res.data;
                }
                throw new Error(res && res.data ? (res.data.detail || res.data.message || 'API 请求失败') : 'API 请求失败');
            } catch (apiErr) {
                console.warn('AI API 调用失败，降级到本地 mock:', apiErr);
            }
        }
        return {
            reply: generateMockAIReply(message),
            conversation_id: _aiConversationId || ('mock-conv-' + Date.now())
        };
    }

    function showAIError(msgId, errorMsg) {
        var msgEl = document.getElementById(msgId);
        if (!msgEl) return;
        var contentEl = msgEl.querySelector('.ai-msg-content');
        var errorEl = msgEl.querySelector('.ai-error-area');
        var retryEl = msgEl.querySelector('.ai-retry-area');
        var thinkingEl = msgEl.querySelector('.ai-thinking-text');
        if (thinkingEl) thinkingEl.style.display = 'none';
        if (contentEl) contentEl.textContent = '抱歉，AI 服务暂时不可用';
        if (errorEl) {
            errorEl.textContent = errorMsg;
            errorEl.classList.remove('hidden');
        }
        if (retryEl) retryEl.classList.remove('hidden');
    }

    function retryAIMessage(msgId, message) {
        var msgEl = document.getElementById(msgId);
        if (!msgEl) return;
        var contentEl = msgEl.querySelector('.ai-msg-content');
        var errorEl = msgEl.querySelector('.ai-error-area');
        var retryEl = msgEl.querySelector('.ai-retry-area');
        var thinkingEl = msgEl.querySelector('.ai-thinking-text');
        if (contentEl) contentEl.innerHTML = '<span class="ai-thinking-text">AI 思考中<span class="dot-flash">.</span><span class="dot-flash">.</span><span class="dot-flash">.</span></span>';
        if (errorEl) errorEl.classList.add('hidden');
        if (retryEl) retryEl.classList.add('hidden');

        callAIChat(message).then(function (result) {
            streamAIMessage(msgId, result.reply);
            if (result.conversation_id) {
                _aiConversationId = result.conversation_id;
            }
        }).catch(function (err) {
            showAIError(msgId, err.message || '重试失败，请稍后再试');
        });
    }

    function streamAIMessage(msgId, fullText, onComplete) {
        var msgEl = document.getElementById(msgId);
        if (!msgEl) {
            if (onComplete) onComplete();
            return;
        }
        var contentEl = msgEl.querySelector('.ai-msg-content');
        var msgList = document.getElementById('aiViewMessages');
        if (!contentEl) {
            if (onComplete) onComplete();
            return;
        }
        contentEl.textContent = '';
        var chunks = tokenizeForStream(fullText);
        var idx = 0;
        var intervalMs = 30;
        aiStreamingTimer = setInterval(function () {
            if (idx >= chunks.length) {
                clearInterval(aiStreamingTimer);
                aiStreamingTimer = null;
                if (onComplete) onComplete();
                return;
            }
            contentEl.textContent += chunks[idx];
            idx++;
            if (msgList) msgList.scrollTop = msgList.scrollHeight;
        }, intervalMs);
    }

    function tokenizeForStream(text) {
        var tokens = [];
        var i = 0;
        while (i < text.length) {
            var c = text[i];
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

    function escapeHtml(str) {
        if (str === null) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function ensureMoreModal() {
        var existing = document.getElementById('more-action-modal');
        if (existing) return existing;
        var wrapper = document.createElement('div');
        wrapper.id = 'more-action-modal';
        wrapper.className = 'hidden fixed inset-0 z-[1000] bg-black/40 flex items-center justify-center p-4';
        wrapper.onclick = function (e) {
            if (e.target === wrapper) wrapper.classList.add('hidden');
        };
        wrapper.innerHTML =
            '<div class="bg-white rounded-xl w-[480px] max-h-[80vh] flex flex-col shadow-2xl" onclick="event.stopPropagation()">' +
            '<div class="flex items-center justify-between p-4 border-b border-bg-border">' +
            '<h3 class="text-base font-semibold text-fg-primary" id="more-action-title">标题</h3>' +
            '<button class="text-fg-tertiary hover:text-fg-secondary" aria-label="关闭" onclick="document.getElementById(\'more-action-modal\').classList.add(\'hidden\')"><iconify-icon icon="mdi:close" class="text-xl"></iconify-icon></button>' +
            '</div>' +
            '<div class="p-5 overflow-y-auto" id="more-action-body"></div>' +
            '<div class="p-4 border-t border-bg-border flex justify-end gap-2" id="more-action-footer"></div>' +
            '</div>';
        document.body.appendChild(wrapper);
        return wrapper;
    }

    function showMoreModal(title, bodyHtml, footerHtml) {
        var m = ensureMoreModal();
        document.getElementById('more-action-title').textContent = title;
        document.getElementById('more-action-body').innerHTML = bodyHtml;
        document.getElementById('more-action-footer').innerHTML = footerHtml || '';
        m.classList.remove('hidden');
    }

    function openFeedbackModal() {
        showMoreModal(
            '问题反馈',
            '<p class="text-sm text-fg-secondary mb-3">感谢您的反馈, 我们会尽快查看并改进。</p>' +
                '<label class="block text-xs text-fg-tertiary mb-1">问题类型</label>' +
                '<select id="feedback-type" class="w-full mb-3 bg-bg-subtle border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand focus:bg-white">' +
                '<option>功能建议</option><option>界面问题</option><option>性能问题</option><option>数据错误</option><option>其他</option>' +
                '</select>' +
                '<label class="block text-xs text-fg-tertiary mb-1">详细描述</label>' +
                '<textarea id="feedback-content" rows="5" placeholder="请描述问题或建议..." class="w-full bg-bg-subtle border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand focus:bg-white resize-none"></textarea>' +
                '<label class="block text-xs text-fg-tertiary mb-1 mt-3">联系邮箱 (可选)</label>' +
                '<input id="feedback-email" type="email" placeholder="your@email.com" class="w-full bg-bg-subtle border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand focus:bg-white"/>',
            '<button class="px-3 py-1.5 text-xs text-fg-secondary hover:bg-bg-subtle rounded-lg" onclick="document.getElementById(\'more-action-modal\').classList.add(\'hidden\')">取消</button>' +
                '<button class="px-4 py-1.5 text-xs font-semibold text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="submitFeedback()">提交反馈</button>'
        );
    }

    function submitFeedback() {
        var type = (document.getElementById('feedback-type') || {}).value || '';
        var content = (document.getElementById('feedback-content') || {}).value || '';
        var email = (document.getElementById('feedback-email') || {}).value || '';
        if (!content.trim()) {
            showToast('请填写详细描述', 'warning');
            return;
        }
        var list = JSON.parse(localStorage.getItem('lexprime_feedback') || '[]');
        list.push({ ts: Date.now(), type: type, content: content, email: email });
        localStorage.setItem('lexprime_feedback', JSON.stringify(list));
        document.getElementById('more-action-modal').classList.add('hidden');
        showToast('反馈已提交, 感谢您的支持!', 'success');
    }

    function openUserGuideModal() {
        showMoreModal(
            '用户指南',
            '<div class="text-sm text-fg-secondary space-y-3">' +
                '<div class="bg-brand-tint3 p-3 rounded-lg"><p class="font-semibold text-fg-primary mb-1">快速开始</p><p>登录后进入工作台, 点击左侧菜单选择功能 (案件管理 / 日程 / 客户 / 模板 / 智库等)。</p></div>' +
                '<div><p class="font-semibold text-fg-primary mb-1">案件管理</p><p>在"案件管理"列表新建/编辑/归档案件, 详情页可编辑当事人、证据目录、时间线、案件分析。</p></div>' +
                '<div><p class="font-semibold text-fg-primary mb-1">日程管理</p><p>工作台"今日日程"或左侧"日程管理"查看, 支持新增/编辑/冲突检测。</p></div>' +
                '<div><p class="font-semibold text-fg-primary mb-1">AI 助手 (智库问答)</p><p>切换到 "AI 对话" 标签, 选择对话或新开会话, 提问法律问题 (基于判例库 / 法规库 / 客户档案 RAG 检索)。</p></div>' +
                '<div><p class="font-semibold text-fg-primary mb-1">模板管理</p><p>左侧"模板管理": 官方模板 (内置 8 大类) / 个人模板 (自建分类)。点击"+"上传本地模板 (.docx / .md)。</p></div>' +
                '<div><p class="font-semibold text-fg-primary mb-1">快捷键</p><p>Ctrl+K (智库搜索) / Ctrl+/ (AI 助手) / Esc (关闭弹窗)。</p></div>' +
                '<div><p class="font-semibold text-fg-primary mb-1">常见问题</p><p>遇到问题: 点击"更多 → 问题反馈", 24h 内回复。</p></div>' +
                '</div>',
            '<button class="px-4 py-1.5 text-xs font-semibold text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="document.getElementById(\'more-action-modal\').classList.add(\'hidden\')">我知道了</button>'
        );
    }

    function openContactModal() {
        showMoreModal(
            '联系我们',
            '<div class="text-sm text-fg-secondary space-y-3">' +
                '<div class="flex items-start gap-3 p-3 bg-brand-tint3 rounded-lg">' +
                '<iconify-icon class="text-xl text-brand flex-shrink-0" icon="mdi:email-outline"></iconify-icon>' +
                '<div><p class="font-semibold text-fg-primary">商务合作</p><p class="mt-0.5">contact@lexprime.cn</p></div>' +
                '</div>' +
                '<div class="flex items-start gap-3 p-3 bg-bg-subtle rounded-lg">' +
                '<iconify-icon class="text-xl text-fg-tertiary flex-shrink-0" icon="mdi:shield-account-outline"></iconify-icon>' +
                '<div><p class="font-semibold text-fg-primary">技术/账号支持</p><p class="mt-0.5">support@lexprime.cn</p></div>' +
                '</div>' +
                '<div class="flex items-start gap-3 p-3 bg-bg-subtle rounded-lg">' +
                '<iconify-icon class="text-xl text-fg-tertiary flex-shrink-0" icon="mdi:cellphone"></iconify-icon>' +
                '<div><p class="font-semibold text-fg-primary">紧急热线 (工作日 9:00-18:00)</p><p class="mt-0.5">400-LEX-PRIME (400-539-774)</p></div>' +
                '</div>' +
                '<div class="flex items-start gap-3 p-3 bg-bg-subtle rounded-lg">' +
                '<iconify-icon class="text-xl text-fg-tertiary flex-shrink-0" icon="mdi:map-marker-outline"></iconify-icon>' +
                '<div><p class="font-semibold text-fg-primary">公司地址</p><p class="mt-0.5">北京市朝阳区建国路 88 号 SOHO 现代城 B 座 18 层</p></div>' +
                '</div>' +
                '<div class="flex items-start gap-3 p-3 bg-bg-subtle rounded-lg">' +
                '<iconify-icon class="text-xl text-fg-tertiary flex-shrink-0" icon="mdi:wechat"></iconify-icon>' +
                '<div><p class="font-semibold text-fg-primary">微信公众号</p><p class="mt-0.5">LexPrime元枢法智 (lawyer-assistant)</p></div>' +
                '</div>' +
                '</div>',
            '<button class="px-4 py-1.5 text-xs font-semibold text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="document.getElementById(\'more-action-modal\').classList.add(\'hidden\')">关闭</button>'
        );
    }

    // ===== 通用流式输出工具 =====
    function streamTextToElement(elementId, text, onComplete) {
        var el = document.getElementById(elementId);
        if (!el) {
            if (onComplete) onComplete();
            return null;
        }
        el.textContent = '';
        var tokens = tokenizeForStream(text);
        var idx = 0;
        var timer = setInterval(function () {
            if (idx >= tokens.length) {
                clearInterval(timer);
                if (onComplete) onComplete();
                return;
            }
            var chunkSize = Math.min(2, tokens.length - idx);
            var chunk = tokens.slice(idx, idx + chunkSize).join('');
            el.textContent += chunk;
            idx += chunkSize;
            var scrollContainer = el.closest('.overflow-y-auto');
            if (scrollContainer) {
                scrollContainer.scrollTop = scrollContainer.scrollHeight;
            }
        }, 25);
        return timer;
    }

    function streamHtmlToElement(elementId, htmlText, onComplete) {
        var el = document.getElementById(elementId);
        if (!el) {
            if (onComplete) onComplete();
            return null;
        }
        el.innerHTML = '';
        var tokens = tokenizeForStream(htmlText);
        var idx = 0;
        var currentHtml = '';
        var timer = setInterval(function () {
            if (idx >= tokens.length) {
                clearInterval(timer);
                if (onComplete) onComplete();
                return;
            }
            var chunkSize = Math.min(3, tokens.length - idx);
            var chunk = tokens.slice(idx, idx + chunkSize).join('');
            currentHtml += chunk;
            el.innerHTML = currentHtml;
            idx += chunkSize;
            var scrollContainer = el.closest('.overflow-y-auto');
            if (scrollContainer) {
                scrollContainer.scrollTop = scrollContainer.scrollHeight;
            }
        }, 20);
        return timer;
    }

    // ===== AI 案件摘要功能 =====
    var _caseSummaryTimer = null;

    function generateCaseSummary(caseData) {
        var data = caseData || {};
        var caseName = data.caseName || '某案件';
        var caseType = data.caseType || '合同纠纷';
        var parties = data.parties || '原告与被告';
        var amount = data.amount || 'XX万元';

        var summary = {
            overview:
                '**案件概况**\n\n本案为' +
                caseType +
                '案件，案号为' +
                (data.caseNumber || '(2026)京01民初XX号') +
                '。\n\n**当事人情况：**\n- ' +
                parties +
                '\n- 涉案金额：' +
                amount +
                '\n- 受理法院：' +
                (data.court || '北京市第一中级人民法院') +
                '\n\n**案件背景：**\n原被告双方于' +
                (data.signDate || '2025年') +
                '签订相关合同，后因履行过程中产生争议，原告遂提起诉讼。',
            disputes:
                '**争议焦点**\n\n1. **合同效力问题**：案涉合同是否合法有效，双方权利义务如何认定\n2. **违约事实认定**：被告是否存在违约行为，违约程度如何\n3. **损失计算标准**：原告主张的损失金额是否有事实和法律依据\n4. **责任承担比例**：双方是否均有过错，责任如何划分',
            evidence:
                '**证据分析**\n\n**优势证据：**\n- 书面合同原件，证明双方权利义务关系\n- 履行凭证（送货单/对账单/转账记录等），证明合同履行情况\n- 沟通记录（邮件/微信/函件），证明双方协商过程\n\n**证据薄弱点：**\n- 部分口头约定缺乏书面佐证\n- 损失计算依据需进一步补强\n- 部分证据形成时间存在疑点',
            risk:
                '**风险评估**\n\n**诉讼风险（中等偏高）：**\n- 事实认定风险：部分事实缺乏直接证据支持\n- 法律适用风险：相关法律条款存在解释空间\n- 执行风险：被告偿付能力需进一步调查\n\n**建议应对：**\n- 补充关键证据，形成完整证据链\n- 申请财产保全，确保判决可执行\n- 做好调解预案，降低诉讼成本',
            nextSteps:
                '**下一步建议**\n\n1. **证据补强**（3日内）：补充完善关键证据，特别是损失计算依据\n2. **保全申请**（5日内）：向法院申请财产保全，查封被告银行账户及资产\n3. **庭前准备**（开庭前）：准备质证意见、代理词、答辩预案\n4. **调解策略**：在诉讼过程中保持调解渠道，争取最优解决方案\n5. **执行预案**：提前调查被告财产线索，为执行阶段做准备'
        };

        return summary;
    }

    function generateCaseSummaryHtml(summary) {
        var sections = [
            { key: 'overview', title: '案件概况', icon: 'mdi:file-document-outline', color: 'blue' },
            { key: 'disputes', title: '争议焦点', icon: 'mdi:scale-balance', color: 'purple' },
            { key: 'evidence', title: '证据分析', icon: 'mdi:file-find-outline', color: 'green' },
            { key: 'risk', title: '风险评估', icon: 'mdi:alert-triangle-outline', color: 'amber' },
            { key: 'nextSteps', title: '下一步建议', icon: 'mdi:route', color: 'red' }
        ];

        var html = '';
        sections.forEach(function (section) {
            var content = summary[section.key] || '';
            var colorClass = {
                blue: 'from-blue-500 to-brand',
                purple: 'from-purple-500 to-wiki',
                green: 'from-green-500 to-success',
                amber: 'from-amber-500 to-warning',
                red: 'from-red-500 to-danger'
            }[section.color];
            var bgClass = {
                blue: 'bg-blue-50 border-blue-100',
                purple: 'bg-purple-50 border-purple-100',
                green: 'bg-green-50 border-green-100',
                amber: 'bg-amber-50 border-amber-100',
                red: 'bg-red-50 border-red-100'
            }[section.color];
            var textClass = {
                blue: 'text-brand',
                purple: 'text-wiki',
                green: 'text-success',
                amber: 'text-warning',
                red: 'text-danger'
            }[section.color];

            html +=
                '<div class="ai-summary-section mb-4">' +
                '<div class="flex items-center gap-2.5 mb-3">' +
                '<div class="w-8 h-8 rounded-lg bg-gradient-to-br ' +
                colorClass +
                ' flex items-center justify-center flex-shrink-0 shadow-sm">' +
                '<iconify-icon icon="' +
                section.icon +
                '" class="text-white text-base"></iconify-icon>' +
                '</div>' +
                '<h4 class="text-sm font-bold text-fg-primary">' +
                section.title +
                '</h4>' +
                '</div>' +
                '<div class="' +
                bgClass +
                ' border rounded-xl p-4 ml-10">' +
                '<div class="text-xs text-fg-secondary leading-relaxed whitespace-pre-wrap ai-summary-content" data-section="' +
                section.key +
                '">' +
                escapeHtml(content) +
                '</div>' +
                '</div>' +
                '</div>';
        });

        html +=
            '<div class="mt-6 pt-4 border-t border-bg-border">' +
            '<div class="flex items-start gap-2 p-3 bg-bg-subtle rounded-lg">' +
            '<iconify-icon icon="mdi:information-outline" class="text-fg-tertiary text-base flex-shrink-0 mt-0.5"></iconify-icon>' +
            '<p class="text-[11px] text-fg-tertiary leading-relaxed">' +
            'AI 生成内容仅供参考，不构成法律意见。具体案件请结合实际情况，由专业律师审核判断。' +
            '</p>' +
            '</div>' +
            '</div>';

        return html;
    }

    function openCaseSummaryModal() {
        var caseName = (document.getElementById('case-detail-title') || {}).textContent || '案件';
        var caseNumber = (document.getElementById('field-basic-caseNumber-header') || {}).textContent || '';

        var content =
            '<div class="ai-summary-modal">' +
            '<div class="ai-summary-header bg-gradient-to-r from-brand via-brand to-ai rounded-xl p-5 mb-4 relative overflow-hidden">' +
            '<div class="absolute top-0 right-0 w-40 h-40 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2 blur-2xl"></div>' +
            '<div class="relative z-10 flex items-center gap-3">' +
            '<div class="w-12 h-12 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center flex-shrink-0">' +
            '<iconify-icon icon="mdi:robot" class="text-2xl text-white"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<h3 class="text-lg font-bold text-white mb-0.5">AI 案件摘要</h3>' +
            '<p class="text-xs text-white/80">' +
            escapeHtml(caseName) +
            (caseNumber ? ' · ' + caseNumber : '') +
            '</p>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '<div class="ai-summary-loading flex flex-col items-center justify-center py-12" id="case-summary-loading">' +
            '<div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-tint to-brand-tint2 flex items-center justify-center mb-4 animate-pulse">' +
            '<iconify-icon icon="mdi:brain" class="text-3xl text-brand animate-bounce"></iconify-icon>' +
            '</div>' +
            '<p class="text-sm font-medium text-fg-primary mb-1">AI 正在分析案件...</p>' +
            '<p class="text-xs text-fg-tertiary">正在整理案件概况、争议焦点、证据分析等内容</p>' +
            '<div class="mt-4 w-64">' +
            '<div class="skeleton skeleton-line mb-2"></div>' +
            '<div class="skeleton skeleton-line mb-2" style="width: 80%;"></div>' +
            '<div class="skeleton skeleton-line" style="width: 60%;"></div>' +
            '</div>' +
            '</div>' +
            '<div class="ai-summary-content-wrap hidden max-h-[50vh] overflow-y-auto pr-2" id="case-summary-content"></div>' +
            '</div>';

        var footer =
            '<div class="flex items-center justify-between w-full">' +
            '<div class="flex items-center gap-2">' +
            '<button class="text-xs text-fg-tertiary hover:text-fg-secondary transition-colors flex items-center gap-1" onclick="regenerateCaseSummary()">' +
            '<iconify-icon icon="mdi:refresh" class="text-sm"></iconify-icon>重新生成' +
            '</button>' +
            '</div>' +
            '<div class="flex items-center gap-2">' +
            '<button class="px-3 py-1.5 text-xs text-fg-secondary bg-bg-subtle hover:bg-bg rounded-lg transition-colors flex items-center gap-1" onclick="copyCaseSummary()">' +
            '<iconify-icon icon="mdi:content-copy" class="text-sm"></iconify-icon>复制' +
            '</button>' +
            '<button class="px-3 py-1.5 text-xs text-fg-secondary bg-bg-subtle hover:bg-bg rounded-lg transition-colors flex items-center gap-1" onclick="exportCaseSummary()">' +
            '<iconify-icon icon="mdi:download" class="text-sm"></iconify-icon>导出' +
            '</button>' +
            '<button class="px-4 py-1.5 text-xs text-white bg-gradient-to-r from-brand to-ai hover:shadow-md hover:shadow-brand/20 rounded-lg transition-all flex items-center gap-1" onclick="closeCaseSummaryModal()">' +
            '完成' +
            '</button>' +
            '</div>' +
            '</div>';

        if (_closeCaseSummaryModal) _closeCaseSummaryModal();

        _closeCaseSummaryModal = Utils.showModal({
            id: 'case-summary-modal',
            title: '',
            content: content,
            footer: footer,
            size: 'xl',
            hideHeader: true,
            onClose: function () {
                _closeCaseSummaryModal = null;
                if (_caseSummaryTimer) {
                    clearInterval(_caseSummaryTimer);
                    _caseSummaryTimer = null;
                }
            }
        });

        setTimeout(startCaseSummary, 600);
    }

    var _closeCaseSummaryModal = null;

    async function startCaseSummary() {
        var caseData = {
            caseName: (document.getElementById('case-detail-title') || {}).textContent || '',
            caseNumber: (document.getElementById('field-basic-caseNumber-header') || {}).textContent || '',
            caseType: (document.getElementById('field-basic-caseType') || {}).textContent || '',
            amount: (document.getElementById('field-basic-claimAmount') || {}).textContent || '',
            court: (document.querySelector('.case-detail-court') || {}).textContent || '北京市第一中级人民法院',
            signDate: (document.getElementById('field-basic-signDate') || {}).textContent || '',
            plaintiff: (document.getElementById('field-client-name') || {}).textContent || '',
            defendant: (document.getElementById('field-opponent-name') || {}).textContent || ''
        };

        var loadingEl = document.getElementById('case-summary-loading');
        var contentEl = document.getElementById('case-summary-content');
        if (!loadingEl || !contentEl) return;

        try {
            var summary = await callAICaseSummary(caseData);
            var html = generateCaseSummaryHtml(summary);

            loadingEl.classList.add('hidden');
            contentEl.classList.remove('hidden');
            contentEl.innerHTML = html;

            streamCaseSummarySections(summary);
        } catch (err) {
            showCaseSummaryError(err.message || '生成案件摘要失败，请重试');
        }
    }

    async function callAICaseSummary(caseData) {
        if (typeof API !== 'undefined' && API.ai && API.ai.caseSummary) {
            try {
                var res = await API.ai.caseSummary(caseData);
                if (res && res.ok && res.data) {
                    var data = res.data;
                    return {
                        overview: data.overview || '',
                        disputes: data.disputes || '',
                        evidence: data.evidence || '',
                        risk: data.risk || '',
                        nextSteps: data.next_steps || ''
                    };
                }
                throw new Error(res && res.data ? (res.data.detail || res.data.message || 'API 请求失败') : 'API 请求失败');
            } catch (apiErr) {
                console.warn('AI 案件摘要 API 调用失败，降级到本地 mock:', apiErr);
            }
        }
        return generateCaseSummary(caseData);
    }

    function showCaseSummaryError(errorMsg) {
        var loadingEl = document.getElementById('case-summary-loading');
        var contentEl = document.getElementById('case-summary-content');
        if (!loadingEl || !contentEl) return;

        loadingEl.classList.add('hidden');
        contentEl.classList.remove('hidden');
        contentEl.innerHTML =
            '<div class="flex flex-col items-center justify-center py-12">' +
            '<div class="w-16 h-16 rounded-2xl bg-danger-tint/50 flex items-center justify-center mb-4">' +
            '<iconify-icon icon="mdi:alert-circle-outline" class="text-3xl text-danger"></iconify-icon>' +
            '</div>' +
            '<p class="text-sm font-medium text-fg-primary mb-1">生成失败</p>' +
            '<p class="text-xs text-fg-tertiary mb-4">' + escapeHtml(errorMsg) + '</p>' +
            '<button class="px-4 py-2 text-xs text-white bg-brand hover:bg-brand/90 rounded-lg transition-colors" onclick="regenerateCaseSummary()">' +
            '重新生成' +
            '</button>' +
            '</div>';
    }

    function streamCaseSummarySections(summary) {
        var sections = ['overview', 'disputes', 'evidence', 'risk', 'nextSteps'];
        var sectionIdx = 0;

        function streamNextSection() {
            if (sectionIdx >= sections.length) return;
            var key = sections[sectionIdx];
            var contentEl = document.querySelector('.ai-summary-content[data-section="' + key + '"]');
            if (!contentEl) {
                sectionIdx++;
                streamNextSection();
                return;
            }
            var text = summary[key] || '';
            contentEl.textContent = '';
            var tokens = tokenizeForStream(text);
            var idx = 0;
            _caseSummaryTimer = setInterval(function () {
                if (idx >= tokens.length) {
                    clearInterval(_caseSummaryTimer);
                    _caseSummaryTimer = null;
                    sectionIdx++;
                    setTimeout(streamNextSection, 200);
                    return;
                }
                var chunkSize = Math.min(3, tokens.length - idx);
                var chunk = tokens.slice(idx, idx + chunkSize).join('');
                contentEl.textContent += chunk;
                idx += chunkSize;
                var scrollContainer = document.getElementById('case-summary-content');
                if (scrollContainer) {
                    scrollContainer.scrollTop = scrollContainer.scrollHeight;
                }
            }, 15);
        }

        streamNextSection();
    }

    function regenerateCaseSummary() {
        var loadingEl = document.getElementById('case-summary-loading');
        var contentEl = document.getElementById('case-summary-content');
        if (loadingEl) loadingEl.classList.remove('hidden');
        if (contentEl) contentEl.classList.add('hidden');
        if (_caseSummaryTimer) {
            clearInterval(_caseSummaryTimer);
            _caseSummaryTimer = null;
        }
        setTimeout(startCaseSummary, 500);
    }

    function copyCaseSummary() {
        var contentEl = document.getElementById('case-summary-content');
        if (!contentEl) return;
        var text = contentEl.innerText || '';
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(function () {
                Utils.showToast('success', '案件摘要已复制到剪贴板');
            });
        } else {
            Utils.showToast('请手动选择文本复制');
        }
    }

    function exportCaseSummary() {
        var contentEl = document.getElementById('case-summary-content');
        if (!contentEl) return;
        var text = contentEl.innerText || '';
        var caseName = (document.getElementById('case-detail-title') || {}).textContent || '案件';
        var filename = '案件摘要_' + caseName + '_' + new Date().getTime() + '.txt';
        var blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        Utils.showToast('success', '已导出: ' + filename);
    }

    function closeCaseSummaryModal() {
        if (_closeCaseSummaryModal) {
            _closeCaseSummaryModal();
            _closeCaseSummaryModal = null;
        }
    }

    // ===== AI 文书润色功能 =====
    var _polishTimer = null;
    var _polishOriginal = '';
    var _polishResult = '';
    var _polishDiff = [];

    var POLISH_OPTIONS = {
        legalTerms: { label: '法律用语规范', icon: 'mdi:gavel', default: true },
        logic: { label: '逻辑优化', icon: 'mdi:sitemap', default: true },
        typos: { label: '错别字修正', icon: 'mdi:spellcheck', default: true },
        format: { label: '格式统一', icon: 'mdi:format-align-left', default: true },
        tone: { label: '语气调整', icon: 'mdi:account-tie-voice', default: false }
    };

    function polishDocument(content, options) {
        if (!content) return '';
        var opts = options || {};
        var result = content;

        if (opts.legalTerms) {
            result = result
                .replace(/借钱/g, '借款')
                .replace(/欠钱/g, '拖欠款项')
                .replace(/不给钱/g, '拒不支付')
                .replace(/说好了/g, '约定')
                .replace(/答应/g, '承诺')
                .replace(/打官司/g, '提起诉讼')
                .replace(/告他/g, '追究其法律责任')
                .replace(/差不多/g, '大致相当')
                .replace(/大概/g, '约计');
        }

        if (opts.typos) {
            result = result
                .replace(/做为/g, '作为')
                .replace(/签定/g, '签订')
                .replace(/帐号/g, '账号')
                .replace(/帐户/g, '账户')
                .replace(/其它/g, '其他')
                .replace(/其它的/g, '其他的')
                .replace(/权利/g, '权利')
                .replace(/义务/g, '义务');
        }

        if (opts.format) {
            result = result
                .replace(/\n{3,}/g, '\n\n')
                .replace(/[ \t]+$/gm, '')
                .replace(/^[ \t]+/gm, '');
        }

        if (opts.logic) {
            var logicEnhancements = [
                { from: /因此，/g, to: '综上所述，' },
                { from: /因为/g, to: '鉴于' },
                { from: /所以/g, to: '故' }
            ];
            logicEnhancements.forEach(function (e) {
                result = result.replace(e.from, e.to);
            });
        }

        if (opts.tone) {
            result = result
                .replace(/你方/g, '贵方')
                .replace(/我们/g, '我方')
                .replace(/你公司/g, '贵司')
                .replace(/我公司/g, '我司');
        }

        return result;
    }

    function buildDiff(original, polished) {
        var diff = [];
        var origLines = original.split('\n');
        var polLines = polished.split('\n');
        var maxLen = Math.max(origLines.length, polLines.length);

        for (var i = 0; i < maxLen; i++) {
            var origLine = origLines[i] || '';
            var polLine = polLines[i] || '';
            if (origLine === polLine) {
                diff.push({ type: 'same', original: origLine, polished: polLine });
            } else {
                diff.push({ type: 'modified', original: origLine, polished: polLine });
            }
        }
        return diff;
    }

    function openPolishPanel() {
        var outputEl = document.getElementById('ai-doc-output');
        if (!outputEl) {
            Utils.showToast('请先生成文书内容');
            return;
        }
        var content = outputEl.textContent || '';
        if (!content.trim()) {
            Utils.showToast('请先生成文书内容');
            return;
        }
        _polishOriginal = content;

        var contentHtml =
            '<div class="ai-polish-panel">' +
            '<div class="mb-4">' +
            '<h4 class="text-sm font-bold text-fg-primary mb-3 flex items-center gap-2">' +
            '<iconify-icon icon="mdi:auto-fix" class="text-wiki"></iconify-icon>润色选项' +
            '</h4>' +
            '<div class="grid grid-cols-2 md:grid-cols-3 gap-2" id="polish-options">' +
            buildPolishOptionsHtml() +
            '</div>' +
            '</div>' +
            '<div class="ai-polish-loading flex flex-col items-center justify-center py-12" id="polish-loading">' +
            '<div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center mb-4">' +
            '<iconify-icon icon="mdi:wand" class="text-3xl text-wiki animate-bounce"></iconify-icon>' +
            '</div>' +
            '<p class="text-sm font-medium text-fg-primary mb-1">AI 正在润色文书...</p>' +
            '<p class="text-xs text-fg-tertiary">正在优化法律用语、修正错别字、调整逻辑结构</p>' +
            '</div>' +
            '<div class="ai-polish-result hidden" id="polish-result">' +
            '<div class="flex items-center justify-between mb-3">' +
            '<h4 class="text-sm font-bold text-fg-primary flex items-center gap-2">' +
            '<iconify-icon icon="mdi:compare" class="text-brand"></iconify-icon>对比视图' +
            '</h4>' +
            '<div class="flex items-center gap-2">' +
            '<button class="text-xs px-2.5 py-1 bg-success-tint text-success rounded-lg hover:bg-success-tint/70 transition-colors flex items-center gap-1" onclick="acceptAllPolish()">' +
            '<iconify-icon icon="mdi:check-all" class="text-xs"></iconify-icon>全部采纳' +
            '</button>' +
            '<button class="text-xs px-2.5 py-1 bg-danger-tint text-danger rounded-lg hover:bg-danger-tint/70 transition-colors flex items-center gap-1" onclick="rejectAllPolish()">' +
            '<iconify-icon icon="mdi:close" class="text-xs"></iconify-icon>全部放弃' +
            '</button>' +
            '</div>' +
            '<div class="mb-3" id="polish-stats"></div>' +
            '<div class="grid grid-cols-2 gap-3">' +
            '<div class="border border-bg-border rounded-xl overflow-hidden">' +
            '<div class="px-3 py-2 bg-bg-subtle border-b border-bg-border flex items-center gap-2">' +
            '<span class="text-[11px] font-medium text-fg-secondary">原文</span>' +
            '</div>' +
            '<div class="p-3 max-h-[30vh] overflow-y-auto text-xs leading-relaxed font-mono bg-white" id="polish-original-text"></div>' +
            '</div>' +
            '<div class="border border-success/20 rounded-xl overflow-hidden">' +
            '<div class="px-3 py-2 bg-success-tint/30 border-b border-success/20 flex items-center gap-2">' +
            '<iconify-icon icon="mdi:auto-fix" class="text-success text-xs"></iconify-icon>' +
            '<span class="text-[11px] font-medium text-success">润色后</span>' +
            '</div>' +
            '<div class="p-3 max-h-[30vh] overflow-y-auto text-xs leading-relaxed font-mono bg-white" id="polish-polished-text"></div>' +
            '</div>' +
            '</div>' +
            '<div class="mt-4" id="polish-modifications">' +
            '<div class="flex items-center gap-2 mb-2">' +
            '<iconify-icon icon="mdi:format-list-checks" class="text-brand text-sm"></iconify-icon>' +
            '<span class="text-xs font-semibold text-fg-primary">修改详情</span>' +
            '</div>' +
            '<div class="space-y-2 max-h-[20vh] overflow-y-auto" id="polish-modification-list"></div>' +
            '</div>' +
            '</div>' +
            '</div>';

        var footer =
            '<div class="flex items-center justify-between w-full">' +
            '<button class="text-xs text-fg-tertiary hover:text-fg-secondary transition-colors flex items-center gap-1" onclick="retryPolish()">' +
            '<iconify-icon icon="mdi:refresh" class="text-sm"></iconify-icon>重新润色' +
            '</button>' +
            '<div class="flex items-center gap-2">' +
            '<button class="px-4 py-1.5 text-xs text-fg-secondary bg-bg-subtle hover:bg-bg rounded-lg transition-colors" onclick="closePolishPanel()">取消</button>' +
            '<button class="px-4 py-1.5 text-xs text-white bg-gradient-to-r from-wiki to-pink-500 hover:shadow-md hover:shadow-wiki/20 rounded-lg transition-all flex items-center gap-1" onclick="applyPolish()">' +
            '<iconify-icon icon="mdi:check" class="text-sm"></iconify-icon>应用润色' +
            '</button>' +
            '</div>' +
            '</div>';

        if (_closePolishModal) _closePolishModal();

        _closePolishModal = Utils.showModal({
            id: 'polish-modal',
            title: 'AI 文书润色',
            icon: 'mdi:auto-fix',
            content: contentHtml,
            footer: footer,
            size: 'xl',
            onClose: function () {
                _closePolishModal = null;
                if (_polishTimer) {
                    clearInterval(_polishTimer);
                    _polishTimer = null;
                }
            }
        });

        setTimeout(startPolish, 300);
    }

    var _closePolishModal = null;

    function buildPolishOptionsHtml() {
        var html = '';
        for (var key in POLISH_OPTIONS) {
            if (!POLISH_OPTIONS.hasOwnProperty(key)) continue;
            var opt = POLISH_OPTIONS[key];
            var checked = opt.default ? 'checked' : '';
            html +=
                '<label class="flex items-center gap-2 p-3 bg-bg-subtle rounded-lg cursor-pointer hover:bg-brand-tint/30 transition-colors border border-transparent hover:border-brand/30 polish-option-label" data-option="' +
                key +
                '">' +
                '<input type="checkbox" class="polish-option-checkbox rounded border-bg-border text-brand focus:ring-brand" data-option="' +
                key +
                '" ' +
                checked +
                '/>' +
                '<iconify-icon icon="' +
                opt.icon +
                '" class="text-brand text-base flex-shrink-0"></iconify-icon>' +
                '<span class="text-xs text-fg-primary font-medium">' +
                opt.label +
                '</span>' +
                '</label>';
        }
        return html;
    }

    function getSelectedPolishOptions() {
        var opts = {};
        var checkboxes = document.querySelectorAll('.polish-option-checkbox');
        checkboxes.forEach(function (cb) {
            var key = cb.getAttribute('data-option');
            opts[key] = cb.checked;
        });
        return opts;
    }

    async function startPolish() {
        var opts = getSelectedPolishOptions();
        var hasAny = Object.values(opts).some(function (v) { return v; });
        if (!hasAny) {
            Utils.showToast('请至少选择一项润色选项');
            return;
        }

        var loadingEl = document.getElementById('polish-loading');
        var resultEl = document.getElementById('polish-result');
        if (!loadingEl || !resultEl) return;

        try {
            var result = await callAIPolish(_polishOriginal, opts);
            _polishResult = result.polished_content || _polishOriginal;
            _polishDiff = result.modifications || [];
            _polishStats = result.stats || {};

            loadingEl.classList.add('hidden');
            resultEl.classList.remove('hidden');
            updatePolishStats(_polishStats);
            streamPolishResult();
        } catch (err) {
            showPolishError(err.message || '润色失败，请重试');
        }
    }

    var _polishStats = {};

    async function callAIPolish(content, options) {
        if (typeof API !== 'undefined' && API.ai && API.ai.polishDocument) {
            try {
                var res = await API.ai.polishDocument(content, options);
                if (res && res.ok && res.data) {
                    return res.data;
                }
                throw new Error(res && res.data ? (res.data.detail || res.data.message || 'API 请求失败') : 'API 请求失败');
            } catch (apiErr) {
                console.warn('AI 文书润色 API 调用失败，降级到本地 mock:', apiErr);
            }
        }
        var polished = polishDocument(content, options);
        var mods = buildDiff(content, polished);
        return {
            polished_content: polished,
            modifications: mods,
            stats: {
                total_modifications: mods.filter(function (m) { return m.type === 'modified'; }).length
            }
        };
    }

    function updatePolishStats(stats) {
        var statsEl = document.getElementById('polish-stats');
        if (!statsEl || !stats) return;
        var total = stats.total_modifications || 0;
        var legalTerms = stats.legal_terms || 0;
        var typos = stats.typos || 0;
        var logic = stats.logic || 0;
        var tone = stats.tone || 0;

        statsEl.innerHTML =
            '<div class="flex items-center gap-3 flex-wrap">' +
            '<span class="text-xs text-fg-tertiary">修改统计:</span>' +
            '<span class="text-xs px-2 py-0.5 bg-brand-tint text-brand rounded-full">共 ' + total + ' 处</span>' +
            (legalTerms > 0 ? '<span class="text-xs px-2 py-0.5 bg-purple-50 text-purple-600 rounded-full">法律用语 ' + legalTerms + '</span>' : '') +
            (typos > 0 ? '<span class="text-xs px-2 py-0.5 bg-green-50 text-green-600 rounded-full">错别字 ' + typos + '</span>' : '') +
            (logic > 0 ? '<span class="text-xs px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full">逻辑优化 ' + logic + '</span>' : '') +
            (tone > 0 ? '<span class="text-xs px-2 py-0.5 bg-amber-50 text-amber-600 rounded-full">语气调整 ' + tone + '</span>' : '') +
            '</div>';
    }

    function showPolishError(errorMsg) {
        var loadingEl = document.getElementById('polish-loading');
        var resultEl = document.getElementById('polish-result');
        if (!loadingEl || !resultEl) return;

        loadingEl.classList.add('hidden');
        resultEl.classList.remove('hidden');
        resultEl.innerHTML =
            '<div class="flex flex-col items-center justify-center py-12">' +
            '<div class="w-16 h-16 rounded-2xl bg-danger-tint/50 flex items-center justify-center mb-4">' +
            '<iconify-icon icon="mdi:alert-circle-outline" class="text-3xl text-danger"></iconify-icon>' +
            '</div>' +
            '<p class="text-sm font-medium text-fg-primary mb-1">润色失败</p>' +
            '<p class="text-xs text-fg-tertiary mb-4">' + escapeHtml(errorMsg) + '</p>' +
            '<button class="px-4 py-2 text-xs text-white bg-brand hover:bg-brand/90 rounded-lg transition-colors" onclick="retryPolish()">' +
            '重新润色' +
            '</button>' +
            '</div>';
    }

    function streamPolishResult() {
        var origEl = document.getElementById('polish-original-text');
        var polEl = document.getElementById('polish-polished-text');
        if (!origEl || !polEl) return;

        origEl.textContent = '';
        polEl.textContent = '';

        var origTokens = tokenizeForStream(_polishOriginal);
        var polTokens = tokenizeForStream(_polishResult);
        var origIdx = 0;
        var polIdx = 0;

        function streamOrig() {
            if (origIdx >= origTokens.length) return;
            var chunkSize = Math.min(4, origTokens.length - origIdx);
            var chunk = origTokens.slice(origIdx, origIdx + chunkSize).join('');
            origEl.textContent += chunk;
            origIdx += chunkSize;
            origEl.scrollTop = origEl.scrollHeight;
            setTimeout(streamOrig, 10);
        }

        function streamPol() {
            if (polIdx >= polTokens.length) return;
            var chunkSize = Math.min(4, polTokens.length - polIdx);
            var chunk = polTokens.slice(polIdx, polIdx + chunkSize).join('');
            polEl.textContent += chunk;
            polIdx += chunkSize;
            polEl.scrollTop = polEl.scrollHeight;
            setTimeout(streamPol, 10);
        }

        streamOrig();
        setTimeout(streamPol, 300);
        setTimeout(renderPolishModifications, 500);
    }

    function renderPolishModifications() {
        var listEl = document.getElementById('polish-modification-list');
        if (!listEl || !_polishDiff || _polishDiff.length === 0) return;

        var typeLabelMap = {
            legal_terms: { label: '法律用语', color: 'purple' },
            typo: { label: '错别字', color: 'green' },
            logic: { label: '逻辑优化', color: 'blue' },
            tone: { label: '语气调整', color: 'amber' },
            modified: { label: '修改', color: 'brand' }
        };

        var html = '';
        var count = 0;
        _polishDiff.forEach(function (item) {
            if (item.type === 'same') return;
            count++;
            if (count > 20) return;
            var typeInfo = typeLabelMap[item.type] || typeLabelMap.modified;
            html +=
                '<div class="flex items-start gap-2 p-2 bg-bg-subtle rounded-lg">' +
                '<span class="text-[10px] px-1.5 py-0.5 bg-' + typeInfo.color + '-tint text-' + typeInfo.color + ' rounded flex-shrink-0 mt-0.5">' +
                typeInfo.label +
                '</span>' +
                '<div class="flex-1 min-w-0 space-y-1">' +
                '<div class="flex items-start gap-1.5">' +
                '<iconify-icon icon="mdi:minus" class="text-danger text-xs flex-shrink-0 mt-0.5"></iconify-icon>' +
                '<span class="text-xs text-fg-secondary line-through decoration-danger/50 break-all">' +
                escapeHtml(item.original || '') +
                '</span>' +
                '</div>' +
                '<div class="flex items-start gap-1.5">' +
                '<iconify-icon icon="mdi:plus" class="text-success text-xs flex-shrink-0 mt-0.5"></iconify-icon>' +
                '<span class="text-xs text-fg-primary break-all">' +
                escapeHtml(item.polished || '') +
                '</span>' +
                '</div>' +
                '</div>' +
                '</div>';
        });

        if (count === 0) {
            html =
                '<div class="text-center py-4 text-xs text-fg-tertiary">' +
                '未检测到明显修改' +
                '</div>';
        } else if (count > 20) {
            html +=
                '<div class="text-center text-xs text-fg-tertiary pt-2">' +
                '仅显示前 20 条修改' +
                '</div>';
        }

        listEl.innerHTML = html;
    }

    function retryPolish() {
        var loadingEl = document.getElementById('polish-loading');
        var resultEl = document.getElementById('polish-result');
        if (loadingEl) loadingEl.classList.remove('hidden');
        if (resultEl) resultEl.classList.add('hidden');
        if (_polishTimer) {
            clearInterval(_polishTimer);
            _polishTimer = null;
        }
        setTimeout(startPolish, 300);
    }

    function acceptAllPolish() {
        _polishAccepted = true;
        Utils.showToast('success', '已全部采纳润色建议');
    }

    function rejectAllPolish() {
        _polishAccepted = false;
        Utils.showToast('已放弃所有润色建议');
    }

    var _polishAccepted = true;

    function applyPolish() {
        if (!_polishAccepted) {
            closePolishPanel();
            return;
        }
        var outputEl = document.getElementById('ai-doc-output');
        if (outputEl && _polishResult) {
            outputEl.textContent = _polishResult;
            if (typeof window.currentOutput !== 'undefined') {
                window.currentOutput = _polishResult;
            }
        }
        closePolishPanel();
        Utils.showToast('success', '润色结果已应用');
    }

    function closePolishPanel() {
        if (_closePolishModal) {
            _closePolishModal();
            _closePolishModal = null;
        }
    }

    // ===== AI 智能填空功能 =====
    async function autoFillTemplate(templateId) {
        var caseInfo = collectCaseInfoForFill();
        try {
            var result = await callAIAutoFill(templateId || '', caseInfo);
            var filledData = result.filled_fields || {};
            var filledCount = applyAutoFill(filledData);
            Utils.showToast('success', 'AI 智能填空完成，已填充 ' + filledCount + ' 个字段');
            return filledData;
        } catch (err) {
            Utils.showToast('error', '智能填空失败: ' + (err.message || '请稍后重试'));
            var filledCount = applyAutoFill(caseInfo);
            Utils.showToast('success', '已使用本地数据填充 ' + filledCount + ' 个字段');
            return caseInfo;
        }
    }

    async function callAIAutoFill(templateId, caseInfo) {
        if (typeof API !== 'undefined' && API.ai && API.ai.autoFill) {
            try {
                var res = await API.ai.autoFill(templateId, caseInfo);
                if (res && res.ok && res.data) {
                    return res.data;
                }
                throw new Error(res && res.data ? (res.data.detail || res.data.message || 'API 请求失败') : 'API 请求失败');
            } catch (apiErr) {
                console.warn('AI 智能填空 API 调用失败，降级到本地 mock:', apiErr);
            }
        }
        return {
            filled_fields: caseInfo,
            filled_count: Object.keys(caseInfo).filter(function (k) { return caseInfo[k]; }).length
        };
    }

    function collectCaseInfoForFill() {
        var data = {};
        var fieldMap = {
            'field-client-name': 'plaintiff',
            'field-opponent-name': 'defendant',
            'field-basic-caseType': 'cause',
            'field-basic-claimAmount': 'amount',
            'field-client-phone': 'phone',
            'field-client-legalRep': 'legalRep'
        };
        for (var fieldId in fieldMap) {
            if (!fieldMap.hasOwnProperty(fieldId)) continue;
            var el = document.getElementById(fieldId);
            if (el) {
                data[fieldMap[fieldId]] = el.textContent.trim();
            }
        }
        if (typeof window.currentCaseIndex !== 'undefined' && window.currentCaseIndex >= 0) {
            data.caseIndex = window.currentCaseIndex;
        }
        return data;
    }

    function applyAutoFill(data) {
        var count = 0;
        if (!data) return count;
        var inputs = document.querySelectorAll('.template-var-input, [data-template-var], #ai-doc-form-fields input, #ai-doc-form-fields textarea');
        inputs.forEach(function (input) {
            var varName = input.getAttribute('data-template-var') || input.id;
            if (!varName) return;
            var key = varName.replace('ai-doc-field-', '');
            if (data[key] && !input.value) {
                input.value = data[key];
                count++;
                input.classList.add('ai-filled');
                setTimeout(function () {
                    input.classList.remove('ai-filled');
                }, 1000);
            }
        });
        return count;
    }

    function openAutoFillSuggest() {
        var data = collectCaseInfoForFill();
        var dataCount = Object.keys(data).filter(function (k) { return data[k]; }).length;

        var content =
            '<div class="ai-autofill-panel">' +
            '<div class="flex items-start gap-3 p-4 bg-brand-tint/30 rounded-xl mb-4">' +
            '<div class="w-10 h-10 rounded-lg bg-gradient-to-br from-brand to-ai flex items-center justify-center flex-shrink-0">' +
            '<iconify-icon icon="mdi:magic-staff" class="text-white text-xl"></iconify-icon>' +
            '</div>' +
            '<div>' +
            '<h4 class="text-sm font-bold text-fg-primary mb-1">AI 智能填空</h4>' +
            '<p class="text-xs text-fg-secondary leading-relaxed">检测到当前案件信息，可自动填充 ' +
            dataCount +
            ' 个模板字段。是否立即填充？</p>' +
            '</div>' +
            '</div>' +
            '<div class="space-y-2">' +
            buildFillPreview(data) +
            '</div>' +
            '</div>';

        var footer =
            '<div class="flex items-center justify-end gap-2 w-full">' +
            '<button class="px-4 py-1.5 text-xs text-fg-secondary bg-bg-subtle hover:bg-bg rounded-lg transition-colors" onclick="closeAutoFillModal()">取消</button>' +
            '<button class="px-4 py-1.5 text-xs text-white bg-gradient-to-r from-brand to-ai hover:shadow-md hover:shadow-brand/20 rounded-lg transition-all flex items-center gap-1" onclick="confirmAutoFill()">' +
            '<iconify-icon icon="mdi:auto-fix" class="text-sm"></iconify-icon>一键填充' +
            '</button>' +
            '</div>';

        if (_closeAutoFillModal) _closeAutoFillModal();

        _closeAutoFillModal = Utils.showModal({
            id: 'autofill-modal',
            title: 'AI 智能填空',
            icon: 'mdi:magic-staff',
            content: content,
            footer: footer,
            size: 'md'
        });
    }

    var _closeAutoFillModal = null;

    function buildFillPreview(data) {
        var labelMap = {
            plaintiff: '原告',
            defendant: '被告',
            cause: '案由',
            amount: '标的金额',
            phone: '联系电话',
            legalRep: '法定代表人'
        };
        var html = '';
        var count = 0;
        for (var key in data) {
            if (!data.hasOwnProperty(key) || !data[key] || key === 'caseIndex') continue;
            var label = labelMap[key] || key;
            count++;
            html +=
                '<div class="flex items-center justify-between p-3 bg-bg-subtle rounded-lg">' +
                '<span class="text-xs text-fg-tertiary">' +
                label +
                '</span>' +
                '<span class="text-xs text-fg-primary font-medium truncate max-w-[60%]" title="' +
                escapeHtml(data[key]) +
                '">' +
                escapeHtml(data[key]) +
                '</span>' +
                '</div>';
        }
        if (count === 0) {
            html = '<p class="text-xs text-fg-tertiary text-center py-4">暂无可填充的字段</p>';
        }
        return html;
    }

    function confirmAutoFill() {
        var data = collectCaseInfoForFill();
        var count = applyAutoFill(data);
        closeAutoFillModal();
        Utils.showToast('success', '已自动填充 ' + count + ' 个字段');
    }

    function closeAutoFillModal() {
        if (_closeAutoFillModal) {
            _closeAutoFillModal();
            _closeAutoFillModal = null;
        }
    }

    // ===== 浮动 AI 助手 =====
    var _floatingAIIsOpen = false;

    function initFloatingAI() {
        if (document.getElementById('floating-ai-btn')) return;

        var btn = document.createElement('div');
        btn.id = 'floating-ai-btn';
        btn.className = 'floating-ai-btn';
        btn.innerHTML =
            '<button class="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand via-brand to-ai shadow-lg shadow-brand/30 flex items-center justify-center hover:shadow-xl hover:shadow-brand/40 transition-all duration-300 hover:scale-110 group" onclick="toggleFloatingAI()">' +
            '<iconify-icon icon="mdi:robot" class="text-2xl text-white group-hover:animate-bounce"></iconify-icon>' +
            '</button>';
        document.body.appendChild(btn);

        var panel = document.createElement('div');
        panel.id = 'floating-ai-panel';
        panel.className = 'floating-ai-panel hidden';
        panel.innerHTML = buildFloatingAIPanelHtml();
        document.body.appendChild(panel);

        document.addEventListener('click', function (e) {
            if (!_floatingAIIsOpen) return;
            var panel = document.getElementById('floating-ai-panel');
            var btn = document.getElementById('floating-ai-btn');
            if (!panel || !btn) return;
            if (!panel.contains(e.target) && !btn.contains(e.target)) {
                closeFloatingAI();
            }
        });
    }

    function buildFloatingAIPanelHtml() {
        var pageContext = getCurrentPageContext();
        var quickActions = getQuickActionsForPage(pageContext.page);

        var actionsHtml = '';
        quickActions.forEach(function (action) {
            actionsHtml +=
                '<button class="w-full flex items-center gap-2.5 p-2.5 rounded-lg hover:bg-brand-tint/30 transition-colors text-left group" onclick="' +
                action.action +
                '">' +
                '<div class="w-8 h-8 rounded-lg bg-' +
                action.color +
                '-tint flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">' +
                '<iconify-icon icon="' +
                action.icon +
                '" class="text-base text-' +
                action.color +
                '"></iconify-icon>' +
                '</div>' +
                '<div class="flex-1 min-w-0">' +
                '<p class="text-xs font-medium text-fg-primary">' +
                action.label +
                '</p>' +
                '<p class="text-[10px] text-fg-tertiary truncate">' +
                action.desc +
                '</p>' +
                '</div>' +
                '<iconify-icon icon="mdi:chevron-right" class="text-fg-tertiary text-sm"></iconify-icon>' +
                '</button>';
        });

        return (
            '<div class="floating-ai-panel-inner bg-white rounded-2xl shadow-2xl border border-bg-border overflow-hidden w-80">' +
            '<div class="p-4 bg-gradient-to-r from-brand via-brand to-ai relative overflow-hidden">' +
            '<div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2 blur-xl"></div>' +
            '<div class="relative z-10 flex items-center gap-3">' +
            '<div class="w-10 h-10 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center flex-shrink-0">' +
            '<iconify-icon icon="mdi:robot" class="text-xl text-white"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<h4 class="text-sm font-bold text-white">LexPrime AI 助手</h4>' +
            '<p class="text-[11px] text-white/80 truncate">' +
            pageContext.title +
            '</p>' +
            '</div>' +
            '<button class="w-7 h-7 rounded-lg bg-white/20 hover:bg-white/30 flex items-center justify-center text-white transition-colors" onclick="closeFloatingAI()">' +
            '<iconify-icon icon="mdi:close" class="text-sm"></iconify-icon>' +
            '</button>' +
            '</div>' +
            '</div>' +
            '<div class="p-3 border-b border-bg-border bg-bg-subtle/50">' +
            '<p class="text-[11px] text-fg-tertiary mb-2 font-medium">快捷操作</p>' +
            '<div class="space-y-1">' +
            actionsHtml +
            '</div>' +
            '</div>' +
            '<div class="p-3">' +
            '<p class="text-[11px] text-fg-tertiary mb-2 font-medium">快速提问</p>' +
            '<div class="space-y-2">' +
            '<div class="flex gap-2">' +
            '<input type="text" id="floating-ai-input" placeholder="输入问题..." class="flex-1 px-3 py-2 text-xs bg-bg-subtle border border-bg-border rounded-lg focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10 focus:bg-white transition-all" onkeydown="if(event.key===\'Enter\')sendFloatingAIMessage()"/>' +
            '<button class="px-3 py-2 bg-gradient-to-r from-brand to-ai text-white rounded-lg hover:shadow-md hover:shadow-brand/20 transition-all" onclick="sendFloatingAIMessage()">' +
            '<iconify-icon icon="mdi:send" class="text-sm"></iconify-icon>' +
            '</button>' +
            '</div>' +
            '<div id="floating-ai-response" class="hidden mt-2 p-3 bg-brand-tint/30 rounded-lg border border-brand/10 max-h-40 overflow-y-auto">' +
            '<div class="flex items-start gap-2">' +
            '<iconify-icon icon="mdi:robot" class="text-brand text-sm flex-shrink-0 mt-0.5"></iconify-icon>' +
            '<p class="text-xs text-fg-secondary leading-relaxed" id="floating-ai-response-text"></p>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '<div class="px-3 py-2 bg-bg-subtle/50 border-t border-bg-border flex items-center justify-between">' +
            '<button class="text-[10px] text-fg-tertiary hover:text-brand transition-colors flex items-center gap-1" onclick="switchView(\'ai\'); closeFloatingAI()">' +
            '<iconify-icon icon="mdi:open-in-new" class="text-xs"></iconify-icon>打开完整对话' +
            '</button>' +
            '<span class="text-[10px] text-fg-tertiary">Ctrl+/ 快捷唤起</span>' +
            '</div>' +
            '</div>'
        );
    }

    function getCurrentPageContext() {
        var page = 'unknown';
        var title = '随时为您服务';

        var viewEls = document.querySelectorAll('.view-content');
        viewEls.forEach(function (el) {
            if (!el.classList.contains('hidden')) {
                page = el.id.replace('view-', '');
            }
        });

        var titleMap = {
            workstation: '工作台',
            'case-list': '案件列表',
            case: '案件详情',
            'schedule-calendar': '日程管理',
            client: '客户管理',
            template: '模板管理',
            'ai-doc': 'AI 文书生成',
            knowledge: '法律智库',
            ai: 'AI 对话'
        };
        title = titleMap[page] || title;

        return { page: page, title: title };
    }

    function getQuickActionsForPage(page) {
        var actions = [];
        switch (page) {
        case 'case':
            actions = [
                { label: 'AI 案件摘要', desc: '一键生成案件分析报告', icon: 'mdi:file-document-outline', color: 'brand', action: 'openCaseSummaryModal()' },
                { label: '一键提取要点', desc: '智能提取案件关键信息', icon: 'mdi:select-drag', color: 'wiki', action: 'openAIExtractModal()' },
                { label: '生成起诉状', desc: '基于案件信息自动起草', icon: 'mdi:gavel', color: 'success', action: 'switchView(\'ai-doc\'); closeFloatingAI()' }
            ];
            break;
        case 'ai-doc':
            actions = [
                { label: 'AI 文书润色', desc: '优化法律用语和逻辑', icon: 'mdi:auto-fix', color: 'wiki', action: 'openPolishPanel()' },
                { label: '智能填空', desc: '从案件信息自动填充', icon: 'mdi:magic-staff', color: 'brand', action: 'openAutoFillSuggest()' },
                { label: '生成答辩状', desc: '切换文书类型为答辩状', icon: 'mdi:shield-check-outline', color: 'success', action: 'selectAIDocType(\'defense\', document.querySelector(\'[data-type="defense"]\')); closeFloatingAI()' }
            ];
            break;
        case 'template':
            actions = [
                { label: 'AI 智能填空', desc: '自动填充模板变量', icon: 'mdi:magic-staff', color: 'brand', action: 'openAutoFillSuggest()' },
                { label: '搜索模板', desc: '快速找到需要的模板', icon: 'mdi:file-search-outline', color: 'wiki', action: 'closeFloatingAI()' },
                { label: '上传模板', desc: '上传您的个人模板', icon: 'mdi:cloud-upload-outline', color: 'success', action: 'openUploadTemplateModal(); closeFloatingAI()' }
            ];
            break;
        default:
            actions = [
                { label: 'AI 对话', desc: '随时提问法律问题', icon: 'mdi:message-text-outline', color: 'brand', action: 'switchView(\'ai\'); closeFloatingAI()' },
                { label: '文书生成', desc: 'AI 起草法律文书', icon: 'mdi:file-document-edit-outline', color: 'wiki', action: 'switchView(\'ai-doc\'); closeFloatingAI()' },
                { label: '类案检索', desc: '查找相似判例', icon: 'mdi:book-search-outline', color: 'success', action: 'switchView(\'knowledge\'); closeFloatingAI()' }
            ];
        }
        return actions;
    }

    function toggleFloatingAI() {
        if (_floatingAIIsOpen) {
            closeFloatingAI();
        } else {
            openFloatingAI();
        }
    }

    function openFloatingAI() {
        var panel = document.getElementById('floating-ai-panel');
        var btn = document.getElementById('floating-ai-btn');
        if (!panel || !btn) return;

        var pageContext = getCurrentPageContext();
        var quickActions = getQuickActionsForPage(pageContext.page);
        var actionsContainer = panel.querySelector('.space-y-1');
        if (actionsContainer) {
            var actionsHtml = '';
            quickActions.forEach(function (action) {
                actionsHtml +=
                    '<button class="w-full flex items-center gap-2.5 p-2.5 rounded-lg hover:bg-brand-tint/30 transition-colors text-left group" onclick="' +
                    action.action +
                    '">' +
                    '<div class="w-8 h-8 rounded-lg bg-' +
                    action.color +
                    '-tint flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">' +
                    '<iconify-icon icon="' +
                    action.icon +
                    '" class="text-base text-' +
                    action.color +
                    '"></iconify-icon>' +
                    '</div>' +
                    '<div class="flex-1 min-w-0">' +
                    '<p class="text-xs font-medium text-fg-primary">' +
                    action.label +
                    '</p>' +
                    '<p class="text-[10px] text-fg-tertiary truncate">' +
                    action.desc +
                    '</p>' +
                    '</div>' +
                    '<iconify-icon icon="mdi:chevron-right" class="text-fg-tertiary text-sm"></iconify-icon>' +
                    '</button>';
            });
            actionsContainer.innerHTML = actionsHtml;
        }

        var titleEl = panel.querySelector('p.text-\\[11px\\]');
        if (titleEl) titleEl.textContent = pageContext.title;

        panel.classList.remove('hidden');
        _floatingAIIsOpen = true;

        var responseEl = document.getElementById('floating-ai-response');
        if (responseEl) responseEl.classList.add('hidden');
    }

    function closeFloatingAI() {
        var panel = document.getElementById('floating-ai-panel');
        if (!panel) return;
        panel.classList.add('hidden');
        _floatingAIIsOpen = false;
    }

    async function sendFloatingAIMessage() {
        var input = document.getElementById('floating-ai-input');
        var responseEl = document.getElementById('floating-ai-response');
        var responseText = document.getElementById('floating-ai-response-text');
        if (!input || !responseEl || !responseText) return;

        var text = (input.value || '').trim();
        if (!text) return;

        responseEl.classList.remove('hidden');
        responseText.textContent = 'AI 思考中...';

        input.value = '';

        try {
            var result = await callAIChat(text);
            streamTextToElement('floating-ai-response-text', result.reply);
            if (result.conversation_id) {
                _aiConversationId = result.conversation_id;
            }
        } catch (err) {
            responseText.textContent = '抱歉，AI 服务暂时不可用，请稍后重试';
            setTimeout(function () {
                var reply = generateMockAIReply(text);
                streamTextToElement('floating-ai-response-text', reply);
            }, 500);
        }
    }

    // ===== AI 可用性检测 =====
    function isAIAvailable() {
        return true;
    }

    // ===== 初始化 =====
    function initAIEnhancements() {
        initFloatingAI();

        if (typeof Utils !== 'undefined' && typeof Utils.registerShortcut === 'function') {
            Utils.registerShortcut('ctrl+/', function () {
                toggleFloatingAI();
            }, {
                description: '唤起 AI 助手',
                category: 'action',
                allowInInput: true
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAIEnhancements);
    } else {
        initAIEnhancements();
    }

    globalThis.switchAITab = switchAITab;
    globalThis.startNewChat = startNewChat;
    globalThis.selectHistory = selectHistory;
    globalThis.filterHistory = filterHistory;
    globalThis.switchAIView = switchAIView;
    globalThis.selectAIHistory = selectAIHistory;
    globalThis.filterAIHistory = filterAIHistory;
    globalThis.toggleAISidebar = toggleAISidebar;
    globalThis.toggleMoreMenu = toggleMoreMenu;
    globalThis.handleMoreAction = handleMoreAction;
    globalThis.openAIExtractModal = openAIExtractModal;
    globalThis.selectExtractSource = selectExtractSource;
    globalThis.closeAIExtractModal = closeAIExtractModal;
    globalThis.startAIExtract = startAIExtract;
    globalThis.copyExtractResult = copyExtractResult;
    globalThis.exportExtractResult = exportExtractResult;
    globalThis.handleAIInputKeydown = handleAIInputKeydown;
    globalThis.quickAsk = quickAsk;
    globalThis.sendAIMessage = sendAIMessage;
    globalThis.retryAIMessage = retryAIMessage;
    globalThis.submitFeedback = submitFeedback;
    globalThis.openFeedbackModal = openFeedbackModal;
    globalThis.openUserGuideModal = openUserGuideModal;
    globalThis.openContactModal = openContactModal;

    globalThis.generateCaseSummary = generateCaseSummary;
    globalThis.openCaseSummaryModal = openCaseSummaryModal;
    globalThis.regenerateCaseSummary = regenerateCaseSummary;
    globalThis.copyCaseSummary = copyCaseSummary;
    globalThis.exportCaseSummary = exportCaseSummary;
    globalThis.closeCaseSummaryModal = closeCaseSummaryModal;

    globalThis.polishDocument = polishDocument;
    globalThis.openPolishPanel = openPolishPanel;
    globalThis.retryPolish = retryPolish;
    globalThis.acceptAllPolish = acceptAllPolish;
    globalThis.rejectAllPolish = rejectAllPolish;
    globalThis.applyPolish = applyPolish;
    globalThis.closePolishPanel = closePolishPanel;

    globalThis.autoFillTemplate = autoFillTemplate;
    globalThis.openAutoFillSuggest = openAutoFillSuggest;
    globalThis.confirmAutoFill = confirmAutoFill;
    globalThis.closeAutoFillModal = closeAutoFillModal;

    globalThis.initFloatingAI = initFloatingAI;
    globalThis.toggleFloatingAI = toggleFloatingAI;
    globalThis.openFloatingAI = openFloatingAI;
    globalThis.closeFloatingAI = closeFloatingAI;
    globalThis.sendFloatingAIMessage = sendFloatingAIMessage;
    globalThis.isAIAvailable = isAIAvailable;
})();
