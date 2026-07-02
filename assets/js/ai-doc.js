/**
 * AI 文书生成 (2026-06-28 Phase 3.2-2)
 *
 * 6 大文书类型: 起诉状/答辩状/律师函/合同/调解书/催告函
 * 实现: 模板 + 用户输入 → 流式 AI 输出 (mock, 模拟 tokenizeForStream)
 * 未来: 接入真实 LLM API (Qwen/DeepSeek 等) 替换 generateAIDocContent
 */

(function () {
    'use strict';

    // ===== 文书类型定义 =====
    var DOC_TYPES = {
        complaint: {
            name: '民事起诉状',
            icon: 'mdi:scale-balance',
            fields: [
                { key: 'plaintiff', label: '原告', placeholder: '姓名/名称', type: 'text' },
                { key: 'defendant', label: '被告', placeholder: '姓名/名称', type: 'text' },
                { key: 'cause', label: '案由', placeholder: '如: 借款合同纠纷', type: 'text' },
                { key: 'court', label: '受理法院', placeholder: '如: 北京市海淀区人民法院', type: 'text' },
                {
                    key: 'claims',
                    label: '诉讼请求',
                    placeholder: '1. 判令被告支付借款本金 XX 元...',
                    type: 'textarea',
                    rows: 4
                },
                {
                    key: 'facts',
                    label: '事实与理由',
                    placeholder: '原被告于 2024 年 X 月 X 日签订...',
                    type: 'textarea',
                    rows: 5
                }
            ]
        },
        defense: {
            name: '民事答辩状',
            icon: 'mdi:shield-check-outline',
            fields: [
                { key: 'defendant', label: '答辩人 (被告)', placeholder: '姓名/名称', type: 'text' },
                { key: 'plaintiff', label: '被答辩人 (原告)', placeholder: '姓名/名称', type: 'text' },
                { key: 'cause', label: '案由', placeholder: '如: 买卖合同纠纷', type: 'text' },
                { key: 'court', label: '受理法院', placeholder: '如: 北京市海淀区人民法院', type: 'text' },
                {
                    key: 'response',
                    label: '答辩事项',
                    placeholder: '请求法院依法驳回原告的全部诉讼请求...',
                    type: 'textarea',
                    rows: 4
                },
                {
                    key: 'facts',
                    label: '事实与理由',
                    placeholder: '针对原告诉讼请求, 答辩如下...',
                    type: 'textarea',
                    rows: 5
                }
            ]
        },
        'lawyer-letter': {
            name: '律师函',
            icon: 'mdi:email-arrow-right-outline',
            fields: [
                { key: 'recipient', label: '收件人', placeholder: '公司/个人名称', type: 'text' },
                { key: 'subject', label: '事项主题', placeholder: '如: 关于催收 XX 款项的律师函', type: 'text' },
                {
                    key: 'background',
                    label: '背景说明',
                    placeholder: '委托人 X 与贵司于 2024 年 X 月 X 日签订...',
                    type: 'textarea',
                    rows: 4
                },
                {
                    key: 'demand',
                    label: '要求事项',
                    placeholder: '1. 立即支付欠款 XX 元; 2. 三日内联系...',
                    type: 'textarea',
                    rows: 4
                },
                { key: 'deadline', label: '回复期限', placeholder: '如: 7 日内', type: 'text' }
            ]
        },
        contract: {
            name: '合同 (通用)',
            icon: 'mdi:file-sign',
            fields: [
                {
                    key: 'contract_type',
                    label: '合同类型',
                    placeholder: '如: 服务合同/买卖合同/借款合同',
                    type: 'text'
                },
                { key: 'partyA', label: '甲方', placeholder: '姓名/名称', type: 'text' },
                { key: 'partyB', label: '乙方', placeholder: '姓名/名称', type: 'text' },
                {
                    key: 'subject',
                    label: '标的/服务内容',
                    placeholder: '甲方向乙方提供 XX 服务...',
                    type: 'textarea',
                    rows: 3
                },
                { key: 'amount', label: '金额', placeholder: '如: 100,000 元', type: 'text' },
                { key: 'deadline', label: '履行期限', placeholder: '如: 自合同签订之日起 30 日内', type: 'text' },
                {
                    key: 'key_terms',
                    label: '关键条款',
                    placeholder: '违约责任/争议解决/保密等特殊要求',
                    type: 'textarea',
                    rows: 3
                }
            ]
        },
        mediation: {
            name: '调解协议',
            icon: 'mdi:handshake-outline',
            fields: [
                { key: 'partyA', label: '甲方', placeholder: '姓名/名称', type: 'text' },
                { key: 'partyB', label: '乙方', placeholder: '姓名/名称', type: 'text' },
                { key: 'dispute', label: '争议事项', placeholder: '双方因 XX 产生纠纷...', type: 'textarea', rows: 3 },
                {
                    key: 'agreement',
                    label: '调解方案',
                    placeholder: '1. 乙方于 X 日内支付 XX 元; 2. 双方再无其他争议...',
                    type: 'textarea',
                    rows: 4
                },
                { key: 'mediator', label: '调解人/调解机构', placeholder: '如: XX 人民调解委员会', type: 'text' }
            ]
        },
        'demand-letter': {
            name: '催告函',
            icon: 'mdi:bell-ring-outline',
            fields: [
                { key: 'recipient', label: '收件人', placeholder: '姓名/名称', type: 'text' },
                { key: 'debt_subject', label: '债务事项', placeholder: '借款/货款/租金等', type: 'text' },
                { key: 'amount', label: '应付款项', placeholder: '如: 50,000 元', type: 'text' },
                { key: 'due_date', label: '原定付款日期', placeholder: '如: 2025-06-30', type: 'text' },
                { key: 'deadline', label: '催告付款期限', placeholder: '如: 7 日内', type: 'text' },
                {
                    key: 'consequence',
                    label: '后果说明',
                    placeholder: '逾期将通过法律途径追偿, 包括违约金、诉讼费、律师费等',
                    type: 'textarea',
                    rows: 3
                }
            ]
        }
    };

    var currentDocType = 'complaint';
    var currentOutput = '';

    // ===== UI 控制 =====
    function selectAIDocType(type, btn) {
        currentDocType = type;
        document.querySelectorAll('#ai-doc-type-chips .ai-doc-type-chip').forEach(function (c) {
            c.classList.remove('active');
        });
        if (btn) btn.classList.add('active');
        renderFormFields(type);
    }

    function renderFormFields(type) {
        var docDef = DOC_TYPES[type];
        if (!docDef) return;
        var container = document.getElementById('ai-doc-form-fields');
        if (!container) return;
        var html = '';
        docDef.fields.forEach(function (field) {
            var inputHtml = '';
            if (field.type === 'textarea') {
                inputHtml =
                    '<textarea id="ai-doc-field-' +
                    field.key +
                    '" placeholder="' +
                    escapeHtml(field.placeholder) +
                    '" rows="' +
                    (field.rows || 3) +
                    '" class="w-full bg-bg-subtle border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand focus:bg-white transition-colors resize-none"></textarea>';
            } else {
                inputHtml =
                    '<input type="text" id="ai-doc-field-' +
                    field.key +
                    '" placeholder="' +
                    escapeHtml(field.placeholder) +
                    '" class="w-full bg-bg-subtle border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand focus:bg-white transition-colors"/>';
            }
            html +=
                '<div>' +
                '<label class="block text-xs font-medium text-fg-secondary mb-1">' +
                escapeHtml(field.label) +
                '</label>' +
                inputHtml +
                '</div>';
        });
        container.innerHTML = html;
    }

    function collectFormData() {
        var docDef = DOC_TYPES[currentDocType];
        if (!docDef) return {};
        var data = {};
        docDef.fields.forEach(function (field) {
            var el = document.getElementById('ai-doc-field-' + field.key);
            if (el) data[field.key] = el.value.trim();
        });
        return data;
    }

    // ===== AI 生成 (mock 流式输出) =====
    function generateAIDocument() {
        var data = collectFormData();

        // 简单校验: 至少填一个字段
        var hasAny = Object.values(data).some(function (v) {
            return v && v.length > 0;
        });
        if (!hasAny) {
            showToast('请至少填写一项内容');
            return;
        }

        // 隐藏空态, 显示 typing
        document.getElementById('ai-doc-empty').classList.add('hidden');
        document.getElementById('ai-doc-actions').classList.add('hidden');
        document.getElementById('ai-doc-output-wrap').classList.add('hidden');
        document.getElementById('ai-doc-typing').classList.remove('hidden');
        document.getElementById('ai-doc-output').textContent = '';

        // 模拟生成
        setTimeout(function () {
            var fullText = generateMockDocument(currentDocType, data);
            streamOutput(fullText);
        }, 400);
    }

    function streamOutput(text) {
        document.getElementById('ai-doc-typing').classList.add('hidden');
        document.getElementById('ai-doc-output-wrap').classList.remove('hidden');
        var outputEl = document.getElementById('ai-doc-output');
        outputEl.textContent = '';
        currentOutput = text;

        // 按字符流式输出 (中文按字, 英文按词)
        var tokens = tokenizeForStream(text);
        var i = 0;
        function nextChunk() {
            if (i >= tokens.length) {
                document.getElementById('ai-doc-actions').classList.remove('hidden');
                return;
            }
            var chunkSize = Math.min(3, tokens.length - i);
            var chunk = tokens.slice(i, i + chunkSize).join('');
            outputEl.textContent += chunk;
            i += chunkSize;
            setTimeout(nextChunk, 30);
        }
        nextChunk();
    }

    function tokenizeForStream(text) {
        var tokens = [];
        var buf = '';
        for (var i = 0; i < text.length; i++) {
            var ch = text[i];
            if (/[\u4e00-\u9fa5]/.test(ch)) {
                // 中文字符单独成 token
                if (buf) {
                    tokens.push(buf);
                    buf = '';
                }
                tokens.push(ch);
            } else if (/[a-zA-Z0-9]/.test(ch)) {
                buf += ch;
            } else {
                // 标点/空格
                if (buf) {
                    tokens.push(buf);
                    buf = '';
                }
                tokens.push(ch);
            }
        }
        if (buf) tokens.push(buf);
        return tokens;
    }

    // ===== Mock 文书模板生成 =====
    function generateMockDocument(type, data) {
        var d = new Date();
        var dateStr = d.getFullYear() + ' 年 ' + (d.getMonth() + 1) + ' 月 ' + d.getDate() + ' 日';
        var docDef = DOC_TYPES[type];
        var docName = docDef ? docDef.name : '法律文书';

        var tpl = '';
        if (type === 'complaint') {
            tpl = generateComplaint(data, dateStr);
        } else if (type === 'defense') {
            tpl = generateDefense(data, dateStr);
        } else if (type === 'lawyer-letter') {
            tpl = generateLawyerLetter(data, dateStr);
        } else if (type === 'contract') {
            tpl = generateContract(data, dateStr);
        } else if (type === 'mediation') {
            tpl = generateMediation(data, dateStr);
        } else if (type === 'demand-letter') {
            tpl = generateDemandLetter(data, dateStr);
        } else {
            tpl = '(未知文书类型)';
        }
        return tpl;
    }

    function generateComplaint(d, date) {
        var plaintiff = d.plaintiff || '______';
        var defendant = d.defendant || '______';
        var cause = d.cause || '______';
        var court = d.court || '______';
        var claims = d.claims || '1. 判令被告...; 2. 本案诉讼费由被告承担。';
        var facts = d.facts || '原被告...';

        return (
            '民 事 起 诉 状\n\n' +
            '原告: ' +
            plaintiff +
            '\n' +
            '被告: ' +
            defendant +
            '\n' +
            '案由: ' +
            cause +
            '\n\n' +
            '诉讼请求:\n' +
            claims +
            '\n\n' +
            '事实与理由:\n' +
            facts +
            '\n\n' +
            '此致\n' +
            court +
            '\n\n' +
            '附:\n' +
            '1. 本起诉状副本 1 份\n' +
            '2. 证据材料 1 套\n' +
            '3. 原告身份证明\n\n' +
            '起诉人: ________ (签名或盖章)\n' +
            '            ' +
            date +
            '\n'
        );
    }

    function generateDefense(d, date) {
        var defendant = d.defendant || '______';
        var plaintiff = d.plaintiff || '______';
        var cause = d.cause || '______';
        var court = d.court || '______';
        var response = d.response || '请求依法驳回原告全部诉讼请求。';
        var facts = d.facts || '针对原告诉讼请求, 答辩如下: ...';

        return (
            '民 事 答 辩 状\n\n' +
            '答辩人 (被告): ' +
            defendant +
            '\n' +
            '被答辩人 (原告): ' +
            plaintiff +
            '\n' +
            '案由: ' +
            cause +
            '\n\n' +
            '答辩事项:\n' +
            response +
            '\n\n' +
            '事实与理由:\n' +
            facts +
            '\n\n' +
            '此致\n' +
            court +
            '\n\n' +
            '附: 相关证据材料 1 套\n\n' +
            '答辩人: ________ (签名或盖章)\n' +
            '            ' +
            date +
            '\n'
        );
    }

    function generateLawyerLetter(d, date) {
        var recipient = d.recipient || '______';
        var subject = d.subject || '关于 XX 事项的律师函';
        var background = d.background || '受委托人 X 委托, 就 XX 事项致函贵司。';
        var demand = d.demand || '请贵司在收到本函后 7 日内: ...';
        var deadline = d.deadline || '7 日内';

        return (
            '律 师 函\n\n' +
            '致: ' +
            recipient +
            '\n\n' +
            '关于: ' +
            subject +
            '\n\n' +
            '________ 律师事务所\n' +
            '接受委托人 X 的委托, 并指派本律师就上述事项向贵司致函如下:\n\n' +
            '一、事实与背景\n' +
            background +
            '\n\n' +
            '二、本律师意见\n' +
            '根据上述事实, 结合相关法律法规, 本律师认为: 贵司的行为已构成违约, 应承担相应法律责任。\n\n' +
            '三、要求事项\n' +
            demand +
            '\n\n' +
            '四、回复期限\n' +
            '请贵司在 ' +
            deadline +
            ' 以书面形式回复本律师, 逾期未回复, 委托人将依法采取进一步法律行动, 包括但不限于提起诉讼/仲裁。\n\n' +
            '特此函告。\n\n' +
            '________ 律师事务所\n' +
            '承办律师: ________\n' +
            '            ' +
            date +
            '\n'
        );
    }

    function generateContract(d, date) {
        var type = d.contract_type || '服务';
        var partyA = d.partyA || '甲方';
        var partyB = d.partyB || '乙方';
        var subject = d.subject || '______';
        var amount = d.amount || '______';
        var deadline = d.deadline || '______';
        var keyTerms = d.key_terms || '违约责任: 违约方应按合同金额 30% 支付违约金。';

        return (
            type.toUpperCase() +
            '合 同\n\n' +
            '甲方: ' +
            partyA +
            '\n' +
            '乙方: ' +
            partyB +
            '\n\n' +
            '鉴于: 双方就 ' +
            subject +
            ' 经友好协商, 达成如下协议:\n\n' +
            '第一条 标的\n' +
            subject +
            '\n\n' +
            '第二条 金额\n本合同总金额为人民币 ' +
            amount +
            ' 元。\n\n' +
            '第三条 履行期限\n' +
            deadline +
            '\n\n' +
            '第四条 双方权利义务\n4.1 甲方应按时支付合同款项。\n4.2 乙方应按约定提供产品/服务。\n\n' +
            '第五条 违约责任\n' +
            keyTerms +
            '\n\n' +
            '第六条 争议解决\n因本合同发生的争议, 双方协商解决; 协商不成的, 提交合同签订地人民法院诉讼解决。\n\n' +
            '第七条 其他\n本合同自双方签字盖章之日起生效, 一式两份, 甲乙双方各执一份。\n\n' +
            '甲方: ________ (签字盖章)         乙方: ________ (签字盖章)\n' +
            '        日期: ' +
            date +
            '                  日期: ' +
            date +
            '\n'
        );
    }

    function generateMediation(d, date) {
        var partyA = d.partyA || '甲方';
        var partyB = d.partyB || '乙方';
        var dispute = d.dispute || '______';
        var agreement = d.agreement || '双方协商一致, 达成如下协议: ...';
        var mediator = d.mediator || 'XX 人民调解委员会';

        return (
            '人 民 调 解 协 议 书\n\n' +
            '甲方: ' +
            partyA +
            '\n' +
            '乙方: ' +
            partyB +
            '\n' +
            '调解人: ' +
            mediator +
            '\n\n' +
            '纠纷简要情况:\n' +
            dispute +
            '\n\n' +
            '经调解, 双方自愿达成如下协议:\n' +
            agreement +
            '\n\n' +
            '本协议自双方签字之日起生效, 双方应共同遵守。\n' +
            '本协议一式三份, 双方当事人各执一份, 调解机构留存一份。\n\n' +
            '甲方: ________ (签字)                 乙方: ________ (签字)\n\n' +
            '调解人: ________\n' +
            '            ' +
            mediator +
            '\n' +
            '            ' +
            date +
            '\n'
        );
    }

    function generateDemandLetter(d, date) {
        var recipient = d.recipient || '______';
        var subject = d.debt_subject || 'XX 款项';
        var amount = d.amount || '______';
        var dueDate = d.due_date || '______';
        var deadline = d.deadline || '7 日内';
        var consequence = d.consequence || '逾期将通过法律途径追偿。';

        return (
            '催 告 函\n\n' +
            '致: ' +
            recipient +
            '\n\n' +
            '我方与贵方就 ' +
            subject +
            ' 一事, 达成如下约定: 贵方应于 ' +
            dueDate +
            ' 之前支付 ' +
            amount +
            ' 元。\n\n' +
            '截至本函发出之日, 贵方仍未履行上述付款义务, 已构成违约。\n\n' +
            '现正式函告如下:\n' +
            '一、请贵方在收到本函 ' +
            deadline +
            ' 内付清上述款项 ' +
            amount +
            ' 元。\n' +
            '二、若贵方逾期未付, 我方将采取以下措施:\n' +
            consequence +
            '\n\n' +
            '特此函告。\n\n' +
            '签发人: ________\n' +
            '        ' +
            date +
            '\n'
        );
    }

    // ===== 操作 =====
    function copyAIDocument() {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(currentOutput).then(function () {
                showToast('已复制到剪贴板');
            });
        } else {
            showToast('请手动选择文本复制');
        }
    }

    function downloadAIDocument() {
        var docDef = DOC_TYPES[currentDocType];
        var docName = docDef ? docDef.name : '法律文书';
        var filename = docName + '_' + new Date().getTime() + '.txt';
        var blob = new Blob([currentOutput], { type: 'text/plain;charset=utf-8' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('已下载: ' + filename);
    }

    // ===== 初始化 =====
    function initAIDocView() {
        var el = document.getElementById('view-ai-doc');
        if (!el || el.dataset.init) return;
        el.dataset.init = '1';
        selectAIDocType('complaint', document.querySelector('.ai-doc-type-chip[data-type="complaint"]'));
    }

    var initObserver = new MutationObserver(function () {
        var el = document.getElementById('view-ai-doc');
        if (el && !el.classList.contains('hidden') && !el.dataset.init) {
            initAIDocView();
        }
    });
    if (document.body) {
        initObserver.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class']
        });
    }

    // ===== 双绑定 =====
    globalThis.selectAIDocType = selectAIDocType;
    globalThis.generateAIDocument = generateAIDocument;
    globalThis.copyAIDocument = copyAIDocument;
    globalThis.downloadAIDocument = downloadAIDocument;
    globalThis.initAIDocView = initAIDocView;
})();
