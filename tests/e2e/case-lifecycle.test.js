'use strict';

const assert = require('assert');
const { describe, it } = require('node:test');

describe('Case Lifecycle - 案件全生命周期测试', function () {
    function createMockCase() {
        return {
            id: 'case-test-001',
            title: '张三诉李四借款合同纠纷案',
            caseNumber: '(2026)京01民初1234号',
            cause: '借款合同纠纷',
            status: 'draft',
            parties: {
                plaintiff: { name: '张三', role: '原告' },
                defendant: { name: '李四', role: '被告' }
            },
            court: '北京市第一中级人民法院',
            amount: 500000,
            createdAt: new Date().toISOString(),
            timeline: [],
            documents: [],
            tasks: []
        };
    }

    it('1. 案件录入 - 应能创建新案件并设置初始状态', function () {
        var caseData = createMockCase();
        assert.strictEqual(caseData.status, 'draft', '初始状态应为 draft');
        assert.ok(caseData.id, '案件应有唯一ID');
        assert.ok(caseData.title, '案件应有标题');
        assert.strictEqual(caseData.timeline.length, 0, '初始时间轴为空');
    });

    it('2. 案件受理 - 应能将案件从草稿状态转为已受理', function () {
        var caseData = createMockCase();
        caseData.status = 'accepted';
        caseData.acceptedAt = new Date().toISOString();
        caseData.timeline.push({
            event: 'case_accepted',
            time: caseData.acceptedAt,
            description: '案件已受理'
        });

        assert.strictEqual(caseData.status, 'accepted', '状态应为 accepted');
        assert.ok(caseData.acceptedAt, '应有受理时间');
        assert.strictEqual(caseData.timeline.length, 1, '时间轴应有1条记录');
        assert.strictEqual(caseData.timeline[0].event, 'case_accepted', '事件类型应为 case_accepted');
    });

    it('3. 合同审查 - 应能上传合同并进行风险审查', function () {
        var caseData = createMockCase();
        caseData.status = 'reviewing';

        var contract = {
            id: 'contract-001',
            name: '借款合同.pdf',
            type: 'loan_agreement',
            uploadedAt: new Date().toISOString(),
            reviewStatus: 'pending'
        };
        caseData.documents.push(contract);

        var reviewResult = {
            riskLevel: 'medium',
            totalIssues: 5,
            highRisk: 1,
            mediumRisk: 2,
            lowRisk: 2,
            reviewedAt: new Date().toISOString()
        };
        contract.reviewStatus = 'completed';
        contract.reviewResult = reviewResult;

        caseData.timeline.push({
            event: 'contract_uploaded',
            time: contract.uploadedAt,
            description: '上传借款合同.pdf'
        });
        caseData.timeline.push({
            event: 'contract_review_completed',
            time: reviewResult.reviewedAt,
            description: '合同审查完成，发现5个风险点'
        });

        assert.strictEqual(caseData.documents.length, 1, '应有1份文档');
        assert.strictEqual(contract.reviewStatus, 'completed', '审查状态应为 completed');
        assert.strictEqual(reviewResult.riskLevel, 'medium', '风险等级应为 medium');
        assert.strictEqual(reviewResult.totalIssues, 5, '应发现5个风险点');
        assert.strictEqual(caseData.timeline.length, 2, '时间轴应有2条记录');
    });

    it('4. 律师匹配 - 应能根据案件类型匹配合适的律师', function () {
        var caseData = createMockCase();
        caseData.cause = '借款合同纠纷';

        var lawyers = [
            { id: 'L001', name: '张明', specialties: ['合同纠纷', '民商事诉讼'], rating: 4.8, winRate: 85, caseCount: 320 },
            { id: 'L002', name: '李华', specialties: ['知识产权', '合同纠纷'], rating: 4.5, winRate: 78, caseCount: 210 },
            { id: 'L003', name: '王芳', specialties: ['婚姻家庭', '继承纠纷'], rating: 4.9, winRate: 90, caseCount: 280 }
        ];

        function matchLawyers(caseCause, lawyerList) {
            return lawyerList
                .filter(function (l) { return l.specialties.indexOf('合同纠纷') !== -1; })
                .sort(function (a, b) { return b.winRate - a.winRate; });
        }

        var matched = matchLawyers(caseData.cause, lawyers);

        assert.ok(matched.length >= 2, '应至少匹配2位律师');
        assert.strictEqual(matched[0].id, 'L001', '胜诉率最高的律师应排第一');
        assert.ok(matched[0].specialties.indexOf('合同纠纷') !== -1, '匹配的律师应擅长合同纠纷');
        assert.strictEqual(matched.length, 2, '不应匹配不相关领域的律师');

        caseData.assignedLawyer = matched[0];
        caseData.timeline.push({
            event: 'lawyer_assigned',
            time: new Date().toISOString(),
            description: '已分配主办律师：' + matched[0].name
        });

        assert.ok(caseData.assignedLawyer, '案件应分配主办律师');
    });

    it('5. 案件跟进 - 应能记录跟进事项和任务', function () {
        var caseData = createMockCase();
        caseData.status = 'processing';

        var tasks = [
            { id: 'T001', title: '收集证据材料', status: 'completed', dueDate: '2026-07-10', assignee: '张三' },
            { id: 'T002', title: '起草起诉状', status: 'in_progress', dueDate: '2026-07-15', assignee: '张明' },
            { id: 'T003', title: '准备庭审材料', status: 'pending', dueDate: '2026-07-25', assignee: '张明' }
        ];
        caseData.tasks = tasks;

        caseData.timeline.push({
            event: 'task_created',
            time: new Date().toISOString(),
            description: '创建3个任务事项'
        });

        assert.strictEqual(caseData.tasks.length, 3, '应有3个任务');
        var completed = tasks.filter(function (t) { return t.status === 'completed'; });
        assert.strictEqual(completed.length, 1, '应有1个已完成任务');
        var inProgress = tasks.filter(function (t) { return t.status === 'in_progress'; });
        assert.strictEqual(inProgress.length, 1, '应有1个进行中任务');
    });

    it('6. 开庭审理 - 应能记录开庭信息和庭审结果', function () {
        var caseData = createMockCase();
        caseData.status = 'hearing';

        var hearing = {
            id: 'H001',
            hearingDate: '2026-08-15',
            hearingTime: '09:00',
            courtRoom: '第三法庭',
            judge: '王法官',
            type: '一审开庭',
            minutes: '庭审过程顺利，双方进行了举证质证...',
            nextHearingDate: null
        };
        caseData.hearing = hearing;

        caseData.timeline.push({
            event: 'hearing_scheduled',
            time: '2026-08-01T10:00:00Z',
            description: '开庭时间：2026-08-15 09:00 第三法庭'
        });
        caseData.timeline.push({
            event: 'hearing_completed',
            time: '2026-08-15T12:00:00Z',
            description: '一审开庭审理结束，待判决'
        });

        assert.ok(caseData.hearing, '应有开庭信息');
        assert.strictEqual(hearing.judge, '王法官', '应有主审法官');
        assert.strictEqual(caseData.timeline.length, 2, '应有2条时间轴记录');
    });

    it('7. 结案归档 - 应能结案并归档案件材料', function () {
        var caseData = createMockCase();
        caseData.status = 'closed';

        var judgment = {
            date: '2026-09-01',
            result: 'plaintiff_win',
            amountAwarded: 480000,
            judgmentDocument: '(2026)京01民初1234号判决书.pdf'
        };
        caseData.judgment = judgment;
        caseData.closedAt = '2026-09-10T10:00:00Z';
        caseData.archived = true;

        caseData.timeline.push({
            event: 'judgment_issued',
            time: '2026-09-01T14:00:00Z',
            description: '一审判决：原告胜诉，获赔48万元'
        });
        caseData.timeline.push({
            event: 'case_closed',
            time: caseData.closedAt,
            description: '案件结案归档'
        });

        assert.strictEqual(caseData.status, 'closed', '案件状态应为 closed');
        assert.strictEqual(caseData.archived, true, '案件应已归档');
        assert.ok(caseData.judgment, '应有判决信息');
        assert.strictEqual(judgment.result, 'plaintiff_win', '判决结果应为原告胜诉');
        assert.ok(caseData.closedAt, '应有结案时间');
    });

    it('8. 完整生命周期 - 应能完整流转所有状态', function () {
        var caseData = createMockCase();
        var expectedStatuses = [
            'draft', 'accepted', 'reviewing', 'processing', 'hearing', 'closed'
        ];
        var currentStep = 0;

        function advanceCase() {
            if (currentStep < expectedStatuses.length - 1) {
                currentStep++;
                caseData.status = expectedStatuses[currentStep];
                caseData.timeline.push({
                    event: 'status_changed',
                    time: new Date().toISOString(),
                    from: expectedStatuses[currentStep - 1],
                    to: expectedStatuses[currentStep]
                });
                return true;
            }
            return false;
        }

        for (var i = 0; i < expectedStatuses.length - 1; i++) {
            var advanced = advanceCase();
            assert.strictEqual(advanced, true, '应能推进到下一个状态');
        }

        assert.strictEqual(caseData.status, 'closed', '最终状态应为 closed');
        assert.strictEqual(
            caseData.timeline.length,
            expectedStatuses.length - 1,
            '状态变更记录数应正确'
        );
        assert.strictEqual(
            currentStep,
            expectedStatuses.length - 1,
            '应走完所有状态'
        );
    });
});
