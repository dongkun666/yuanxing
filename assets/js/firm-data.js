/*
 * LexPrime 律所版 0.1 - Mock 数据
 * 2026-06-28
 *
 * 当后端 API (cases-crawler) 未启动时使用此 mock
 * 后端启动后自动 fallback 到真实 API
 */

(function() {
    'use strict';

    var FIRM_INFO = {
        id: 'firm-demo-001',
        name: '示例律师事务所',
        region: '北京市',
        size: 'medium',
        subscription_tier: 'pro'
    };

    var LAWYERS = [
        {
            id: 'u-1',
            name: '张律师',
            role: 'partner',
            roleLabel: '合伙人',
            email: 'zhang@example-law.com',
            phone: '13800000001',
            avatar_color: 'bg-brand',
            specialties: ['民商事', '知识产权'],
            bio: '20 年律师经验, 合伙人, 律所主任',
            cases_count: 18,
            month_hours: 168,
            is_active: true
        },
        {
            id: 'u-demo-002',
            name: '李律师',
            role: 'senior',
            roleLabel: '高级律师',
            email: 'li@example-law.com',
            phone: '13800000002',
            avatar_color: 'bg-wiki',
            specialties: ['刑事', '行政'],
            bio: '高级律师, 刑事辩护专家, 前检察官',
            cases_count: 12,
            month_hours: 152,
            is_active: true
        },
        {
            id: 'u-demo-003',
            name: '王律师',
            role: 'lawyer',
            roleLabel: '律师',
            email: 'wang@example-law.com',
            phone: '13800000003',
            avatar_color: 'bg-success',
            specialties: ['婚姻家事', '合同纠纷'],
            bio: '律师, 婚姻家事和合同纠纷方向',
            cases_count: 9,
            month_hours: 140,
            is_active: true
        },
        {
            id: 'u-demo-004',
            name: '赵律师',
            role: 'lawyer',
            roleLabel: '律师',
            email: 'zhao@example-law.com',
            phone: '13800000004',
            avatar_color: 'bg-urgent',
            specialties: ['劳动争议', '工伤'],
            bio: '律师, 专注劳动法和工伤赔偿',
            cases_count: 7,
            month_hours: 128,
            is_active: true
        },
        {
            id: 'u-demo-005',
            name: '陈律师',
            role: 'assistant',
            roleLabel: '律师助理',
            email: 'chen@example-law.com',
            phone: '13800000005',
            avatar_color: 'bg-fg-tertiary',
            specialties: ['民商事'],
            bio: '律师助理, 协助主办律师办案',
            cases_count: 3,
            month_hours: 96,
            is_active: true
        },
        {
            id: 'u-demo-006',
            name: '林律师',
            role: 'senior',
            roleLabel: '高级律师',
            email: 'lin@example-law.com',
            phone: '13800000006',
            avatar_color: 'bg-purple-500',
            specialties: ['公司治理', '股权纠纷'],
            bio: '高级律师, 公司法方向',
            cases_count: 11,
            month_hours: 144,
            is_active: false
        }
    ];

    var TIME_ENTRIES = [
        {
            id: 'te-001',
            date: '2026-06-28',
            lawyer_id: 'u-1',
            lawyer_name: '张律师',
            case_title: 'ABC 科技公司诉 XYZ 网络公司合同纠纷',
            description: '起草一审代理意见, 整理证据 5-7',
            hours: 3.5,
            billable: true,
            rate: 1500,
            amount: 5250,
            status: 'draft'
        },
        {
            id: 'te-002',
            date: '2026-06-28',
            lawyer_id: 'u-demo-002',
            lawyer_name: '李律师',
            case_title: '王某涉嫌合同诈骗案',
            description: '准备开庭材料, 阅卷',
            hours: 4.0,
            billable: true,
            rate: 1200,
            amount: 4800,
            status: 'submitted'
        },
        {
            id: 'te-003',
            date: '2026-06-27',
            lawyer_id: 'u-1',
            lawyer_name: '张律师',
            case_title: '客户会议 - 知识产权咨询',
            description: '与客户讨论专利侵权应对策略',
            hours: 2.0,
            billable: true,
            rate: 1500,
            amount: 3000,
            status: 'approved'
        },
        {
            id: 'te-004',
            date: '2026-06-27',
            lawyer_id: 'u-demo-003',
            lawyer_name: '王律师',
            case_title: '刘某离婚案',
            description: '起草财产分割清单',
            hours: 2.5,
            billable: true,
            rate: 1000,
            amount: 2500,
            status: 'submitted'
        },
        {
            id: 'te-005',
            date: '2026-06-26',
            lawyer_id: 'u-demo-004',
            lawyer_name: '赵律师',
            case_title: '员工工伤认定复议案',
            description: '准备复议申请材料',
            hours: 3.0,
            billable: true,
            rate: 1000,
            amount: 3000,
            status: 'approved'
        },
        {
            id: 'te-006',
            date: '2026-06-26',
            lawyer_id: 'u-demo-002',
            lawyer_name: '李律师',
            case_title: '内部培训',
            description: '刑辩经验分享会',
            hours: 1.5,
            billable: false,
            rate: 0,
            amount: 0,
            status: 'approved'
        },
        {
            id: 'te-007',
            date: '2026-06-25',
            lawyer_id: 'u-1',
            lawyer_name: '张律师',
            case_title: 'ABC 科技公司诉 XYZ 网络公司合同纠纷',
            description: '出庭',
            hours: 5.0,
            billable: true,
            rate: 1500,
            amount: 7500,
            status: 'invoiced'
        },
        {
            id: 'te-008',
            date: '2026-06-25',
            lawyer_id: 'u-demo-005',
            lawyer_name: '陈律师',
            case_title: '协助李律师 - 王某案',
            description: '证据整理, 装订',
            hours: 4.0,
            billable: true,
            rate: 500,
            amount: 2000,
            status: 'submitted'
        }
    ];

    var STATS = {
        lawyers_total: 6,
        lawyers_active: 5,
        partners: 1,
        month_hours: 928,
        last_month_hours: 856,
        hours_growth: 8.4,
        cases_count: 32,
        new_cases_week: 5,
        billable_hours: 720,
        billable_rate: 77.6
    };

    // ===== 暴露到 globalThis =====
    globalThis.FIRM_INFO = FIRM_INFO;
    globalThis.FIRM_LAWYERS = LAWYERS;
    globalThis.FIRM_TIME_ENTRIES = TIME_ENTRIES;
    globalThis.FIRM_STATS = STATS;

    // 兼容旧名
    globalThis.MOCK_FIRM_LAWYERS = LAWYERS;
    globalThis.MOCK_FIRM_TIME_ENTRIES = TIME_ENTRIES;
    globalThis.MOCK_FIRM_STATS = STATS;
})();
