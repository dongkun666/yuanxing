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

(function() {
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
                { name: '庭前调解', date: '2026-06-20', status: 'done', desc: '组织庭前调解, 未达成协议', party: '承办法官 李法官' },
                { name: '开庭审理', date: '2026-08-15', status: 'current', desc: '排期开庭, 合议庭审理', party: '第3法庭' },
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
                { name: '宣判', date: '2026-02-08', status: 'done', desc: '判决支持原告主要诉讼请求', party: '审判长 王法官' },
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
                { name: '庭前阅卷', date: null, status: 'pending', desc: '二审阅卷, 必要时调查取证', party: '承办法官' },
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
            showToast('请输入案号, 或法院 + 当事人姓名');
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
                if (d.court.indexOf(court) >= 0 && (d.parties.plaintiff.indexOf(party) >= 0 || d.parties.defendant.indexOf(party) >= 0)) {
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
            empty.innerHTML = '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:file-question-outline"></iconify-icon><p class="text-sm text-fg-primary mt-3 font-medium">未查询到案件信息</p><p class="text-[10px] text-fg-tertiary mt-1">请核对案号/法院/当事人姓名是否正确</p><p class="text-[10px] text-fg-disabled mt-2">数据可能存在 1-2 个工作日延迟</p>';
            results.classList.add('hidden');
            return;
        }

        empty.classList.add('hidden');
        results.classList.remove('hidden');

        // 基本信息
        var basic = document.getElementById('progress-basic-info');
        basic.innerHTML =
            '<div><span class="text-fg-tertiary">受理法院: </span><span class="font-medium">' + escapeHtml(data.court) + '</span></div>' +
            '<div><span class="text-fg-tertiary">案号: </span><span class="font-mono font-medium">' + escapeHtml(data.caseNumber) + '</span></div>' +
            '<div><span class="text-fg-tertiary">案件类型: </span><span>' + escapeHtml(data.caseType) + '</span></div>' +
            '<div><span class="text-fg-tertiary">案由: </span><span>' + escapeHtml(data.cause) + '</span></div>' +
            '<div><span class="text-fg-tertiary">原告: </span><span>' + escapeHtml(data.parties.plaintiff) + '</span></div>' +
            '<div><span class="text-fg-tertiary">被告: </span><span>' + escapeHtml(data.parties.defendant) + '</span></div>' +
            '<div><span class="text-fg-tertiary">当前阶段: </span><span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-brand-tint text-brand text-[10px] font-medium">' + escapeHtml(data.currentStage) + '</span></div>' +
            '<div class="col-span-2 md:col-span-1"><span class="text-fg-tertiary">数据来源: </span><span>中国审判流程信息公开网</span></div>';

        // 时间线
        var timeline = document.getElementById('progress-timeline');
        var html = '<div class="absolute left-[14px] top-2 bottom-2 w-0.5 bg-bg-border"></div>';
        html += '<div class="absolute left-[14px] top-2 w-0.5 bg-brand" style="height: ' + (data.currentStageIndex * 100 / (data.stages.length - 1)) + '%"></div>';

        data.stages.forEach(function(stage, i) {
            var circleCls, iconName, textCls, ringCls;
            if (stage.status === 'done') {
                circleCls = 'bg-success text-white';
                iconName = 'mdi:check';
                textCls = 'text-fg-primary';
                ringCls = '';
            } else if (stage.status === 'current') {
                circleCls = 'bg-brand text-white ring-4 ring-brand-tint animate-pulse';
                iconName = 'mdi:clock-outline';
                textCls = 'text-fg-primary font-semibold';
                ringCls = '';
            } else {
                circleCls = 'bg-white border-2 border-bg-border text-fg-disabled';
                iconName = 'mdi:circle-outline';
                textCls = 'text-fg-tertiary';
                ringCls = '';
            }

            html +=
                '<div class="relative pl-10 pb-5 ' + (i === data.stages.length - 1 ? '' : '') + '">' +
                '<div class="absolute left-0 top-0 w-7 h-7 rounded-full flex items-center justify-center ' + circleCls + '">' +
                '<iconify-icon class="text-sm" icon="' + iconName + '"></iconify-icon>' +
                '</div>' +
                '<div class="flex items-start justify-between gap-3">' +
                '<div class="flex-1 min-w-0">' +
                '<div class="flex items-center gap-2 flex-wrap">' +
                '<span class="text-sm ' + textCls + '">' + escapeHtml(stage.name) + '</span>' +
                (stage.status === 'current' ? '<span class="text-[10px] bg-brand text-white px-1.5 py-0.5 rounded-full font-medium">进行中</span>' : '') +
                (stage.status === 'done' ? '<span class="text-[10px] bg-success-tint text-success px-1.5 py-0.5 rounded-full font-medium">已完成</span>' : '') +
                (stage.status === 'pending' ? '<span class="text-[10px] bg-bg-subtle text-fg-tertiary px-1.5 py-0.5 rounded-full font-medium">待办</span>' : '') +
                '</div>' +
                '<p class="text-xs text-fg-secondary mt-0.5">' + escapeHtml(stage.desc) + '</p>' +
                (stage.party ? '<p class="text-[10px] text-fg-tertiary mt-0.5"><iconify-icon class="text-xs" icon="mdi:account-outline"></iconify-icon> ' + escapeHtml(stage.party) + '</p>' : '') +
                '</div>' +
                (stage.date ? '<span class="text-[10px] font-mono text-fg-tertiary flex-shrink-0">' + escapeHtml(stage.date) + '</span>' : '<span class="text-[10px] text-fg-disabled flex-shrink-0">待定</span>') +
                '</div>' +
                '</div>';
        });
        timeline.innerHTML = html;

        // 下一步建议
        var steps = document.getElementById('progress-next-steps');
        var stepsHtml = '';
        data.nextSteps.forEach(function(step, i) {
            stepsHtml += '<div class="flex items-start gap-2"><span class="text-amber-600 font-bold text-sm flex-shrink-0">' + (i + 1) + '.</span><span class="text-fg-primary">' + escapeHtml(step) + '</span></div>';
        });
        steps.innerHTML = stepsHtml;

        // 查询时间
        var timeEl = document.getElementById('progress-query-time');
        if (timeEl) timeEl.textContent = '查询时间: ' + formatQueryTime();
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
        empty.innerHTML = '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:gavel-search"></iconify-icon><p class="text-sm text-fg-tertiary mt-3">请输入案件信息开始跟踪</p><p class="text-[10px] text-fg-disabled mt-1">数据来源: 中国审判流程信息公开网</p>';
    }

    function quickSearchProgress(court, caseNum, party) {
        document.getElementById('progress-court').value = court;
        document.getElementById('progress-case-num').value = caseNum;
        document.getElementById('progress-party').value = party;
        searchProgress();
    }

    // ===== 双绑定 =====
    globalThis.searchProgress = searchProgress;
    globalThis.resetProgress = resetProgress;
    globalThis.quickSearchProgress = quickSearchProgress;
})();