'use strict';

const assert = require('assert');
const { describe, it } = require('node:test');

describe('Collaboration Flow - 协作流程测试', function () {
    function createMockUser(id, name, role) {
        return {
            id: id,
            name: name,
            email: id + '@example.com',
            role: role,
            avatar: ''
        };
    }

    function createMockTeam() {
        return {
            id: 'team-001',
            name: '诉讼团队',
            description: '专注民商事诉讼',
            ownerId: 'U001',
            members: [],
            cases: [],
            tasks: [],
            comments: [],
            createdAt: new Date().toISOString()
        };
    }

    it('1. 团队创建 - 应能创建新团队并设置信息', function () {
        var owner = createMockUser('U001', '张明', 'owner');
        var team = createMockTeam();
        team.ownerId = owner.id;

        team.members.push({
            userId: owner.id,
            name: owner.name,
            role: 'owner',
            joinedAt: team.createdAt
        });

        assert.strictEqual(team.id, 'team-001', '团队应有ID');
        assert.strictEqual(team.name, '诉讼团队', '团队应有名称');
        assert.strictEqual(team.ownerId, 'U001', '团队应有所有者');
        assert.strictEqual(team.members.length, 1, '初始应有1个成员（所有者）');
        assert.strictEqual(team.members[0].role, 'owner', '所有者角色应为 owner');
    });

    it('2. 成员邀请 - 应能邀请新成员加入团队', function () {
        var team = createMockTeam();
        var owner = createMockUser('U001', '张明', 'owner');
        team.members.push({ userId: owner.id, name: owner.name, role: 'owner', joinedAt: team.createdAt });

        var invitations = [];

        function inviteMember(email, role) {
            if (!email || email.indexOf('@') === -1) {
                return { success: false, error: '邮箱无效' };
            }
            var alreadyMember = team.members.some(function (m) { return m.email === email; });
            if (alreadyMember) {
                return { success: false, error: '该用户已是团队成员' };
            }
            var invitation = {
                id: 'inv-' + Date.now(),
                email: email,
                role: role || 'member',
                status: 'pending',
                invitedAt: new Date().toISOString(),
                invitedBy: owner.id
            };
            invitations.push(invitation);
            return { success: true, invitation: invitation };
        }

        var invite1 = inviteMember('lawyer1@example.com', 'member');
        assert.strictEqual(invite1.success, true, '邀请应成功');
        assert.strictEqual(invitations.length, 1, '应有1条邀请记录');
        assert.strictEqual(invite1.invitation.status, 'pending', '邀请状态应为 pending');
        assert.strictEqual(invite1.invitation.role, 'member', '角色应为 member');

        var invite2 = inviteMember('lawyer2@example.com', 'admin');
        assert.strictEqual(invite2.success, true, '邀请管理员应成功');
        assert.strictEqual(invitations.length, 2, '应有2条邀请记录');

        var invalidInvite = inviteMember('invalid-email', 'member');
        assert.strictEqual(invalidInvite.success, false, '无效邮箱邀请应失败');

        function acceptInvitation(invitationId, user) {
            var inv = invitations.find(function (i) { return i.id === invitationId; });
            if (!inv || inv.status !== 'pending') {
                return { success: false, error: '邀请无效' };
            }
            inv.status = 'accepted';
            team.members.push({
                userId: user.id,
                name: user.name,
                email: inv.email,
                role: inv.role,
                joinedAt: new Date().toISOString()
            });
            return { success: true, member: team.members[team.members.length - 1] };
        }

        var newMember = createMockUser('U002', '李华', 'lawyer');
        var acceptResult = acceptInvitation(invite1.invitation.id, newMember);
        assert.strictEqual(acceptResult.success, true, '接受邀请应成功');
        assert.strictEqual(team.members.length, 2, '团队成员数应为2');
        assert.strictEqual(team.members[1].role, 'member', '新成员角色应为 member');
    });

    it('3. 任务分配 - 应能创建和分配团队任务', function () {
        var team = createMockTeam();
        team.members = [
            { userId: 'U001', name: '张明', role: 'owner' },
            { userId: 'U002', name: '李华', role: 'member' },
            { userId: 'U003', name: '王芳', role: 'member' }
        ];

        function createTask(title, description, assigneeId, dueDate) {
            var task = {
                id: 'task-' + Date.now(),
                title: title,
                description: description || '',
                assigneeId: assigneeId || null,
                creatorId: 'U001',
                status: 'pending',
                priority: 'medium',
                dueDate: dueDate || null,
                createdAt: new Date().toISOString(),
                completedAt: null
            };
            team.tasks.push(task);
            return task;
        }

        function updateTaskStatus(taskId, status) {
            var task = team.tasks.find(function (t) { return t.id === taskId; });
            if (!task) {
                return { success: false, error: '任务不存在' };
            }
            task.status = status;
            if (status === 'completed') {
                task.completedAt = new Date().toISOString();
            }
            return { success: true, task: task };
        }

        function reassignTask(taskId, assigneeId) {
            var task = team.tasks.find(function (t) { return t.id === taskId; });
            var assignee = team.members.find(function (m) { return m.userId === assigneeId; });
            if (!task || !assignee) {
                return { success: false, error: '任务或成员不存在' };
            }
            task.assigneeId = assigneeId;
            return { success: true, task: task };
        }

        var task1 = createTask('起草起诉状', '为张三诉李四案起草起诉状', 'U002', '2026-07-15');
        assert.ok(task1.id, '任务应有ID');
        assert.strictEqual(task1.title, '起草起诉状', '任务标题应正确');
        assert.strictEqual(task1.assigneeId, 'U002', '任务应分配给U002');
        assert.strictEqual(task1.status, 'pending', '初始状态应为 pending');
        assert.strictEqual(team.tasks.length, 1, '应有1个任务');

        createTask('收集证据', '整理案件证据材料', 'U003', '2026-07-10');
        createTask('准备庭审材料', null, 'U001', '2026-07-25');
        assert.strictEqual(team.tasks.length, 3, '应有3个任务');

        var updateResult = updateTaskStatus(task1.id, 'in_progress');
        assert.strictEqual(updateResult.success, true, '更新状态应成功');
        assert.strictEqual(task1.status, 'in_progress', '状态应变为 in_progress');

        var reassignResult = reassignTask(task1.id, 'U003');
        assert.strictEqual(reassignResult.success, true, '重新分配应成功');
        assert.strictEqual(task1.assigneeId, 'U003', '负责人应变为U003');

        var completeResult = updateTaskStatus(task1.id, 'completed');
        assert.strictEqual(completeResult.success, true, '完成任务应成功');
        assert.strictEqual(task1.status, 'completed', '状态应变为 completed');
        assert.ok(task1.completedAt, '应有完成时间');

        var completedCount = team.tasks.filter(function (t) { return t.status === 'completed'; }).length;
        assert.strictEqual(completedCount, 1, '应有1个已完成任务');
    });

    it('4. 评论讨论 - 应能在任务和案件中评论讨论', function () {
        var team = createMockTeam();
        team.members = [
            { userId: 'U001', name: '张明', role: 'owner' },
            { userId: 'U002', name: '李华', role: 'member' }
        ];

        team.tasks.push({
            id: 'T001',
            title: '起草起诉状',
            comments: []
        });

        team.cases.push({
            id: 'C001',
            title: '张三诉李四案',
            comments: []
        });

        function addComment(targetType, targetId, authorId, content) {
            var target = null;
            if (targetType === 'task') {
                target = team.tasks.find(function (t) { return t.id === targetId; });
            } else if (targetType === 'case') {
                target = team.cases.find(function (c) { return c.id === targetId; });
            }
            if (!target) {
                return { success: false, error: '目标不存在' };
            }
            var author = team.members.find(function (m) { return m.userId === authorId; });
            if (!author) {
                return { success: false, error: '用户不存在' };
            }
            var comment = {
                id: 'cmt-' + Date.now() + Math.random(),
                authorId: authorId,
                authorName: author.name,
                content: content,
                createdAt: new Date().toISOString(),
                replyTo: null,
                likes: 0
            };
            target.comments.push(comment);
            return { success: true, comment: comment };
        }

        var cmt1 = addComment('task', 'T001', 'U001', '起诉状初稿已完成，请审阅。');
        assert.strictEqual(cmt1.success, true, '添加评论应成功');
        assert.ok(cmt1.comment.id, '评论应有ID');
        assert.strictEqual(cmt1.comment.authorId, 'U001', '评论作者应为U001');
        assert.strictEqual(team.tasks[0].comments.length, 1, '任务应有1条评论');

        var cmt2 = addComment('task', 'T001', 'U002', '收到，我来检查一下。');
        assert.strictEqual(team.tasks[0].comments.length, 2, '任务应有2条评论');

        var caseComment = addComment('case', 'C001', 'U001', '这个案件的证据需要补充。');
        assert.strictEqual(caseComment.success, true, '案件评论应成功');
        assert.strictEqual(team.cases[0].comments.length, 1, '案件应有1条评论');

        function likeComment(targetType, targetId, commentId) {
            var target = null;
            if (targetType === 'task') {
                target = team.tasks.find(function (t) { return t.id === targetId; });
            } else if (targetType === 'case') {
                target = team.cases.find(function (c) { return c.id === targetId; });
            }
            if (!target) return { success: false };
            var comment = target.comments.find(function (c) { return c.id === commentId; });
            if (!comment) return { success: false };
            comment.likes++;
            return { success: true, likes: comment.likes };
        }

        var likeResult = likeComment('task', 'T001', cmt1.comment.id);
        assert.strictEqual(likeResult.success, true, '点赞应成功');
        assert.strictEqual(likeResult.likes, 1, '点赞数应为1');
    });
});
