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

    function handleMoreAction(action) {
        document.getElementById('moreMenuWork').classList.add('hidden');
        document.getElementById('moreMenuAI').classList.add('hidden');
        if (action === 'settings') {
            switchSidebarTab('work');
            switchView('account-settings');
        } else if (action === 'check-update') {
            var current = window.APP_VERSION || '0.7.0';
            if (typeof showToast === 'function') {
                showToast('当前版本: v' + current + ' · 已是最新版本');
            }
        } else if (action === 'feedback') {
            openFeedbackModal();
        } else if (action === 'guide') {
            openUserGuideModal();
        } else if (action === 'contact') {
            openContactModal();
        } else if (action === 'logout') {
            if (confirm('确认退出登录？')) {
                if (typeof Auth !== 'undefined' && Auth.logout) {
                    Auth.logout();
                }
                showToast('已退出登录');
            }
        }
    }

    var _closeAIExtractModal = null;

    function buildAIExtractContent() {
        return '<div class="space-y-5">' +
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
        '</div>';
    }

    function openAIExtractModal() {
        var content = buildAIExtractContent();
        var footer = '' +
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
            onClose: function() {
                _closeAIExtractModal = null;
            }
        });

        setTimeout(function() {
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
        alert('报告已导出为Markdown格式（演示功能）');
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
    function sendAIMessage() {
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
            '<p class="text-sm leading-relaxed text-fg-secondary whitespace-pre-wrap ai-msg-content">思考中<span class="dot-flash">.</span><span class="dot-flash">.</span><span class="dot-flash">.</span></p>' +
            '<span class="text-[10px] text-fg-tertiary mt-2 block ai-msg-time">刚刚</span>' +
            '</div>' +
            '</div>';
        msgList.insertAdjacentHTML('beforeend', aiHtml);
        msgList.scrollTop = msgList.scrollHeight;
        var fullReply = generateMockAIReply(text);
        streamAIMessage(aiMsgId, fullReply, function () {
            if (sendBtn) {
                sendBtn.disabled = false;
                sendBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            }
            if (sendIcon) sendIcon.setAttribute('icon', 'mdi:send');
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
            '<button class="text-fg-tertiary hover:text-fg-secondary" onclick="document.getElementById(\'more-action-modal\').classList.add(\'hidden\')"><iconify-icon icon="mdi:close" class="text-xl"></iconify-icon></button>' +
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

    globalThis.switchAITab = switchAITab;
    globalThis.startNewChat = startNewChat;
    globalThis.selectHistory = selectHistory;
    globalThis.filterHistory = filterHistory;
    globalThis.switchAIView = switchAIView;
    globalThis.selectAIHistory = selectAIHistory;
    globalThis.filterAIHistory = filterAIHistory;
    globalThis.toggleMoreMenu = toggleMoreMenu;
    globalThis.handleMoreAction = handleMoreAction;
    globalThis.openAIExtractModal = openAIExtractModal;
    globalThis.selectExtractSource = selectExtractSource;
    globalThis.closeAIExtractModal = closeAIExtractModal;
    globalThis.startAIExtract = startAIExtract;
    globalThis.copyExtractResult = copyExtractResult;
    globalThis.exportExtractResult = exportExtractResult;
    globalThis.handleAIInputKeydown = handleAIInputKeydown;
    globalThis.sendAIMessage = sendAIMessage;
    globalThis.submitFeedback = submitFeedback;
    globalThis.openFeedbackModal = openFeedbackModal;
    globalThis.openUserGuideModal = openUserGuideModal;
    globalThis.openContactModal = openContactModal;
})();
