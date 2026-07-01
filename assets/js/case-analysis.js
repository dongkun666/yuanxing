/**
 * 智能卷宗分析模块
 * 包含: 案件选择联动、AI分析模拟、分析结果动态渲染
 */
(function() {
    'use strict';

    // ===== 分析结果数据（按案件索引） =====
    var analysisResults = {
        0: {
            caseNo: '(2026)京01民初128号',
            caseName: '张三诉李四民间借贷纠纷',
            type: '民间借贷纠纷',
            amount: 500000,
            stage: '一审',
            complexity: '中等',
            materialCount: 12,
            summary: [
                '原告张三与被告李四系朋友关系。2025年3月，李四以资金周转为由向张三借款人民币50万元，约定年利率15%，借款期限6个月，并出具借条一份。',
                '借款到期后，李四仅偿还本金10万元及部分利息，剩余40万元本金及利息经多次催要未果。张三遂诉至法院，要求李四偿还剩余借款本金及利息。'
            ],
            sources: '起诉状、借条、转账记录、催收聊天记录',
            disputes: [
                {
                    title: '焦点一：借款合同是否成立并生效',
                    desc: '借条形式要件完整，有双方签字捺印。转账记录显示50万元已实际交付。被告可能抗辩款项性质为投资款而非借款。',
                    reference: '类案参考：近3年本法院87件类似案件中，72件认定借款关系成立（约82.8%）',
                    severity: 'brand'
                },
                {
                    title: '焦点二：利息约定是否超过法定上限',
                    desc: '约定年利率15%，当前LPR为3.45%，4倍LPR为13.8%。超出部分法院可能不予支持。',
                    reference: '⚠️ 超出的1.2%部分需调整，建议修改为按LPR 4倍计算',
                    severity: 'urgent'
                },
                {
                    title: '焦点三：被告已还款10万元的性质认定',
                    desc: '被告主张10万元为本金还款。根据《民法典》第561条，双方无约定时按实现债权的费用→利息→主债务顺序抵充。',
                    reference: '🔴 缺少还款明细记录，建议补充银行流水以明确抵充顺序',
                    severity: 'danger'
                }
            ],
            existingEvidence: [
                { name: '借条（原件）', level: '采信度高', levelColor: 'success' },
                { name: '银行转账记录', level: '采信度高', levelColor: 'success' },
                { name: '微信催收聊天记录', level: '需公证', levelColor: 'urgent' },
                { name: '被告还款记录', level: '需补充', levelColor: 'urgent' }
            ],
            missingEvidence: [
                { name: '被告身份信息（身份证复印件）', priority: 'danger' },
                { name: '利息计算明细表', priority: 'urgent' },
                { name: '催收过程完整记录', priority: 'urgent' },
                { name: '财产保全申请（如需）', priority: 'tertiary' }
            ],
            strategies: [
                {
                    label: 'A',
                    title: '方案A：诉讼为主',
                    desc: '以借条和转账记录为核心证据，主张借款本金40万元及按LPR 4倍计算的利息。同时申请财产保全。',
                    pros: '可直接执行',
                    cons: '诉讼周期较长',
                    color: 'brand'
                },
                {
                    label: 'B',
                    title: '方案B：调解优先',
                    desc: '在法院主持下进行调解，争取被告分期还款方案。可适当减免利息以换取快速回款。',
                    pros: '快速结案、成本低',
                    cons: '可能需让步',
                    color: 'urgent'
                }
            ]
        },
        1: {
            caseNo: '(2026)京02民初256号',
            caseName: '王五诉某科技公司劳动争议',
            type: '劳动争议',
            amount: 180000,
            stage: '仲裁',
            complexity: '较高',
            materialCount: 8,
            summary: [
                '申请人王五于2024年6月入职被申请人某科技公司，担任高级工程师岗位，双方签订3年期劳动合同，月薪人民币25000元。',
                '2025年12月，公司以"业务调整"为由单方面解除劳动合同，未提前30日通知且未支付经济补偿金。王五主张公司违法解除，要求支付赔偿金、未休年假工资及加班费。'
            ],
            sources: '劳动合同、工资流水、解除通知函、考勤记录、微信工作群聊天记录',
            disputes: [
                {
                    title: '焦点一：解除劳动合同是否合法',
                    desc: '公司主张"客观情况发生重大变化"。但王五所在部门仍在正常运营，且公司未提供岗位调整方案，直接解除不符合《劳动合同法》第40条程序要求。',
                    reference: '类案参考：同类案件中，公司败诉率约76%（2024年北京市劳动仲裁数据）',
                    severity: 'brand'
                },
                {
                    title: '焦点二：赔偿金计算基数争议',
                    desc: '王五主张以离职前12个月平均工资（含年终奖、绩效）为基数。公司主张仅按基本工资计算，差额约¥8,000/月。',
                    reference: '⚠️ 根据《劳动合同法实施条例》第27条，经济补偿基数应包含全部工资性收入',
                    severity: 'urgent'
                },
                {
                    title: '焦点三：加班费举证责任',
                    desc: '考勤记录显示王五在离职前6个月平均每月加班约30小时，但公司主张加班系"自愿"且已通过调休补偿。',
                    reference: '🔴 加班审批记录缺失，建议补充钉钉/企业微信加班申请截图',
                    severity: 'danger'
                }
            ],
            existingEvidence: [
                { name: '劳动合同（原件）', level: '采信度高', levelColor: 'success' },
                { name: '工资流水（近12月）', level: '采信度高', levelColor: 'success' },
                { name: '解除通知函', level: '采信度高', levelColor: 'success' },
                { name: '考勤记录截图', level: '部分采信', levelColor: 'warning' }
            ],
            missingEvidence: [
                { name: '加班审批记录', priority: 'danger' },
                { name: '社保缴纳明细', priority: 'urgent' },
                { name: '年终奖发放通知', priority: 'urgent' },
                { name: '离职前绩效评估', priority: 'tertiary' }
            ],
            strategies: [
                {
                    label: 'A',
                    title: '方案A：劳动仲裁全面主张',
                    desc: '主张违法解除赔偿金（2N=¥100,000）、未休年假工资（¥11,494）、加班费（¥68,966），合计约¥180,460。',
                    pros: '主张全面，可能获得高额赔偿',
                    cons: '举证要求高，需充分准备',
                    color: 'brand'
                },
                {
                    label: 'B',
                    title: '方案B：仲裁+协商和解',
                    desc: '先提起仲裁施压，同步与公司协商和解方案。目标金额¥120,000-150,000，换取快速结案。',
                    pros: '周期短、风险低',
                    cons: '可能低于预期金额',
                    color: 'urgent'
                }
            ]
        },
        2: {
            caseNo: '(2026)京03民初789号',
            caseName: '某公司诉赵六合同纠纷',
            type: '合同纠纷',
            amount: 1200000,
            stage: '一审',
            complexity: '高',
            materialCount: 15,
            summary: [
                '原告某公司与被告赵六于2025年1月签订《设备采购合同》，约定赵六向原告采购价值人民币120万元的工业设备，分三期付款。',
                '赵六支付首期款36万元后，以设备存在质量问题为由拒绝支付第二期及第三期款项共计84万元。原告经检测认为设备符合合同约定的质量标准，遂诉至法院。'
            ],
            sources: '设备采购合同、设备检测报告、付款凭证、质量异议函、往来邮件、鉴定申请',
            disputes: [
                {
                    title: '焦点一：设备质量是否符合合同约定',
                    desc: '合同约定设备需通过ISO 9001标准检测。原告提供的检测报告显示合格，但被告委托第三方检测发现部分参数偏差。关键争议在于检测标准和方法的选择。',
                    reference: '类案参考：设备质量纠纷中，检测标准争议占比约45%，司法鉴定是关键证据',
                    severity: 'brand'
                },
                {
                    title: '焦点二：被告拒付是否构成根本违约',
                    desc: '被告主张先履行抗辩权（《民法典》第527条），认为质量问题导致合同目的无法实现。原告主张质量偏差在合理范围内，不构成根本违约。',
                    reference: '⚠️ 是否申请司法鉴定将直接影响案件走向，建议尽早提交鉴定申请',
                    severity: 'urgent'
                },
                {
                    title: '焦点三：违约金与实际损失的关系',
                    desc: '合同约定违约方需支付合同总价20%的违约金（¥240,000）。被告主张违约金过高，请求法院予以调整。',
                    reference: '🔴 建议提前准备实际损失证据（仓储费、融资成本等），以支持违约金合理性',
                    severity: 'danger'
                }
            ],
            existingEvidence: [
                { name: '设备采购合同', level: '采信度高', levelColor: 'success' },
                { name: '原告检测报告', level: '采信度中', levelColor: 'warning' },
                { name: '付款凭证（36万）', level: '采信度高', levelColor: 'success' },
                { name: '质量异议往来邮件', level: '采信度高', levelColor: 'success' }
            ],
            missingEvidence: [
                { name: '司法鉴定申请书', priority: 'danger' },
                { name: '设备交付验收单', priority: 'danger' },
                { name: '第三方检测报告完整版', priority: 'urgent' },
                { name: '实际损失计算明细', priority: 'urgent' }
            ],
            strategies: [
                {
                    label: 'A',
                    title: '方案A：申请司法鉴定+主张全额',
                    desc: '申请法院委托专业机构对设备进行质量鉴定。在鉴定基础上主张全额货款84万元及违约金24万元。',
                    pros: '鉴定结果权威性强，胜诉后执行有力',
                    cons: '鉴定周期长（3-6月），费用较高',
                    color: 'brand'
                },
                {
                    label: 'B',
                    title: '方案B：承认部分瑕疵+协商降价',
                    desc: '承认设备存在轻微瑕疵，提出补偿维修或降价方案（减少10-15%），换取被告继续付款。',
                    pros: '快速回款、维系合作',
                    cons: '需让步，可能影响后续维权',
                    color: 'urgent'
                }
            ]
        }
    };

    var currentAnalysisCase = 0;
    var isAnalyzing = false;

    // ===== 初始化 =====
    function initCaseAnalysis() {
        var viewEl = document.getElementById('view-case-analysis');
        if (!viewEl || viewEl.classList.contains('hidden')) return;

        // 绑定案件选择器
        var select = viewEl.querySelector('select');
        if (select) {
            select.value = String(currentAnalysisCase);
            select.onchange = function() {
                currentAnalysisCase = parseInt(this.value);
            };
        }

        // 绑定开始分析按钮
        var analyzeBtn = viewEl.querySelector('button.bg-brand');
        if (analyzeBtn) {
            analyzeBtn.onclick = function() { startAnalysis(); };
        }
    }

    // ===== 开始分析 =====
    function startAnalysis() {
        if (isAnalyzing) return;
        isAnalyzing = true;

        var viewEl = document.getElementById('view-case-analysis');
        if (!viewEl) return;

        var analyzeBtn = viewEl.querySelector('button.bg-brand');
        var originalText = analyzeBtn.textContent;
        analyzeBtn.textContent = '分析中...';
        analyzeBtn.disabled = true;

        // 添加加载状态到各模块
        var modules = viewEl.querySelectorAll('.bg-white.rounded-xl');
        modules.forEach(function(m) {
            m.style.opacity = '0.5';
            m.style.pointerEvents = 'none';
        });

        // 模拟AI分析过程（2秒延迟）
        setTimeout(function() {
            var data = analysisResults[currentAnalysisCase] || analysisResults[0];
            renderAnalysisResults(data);

            // 恢复UI
            modules.forEach(function(m) {
                m.style.opacity = '1';
                m.style.pointerEvents = 'auto';
            });
            analyzeBtn.textContent = '重新分析';
            analyzeBtn.disabled = false;
            isAnalyzing = false;

            if (typeof showToast === 'function') {
                showToast('分析完成 · ' + data.caseName);
            }
        }, 2000);
    }

    // ===== 渲染分析结果 =====
    function renderAnalysisResults(data) {
        var viewEl = document.getElementById('view-case-analysis');
        if (!viewEl) return;

        // 案情摘要
        var summaryEl = viewEl.querySelector('.col-span-2 .space-y-2.text-xs');
        if (summaryEl) {
            summaryEl.innerHTML = data.summary.map(function(p) { return '<p>' + escapeHtml(p) + '</p>'; }).join('');
        }
        var sourceEl = viewEl.querySelector('.col-span-2 .text-\\[10px\\].text-fg-tertiary span:last-child');
        if (!sourceEl) {
            var sourceDiv = viewEl.querySelector('.col-span-2 .flex.items-center.gap-2.text-\\[10px\\]');
            if (sourceDiv) {
                var spans = sourceDiv.querySelectorAll('span');
                if (spans.length >= 2) sourceEl = spans[1];
            }
        }
        if (sourceEl) {
            sourceEl.textContent = '信息来源：' + data.sources;
        }

        // 关键信息
        var infoValues = {
            '案由': data.type,
            '标的金额': '¥' + Number(data.amount).toLocaleString(),
            '代理阶段': data.stage,
            '复杂度': data.complexity,
            '材料数量': data.materialCount + ' 份'
        };
        var infoRows = viewEl.querySelectorAll('.col-span-3 > div:last-child .space-y-3 > div');
        infoRows.forEach(function(row) {
            var labelEl = row.querySelector('span:first-child');
            var valueEl = row.querySelector('span:last-child');
            if (labelEl && valueEl && infoValues[labelEl.textContent.replace(/[：:]/g, '')]) {
                var newLabel = Object.keys(infoValues).find(function(k) { return labelEl.textContent.indexOf(k) >= 0; });
                if (newLabel) {
                    valueEl.textContent = infoValues[newLabel];
                    if (newLabel === '复杂度') {
                        valueEl.className = 'text-urgent font-medium';
                    }
                }
            }
        });

        // 争议焦点
        renderDisputes(viewEl, data.disputes);

        // 证据评估
        renderEvidence(viewEl, data);

        // 策略建议
        renderStrategies(viewEl, data.strategies);
    }

    function renderDisputes(viewEl, disputes) {
        var disputesContainer = viewEl.querySelectorAll('.bg-white.rounded-xl.border.border-bg-border.p-5');
        var disputesEl = null;
        for (var i = 0; i < disputesContainer.length; i++) {
            if (disputesContainer[i].querySelector('iconify-icon[icon="mdi:target"]')) {
                disputesEl = disputesContainer[i].querySelector('.space-y-3');
                break;
            }
        }
        if (!disputesEl) return;

        var html = '';
        disputes.forEach(function(d) {
            var colorBorder = 'border-' + d.severity;
            html += '<div class="p-3 rounded-lg bg-bg-subtle border-l-4 ' + colorBorder + '">' +
                '<p class="text-xs font-medium text-fg-primary">' + escapeHtml(d.title) + '</p>' +
                '<p class="text-[10px] text-fg-secondary mt-1">' + escapeHtml(d.desc) + '</p>' +
                '<p class="text-[10px] text-' + d.severity + ' mt-1">' + escapeHtml(d.reference) + '</p>' +
            '</div>';
        });
        disputesEl.innerHTML = html;
    }

    function renderEvidence(viewEl, data) {
        var grid2 = viewEl.querySelector('.grid.grid-cols-2');
        if (!grid2) return;
        var cards = grid2.querySelectorAll(':scope > div');

        // 已有证据
        if (cards[0]) {
            var existingContainer = cards[0].querySelector('.space-y-2');
            if (existingContainer) {
                existingContainer.innerHTML = data.existingEvidence.map(function(e, i) {
                    var border = i < data.existingEvidence.length - 1 ? 'border-b border-bg-border' : '';
                    return '<div class="flex items-center justify-between text-xs py-2 ' + border + '">' +
                        '<span class="text-fg-secondary">' + escapeHtml(e.name) + '</span>' +
                        '<span class="text-[10px] text-' + e.levelColor + ' font-medium">' + escapeHtml(e.level) + '</span>' +
                    '</div>';
                }).join('');
            }
        }

        // 缺失证据
        if (cards[1]) {
            var missingContainer = cards[1].querySelector('.space-y-2');
            if (missingContainer) {
                missingContainer.innerHTML = data.missingEvidence.map(function(e, i) {
                    var border = i < data.missingEvidence.length - 1 ? 'border-b border-bg-border' : '';
                    var iconColor = 'text-' + e.priority;
                    return '<div class="flex items-center gap-2 text-xs py-2 ' + border + '">' +
                        '<iconify-icon class="' + iconColor + ' text-sm" icon="mdi:circle-small"></iconify-icon>' +
                        '<span class="text-fg-secondary">' + escapeHtml(e.name) + '</span>' +
                    '</div>';
                }).join('');
            }
        }
    }

    function renderStrategies(viewEl, strategies) {
        // 找到策略建议区域
        var allCards = viewEl.querySelectorAll('.bg-white.rounded-xl.border.border-bg-border.p-5');
        var strategyEl = null;
        for (var i = 0; i < allCards.length; i++) {
            if (allCards[i].querySelector('iconify-icon[icon="mdi:lightbulb-outline"]')) {
                strategyEl = allCards[i].querySelector('.space-y-2.text-xs.text-fg-secondary');
                break;
            }
        }
        if (!strategyEl) return;

        var html = '';
        strategies.forEach(function(s) {
            html += '<div class="flex items-start gap-2 p-2.5 rounded-lg bg-bg-subtle">' +
                '<span class="flex-shrink-0 w-5 h-5 rounded-full bg-' + s.color + ' text-white text-[10px] font-bold flex items-center justify-center mt-0.5">' + s.label + '</span>' +
                '<div>' +
                    '<p class="font-medium text-fg-primary">' + escapeHtml(s.title) + '</p>' +
                    '<p class="mt-0.5">' + escapeHtml(s.desc) + '</p>' +
                    '<p class="text-[10px] text-brand mt-1">优势：' + escapeHtml(s.pros) + ' | 劣势：' + escapeHtml(s.cons) + '</p>' +
                '</div>' +
            '</div>';
        });
        strategyEl.innerHTML = html;
    }

    function escapeHtml(str) {
        return String(str || '').replace(/[&<>"']/g, function(m) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
        });
    }

    // ===== 视图加载监听 =====
    function watchCaseAnalysisView() {
        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(m) {
                if (m.target.id === 'view-case-analysis' && !m.target.classList.contains('hidden')) {
                    initCaseAnalysis();
                }
            });
        });
        var viewEl = document.getElementById('view-case-analysis');
        if (viewEl) {
            observer.observe(viewEl, { attributes: true, attributeFilter: ['class'] });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', watchCaseAnalysisView);
    } else {
        watchCaseAnalysisView();
    }

    // 全局暴露
    window.startCaseAnalysis = startAnalysis;
    window.initCaseAnalysis = initCaseAnalysis;
})();
