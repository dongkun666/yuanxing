/**
 * 案件进度跟踪 (2026-06-28 Phase 3.2-1)
 *
 * 真实数据源: 中国审判流程信息公开网 (splcgk.court.gov.cn) - 需要滑块验证, 难直接接入
 * 当前实现: mock 数据 + 真实查询界面 + 跳转官方链接
 * 未来接入: 商业 API 或 OCR 验证码识别
 *
 * 设计: 5 个进度阶段 (立案→审理→判决→执行→终结)
 *      + 关键节点时间 + 下一步建议
 */

(function () {
    'use strict';

    // ===== Mock 数据库 (5 阶段 + 时间) =====
    var MOCK_PROGRESS = {
        '北京市第一中级人民法院:(2026)京01民初128号': {
            court: '北京市第一中级人民法院',
            caseNumber: '(2026)京01民初128号',
            caseType: '民事一审',
            cause: '买卖合同纠纷',
            parties: { plaintiff: '李明', defendant: '北京众鑫达科技股份有限公司' },
            currentStage: '审理中',
            currentStageIndex: 2,
            stages: [
                { name: '立案', date: '2026-06-01', status: 'done', desc: '法院正式立案', party: '立案庭' },
                { name: '送达', date: '2026-06-05', status: 'done', desc: '起诉状副本送达被告', party: '立案庭' },
                {
                    name: '庭前调解',
                    date: '2026-06-20',
                    status: 'done',
                    desc: '组织庭前调解, 未达成协议',
                    party: '承办法官 李法官'
                },
                {
                    name: '开庭审理',
                    date: '2026-08-15',
                    status: 'current',
                    desc: '排期开庭, 合议庭审理',
                    party: '第3法庭'
                },
                { name: '宣判', date: null, status: 'pending', desc: '预计开庭后 30 日内', party: null }
            ],
            nextSteps: [
                '提前 3 个工作日再次通知当事人开庭时间',
                '准备证据原件庭审质证',
                '梳理争议焦点辩论提纲',
                '关注 8/15 庭审实际进展, 及时调整诉讼策略'
            ]
        },
        '上海市浦东新区人民法院:(2025)沪0115民初4321号': {
            court: '上海市浦东新区人民法院',
            caseNumber: '(2025)沪0115民初4321号',
            caseType: '民事一审',
            cause: '股权转让纠纷',
            parties: { plaintiff: '王五', defendant: '诚信投资公司' },
            currentStage: '已判决',
            currentStageIndex: 4,
            stages: [
                { name: '立案', date: '2025-08-12', status: 'done', desc: '法院正式立案', party: '立案庭' },
                { name: '送达', date: '2025-08-20', status: 'done', desc: '完成送达', party: '立案庭' },
                { name: '开庭审理', date: '2025-11-10', status: 'done', desc: '已开庭审理', party: '第2法庭' },
                {
                    name: '宣判',
                    date: '2026-02-08',
                    status: 'done',
                    desc: '判决支持原告主要诉讼请求',
                    party: '审判长 王法官'
                },
                { name: '执行申请', date: null, status: 'pending', desc: '判决生效后 2 年内可申请执行', party: null }
            ],
            nextSteps: [
                '判决书已送达, 15 日上诉期至 2026-02-23',
                '若对方不上诉, 准备申请执行材料 (判决书 + 生效证明)',
                '准备执行申请书, 申请执行标的 ¥258 万',
                '若对方上诉, 准备二审应诉材料'
            ]
        },
        '深圳市中级人民法院:(2025)粤03民终5678号': {
            court: '深圳市中级人民法院',
            caseNumber: '(2025)粤03民终5678号',
            caseType: '民事二审',
            cause: '技术服务合同纠纷',
            parties: { plaintiff: '众鑫达公司', defendant: '南方科技公司' },
            currentStage: '已立案',
            currentStageIndex: 1,
            stages: [
                { name: '立案', date: '2025-12-15', status: 'done', desc: '二审立案受理', party: '立案庭' },
                { name: '送达', date: '2025-12-28', status: 'current', desc: '正在送达上诉状副本', party: '立案庭' },
                {
                    name: '庭前阅卷',
                    date: null,
                    status: 'pending',
                    desc: '二审阅卷, 必要时调查取证',
                    party: '承办法官'
                },
                { name: '开庭审理', date: null, status: 'pending', desc: '二审开庭审理', party: '合议庭' },
                { name: '终审判决', date: null, status: 'pending', desc: '二审判决为终审', party: '合议庭' }
            ],
            nextSteps: [
                '关注上诉状副本送达情况',
                '准备二审答辩状 (15 日内提交)',
                '调取一审全部卷宗, 整理二审代理意见',
                '与当事人沟通二审策略, 评估和解可能性'
            ]
        }
    };

    // ===== 查询逻辑 =====
    function searchProgress() {
        var court = document.getElementById('progress-court').value.trim();
        var caseNum = document.getElementById('progress-case-num').value.trim();
        var party = document.getElementById('progress-party').value.trim();

        if (!caseNum && !(court && party)) {
            if (typeof showToast === 'function') showToast('请输入案号, 或法院 + 当事人姓名');
            return;
        }

        // 显示 loading (用 toast 替代, 简单)
        // 实际 mock 数据
        var data = mockQuery(court, caseNum, party);
        renderProgress(data, court, caseNum, party);
    }

    function mockQuery(court, caseNum, party) {
        // 优先按完整案号
        if (caseNum) {
            for (var key in MOCK_PROGRESS) {
                var k = key.split(':');
                if (k[1] === caseNum) return MOCK_PROGRESS[key];
            }
        }
        // 按法院 + 当事人匹配
        if (court && party) {
            for (var key2 in MOCK_PROGRESS) {
                var d = MOCK_PROGRESS[key2];
                if (
                    d.court.indexOf(court) >= 0 &&
                    (d.parties.plaintiff.indexOf(party) >= 0 || d.parties.defendant.indexOf(party) >= 0)
                ) {
                    return d;
                }
            }
        }
        return null;
    }

    function renderProgress(data, court, caseNum, party) {
        var results = document.getElementById('progress-results');
        var empty = document.getElementById('progress-empty');

        if (!data) {
            empty.classList.remove('hidden');
            empty.innerHTML =
                '<div class="w-20 h-20 mx-auto rounded-full bg-bg-subtle flex items-center justify-center mb-4">' +
                '<iconify-icon class="text-4xl text-fg-disabled" icon="mdi:file-question-outline"></iconify-icon>' +
                '</div>' +
                '<p class="text-sm font-medium text-fg-secondary">未查询到案件信息</p>' +
                '<p class="text-xs text-fg-tertiary mt-1.5">请核对案号/法院/当事人姓名是否正确</p>' +
                '<p class="text-[11px] text-fg-disabled mt-2">数据可能存在 1-2 个工作日延迟</p>' +
                '<div class="mt-5 flex items-center justify-center gap-2 flex-wrap">' +
                '<button class="px-4 py-2 text-xs font-medium text-brand bg-brand-tint2 hover:bg-brand-tint rounded-lg transition-colors flex items-center gap-1.5" onclick="quickSearchProgress(\'北京市第一中级人民法院\', \'(2026)京01民初128号\', \'李明\')">' +
                '<iconify-icon icon="mdi:play-circle-outline" class="text-sm"></iconify-icon>体验示例' +
                '</button>' +
                '</div>';
            results.classList.add('hidden');
            return;
        }

        empty.classList.add('hidden');
        results.classList.remove('hidden');

        // 更新渐变头部显示
        var caseNumDisplay = document.getElementById('progress-case-number-display');
        if (caseNumDisplay) caseNumDisplay.textContent = data.caseNumber;

        var currentStageDisplay = document.getElementById('progress-current-stage-display');
        if (currentStageDisplay) currentStageDisplay.textContent = data.currentStage;

        var causeDisplay = document.getElementById('progress-cause-display');
        if (causeDisplay) causeDisplay.textContent = data.cause;

        var courtDisplay = document.getElementById('progress-court-display');
        if (courtDisplay) courtDisplay.textContent = data.court + ' · ' + data.caseType;

        var plaintiffDisplay = document.getElementById('progress-plaintiff-display');
        if (plaintiffDisplay) plaintiffDisplay.textContent = data.parties.plaintiff;

        var defendantDisplay = document.getElementById('progress-defendant-display');
        if (defendantDisplay) defendantDisplay.textContent = data.parties.defendant;

        var stageDisplay = document.getElementById('progress-stage-display');
        if (stageDisplay)
            stageDisplay.textContent = '第 ' + (data.currentStageIndex + 1) + ' / ' + data.stages.length + ' 阶段';

        // 基本信息详情
        var basic = document.getElementById('progress-basic-info');
        if (basic) {
            basic.innerHTML =
                '<div class="flex items-center gap-2">' +
                '<span class="w-6 h-6 rounded bg-brand-tint flex items-center justify-center flex-shrink-0">' +
                '<iconify-icon icon="mdi:scale-balance" class="text-xs text-brand"></iconify-icon>' +
                '</span>' +
                '<div>' +
                '<p class="text-[11px] text-fg-tertiary">案件类型</p>' +
                '<p class="text-xs font-medium text-fg-primary">' +
                escapeHtml(data.caseType) +
                '</p>' +
                '</div>' +
                '</div>' +
                '<div class="flex items-center gap-2">' +
                '<span class="w-6 h-6 rounded bg-success-tint flex items-center justify-center flex-shrink-0">' +
                '<iconify-icon icon="mdi:tag-outline" class="text-xs text-success"></iconify-icon>' +
                '</span>' +
                '<div>' +
                '<p class="text-[11px] text-fg-tertiary">案由</p>' +
                '<p class="text-xs font-medium text-fg-primary">' +
                escapeHtml(data.cause) +
                '</p>' +
                '</div>' +
                '</div>' +
                '<div class="flex items-center gap-2">' +
                '<span class="w-6 h-6 rounded bg-wiki-tint flex items-center justify-center flex-shrink-0">' +
                '<iconify-icon icon="mdi:information-outline" class="text-xs text-wiki"></iconify-icon>' +
                '</span>' +
                '<div>' +
                '<p class="text-[11px] text-fg-tertiary">当前阶段</p>' +
                '<p class="text-xs font-medium text-fg-primary">' +
                '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-brand-tint text-brand text-[10px] font-medium">' +
                escapeHtml(data.currentStage) +
                '</span>' +
                '</p>' +
                '</div>' +
                '</div>';
        }

        // 时间线 - 升级样式
        var timeline = document.getElementById('progress-timeline');
        var html = '<div class="absolute left-[18px] top-4 bottom-4 w-0.5 bg-bg-border"></div>';
        var progressPercent = data.stages.length > 1 ? (data.currentStageIndex * 100) / (data.stages.length - 1) : 0;
        html +=
            '<div class="absolute left-[18px] top-4 w-0.5 bg-gradient-to-b from-brand to-ai rounded-full" style="height: ' +
            progressPercent +
            '%"></div>';

        data.stages.forEach(function (stage, i) {
            var circleCls, iconName, textCls, badgeCls, cardCls;
            if (stage.status === 'done') {
                circleCls = 'bg-gradient-to-br from-green-400 to-success text-white shadow-lg shadow-success/20';
                iconName = 'mdi:check';
                textCls = 'text-fg-primary';
                badgeCls = 'bg-success-tint text-success';
                cardCls = 'bg-white border-bg-border hover:border-success/30 hover:shadow-md';
            } else if (stage.status === 'current') {
                circleCls =
                    'bg-gradient-to-br from-brand to-ai text-white ring-4 ring-brand-tint animate-pulse shadow-xl shadow-brand/30';
                iconName = 'mdi:clock-outline';
                textCls = 'text-fg-primary font-semibold';
                badgeCls = 'bg-gradient-to-r from-brand to-ai text-white';
                cardCls = 'bg-gradient-to-br from-white to-brand-tint3/30 border-2 border-brand/30 shadow-lg';
            } else {
                circleCls = 'bg-white border-2 border-bg-border text-fg-disabled';
                iconName = 'mdi:circle-outline';
                textCls = 'text-fg-tertiary';
                badgeCls = 'bg-bg-subtle text-fg-tertiary';
                cardCls = 'bg-bg-subtle/30 border-bg-border/50';
            }

            var statusLabel = '';
            if (stage.status === 'current') {
                statusLabel =
                    '<span class="text-[10px] ' +
                    badgeCls +
                    ' px-2 py-0.5 rounded-full font-bold flex items-center gap-0.5"><iconify-icon class="text-[10px]" icon="mdi:lightning-bolt"></iconify-icon>进行中</span>';
            } else if (stage.status === 'done') {
                statusLabel =
                    '<span class="text-[10px] ' + badgeCls + ' px-2 py-0.5 rounded-full font-medium">已完成</span>';
            } else {
                statusLabel =
                    '<span class="text-[10px] ' + badgeCls + ' px-2 py-0.5 rounded-full font-medium">待办</span>';
            }

            html +=
                '<div class="relative pl-12 pb-5 last:pb-0">' +
                '<div class="absolute left-0 top-0 w-9 h-9 rounded-full flex items-center justify-center z-10 ' +
                circleCls +
                '">' +
                '<iconify-icon class="text-base" icon="' +
                iconName +
                '"></iconify-icon>' +
                '</div>' +
                '<div class="rounded-xl border p-4 transition-all duration-300 ' +
                cardCls +
                '">' +
                '<div class="flex items-start justify-between gap-3">' +
                '<div class="flex-1 min-w-0">' +
                '<div class="flex items-center gap-2 flex-wrap mb-1">' +
                '<span class="text-sm ' +
                textCls +
                ' font-medium">' +
                escapeHtml(stage.name) +
                '</span>' +
                statusLabel +
                '</div>' +
                '<p class="text-xs text-fg-secondary leading-relaxed">' +
                escapeHtml(stage.desc) +
                '</p>' +
                (stage.party
                    ? '<p class="text-[11px] text-fg-tertiary mt-1.5 flex items-center gap-1"><iconify-icon class="text-xs" icon="mdi:account-outline"></iconify-icon> ' +
                      escapeHtml(stage.party) +
                      '</p>'
                    : '') +
                '</div>' +
                (stage.date
                    ? '<span class="text-[11px] font-mono text-fg-tertiary flex-shrink-0 bg-bg-subtle px-2 py-1 rounded">' +
                      escapeHtml(stage.date) +
                      '</span>'
                    : '<span class="text-[11px] text-fg-disabled flex-shrink-0 bg-bg-subtle px-2 py-1 rounded">待定</span>') +
                '</div>' +
                '</div>' +
                '</div>';
        });
        timeline.innerHTML = html;

        // 下一步建议 - 升级样式
        var steps = document.getElementById('progress-next-steps');
        if (steps) {
            var stepsHtml = '';
            data.nextSteps.forEach(function (step, i) {
                stepsHtml +=
                    '<div class="flex items-start gap-3 p-3 bg-white/60 rounded-lg hover:bg-white/80 transition-colors">' +
                    '<div class="w-6 h-6 rounded-full bg-gradient-to-br from-amber-400 to-warning flex items-center justify-center flex-shrink-0 text-white text-xs font-bold shadow-sm">' +
                    (i + 1) +
                    '</div>' +
                    '<span class="text-sm text-fg-primary leading-relaxed">' +
                    escapeHtml(step) +
                    '</span>' +
                    '</div>';
            });
            steps.innerHTML = stepsHtml;
        }

        // 查询时间
        var timeEl = document.getElementById('progress-query-time');
        if (timeEl) timeEl.textContent = '查询于 ' + formatQueryTime();

        // 触发入场动画
        if (typeof Animations !== 'undefined' && Animations.initPageAnimations) {
            Animations.initPageAnimations(results);
        }
    }

    function formatQueryTime() {
        var d = new Date();
        var y = d.getFullYear();
        var m = String(d.getMonth() + 1).padStart(2, '0');
        var dd = String(d.getDate()).padStart(2, '0');
        var hh = String(d.getHours()).padStart(2, '0');
        var mm = String(d.getMinutes()).padStart(2, '0');
        var ss = String(d.getSeconds()).padStart(2, '0');
        return y + '-' + m + '-' + dd + ' ' + hh + ':' + mm + ':' + ss;
    }

    function resetProgress() {
        document.getElementById('progress-court').value = '';
        document.getElementById('progress-case-num').value = '';
        document.getElementById('progress-party').value = '';
        document.getElementById('progress-results').classList.add('hidden');
        var empty = document.getElementById('progress-empty');
        empty.classList.remove('hidden');
        empty.innerHTML =
            '<div class="w-20 h-20 mx-auto rounded-full bg-bg-subtle flex items-center justify-center mb-4">' +
            '<iconify-icon class="text-4xl text-fg-disabled" icon="mdi:gavel-search"></iconify-icon>' +
            '</div>' +
            '<p class="text-sm font-medium text-fg-secondary">请输入案件信息开始跟踪</p>' +
            '<p class="text-xs text-fg-tertiary mt-1.5">数据来源: 中国审判流程信息公开网</p>' +
            '<div class="mt-6 flex items-center justify-center gap-2 flex-wrap">' +
            '<button class="px-4 py-2 text-xs font-medium text-brand bg-brand-tint2 hover:bg-brand-tint rounded-lg transition-colors flex items-center gap-1.5" onclick="quickSearchProgress(\'北京市第一中级人民法院\', \'(2026)京01民初128号\', \'李明\')">' +
            '<iconify-icon icon="mdi:play-circle-outline" class="text-sm"></iconify-icon>体验示例' +
            '</button>' +
            '</div>';
    }

    function quickSearchProgress(court, caseNum, party) {
        document.getElementById('progress-court').value = court;
        document.getElementById('progress-case-num').value = caseNum;
        document.getElementById('progress-party').value = party;
        searchProgress();
    }

    function initCaseProgress() {
        var root = document.getElementById('view-case-progress');
        if (!root) return;
        resetProgress();
    }

    globalThis.searchProgress = searchProgress;
    globalThis.resetProgress = resetProgress;
    globalThis.quickSearchProgress = quickSearchProgress;
    globalThis.initCaseProgress = initCaseProgress;
})();
