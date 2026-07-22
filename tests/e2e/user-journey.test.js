'use strict';

const assert = require('assert');
const { describe, it } = require('node:test');

describe('User Journey - 用户旅程测试', function () {
    function createMockUser() {
        return {
            id: null,
            email: null,
            name: null,
            role: 'visitor',
            isLoggedIn: false,
            createdAt: null,
            lastLoginAt: null,
            onboardingCompleted: false,
            subscription: null,
            usage: {
                casesViewed: 0,
                searchesPerformed: 0,
                contractsReviewed: 0,
                documentsGenerated: 0
            },
            preferences: {
                theme: 'light',
                notifications: true,
                language: 'zh-CN'
            }
        };
    }

    function createMockApp() {
        return {
            users: [],
            registeredEmails: {},
            features: {
                basicSearch: { limit: 10, paid: false },
                caseView: { limit: 20, paid: false },
                contractReview: { limit: 3, paid: true },
                docGeneration: { limit: 5, paid: true },
                advancedAnalytics: { limit: -1, paid: true }
            },
            plans: [
                { id: 'free', name: '免费版', price: 0, limits: { search: 10, caseView: 20, contractReview: 0, docGen: 0 } },
                { id: 'pro', name: '专业版', price: 299, limits: { search: -1, caseView: -1, contractReview: 50, docGen: 100 } },
                { id: 'enterprise', name: '企业版', price: 999, limits: { search: -1, caseView: -1, contractReview: -1, docGen: -1 } }
            ]
        };
    }

    it('1. 注册 - 新用户应能完成注册流程', function () {
        var app = createMockApp();
        var user = createMockUser();

        var registrationData = {
            email: 'test@example.com',
            password: 'TestPass123!',
            name: '测试用户',
            phone: '13800138000'
        };

        function validateEmail(email) {
            return typeof email === 'string' && email.indexOf('@') !== -1;
        }

        function validatePassword(password) {
            return typeof password === 'string' && password.length >= 8;
        }

        assert.strictEqual(validateEmail(registrationData.email), true, '邮箱格式应有效');
        assert.strictEqual(validatePassword(registrationData.password), true, '密码强度应达标');

        function registerUser(data) {
            if (app.registeredEmails[data.email]) {
                return { success: false, error: '邮箱已注册' };
            }
            var newUser = createMockUser();
            newUser.id = 'user-' + Date.now();
            newUser.email = data.email;
            newUser.name = data.name;
            newUser.role = 'user';
            newUser.createdAt = new Date().toISOString();
            newUser.subscription = { plan: 'free', status: 'active' };
            app.users.push(newUser);
            app.registeredEmails[data.email] = true;
            return { success: true, user: newUser };
        }

        var result = registerUser(registrationData);
        assert.strictEqual(result.success, true, '注册应成功');
        assert.ok(result.user.id, '用户应有ID');
        assert.strictEqual(result.user.email, registrationData.email, '邮箱应正确');
        assert.strictEqual(result.user.role, 'user', '角色应为 user');
        assert.ok(result.user.subscription, '应有默认订阅');
        assert.strictEqual(result.user.subscription.plan, 'free', '默认应为免费版');
        assert.strictEqual(app.users.length, 1, '应用应有1个用户');

        var duplicateResult = registerUser(registrationData);
        assert.strictEqual(duplicateResult.success, false, '重复注册应失败');
    });

    it('2. 登录 - 用户应能登录和登出', function () {
        var app = createMockApp();
        var user = createMockUser();
        user.id = 'user-001';
        user.email = 'test@example.com';
        user.passwordHash = 'hashed_password';
        user.name = '测试用户';
        user.role = 'user';
        app.users.push(user);

        function login(email, password) {
            var found = app.users.find(function (u) { return u.email === email; });
            if (!found) {
                return { success: false, error: '用户不存在' };
            }
            found.isLoggedIn = true;
            found.lastLoginAt = new Date().toISOString();
            return { success: true, user: found };
        }

        function logout(u) {
            u.isLoggedIn = false;
            return true;
        }

        var loginResult = login('test@example.com', 'password');
        assert.strictEqual(loginResult.success, true, '登录应成功');
        assert.strictEqual(loginResult.user.isLoggedIn, true, '用户应处于登录状态');
        assert.ok(loginResult.user.lastLoginAt, '应记录最后登录时间');

        var wrongLogin = login('wrong@example.com', 'password');
        assert.strictEqual(wrongLogin.success, false, '错误邮箱登录应失败');

        logout(user);
        assert.strictEqual(user.isLoggedIn, false, '登出后应为未登录状态');
    });

    it('3. 首次使用 - 新用户应完成引导流程', function () {
        var user = createMockUser();
        user.id = 'user-001';
        user.name = '测试用户';
        user.onboardingCompleted = false;

        var onboardingSteps = [
            { id: 'welcome', title: '欢迎使用 LexPrime', completed: false },
            { id: 'profile', title: '完善个人资料', completed: false },
            { id: 'preferences', title: '设置偏好', completed: false },
            { id: 'tour', title: '功能导览', completed: false },
            { id: 'done', title: '开始使用', completed: false }
        ];

        function completeStep(stepId) {
            var step = onboardingSteps.find(function (s) { return s.id === stepId; });
            if (step) {
                step.completed = true;
                return true;
            }
            return false;
        }

        function getProgress() {
            var completed = onboardingSteps.filter(function (s) { return s.completed; });
            return Math.round((completed.length / onboardingSteps.length) * 100);
        }

        assert.strictEqual(getProgress(), 0, '初始进度应为0%');

        completeStep('welcome');
        assert.strictEqual(getProgress(), 20, '完成第一步后进度应为20%');

        completeStep('profile');
        completeStep('preferences');
        completeStep('tour');
        completeStep('done');

        assert.strictEqual(getProgress(), 100, '所有步骤完成后进度应为100%');

        user.onboardingCompleted = true;
        assert.strictEqual(user.onboardingCompleted, true, '引导流程应标记为已完成');
    });

    it('4. 核心功能 - 用户应能使用主要功能', function () {
        var user = createMockUser();
        user.id = 'user-001';
        user.isLoggedIn = true;
        user.subscription = { plan: 'pro', status: 'active' };

        function performSearch(query) {
            user.usage.searchesPerformed++;
            return {
                success: true,
                query: query,
                total: 25,
                results: [],
                page: 1
            };
        }

        function viewCase(caseId) {
            user.usage.casesViewed++;
            return { id: caseId, title: '测试案件' };
        }

        function reviewContract(contractData) {
            if (user.subscription.plan === 'free' && user.usage.contractsReviewed >= 3) {
                return { success: false, error: '超出免费额度' };
            }
            user.usage.contractsReviewed++;
            return {
                success: true,
                riskLevel: 'medium',
                issues: 5,
                reviewId: 'review-' + Date.now()
            };
        }

        var searchResult = performSearch('借款合同纠纷');
        assert.strictEqual(searchResult.success, true, '搜索应成功');
        assert.strictEqual(user.usage.searchesPerformed, 1, '搜索次数应加1');

        viewCase('case-001');
        assert.strictEqual(user.usage.casesViewed, 1, '查看案件数应加1');

        var reviewResult = reviewContract({ name: '合同.pdf' });
        assert.strictEqual(reviewResult.success, true, '合同审查应成功');
        assert.strictEqual(user.usage.contractsReviewed, 1, '审查次数应加1');
        assert.strictEqual(reviewResult.riskLevel, 'medium', '风险等级应为 medium');
    });

    it('5. 付费转化 - 用户应能升级订阅计划', function () {
        var user = createMockUser();
        user.id = 'user-001';
        user.isLoggedIn = true;
        user.subscription = { plan: 'free', status: 'active' };

        var plans = [
            { id: 'free', name: '免费版', price: 0, features: ['基础搜索', '案件浏览'] },
            { id: 'pro', name: '专业版', price: 299, features: ['无限搜索', '合同审查', '文书生成'] },
            { id: 'enterprise', name: '企业版', price: 999, features: ['全部功能', '团队协作', '专属客服'] }
        ];

        function upgradePlan(planId) {
            var plan = plans.find(function (p) { return p.id === planId; });
            if (!plan) {
                return { success: false, error: '计划不存在' };
            }
            user.subscription = {
                plan: planId,
                status: 'active',
                upgradedAt: new Date().toISOString()
            };
            return { success: true, plan: plan };
        }

        assert.strictEqual(user.subscription.plan, 'free', '初始应为免费版');

        var upgradeResult = upgradePlan('pro');
        assert.strictEqual(upgradeResult.success, true, '升级应成功');
        assert.strictEqual(user.subscription.plan, 'pro', '应升级到专业版');
        assert.strictEqual(user.subscription.status, 'active', '订阅状态应为 active');
        assert.ok(user.subscription.upgradedAt, '应有升级时间');

        var enterpriseResult = upgradePlan('enterprise');
        assert.strictEqual(enterpriseResult.success, true, '升级到企业版应成功');
        assert.strictEqual(user.subscription.plan, 'enterprise', '应升级到企业版');
    });
});
