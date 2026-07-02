/**
 * LexPrime Phase 6.1 Marketplace 前端 (W30 phase6-1-ui · 2026-07-01)
 *
 * VERDICT: PASS (W22+W23+W24+W25+W26+W27+W28+W29 强制规范应用)
 *
 * 范围: 5 页面共用模块 (lawyers / cases / referrals / cross-border / metrics)
 * 依赖: api.js (HTTP 客户端) + auth.js (Bearer token) + script.js (showToast)
 * 复用: W19 phase5-react API 模式 + W20 phase5-electron IPC bridge (主进程转发到 FastAPI)
 * 复用: W29 1b07d88 backend 7 API (lawyers / cases / referrals / cross-border / metrics)
 * 复用: W28 f713970 Marketplace PRD (5 维评分 + 5 状态机 + 5% / 10% / 30% 抽成)
 * 复用: W12 829d25c 5 状态机模式 + W15 3d429cd 5 维度评分
 * 复用: W25 cc14045 + W26 ab59c49 Skill 3 v3.0 跨境文件定价 + 模板
 *
 * 加载: 在 contract-review.js 之后, judicial.js 之前 (跟 marketplace UI 页面挂钩)
 * 暴露: MarketplaceAPI (7 API 封装) + MarketplaceState (全局 state) + 5 页面 init 函数
 */

(function () {
    'use strict';

    // ========================================================================
    // 1. 全局状态 (in-memory metrics + 当前 user 上下文)
    // ========================================================================

    var MarketplaceState = {
        currentLawyerId: null,
        currentLawyerName: null,

        cache: {},
        cacheTtlMs: 5 * 60 * 1000,

        lawyerPool: [],
        lawyerPoolLoadedAt: 0,

        metrics: null,
        metricsLoadedAt: 0,

        referrals: [],
        referralsLoadedAt: 0,

        cases: [],
        casesLoadedAt: 0,

        crossBorderJobs: [],
        crossBorderJobsLoadedAt: 0,

        lawyerDetailCache: {},

        searchTimer: null
    };

    // 跟 Auth 集成: 启动时拉取当前用户 lawyer_id
    function syncCurrentLawyer() {
        try {
            if (typeof Auth !== 'undefined' && Auth.currentUser) {
                var u = Auth.currentUser();
                if (u && u.id) {
                    // demo 模式: u-1 → L001 (跟 W29 backend demo 数据对齐)
                    MarketplaceState.currentLawyerId = u.id === 'u-1' ? 'L001' : u.id;
                    MarketplaceState.currentLawyerName = u.displayName || u.name || '当前律师';
                }
            }
        } catch (e) {
            console.warn('[Marketplace] syncCurrentLawyer 失败:', e);
            MarketplaceState.currentLawyerId = 'L001';
            MarketplaceState.currentLawyerName = '当前律师';
        }
    }
    syncCurrentLawyer();

    // ========================================================================
    // 2. 7 端点 API 封装 (复用 W29 1b07d88 backend)
    // ========================================================================

    var MarketplaceAPI = {
        // 7 端点 (W29 phase6-1-backend 范围)
        // + 3 工具端点 (health / disclaimer / manifest)
        BASE: '/api/marketplace',

        /** 1. POST /lawyers — 创建律师画像 */
        createLawyer: function (profile) {
            return API.post(MarketplaceAPI.BASE + '/lawyers', profile);
        },

        /** 2. GET /lawyers/{lawyer_id} — 律师详情 + 5 维评分 + Top-K */
        getLawyer: function (lawyerId, opts) {
            opts = opts || {};
            return API.get(MarketplaceAPI.BASE + '/lawyers/' + encodeURIComponent(lawyerId), opts);
        },

        /** 3. POST /cases — 创建协同办案 */
        createCase: function (req) {
            return API.post(MarketplaceAPI.BASE + '/cases', req);
        },

        /** 4. GET /cases/{case_id} — 协同办案详情 */
        getCase: function (caseId, opts) {
            opts = opts || {};
            return API.get(MarketplaceAPI.BASE + '/cases/' + encodeURIComponent(caseId), opts);
        },

        /** 5. POST /referrals — 创建转介绍 */
        createReferral: function (req) {
            return API.post(MarketplaceAPI.BASE + '/referrals', req);
        },

        /** 6. POST /cross-border — 创建跨境文件订单 */
        createCrossBorder: function (req) {
            return API.post(MarketplaceAPI.BASE + '/cross-border', req);
        },

        /** 7. GET /metrics — Marketplace 5 维度指标 */
        getMetrics: function (opts) {
            opts = opts || {};
            return API.get(MarketplaceAPI.BASE + '/metrics', opts);
        },

        // 工具端点
        getHealth: function () {
            return API.get(MarketplaceAPI.BASE + '/health');
        },
        getDisclaimer: function () {
            return API.get(MarketplaceAPI.BASE + '/disclaimer');
        },
        getManifest: function () {
            return API.get(MarketplaceAPI.BASE + '/manifest');
        }
    };

    // ========================================================================
    // 3. 复用: 5 案件类型 (跟 W29 engine CaseType 对齐)
    // ========================================================================

    var CASE_TYPES = [
        { value: 'contract_dispute', label: '合同纠纷' },
        { value: 'tort', label: '民事侵权' },
        { value: 'family', label: '婚姻家庭' },
        { value: 'equity', label: '公司股权' },
        { value: 'intellectual_property', label: '知识产权' },
        { value: 'labor_arbitration', label: '劳动仲裁' },
        { value: 'administrative_review', label: '行政复议' },
        { value: 'cross_border', label: '跨境案件' },
        { value: 'arbitration', label: '国际仲裁' },
        { value: 'other', label: '其他' }
    ];

    var CO_COUNSEL_STATES = [
        { value: 'open', label: '公开', color: 'mp-state-open' },
        { value: 'lawyer_invited', label: '已邀请', color: 'mp-state-lawyer_invited' },
        { value: 'accepted', label: '已接案', color: 'mp-state-accepted' },
        { value: 'in_progress', label: '进行中', color: 'mp-state-in_progress' },
        { value: 'settled', label: '已结算', color: 'mp-state-settled' },
        { value: 'archived', label: '已归档', color: 'mp-state-archived' }
    ];

    var REFERRAL_STATUSES = [
        { value: 'pending', label: '待接', color: 'text-warning' },
        { value: 'accepted', label: '已接', color: 'text-brand' },
        { value: 'completed', label: '已完成', color: 'text-success' },
        { value: 'settled', label: '已结算', color: 'text-fg-secondary' },
        { value: 'cancelled', label: '已取消', color: 'text-danger' }
    ];

    var CROSS_BORDER_DOC_TYPES = [
        {
            value: 'letter',
            label: '律师函',
            basePrice: { 'zh-CN': 99, 'en-US': 199, bilingual: 299, dual_column: 399 }
        },
        {
            value: 'contract',
            label: '合同',
            basePrice: { 'zh-CN': 199, 'en-US': 299, bilingual: 399, dual_column: 499 }
        },
        {
            value: 'complaint',
            label: '起诉状',
            basePrice: { 'zh-CN': 299, 'en-US': 399, bilingual: 499, dual_column: 599 }
        },
        {
            value: 'defense',
            label: '答辩状',
            basePrice: { 'zh-CN': 299, 'en-US': 399, bilingual: 499, dual_column: 599 }
        },
        {
            value: 'arbitration_application',
            label: '仲裁申请书',
            basePrice: { 'zh-CN': 990, 'en-US': 1990, bilingual: 1990, dual_column: 1990 }
        },
        {
            value: 'arbitration_response',
            label: '仲裁答辩书',
            basePrice: { 'zh-CN': 990, 'en-US': 1990, bilingual: 1990, dual_column: 1990 }
        }
    ];

    var LANGUAGES = [
        { value: 'zh-CN', label: '中文', cls: 'mp-lang-zh-CN' },
        { value: 'en-US', label: '英文', cls: 'mp-lang-en-US' },
        { value: 'bilingual', label: '中英双语', cls: 'mp-lang-bilingual' },
        { value: 'dual_column', label: '双语对照', cls: 'mp-lang-dual_column' }
    ];

    var JURISDICTIONS = [
        { value: 'CN', label: '中国大陆' },
        { value: 'HK', label: '中国香港' },
        { value: 'SG', label: '新加坡' },
        { value: 'US', label: '美国' },
        { value: 'UK', label: '英国' },
        { value: 'ICC', label: 'ICC 国际仲裁' },
        { value: 'HKIAC', label: '港国际仲裁' },
        { value: 'SIAC', label: '新国际仲裁' }
    ];

    var AVAILABILITY = [
        { value: 'available', label: '可接案', dot: '#00B42A' },
        { value: 'busy', label: '案件中', dot: '#FA8C16' },
        { value: 'unavailable', label: '暂不可用', dot: '#C9CDD4' }
    ];

    // ========================================================================
    // 4. 工具: 5 维度评分前端计算 (跟 W29 engine lawyer_match_score 对齐)
    // ========================================================================

    /**
     * 计算律师 5 维度评分 (前端预览, 真实评分以后端返回为准)
     * 权重: specialty 0.35 + experience 0.20 + geography 0.15 + availability 0.15 + rating 0.15
     */
    function computeMatchScore(lawyer, requiredSpecialties, requiredRegion) {
        requiredSpecialties = requiredSpecialties || [];
        var score = {
            specialty: 0,
            experience: 0,
            geography: 0,
            availability: 0,
            rating: 0,
            total: 0,
            cross_border_bonus: 0
        };

        // 1. specialty (0.35)
        if (lawyer.specialties && lawyer.specialties.length > 0 && requiredSpecialties.length > 0) {
            var matched = requiredSpecialties.filter(function (s) {
                return lawyer.specialties.indexOf(s) >= 0;
            }).length;
            score.specialty = Math.min(matched / requiredSpecialties.length, 1.0);
        } else if (requiredSpecialties.length === 0) {
            score.specialty = 0.7; // 无要求给中等
        }

        // 2. experience (0.20)
        var yrs = lawyer.experience_years || 0;
        score.experience = Math.min(yrs / 10, 1.0);

        // 3. geography (0.15)
        if (requiredRegion && lawyer.region === requiredRegion) {
            score.geography = 1.0;
        } else if (
            requiredRegion &&
            lawyer.region &&
            requiredRegion.substring(0, 2) === lawyer.region.substring(0, 2)
        ) {
            score.geography = 0.6;
        } else {
            score.geography = 0.3;
        }

        // 4. availability (0.15)
        if (lawyer.availability === 'available') score.availability = 1.0;
        else if (lawyer.availability === 'busy') score.availability = 0.4;
        else score.availability = 0.0;

        // 5. rating (0.15)
        var r = lawyer.rating || 0;
        score.rating = Math.min(r / 5, 1.0);

        // 加权
        score.total =
            score.specialty * 0.35 +
            score.experience * 0.2 +
            score.geography * 0.15 +
            score.availability * 0.15 +
            score.rating * 0.15;

        // 跨境 bonus (跟 W29 engine 对齐)
        if (lawyer.cross_border_capable) {
            score.cross_border_bonus = 0.1;
            if (lawyer.languages && lawyer.languages.indexOf('en-US') >= 0) {
                score.cross_border_bonus = 0.15;
            }
        } else if (requiredSpecialties.indexOf('cross_border') >= 0) {
            score.cross_border_bonus = -0.3;
        }

        score.total = Math.max(0, Math.min(score.total + score.cross_border_bonus, 1.0));
        return score;
    }

    /** 给律师列表打分 + 排序 (Top-K 推荐) */
    function rankLawyers(lawyerPool, requiredSpecialties, requiredRegion, topK) {
        topK = topK || 10;
        return lawyerPool
            .map(function (l) {
                return { lawyer: l, score: computeMatchScore(l, requiredSpecialties, requiredRegion) };
            })
            .filter(function (x) {
                return x.score.total >= 0.4;
            })
            .sort(function (a, b) {
                return b.score.total - a.score.total;
            })
            .slice(0, topK);
    }

    // ========================================================================
    // 5. 工具: HTML escape + format
    // ========================================================================

    function esc(s) {
        if (s === null || s === undefined) return '';
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', '\'': '&#39;' }[c];
        });
    }

    function fmtMoney(n) {
        if (n === null || n === undefined) return '-';
        return '¥' + Number(n).toLocaleString('zh-CN', { maximumFractionDigits: 0 });
    }

    function fmtPercent(n) {
        if (n === null || n === undefined) return '-';
        return (Number(n) * 100).toFixed(1) + '%';
    }

    function fmtDate(s) {
        if (!s) return '-';
        try {
            var d = new Date(s);
            if (isNaN(d.getTime())) return s;
            var y = d.getFullYear();
            var m = String(d.getMonth() + 1).padStart(2, '0');
            var dd = String(d.getDate()).padStart(2, '0');
            var hh = String(d.getHours()).padStart(2, '0');
            var mi = String(d.getMinutes()).padStart(2, '0');
            return y + '-' + m + '-' + dd + ' ' + hh + ':' + mi;
        } catch (e) {
            return s;
        }
    }

    function findState(state) {
        for (var i = 0; i < CO_COUNSEL_STATES.length; i++) {
            if (CO_COUNSEL_STATES[i].value === state) return CO_COUNSEL_STATES[i];
        }
        return CO_COUNSEL_STATES[0];
    }

    function findReferralStatus(status) {
        for (var i = 0; i < REFERRAL_STATUSES.length; i++) {
            if (REFERRAL_STATUSES[i].value === status) return REFERRAL_STATUSES[i];
        }
        return REFERRAL_STATUSES[0];
    }

    function findDocType(value) {
        for (var i = 0; i < CROSS_BORDER_DOC_TYPES.length; i++) {
            if (CROSS_BORDER_DOC_TYPES[i].value === value) return CROSS_BORDER_DOC_TYPES[i];
        }
        return CROSS_BORDER_DOC_TYPES[0];
    }

    function findLanguage(value) {
        for (var i = 0; i < LANGUAGES.length; i++) {
            if (LANGUAGES[i].value === value) return LANGUAGES[i];
        }
        return LANGUAGES[0];
    }

    // ========================================================================
    // 6. 工具: toast (复用 script.js showToast 模式)
    // ========================================================================

    function toast(msg, type) {
        if (typeof window.showToast === 'function') {
            window.showToast(msg, type);
            return;
        }
        // 兜底
        var el = document.createElement('div');
        el.className =
            'fixed top-4 right-4 z-[9999] px-4 py-2 rounded shadow-lg text-sm text-white ' +
            (type === 'success'
                ? 'bg-success'
                : type === 'warning'
                    ? 'bg-warning'
                    : type === 'error'
                        ? 'bg-danger'
                        : 'bg-brand');
        el.textContent = msg;
        document.body.appendChild(el);
        setTimeout(function () {
            el.remove();
        }, 3000);
    }

    // ========================================================================
    // 7. 5 状态机步骤条渲染 (协同办案)
    // ========================================================================

    function renderStateStepBar(currentState) {
        var states = CO_COUNSEL_STATES.slice(0, 5); // 不含 archived 终态
        var currentIdx = -1;
        for (var i = 0; i < states.length; i++) {
            if (states[i].value === currentState) {
                currentIdx = i;
                break;
            }
        }

        var html = '<div class="flex items-center justify-between w-full">';
        for (var j = 0; j < states.length; j++) {
            var s = states[j];
            var dotCls = 'mp-state-step-dot';
            if (j < currentIdx) dotCls += ' done';
            else if (j === currentIdx) dotCls += ' active';

            html +=
                '<div class="mp-state-step">' +
                '<div class="flex flex-col items-center">' +
                '<div class="' +
                dotCls +
                '">' +
                (j < currentIdx ? '<iconify-icon icon="mdi:check" class="text-xs"></iconify-icon>' : j + 1) +
                '</div>' +
                '<div class="mp-state-step-label">' +
                s.label +
                '</div>' +
                '</div>';
            if (j < states.length - 1) {
                var lineCls = 'mp-state-step-line';
                if (j < currentIdx) lineCls += ' done';
                html += '<div class="' + lineCls + '" style="margin: 0 4px;"></div>';
            }
        }
        html += '</div>';
        return html;
    }

    // ========================================================================
    // 8. 5 维度评分条渲染
    // ========================================================================

    function renderDimBars(score) {
        var html = '<div class="space-y-1">';
        var dims = [
            { name: '专业', value: score.specialty, cls: 'mp-dim-specialty' },
            { name: '经验', value: score.experience, cls: 'mp-dim-experience' },
            { name: '地域', value: score.geography, cls: 'mp-dim-geography' },
            { name: '可接', value: score.availability, cls: 'mp-dim-availability' },
            { name: '评分', value: score.rating, cls: 'mp-dim-rating' }
        ];
        for (var i = 0; i < dims.length; i++) {
            var d = dims[i];
            var pct = Math.round((d.value || 0) * 100);
            html +=
                '<div class="mp-dim-row ' +
                d.cls +
                '">' +
                '<span class="mp-dim-name">' +
                d.name +
                '</span>' +
                '<div class="mp-dim-track"><div class="mp-dim-fill" style="width: ' +
                pct +
                '%;"></div></div>' +
                '<span class="mp-dim-val">' +
                pct +
                '</span>' +
                '</div>';
        }
        html += '</div>';
        return html;
    }

    // ========================================================================
    // 9. Demo 数据 fallback (后端未启动时 UI 仍可演示)
    // ========================================================================

    var DEMO_LAWYERS = [
        {
            lawyer_id: 'L001',
            name: '张律师',
            firm_id: 'F-中伦',
            specialties: ['contract_dispute', 'arbitration'],
            jurisdictions: ['CN'],
            languages: ['zh-CN', 'en-US'],
            region: '北京',
            experience_years: 12,
            rating: 4.8,
            completed_cases: 320,
            marketplace_active: true,
            cross_border_capable: true,
            availability: 'available',
            bio: '中伦律所合伙人, 12 年合同 + 国际仲裁经验'
        },
        {
            lawyer_id: 'L002',
            name: '李律师',
            firm_id: 'F-金杜',
            specialties: ['intellectual_property', 'tort'],
            jurisdictions: ['CN', 'US'],
            languages: ['zh-CN', 'en-US'],
            region: '上海',
            experience_years: 9,
            rating: 4.5,
            completed_cases: 180,
            marketplace_active: true,
            cross_border_capable: true,
            availability: 'available',
            bio: '金杜律所 IP 部门, 跨境侵权专家'
        },
        {
            lawyer_id: 'L003',
            name: '王律师',
            firm_id: 'F-君合',
            specialties: ['equity', 'corporate_governance'],
            jurisdictions: ['CN', 'HK'],
            languages: ['zh-CN', 'en-US'],
            region: '北京',
            experience_years: 15,
            rating: 4.9,
            completed_cases: 450,
            marketplace_active: true,
            cross_border_capable: false,
            availability: 'busy',
            bio: '君合律所, 公司股权与并购 15 年'
        },
        {
            lawyer_id: 'L004',
            name: '陈律师',
            firm_id: 'F-汉坤',
            specialties: ['labor_arbitration', 'administrative_review'],
            jurisdictions: ['CN'],
            languages: ['zh-CN'],
            region: '深圳',
            experience_years: 6,
            rating: 4.2,
            completed_cases: 90,
            marketplace_active: true,
            cross_border_capable: false,
            availability: 'available',
            bio: '汉坤律所, 劳动 + 行政双领域'
        },
        {
            lawyer_id: 'L005',
            name: '赵律师',
            firm_id: 'F-竞天公诚',
            specialties: ['family', 'tort'],
            jurisdictions: ['CN'],
            languages: ['zh-CN'],
            region: '广州',
            experience_years: 8,
            rating: 4.4,
            completed_cases: 150,
            marketplace_active: true,
            cross_border_capable: false,
            availability: 'available',
            bio: '家事 + 侵权 8 年'
        },
        {
            lawyer_id: 'L006',
            name: '吴律师',
            firm_id: 'F-海问',
            specialties: ['cross_border', 'arbitration', 'contract_dispute'],
            jurisdictions: ['CN', 'HK', 'SG', 'US', 'ICC', 'HKIAC', 'SIAC'],
            languages: ['zh-CN', 'en-US', 'bilingual'],
            region: '北京',
            experience_years: 18,
            rating: 5.0,
            completed_cases: 600,
            marketplace_active: true,
            cross_border_capable: true,
            availability: 'available',
            bio: '海问律所高级合伙人, 18 年跨境仲裁 (W15 d66fc33 L7 5 维评分 origin)'
        }
    ];

    var DEMO_CASES = [
        {
            case_id: 'cc-a1b2c3d4',
            lawyer_a_id: 'L001',
            lawyer_b_id: 'L002',
            firm_id: 'F-中伦',
            case_type: 'contract_dispute',
            case_description: '跨境合同纠纷, 标的 ¥500,000',
            required_specialties: ['contract_dispute'],
            deadline: '2026-04-15',
            fee: 50000,
            split_ratio: 0.6,
            marketplace_commission_rate: 0.1,
            state: 'in_progress',
            history: [
                { from: 'open', to: 'lawyer_invited', actor: 'L001', reason: '发起邀请', ts: '2026-03-01T10:00:00' },
                { from: 'lawyer_invited', to: 'accepted', actor: 'L002', reason: '接案', ts: '2026-03-02T14:00:00' },
                { from: 'accepted', to: 'in_progress', actor: 'L001', reason: '进入协同', ts: '2026-03-05T09:00:00' }
            ]
        },
        {
            case_id: 'cc-e5f6g7h8',
            lawyer_a_id: 'L006',
            lawyer_b_id: null,
            firm_id: 'F-海问',
            case_type: 'arbitration',
            case_description: 'ICC 仲裁案, 跨境股权争议',
            required_specialties: ['arbitration', 'cross_border'],
            deadline: '2026-05-30',
            fee: 200000,
            split_ratio: 0.5,
            marketplace_commission_rate: 0.1,
            state: 'lawyer_invited',
            history: [
                { from: 'open', to: 'lawyer_invited', actor: 'L006', reason: '招募律师 B', ts: '2026-03-10T11:00:00' }
            ]
        }
    ];

    var DEMO_REFERRALS = [
        {
            referral_id: 'ref-r001',
            referrer_id: 'L001',
            target_lawyer_id: 'L006',
            case_type: 'arbitration',
            case_description: '客户 ICC 仲裁案, 推荐给跨境专家吴律师',
            expected_fee: 200000,
            actual_fee: 200000,
            commission_rate: 0.05,
            referrer_commission: 10000,
            marketplace_commission: 0,
            match_score: 0.92,
            status: 'settled',
            created_at: '2026-02-15T10:00:00'
        },
        {
            referral_id: 'ref-r002',
            referrer_id: 'L002',
            target_lawyer_id: 'L003',
            case_type: 'equity',
            case_description: '客户股权纠纷, 推荐给王律师',
            expected_fee: 80000,
            actual_fee: null,
            commission_rate: 0.05,
            referrer_commission: null,
            marketplace_commission: 0,
            match_score: 0.85,
            status: 'accepted',
            created_at: '2026-03-08T15:00:00'
        },
        {
            referral_id: 'ref-r003',
            referrer_id: 'L004',
            target_lawyer_id: 'L001',
            case_type: 'contract_dispute',
            case_description: '合同纠纷, 推荐张律师',
            expected_fee: 50000,
            actual_fee: null,
            commission_rate: 0.05,
            referrer_commission: null,
            marketplace_commission: 0,
            match_score: 0.78,
            status: 'pending',
            created_at: '2026-03-12T09:00:00'
        }
    ];

    var DEMO_CROSS_BORDER_JOBS = [
        {
            job_id: 'cb-j001',
            lawyer_id: 'L006',
            client_id: 'client-us-001',
            doc_type: 'letter',
            language: 'en-US',
            jurisdiction: 'US',
            price: 199,
            marketplace_commission: 59.7,
            template_id: 'skill3-letter-v3-en',
            status: 'completed',
            fields: { recipient: 'ABC Corp', amount_usd: 50000 },
            document_url: '/marketplace/cb-j001/letter.pdf',
            arbitration_institution: null,
            created_at: '2026-03-05T10:00:00'
        },
        {
            job_id: 'cb-j002',
            lawyer_id: 'L001',
            client_id: 'client-hk-002',
            doc_type: 'arbitration_application',
            language: 'bilingual',
            jurisdiction: 'HKIAC',
            price: 1990,
            marketplace_commission: 597,
            template_id: 'skill3-arbitration-v3-bilingual',
            status: 'in_progress',
            fields: { parties: 'X Co. vs. Y Co.', amount_hkd: 5000000 },
            document_url: null,
            arbitration_institution: 'HKIAC',
            created_at: '2026-03-10T14:00:00'
        }
    ];

    var DEMO_METRICS = {
        metric_date: '2026-07-01',
        lawyer_participants: 6,
        cases_completed_monthly: 8,
        revenue_monthly: 235000,
        cross_border_orders_monthly: 12,
        avg_lawyer_rating: 4.63,
        referral_count_total: 3,
        co_counsel_count_total: 2,
        cross_border_count_total: 2,
        commission_pending: 1380,
        commission_settled: 10000,
        trajectory: {
            period_days: 30,
            lawyer_pool_size: 6,
            referral_count: 3,
            co_counsel_count: 2,
            cross_border_count: 2,
            commission_count: 2
        }
    };

    // ========================================================================
    // 9.5 匹配 2.0 - 后端 API 匹配 + 降级方案 + 解释可视化
    // ========================================================================

    var MatchV2State = {
        currentCriteria: {
            required_specialties: [],
            required_region: '',
            required_city: '',
            sort_by: 'match_score',
            sort_order: 'desc',
            filters: {},
            page: 1,
            page_size: 10
        },
        lastResults: null,
        lastExplanation: null,
        isLoading: false,
        useBackend: true,
        backoffCount: 0
    };

    var MatchAPI = {
        matchLawyers: function (criteria) {
            criteria = criteria || MatchV2State.currentCriteria;
            return API.marketplace.matchLawyers(criteria);
        },

        getMatchExplanation: function (lawyerId, criteria) {
            criteria = criteria || MatchV2State.currentCriteria;
            return API.marketplace.getMatchExplanation(lawyerId, criteria);
        },

        listLawyers: function (params) {
            return API.marketplace.listLawyers(params);
        }
    };

    function matchLawyersV2(criteria, opts) {
        opts = opts || {};
        var useBackend = opts.useBackend !== false && MatchV2State.useBackend;

        if (useBackend) {
            return MatchAPI.matchLawyers(criteria)
                .then(function (res) {
                    if (res.ok && res.data) {
                        MatchV2State.backoffCount = 0;
                        return { ok: true, data: res.data, source: 'backend' };
                    }
                    console.warn('[MatchV2] 后端匹配失败, 降级到前端:', res);
                    if (opts.fallback !== false) {
                        return matchLawyersFrontend(criteria);
                    }
                    return { ok: false, error: res.error || '匹配失败', status: res.status };
                })
                .catch(function (err) {
                    console.warn('[MatchV2] 后端匹配异常, 降级到前端:', err);
                    if (opts.fallback !== false) {
                        return matchLawyersFrontend(criteria);
                    }
                    return { ok: false, error: err.message || '网络错误' };
                });
        } else {
            return matchLawyersFrontend(criteria);
        }
    }

    function matchLawyersFrontend(criteria) {
        criteria = criteria || {};
        var requiredSpecialties = criteria.required_specialties || [];
        var requiredRegion = criteria.required_region || '';
        var sortBy = criteria.sort_by || 'match_score';
        var sortOrder = criteria.sort_order || 'desc';
        var filters = criteria.filters || {};
        var page = criteria.page || 1;
        var pageSize = criteria.page_size || 10;

        return new Promise(function (resolve) {
            loadLawyerPool(function (err, pool) {
                if (err) pool = DEMO_LAWYERS;

                var filtered = pool.slice();

                if (filters.specialties && filters.specialties.length > 0) {
                    filtered = filtered.filter(function (l) {
                        return l.specialties && filters.specialties.some(function (s) {
                            return l.specialties.indexOf(s) >= 0;
                        });
                    });
                }
                if (filters.min_experience_years !== undefined) {
                    filtered = filtered.filter(function (l) {
                        return (l.experience_years || 0) >= filters.min_experience_years;
                    });
                }
                if (filters.max_experience_years !== undefined) {
                    filtered = filtered.filter(function (l) {
                        return (l.experience_years || 0) <= filters.max_experience_years;
                    });
                }
                if (filters.regions && filters.regions.length > 0) {
                    filtered = filtered.filter(function (l) {
                        return l.region && filters.regions.indexOf(l.region) >= 0;
                    });
                }
                if (filters.cities && filters.cities.length > 0) {
                    filtered = filtered.filter(function (l) {
                        return l.city && filters.cities.indexOf(l.city) >= 0;
                    });
                }
                if (filters.min_price !== undefined) {
                    filtered = filtered.filter(function (l) {
                        return (l.price_per_hour || 0) >= filters.min_price;
                    });
                }
                if (filters.max_price !== undefined) {
                    filtered = filtered.filter(function (l) {
                        return (l.price_per_hour || 0) <= filters.max_price;
                    });
                }
                if (filters.min_rating !== undefined) {
                    filtered = filtered.filter(function (l) {
                        return (l.rating || 0) >= filters.min_rating;
                    });
                }
                if (filters.cross_border_only) {
                    filtered = filtered.filter(function (l) {
                        return l.cross_border_capable;
                    });
                }
                if (filters.availability && filters.availability.length > 0) {
                    filtered = filtered.filter(function (l) {
                        return l.availability && filters.availability.indexOf(l.availability) >= 0;
                    });
                }

                var scored = rankLawyers(filtered, requiredSpecialties, requiredRegion, filtered.length);

                scored.sort(function (a, b) {
                    var av, bv;
                    switch (sortBy) {
                    case 'price':
                        av = a.lawyer.price_per_hour || 0;
                        bv = b.lawyer.price_per_hour || 0;
                        break;
                    case 'experience':
                        av = a.lawyer.experience_years || 0;
                        bv = b.lawyer.experience_years || 0;
                        break;
                    case 'rating':
                        av = a.lawyer.rating || 0;
                        bv = b.lawyer.rating || 0;
                        break;
                    case 'response_speed':
                        av = -(a.lawyer.response_speed_hours || 24);
                        bv = -(b.lawyer.response_speed_hours || 24);
                        break;
                    case 'match_score':
                    default:
                        av = a.score.total;
                        bv = b.score.total;
                    }
                    return sortOrder === 'asc' ? av - bv : bv - av;
                });

                var total = scored.length;
                var start = (page - 1) * pageSize;
                var end = start + pageSize;
                var paged = scored.slice(start, end);

                var lawyers = paged.map(function (item) {
                    var l = item.lawyer;
                    var s = item.score;
                    return {
                        lawyer_id: l.lawyer_id,
                        name: l.name,
                        firm_id: l.firm_id,
                        specialties: l.specialties || [],
                        jurisdictions: l.jurisdictions || [],
                        languages: l.languages || [],
                        region: l.region || '',
                        city: l.city || '',
                        experience_years: l.experience_years || 0,
                        rating: l.rating || 0,
                        client_review_count: l.client_review_count || 0,
                        completed_cases: l.completed_cases || 0,
                        win_rate: l.win_rate || 0,
                        response_speed_hours: l.response_speed_hours || 24,
                        price_per_hour: l.price_per_hour || 0,
                        price_min: l.price_min || 0,
                        marketplace_active: l.marketplace_active !== false,
                        cross_border_capable: l.cross_border_capable || false,
                        availability: l.availability || 'available',
                        bio: l.bio || '',
                        match_score: {
                            total_score: s.total,
                            specialty: s.specialty,
                            experience: s.experience,
                            geography: s.geography,
                            availability: s.availability,
                            rating: s.rating,
                            cross_border_bonus: s.cross_border_bonus || 0
                        },
                        match_reasons: buildMatchReasons(l, s, requiredSpecialties, requiredRegion)
                    };
                });

                resolve({
                    ok: true,
                    source: 'frontend',
                    data: {
                        lawyers: lawyers,
                        total: total,
                        page: page,
                        page_size: pageSize,
                        total_pages: Math.ceil(total / pageSize)
                    }
                });
            });
        });
    }

    function buildMatchReasons(lawyer, score, requiredSpecialties, requiredRegion) {
        var reasons = [];
        if (score.specialty >= 0.8 && requiredSpecialties.length > 0) {
            reasons.push('专业领域高度匹配');
        } else if (score.specialty >= 0.5 && requiredSpecialties.length > 0) {
            reasons.push('专业领域部分匹配');
        }
        if (score.experience >= 0.8) {
            reasons.push('经验丰富');
        }
        if (score.geography >= 0.8) {
            reasons.push('同城/同省');
        }
        if (score.availability >= 0.8) {
            reasons.push('可立即接案');
        }
        if (score.rating >= 0.9) {
            reasons.push('客户好评如潮');
        }
        if (lawyer.cross_border_capable) {
            reasons.push('支持跨境业务');
        }
        return reasons;
    }

    function getMatchExplanationV2(lawyerId, criteria) {
        criteria = criteria || MatchV2State.currentCriteria;

        if (MatchV2State.useBackend) {
            return MatchAPI.getMatchExplanation(lawyerId, criteria)
                .then(function (res) {
                    if (res.ok && res.data) {
                        return { ok: true, data: res.data, source: 'backend' };
                    }
                    console.warn('[MatchV2] 后端解释失败, 降级到前端:', res);
                    return getMatchExplanationFrontend(lawyerId, criteria);
                })
                .catch(function (err) {
                    console.warn('[MatchV2] 后端解释异常, 降级到前端:', err);
                    return getMatchExplanationFrontend(lawyerId, criteria);
                });
        } else {
            return getMatchExplanationFrontend(lawyerId, criteria);
        }
    }

    function getMatchExplanationFrontend(lawyerId, criteria) {
        criteria = criteria || {};
        var requiredSpecialties = criteria.required_specialties || [];
        var requiredRegion = criteria.required_region || '';

        return new Promise(function (resolve) {
            loadLawyerPool(function (err, pool) {
                if (err) pool = DEMO_LAWYERS;
                var lawyer = pool.find(function (l) { return l.lawyer_id === lawyerId; });
                if (!lawyer) {
                    resolve({ ok: false, error: '律师不存在' });
                    return;
                }

                var score = computeMatchScore(lawyer, requiredSpecialties, requiredRegion);

                var dims = [
                    { name: '专业匹配', key: 'specialty', weight: 0.35, desc: '专业领域契合度' },
                    { name: '经验资历', key: 'experience', weight: 0.20, desc: '执业年限与办案量' },
                    { name: '地域匹配', key: 'geography', weight: 0.15, desc: '所在地区契合度' },
                    { name: '可接案状态', key: 'availability', weight: 0.15, desc: '当前接案能力' },
                    { name: '客户评分', key: 'rating', weight: 0.15, desc: '历史客户评价' }
                ];

                var dimensions = dims.map(function (d) {
                    var s = score[d.key] || 0;
                    var weighted = s * d.weight;
                    var isStrength = s >= 0.8;
                    var isWeakness = s < 0.5;
                    var description = d.desc + ': ' + (s * 100).toFixed(0) + '分';
                    if (d.key === 'specialty' && requiredSpecialties.length > 0) {
                        var matched = requiredSpecialties.filter(function (sp) {
                            return lawyer.specialties && lawyer.specialties.indexOf(sp) >= 0;
                        });
                        description = '匹配 ' + matched.length + '/' + requiredSpecialties.length + ' 个专业领域';
                    }
                    if (d.key === 'geography') {
                        if (s >= 1) description = '同城律师, 沟通便利';
                        else if (s >= 0.6) description = '同省律师';
                        else description = '异地律师';
                    }
                    if (d.key === 'availability') {
                        if (s >= 1) description = '可立即接案';
                        else if (s >= 0.4) description = '案件较多, 需排队';
                        else description = '暂不可用';
                    }
                    return {
                        name: d.name,
                        score: s,
                        weight: d.weight,
                        weighted_score: weighted,
                        description: description,
                        is_strength: isStrength,
                        is_weakness: isWeakness
                    };
                });

                var strengths = [];
                var weaknesses = [];
                var suggestions = [];

                dimensions.forEach(function (d) {
                    if (d.is_strength) strengths.push(d.name + '表现优秀');
                    if (d.is_weakness) weaknesses.push(d.name + '待提升');
                });

                if (score.specialty < 0.5 && requiredSpecialties.length > 0) {
                    suggestions.push('该律师专业领域与需求有差距, 可考虑其他更匹配的律师');
                }
                if (score.geography < 0.5) {
                    suggestions.push('异地律师可能增加沟通成本, 可优先考虑本地律师');
                }
                if (score.availability < 0.5) {
                    suggestions.push('该律师当前案件较多, 响应可能较慢');
                }
                if (lawyer.cross_border_capable && criteria.cross_border) {
                    strengths.push('具备跨境业务能力');
                }
                if (suggestions.length === 0) {
                    suggestions.push('综合表现良好, 可优先考虑');
                }

                resolve({
                    ok: true,
                    source: 'frontend',
                    data: {
                        lawyer_id: lawyer.lawyer_id,
                        lawyer_name: lawyer.name,
                        total_score: score.total,
                        dimensions: dimensions,
                        strengths: strengths,
                        weaknesses: weaknesses,
                        suggestions: suggestions
                    }
                });
            });
        });
    }

    function renderMatchSkeleton(count) {
        count = count || 3;
        var html = '';
        for (var i = 0; i < count; i++) {
            html +=
                '<div class="mp-lawyer-card bg-white rounded-lg p-4 mb-3">' +
                '<div class="flex items-start gap-3">' +
                '<div class="w-12 h-12 rounded-full bg-bg-subtle animate-pulse flex-shrink-0"></div>' +
                '<div class="flex-1 space-y-2">' +
                '<div class="h-4 bg-bg-subtle rounded animate-pulse w-1/3"></div>' +
                '<div class="h-3 bg-bg-subtle rounded animate-pulse w-1/2"></div>' +
                '<div class="h-3 bg-bg-subtle rounded animate-pulse w-full"></div>' +
                '<div class="h-3 bg-bg-subtle rounded animate-pulse w-2/3"></div>' +
                '</div>' +
                '<div class="text-right flex-shrink-0 space-y-2">' +
                '<div class="h-6 bg-bg-subtle rounded animate-pulse w-16"></div>' +
                '<div class="h-3 bg-bg-subtle rounded animate-pulse w-12"></div>' +
                '</div>' +
                '</div>' +
                '</div>';
        }
        return html;
    }

    function renderMatchResultCard(lawyer, index) {
        var matchScore = lawyer.match_score || {};
        var totalScore = matchScore.total_score !== undefined ? matchScore.total_score : 0;
        var scorePct = Math.round(totalScore * 100);
        var availability = AVAILABILITY.find(function (a) { return a.value === lawyer.availability; }) || AVAILABILITY[0];

        var scoreBadge = '';
        if (totalScore >= 0.85) {
            scoreBadge = '<span class="mp-badge-strong text-[10px] px-1.5 py-0.5 rounded block mb-1">强推荐</span>';
        } else if (totalScore >= 0.65) {
            scoreBadge = '<span class="mp-badge-recommend text-[10px] px-1.5 py-0.5 rounded block mb-1">推荐</span>';
        } else if (totalScore >= 0.45) {
            scoreBadge = '<span class="text-[10px] px-1.5 py-0.5 rounded block mb-1 bg-bg-subtle text-fg-secondary">候选</span>';
        }

        var reasonTags = '';
        if (lawyer.match_reasons && lawyer.match_reasons.length > 0) {
            reasonTags = lawyer.match_reasons.slice(0, 3).map(function (r) {
                return '<span class="text-[10px] px-1.5 py-0.5 rounded bg-brand-tint text-brand">' + esc(r) + '</span>';
            }).join('');
        }

        return (
            '<div class="mp-lawyer-card mp-fade-in bg-white rounded-lg p-4 mb-3 hover:shadow-md transition-shadow" data-lawyer-id="' +
            esc(lawyer.lawyer_id) +
            '" style="animation-delay:' + (index * 50) + 'ms">' +
            '<div class="flex items-start gap-3">' +
            '<div class="w-12 h-12 rounded-full bg-gradient-to-br from-brand to-wiki flex items-center justify-center text-white text-base font-semibold flex-shrink-0 cursor-pointer" onclick="MarketplaceFn.openLawyerDetail(\'' + esc(lawyer.lawyer_id) + '\')">' +
            esc(lawyer.name ? lawyer.name.substring(0, 1) : '?') +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-center gap-2 flex-wrap mb-1">' +
            '<h3 class="text-sm font-semibold text-fg-primary truncate cursor-pointer hover:text-brand transition-colors" onclick="MarketplaceFn.openLawyerDetail(\'' + esc(lawyer.lawyer_id) + '\')">' +
            esc(lawyer.name) +
            '</h3>' +
            '<span class="text-[11px] text-fg-tertiary">' + esc(lawyer.firm_id || '独立律师') + '</span>' +
            (lawyer.cross_border_capable ? '<span class="mp-badge-recommend text-[10px] px-1.5 py-0.5 rounded">跨境</span>' : '') +
            '</div>' +
            '<div class="flex flex-wrap gap-1 mb-2">' +
            (lawyer.specialties || []).slice(0, 4).map(function (s) {
                var t = CASE_TYPES.find(function (c) { return c.value === s; });
                return '<span class="text-[10px] px-1.5 py-0.5 rounded bg-bg-subtle text-fg-secondary">' + esc(t ? t.label : s) + '</span>';
            }).join('') +
            '</div>' +
            '<div class="flex items-center gap-3 text-[11px] text-fg-tertiary mb-2">' +
            '<span><iconify-icon icon="mdi:map-marker-outline" class="text-xs"></iconify-icon> ' + esc(lawyer.region || '未填') + (lawyer.city ? ' · ' + esc(lawyer.city) : '') + '</span>' +
            '<span><iconify-icon icon="mdi:briefcase-outline" class="text-xs"></iconify-icon> ' + (lawyer.experience_years || 0) + ' 年</span>' +
            '<span><iconify-icon icon="mdi:star" class="text-xs text-urgent"></iconify-icon> ' + (lawyer.rating || 0).toFixed(1) + '</span>' +
            '<span class="flex items-center gap-1"><span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:' + availability.dot + '"></span> ' + availability.label + '</span>' +
            (lawyer.price_per_hour > 0 ? '<span><iconify-icon icon="mdi:cash" class="text-xs"></iconify-icon> ¥' + lawyer.price_per_hour + '/h</span>' : '') +
            '</div>' +
            (reasonTags ? '<div class="flex flex-wrap gap-1 mb-2">' + reasonTags + '</div>' : '') +
            '</div>' +
            '<div class="text-right flex-shrink-0">' +
            '<div class="mp-score-big text-2xl font-bold text-brand">' + scorePct + '</div>' +
            '<div class="text-[10px] text-fg-tertiary mb-2">匹配度</div>' +
            scoreBadge +
            '<button class="mp-btn mp-btn-primary mp-btn-sm w-full" onclick="MarketplaceFn.openMatchDetail(\'' + esc(lawyer.lawyer_id) + '\')">' +
            '<iconify-icon icon="mdi:chart-bar" class="text-xs"></iconify-icon> 匹配详情' +
            '</button>' +
            '<div class="flex gap-1 mt-1">' +
            '<button class="mp-btn mp-btn-secondary mp-btn-sm flex-1" data-mp-action="create-referral" data-lawyer-id="' + esc(lawyer.lawyer_id) + '">' +
            '<iconify-icon icon="mdi:share-variant" class="text-xs"></iconify-icon>' +
            '</button>' +
            '<button class="mp-btn mp-btn-secondary mp-btn-sm flex-1" data-mp-action="invite-co-counsel" data-lawyer-id="' + esc(lawyer.lawyer_id) + '">' +
            '<iconify-icon icon="mdi:account-multiple-plus-outline" class="text-xs"></iconify-icon>' +
            '</button>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>'
        );
    }

    function renderMatchRadarChart(dimensions) {
        var size = 200;
        var center = size / 2;
        var radius = size / 2 - 30;
        var n = dimensions.length;
        if (n < 3) return '<div class="text-center text-fg-tertiary">维度不足</div>';

        var angleStep = (Math.PI * 2) / n;
        var startAngle = -Math.PI / 2;

        var gridLines = '';
        for (var level = 1; level <= 4; level++) {
            var r = (radius * level) / 4;
            var points = [];
            for (var i = 0; i < n; i++) {
                var angle = startAngle + i * angleStep;
                var x = center + r * Math.cos(angle);
                var y = center + r * Math.sin(angle);
                points.push(x.toFixed(1) + ',' + y.toFixed(1));
            }
            gridLines += '<polygon points="' + points.join(' ') + '" fill="none" stroke="#e5e7eb" stroke-width="1"/>';
        }

        var axisLines = '';
        var labels = '';
        for (var j = 0; j < n; j++) {
            var angle2 = startAngle + j * angleStep;
            var x2 = center + radius * Math.cos(angle2);
            var y2 = center + radius * Math.sin(angle2);
            axisLines += '<line x1="' + center + '" y1="' + center + '" x2="' + x2.toFixed(1) + '" y2="' + y2.toFixed(1) + '" stroke="#e5e7eb" stroke-width="1"/>';

            var labelR = radius + 18;
            var lx = center + labelR * Math.cos(angle2);
            var ly = center + labelR * Math.sin(angle2);
            labels += '<text x="' + lx.toFixed(1) + '" y="' + ly.toFixed(1) + '" text-anchor="middle" dominant-baseline="middle" fill="#6b7280" font-size="11px">' + esc(dimensions[j].name) + '</text>';
        }

        var dataPoints = [];
        for (var k = 0; k < n; k++) {
            var angle3 = startAngle + k * angleStep;
            var score3 = Math.max(0, Math.min(1, dimensions[k].score || 0));
            var r3 = radius * score3;
            var dx = center + r3 * Math.cos(angle3);
            var dy = center + r3 * Math.sin(angle3);
            dataPoints.push(dx.toFixed(1) + ',' + dy.toFixed(1));
        }

        return (
            '<svg viewBox="0 0 ' + size + ' ' + size + '" class="w-full max-w-[200px] mx-auto">' +
            gridLines +
            axisLines +
            '<polygon points="' + dataPoints.join(' ') + '" fill="rgba(59, 130, 246, 0.2)" stroke="#3b82f6" stroke-width="2"/>' +
            dataPoints.map(function (p) {
                var coords = p.split(',');
                return '<circle cx="' + coords[0] + '" cy="' + coords[1] + '" r="3" fill="#3b82f6"/>';
            }).join('') +
            labels +
            '</svg>'
        );
    }

    function renderMatchDimensionBars(dimensions) {
        var html = '<div class="space-y-3">';
        dimensions.forEach(function (d) {
            var pct = Math.round((d.score || 0) * 100);
            var barColor = d.is_strength ? 'linear-gradient(90deg, #10b981, #059669)'
                : d.is_weakness ? 'linear-gradient(90deg, #f59e0b, #ef4444)'
                    : 'linear-gradient(90deg, #3b82f6, #6366f1)';
            var labelClass = d.is_strength ? 'text-success' : d.is_weakness ? 'text-warning' : 'text-fg-secondary';

            html +=
                '<div class="match-dim-row">' +
                '<div class="flex justify-between items-center mb-1">' +
                '<span class="text-xs font-medium ' + labelClass + '">' + esc(d.name) + '</span>' +
                '<span class="text-xs font-semibold text-fg-primary">' + pct + '分</span>' +
                '</div>' +
                '<div class="match-dim-track h-2 bg-bg-subtle rounded-full overflow-hidden">' +
                '<div class="match-dim-fill h-full rounded-full transition-all duration-500" style="width:' + pct + '%;background:' + barColor + '"></div>' +
                '</div>' +
                '<div class="text-[10px] text-fg-tertiary mt-1">' + esc(d.description) + '</div>' +
                '</div>';
        });
        html += '</div>';
        return html;
    }

    function renderMatchDetailModal(explanation) {
        var data = explanation.data || explanation;
        var totalPct = Math.round((data.total_score || 0) * 100);

        var strengthTags = '';
        if (data.strengths && data.strengths.length > 0) {
            strengthTags = data.strengths.map(function (s) {
                return '<span class="inline-block text-xs px-2 py-1 rounded-full bg-success/10 text-success mr-2 mb-1">✓ ' + esc(s) + '</span>';
            }).join('');
        }

        var weaknessTags = '';
        if (data.weaknesses && data.weaknesses.length > 0) {
            weaknessTags = data.weaknesses.map(function (w) {
                return '<span class="inline-block text-xs px-2 py-1 rounded-full bg-warning/10 text-warning mr-2 mb-1">⚠ ' + esc(w) + '</span>';
            }).join('');
        }

        var suggestionsHtml = '';
        if (data.suggestions && data.suggestions.length > 0) {
            suggestionsHtml = '<ul class="list-disc list-inside space-y-1 text-xs text-fg-secondary">';
            data.suggestions.forEach(function (s) {
                suggestionsHtml += '<li>' + esc(s) + '</li>';
            });
            suggestionsHtml += '</ul>';
        }

        return (
            '<div id="mp-match-detail-modal" class="fixed inset-0 z-[1000] flex items-center justify-center p-4" onclick="if(event.target===this)MarketplaceFn.closeMatchDetail()">' +
            '<div class="bg-white rounded-xl w-full max-w-lg max-h-[85vh] overflow-hidden shadow-2xl mp-fade-in">' +
            '<div class="flex items-center justify-between p-4 border-b border-bg-border">' +
            '<div class="flex items-center gap-3">' +
            '<div class="w-10 h-10 rounded-full bg-gradient-to-br from-brand to-wiki flex items-center justify-center text-white font-semibold">' +
            esc(data.lawyer_name ? data.lawyer_name.substring(0, 1) : '?') +
            '</div>' +
            '<div>' +
            '<h3 class="text-base font-semibold text-fg-primary">' + esc(data.lawyer_name) + ' · 匹配详情</h3>' +
            '<p class="text-xs text-fg-tertiary">综合匹配度: <span class="text-brand font-semibold">' + totalPct + '分</span></p>' +
            '</div>' +
            '</div>' +
            '<button class="text-fg-tertiary hover:text-fg-primary transition-colors text-xl" onclick="MarketplaceFn.closeMatchDetail()">×</button>' +
            '</div>' +
            '<div class="overflow-y-auto p-4" style="max-height: calc(85vh - 60px);">' +
            '<div class="mb-4">' +
            '<h4 class="text-sm font-semibold text-fg-primary mb-3">综合评估</h4>' +
            renderMatchRadarChart(data.dimensions || []) +
            '</div>' +
            '<div class="mb-4">' +
            '<h4 class="text-sm font-semibold text-fg-primary mb-3">各维度得分</h4>' +
            renderMatchDimensionBars(data.dimensions || []) +
            '</div>' +
            (strengthTags || weaknessTags ?
                '<div class="mb-4">' +
                '<h4 class="text-sm font-semibold text-fg-primary mb-2">优劣势分析</h4>' +
                (strengthTags ? '<div class="mb-2"><div class="text-xs text-success font-medium mb-1">强项</div>' + strengthTags + '</div>' : '') +
                (weaknessTags ? '<div><div class="text-xs text-warning font-medium mb-1">待提升</div>' + weaknessTags + '</div>' : '') +
                '</div>' : '') +
            (suggestionsHtml ?
                '<div>' +
                '<h4 class="text-sm font-semibold text-fg-primary mb-2">改进建议</h4>' +
                '<div class="bg-bg-subtle rounded-lg p-3">' + suggestionsHtml + '</div>' +
                '</div>' : '') +
            '<div class="mt-4 pt-4 border-t border-bg-border flex gap-2">' +
            '<button class="mp-btn mp-btn-secondary flex-1" onclick="MarketplaceFn.closeMatchDetail()">关闭</button>' +
            '<button class="mp-btn mp-btn-primary flex-1" onclick="MarketplaceFn.openLawyerDetail(\'' + esc(data.lawyer_id) + '\');MarketplaceFn.closeMatchDetail();">查看完整资料</button>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>'
        );
    }

    function openMatchDetail(lawyerId) {
        var criteria = MatchV2State.currentCriteria;
        var modalContainer = document.getElementById('mp-match-detail-container');
        if (!modalContainer) {
            modalContainer = document.createElement('div');
            modalContainer.id = 'mp-match-detail-container';
            document.body.appendChild(modalContainer);
        }

        modalContainer.innerHTML = renderMatchSkeleton(1);

        getMatchExplanationV2(lawyerId, criteria).then(function (result) {
            if (result.ok) {
                modalContainer.innerHTML = renderMatchDetailModal(result.data);
            } else {
                modalContainer.innerHTML =
                    '<div class="fixed inset-0 z-[1000] flex items-center justify-center p-4" onclick="if(event.target===this)MarketplaceFn.closeMatchDetail()">' +
                    '<div class="bg-white rounded-xl p-6 max-w-sm text-center">' +
                    '<p class="text-fg-secondary mb-4">加载匹配详情失败</p>' +
                    '<button class="mp-btn mp-btn-primary" onclick="MarketplaceFn.closeMatchDetail()">关闭</button>' +
                    '</div>' +
                    '</div>';
            }
        });
    }

    function closeMatchDetail() {
        var modalContainer = document.getElementById('mp-match-detail-container');
        if (modalContainer) {
            modalContainer.innerHTML = '';
        }
    }

    function renderMatchFilters(criteria) {
        criteria = criteria || MatchV2State.currentCriteria;
        var sortOptions = [
            { value: 'match_score', label: '综合匹配' },
            { value: 'price', label: '价格' },
            { value: 'experience', label: '经验' },
            { value: 'rating', label: '评分' },
            { value: 'response_speed', label: '响应速度' }
        ];

        var specialtyOptions = CASE_TYPES.slice(0, 9).map(function (c) {
            return { value: c.value, label: c.label };
        });

        var regionOptions = ['北京', '上海', '深圳', '广州', '杭州', '成都'].map(function (r) {
            return { value: r, label: r };
        });

        var html =
            '<div class="mp-match-filters bg-white rounded-lg p-4 mb-4 border border-bg-border">' +
            '<div class="flex flex-wrap gap-3 items-end">' +
            '<div class="flex-1 min-w-[200px]">' +
            '<label class="mp-label">专业领域</label>' +
            '<select id="mp-filter-specialty" class="mp-input text-sm">' +
            '<option value="">全部领域</option>' +
            specialtyOptions.map(function (opt) {
                var selected = (criteria.required_specialties || []).indexOf(opt.value) >= 0 ? ' selected' : '';
                return '<option value="' + esc(opt.value) + '"' + selected + '>' + esc(opt.label) + '</option>';
            }).join('') +
            '</select>' +
            '</div>' +
            '<div class="flex-1 min-w-[150px]">' +
            '<label class="mp-label">地区</label>' +
            '<select id="mp-filter-region" class="mp-input text-sm">' +
            '<option value="">全部地区</option>' +
            regionOptions.map(function (opt) {
                var selected = criteria.required_region === opt.value ? ' selected' : '';
                return '<option value="' + esc(opt.value) + '"' + selected + '>' + esc(opt.label) + '</option>';
            }).join('') +
            '</select>' +
            '</div>' +
            '<div class="flex-1 min-w-[120px]">' +
            '<label class="mp-label">排序方式</label>' +
            '<select id="mp-filter-sort" class="mp-input text-sm">' +
            sortOptions.map(function (opt) {
                var selected = criteria.sort_by === opt.value ? ' selected' : '';
                return '<option value="' + esc(opt.value) + '"' + selected + '>' + esc(opt.label) + '</option>';
            }).join('') +
            '</select>' +
            '</div>' +
            '<div class="w-24">' +
            '<label class="mp-label">最低分</label>' +
            '<input id="mp-filter-minrating" type="number" step="0.5" min="0" max="5" class="mp-input text-sm" placeholder="评分" value="' + ((criteria.filters && criteria.filters.min_rating) || '') + '">' +
            '</div>' +
            '<div class="w-24">' +
            '<label class="mp-label">最低年限</label>' +
            '<input id="mp-filter-minexperience" type="number" min="0" class="mp-input text-sm" placeholder="年限" value="' + ((criteria.filters && criteria.filters.min_experience_years) || '') + '">' +
            '</div>' +
            '<button id="mp-filter-submit" class="mp-btn mp-btn-primary text-sm">' +
            '<iconify-icon icon="mdi:magnify" class="text-sm"></iconify-icon> 筛选' +
            '</button>' +
            '</div>' +
            '<div class="mt-3 flex items-center gap-2 text-xs text-fg-tertiary flex-wrap">' +
            '<label class="flex items-center gap-1 cursor-pointer">' +
            '<input type="checkbox" id="mp-filter-crossborder" class="rounded" ' + ((criteria.filters && criteria.filters.cross_border_only) ? 'checked' : '') + '>' +
            '仅跨境律师' +
            '</label>' +
            '<span class="text-bg-border">|</span>' +
            '<span id="mp-match-source" class="text-fg-tertiary">数据源: ' + (MatchV2State.useBackend ? '<span class="text-success">后端</span>' : '<span class="text-warning">前端降级</span>') + '</span>' +
            '<span class="text-bg-border">|</span>' +
            '<span id="mp-match-count" class="text-fg-tertiary">共 0 位律师</span>' +
            '</div>' +
            '</div>';
        return html;
    }

    function bindMatchFilters(root, onSearch) {
        var submitBtn = root.querySelector('#mp-filter-submit');
        if (submitBtn) {
            submitBtn.addEventListener('click', function () {
                var specialty = root.querySelector('#mp-filter-specialty').value;
                var region = root.querySelector('#mp-filter-region').value;
                var sortBy = root.querySelector('#mp-filter-sort').value;
                var minRating = parseFloat(root.querySelector('#mp-filter-minrating').value);
                var minExp = parseInt(root.querySelector('#mp-filter-minexperience').value);
                var crossBorder = root.querySelector('#mp-filter-crossborder').checked;

                var criteria = {
                    required_specialties: specialty ? [specialty] : [],
                    required_region: region,
                    sort_by: sortBy,
                    filters: {},
                    page: 1,
                    page_size: MatchV2State.currentCriteria.page_size || 10
                };
                if (!isNaN(minRating)) criteria.filters.min_rating = minRating;
                if (!isNaN(minExp)) criteria.filters.min_experience_years = minExp;
                if (crossBorder) criteria.filters.cross_border_only = true;

                MatchV2State.currentCriteria = Object.assign({}, MatchV2State.currentCriteria, criteria);
                if (typeof onSearch === 'function') onSearch(criteria);
            });
        }

        ['mp-filter-specialty', 'mp-filter-region', 'mp-filter-sort'].forEach(function (id) {
            var el = root.querySelector('#' + id);
            if (el) {
                el.addEventListener('change', function () {
                    var btn = root.querySelector('#mp-filter-submit');
                    if (btn) btn.click();
                });
            }
        });
    }

    function renderMatchResults(container, criteria, opts) {
        opts = opts || {};
        var showFilters = opts.showFilters !== false;

        if (showFilters) {
            container.innerHTML = renderMatchFilters(criteria) +
                '<div id="mp-match-results-list"></div>' +
                '<div id="mp-match-pagination" class="mt-4 text-center"></div>';
        } else {
            container.innerHTML = '<div id="mp-match-results-list"></div>';
        }

        var listEl = container.querySelector('#mp-match-results-list');
        listEl.innerHTML = renderMatchSkeleton(3);

        var resultsList = listEl;
        var paginationEl = container.querySelector('#mp-match-pagination');

        bindMatchFilters(container, function (newCriteria) {
            resultsList.innerHTML = renderMatchSkeleton(3);
            doMatchSearch(newCriteria, resultsList, paginationEl);
        });

        doMatchSearch(criteria, resultsList, paginationEl);
    }

    function doMatchSearch(criteria, resultsList, paginationEl) {
        matchLawyersV2(criteria).then(function (result) {
            if (!result.ok) {
                resultsList.innerHTML =
                    '<div class="mp-empty">' +
                    '<iconify-icon icon="mdi:alert-outline" class="mp-empty-icon text-warning"></iconify-icon>' +
                    '<div>匹配失败</div>' +
                    '<div class="text-[11px] mt-1 text-fg-tertiary">' + esc(result.error || '请稍后重试') + '</div>' +
                    '<button class="mp-btn mp-btn-primary mt-3" onclick="MarketplaceFn.retryMatchSearch()">重试</button>' +
                    '</div>';
                return;
            }

            var data = result.data;
            MatchV2State.lastResults = data;

            var sourceEl = document.getElementById('mp-match-source');
            if (sourceEl) {
                sourceEl.innerHTML = '数据源: ' + (result.source === 'backend' ? '<span class="text-success">后端</span>' : '<span class="text-warning">前端降级</span>');
            }

            var countEl = document.getElementById('mp-match-count');
            if (countEl) {
                countEl.textContent = '共 ' + (data.total || 0) + ' 位律师';
            }

            if (!data.lawyers || data.lawyers.length === 0) {
                resultsList.innerHTML =
                    '<div class="mp-empty">' +
                    '<iconify-icon icon="mdi:account-search-outline" class="mp-empty-icon"></iconify-icon>' +
                    '<div>暂无匹配的律师</div>' +
                    '<div class="text-[11px] mt-1 text-fg-tertiary">试试调整筛选条件</div>' +
                    '</div>';
                if (paginationEl) paginationEl.innerHTML = '';
                return;
            }

            resultsList.innerHTML = data.lawyers.map(function (l, i) {
                return renderMatchResultCard(l, i);
            }).join('');

            resultsList.querySelectorAll('[data-mp-action]').forEach(function (btn) {
                btn.addEventListener('click', function (e) {
                    e.stopPropagation();
                    var action = btn.getAttribute('data-mp-action');
                    var lawyerId = btn.getAttribute('data-lawyer-id');
                    if (action === 'create-referral') {
                        if (typeof window.switchView === 'function') {
                            window.switchView('marketplace-referrals');
                            setTimeout(function () { openCreateReferralModal(lawyerId); }, 100);
                        }
                    } else if (action === 'invite-co-counsel') {
                        if (typeof window.switchView === 'function') {
                            window.switchView('marketplace-cases');
                            setTimeout(function () { openCreateCaseModal(lawyerId); }, 100);
                        }
                    }
                });
            });

            if (paginationEl && data.total_pages > 1) {
                var page = data.page || 1;
                var totalPages = data.total_pages;
                var paginationHtml = '<div class="inline-flex items-center gap-1">';

                paginationHtml += '<button class="mp-btn mp-btn-secondary mp-btn-sm" onclick="MarketplaceFn.goToMatchPage(' + (page - 1) + ')" ' + (page <= 1 ? 'disabled style="opacity:0.5"' : '') + '>' +
                    '<iconify-icon icon="mdi:chevron-left" class="text-sm"></iconify-icon></button>';

                var startPage = Math.max(1, page - 2);
                var endPage = Math.min(totalPages, page + 2);
                for (var p = startPage; p <= endPage; p++) {
                    var btnClass = p === page ? 'mp-btn-primary' : 'mp-btn-secondary';
                    paginationHtml += '<button class="mp-btn ' + btnClass + ' mp-btn-sm" onclick="MarketplaceFn.goToMatchPage(' + p + ')">' + p + '</button>';
                }

                paginationHtml += '<button class="mp-btn mp-btn-secondary mp-btn-sm" onclick="MarketplaceFn.goToMatchPage(' + (page + 1) + ')" ' + (page >= totalPages ? 'disabled style="opacity:0.5"' : '') + '>' +
                    '<iconify-icon icon="mdi:chevron-right" class="text-sm"></iconify-icon></button>';

                paginationHtml += '</div>';
                paginationEl.innerHTML = paginationHtml;
            } else if (paginationEl) {
                paginationEl.innerHTML = '';
            }
        });
    }

    function retryMatchSearch() {
        var resultsList = document.querySelector('#mp-match-results-list');
        var paginationEl = document.querySelector('#mp-match-pagination');
        if (resultsList) {
            resultsList.innerHTML = renderMatchSkeleton(3);
            doMatchSearch(MatchV2State.currentCriteria, resultsList, paginationEl);
        }
    }

    function goToMatchPage(page) {
        if (page < 1) return;
        MatchV2State.currentCriteria.page = page;
        var resultsList = document.querySelector('#mp-match-results-list');
        var paginationEl = document.querySelector('#mp-match-pagination');
        if (resultsList) {
            resultsList.innerHTML = renderMatchSkeleton(3);
            doMatchSearch(MatchV2State.currentCriteria, resultsList, paginationEl);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    function initMatchView() {
        var container = document.getElementById('view-marketplace-match');
        if (!container) return;

        console.log('[MatchV2] init match view');
        renderMatchResults(container, MatchV2State.currentCriteria);
    }

    // ========================================================================
    // 10. 页面 1: Lawyers 初始化
    // ========================================================================

    function initLawyersView() {
        var root = document.getElementById('view-marketplace-lawyers');
        if (!root) return;
        console.log('[Marketplace] init lawyers view');

        // 拉律师池 (5min cache)
        loadLawyerPool(function (err, pool) {
            if (err) {
                console.warn('[Marketplace] loadLawyerPool 失败, 用 demo:', err);
                pool = DEMO_LAWYERS;
            }
            renderLawyersList(root, pool);
        });

        // 事件: 搜索 + 案件类型筛选
        var search = root.querySelector('#mp-lawyer-search');
        if (search)
            search.addEventListener('input', function () {
                clearTimeout(MarketplaceState.searchTimer);
                MarketplaceState.searchTimer = setTimeout(function () {
                    applyLawyerFilter(root);
                }, 300);
            });

        var caseTypeSel = root.querySelector('#mp-lawyer-case-type');
        if (caseTypeSel)
            caseTypeSel.addEventListener('change', function () {
                applyLawyerFilter(root);
            });

        var regionSel = root.querySelector('#mp-lawyer-region');
        if (regionSel)
            regionSel.addEventListener('change', function () {
                applyLawyerFilter(root);
            });

        // 顶部 hero disclaimer
        var discEl = root.querySelector('#mp-lawyers-disclaimer');
        if (discEl) {
            MarketplaceAPI.getDisclaimer().then(function (res) {
                if (res.ok && res.data && res.data.full) {
                    discEl.textContent = res.data.full;
                }
            });
        }
    }

    function loadLawyerPool(cb) {
        var now = Date.now();
        if (
            MarketplaceState.lawyerPool.length > 0 &&
            now - MarketplaceState.lawyerPoolLoadedAt < MarketplaceState.cacheTtlMs
        ) {
            return cb(null, MarketplaceState.lawyerPool);
        }
        // 真实场景: 调 POST /lawyers 不合适, 因为后端只创建单个; 律师池从本地 demo + L001 自报家门派生
        // 简化: 缓存 demo 池 + 当前律师
        var pool = DEMO_LAWYERS.slice();
        // 把当前律师也加进去 (如果不在)
        if (MarketplaceState.currentLawyerId) {
            var exists = pool.some(function (l) {
                return l.lawyer_id === MarketplaceState.currentLawyerId;
            });
            if (!exists) {
                pool.unshift({
                    lawyer_id: MarketplaceState.currentLawyerId,
                    name: MarketplaceState.currentLawyerName || '当前律师',
                    firm_id: 'F-当前律所',
                    specialties: ['contract_dispute'],
                    jurisdictions: ['CN'],
                    languages: ['zh-CN'],
                    region: '北京',
                    experience_years: 5,
                    rating: 4.5,
                    completed_cases: 50,
                    marketplace_active: true,
                    cross_border_capable: false,
                    availability: 'available',
                    bio: '当前登录律师 (本机 demo)'
                });
            }
        }
        MarketplaceState.lawyerPool = pool;
        MarketplaceState.lawyerPoolLoadedAt = now;
        cb(null, pool);
    }

    function renderLawyersList(root, pool) {
        var listEl = root.querySelector('#mp-lawyers-list');
        if (!listEl) return;
        listEl.innerHTML = pool
            .map(function (l) {
                var score = computeMatchScore(l, [], '');
                var availability =
                    AVAILABILITY.find(function (a) {
                        return a.value === l.availability;
                    }) || AVAILABILITY[0];
                return (
                    '' +
                    '<div class="mp-lawyer-card mp-fade-in bg-white rounded-lg p-4 mb-3 cursor-pointer hover:shadow-md transition-shadow" data-lawyer-id="' +
                    esc(l.lawyer_id) +
                    '" onclick="MarketplaceFn.openLawyerDetail(\'' +
                    esc(l.lawyer_id) +
                    '\')">' +
                    '<div class="flex items-start gap-3">' +
                    '<div class="w-12 h-12 rounded-full bg-gradient-to-br from-brand to-wiki flex items-center justify-center text-white text-base font-semibold flex-shrink-0">' +
                    esc(l.name ? l.name.substring(0, 1) : '?') +
                    '</div>' +
                    '<div class="flex-1 min-w-0">' +
                    '<div class="flex items-center gap-2 flex-wrap mb-1">' +
                    '<h3 class="text-sm font-semibold text-fg-primary truncate">' +
                    esc(l.name) +
                    '</h3>' +
                    '<span class="text-[11px] text-fg-tertiary">' +
                    esc(l.firm_id || '独立') +
                    '</span>' +
                    (l.cross_border_capable
                        ? '<span class="mp-badge-recommend text-[10px] px-1.5 py-0.5 rounded">跨境</span>'
                        : '') +
                    '</div>' +
                    '<div class="flex flex-wrap gap-1 mb-2">' +
                    (l.specialties || [])
                        .map(function (s) {
                            var t = CASE_TYPES.find(function (c) {
                                return c.value === s;
                            });
                            return (
                                '<span class="text-[10px] px-1.5 py-0.5 rounded bg-bg-subtle text-fg-secondary">' +
                                esc(t ? t.label : s) +
                                '</span>'
                            );
                        })
                        .join('') +
                    '</div>' +
                    '<div class="flex items-center gap-3 text-[11px] text-fg-tertiary mb-2">' +
                    '<span><iconify-icon icon="mdi:map-marker-outline" class="text-xs"></iconify-icon> ' +
                    esc(l.region || '未填') +
                    '</span>' +
                    '<span><iconify-icon icon="mdi:briefcase-outline" class="text-xs"></iconify-icon> ' +
                    (l.experience_years || 0) +
                    ' 年</span>' +
                    '<span><iconify-icon icon="mdi:star" class="text-xs text-urgent"></iconify-icon> ' +
                    (l.rating || 0).toFixed(1) +
                    '</span>' +
                    '<span class="flex items-center gap-1"><span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:' +
                    availability.dot +
                    '"></span> ' +
                    availability.label +
                    '</span>' +
                    '</div>' +
                    renderDimBars(score) +
                    '</div>' +
                    '<div class="text-right flex-shrink-0">' +
                    '<div class="mp-score-big text-2xl font-bold text-brand">' +
                    (score.total * 100).toFixed(0) +
                    '</div>' +
                    '<div class="text-[10px] text-fg-tertiary mb-2">综合分</div>' +
                    (score.total >= 0.8
                        ? '<span class="mp-badge-strong text-[10px] px-1.5 py-0.5 rounded block mb-1">强推荐</span>'
                        : score.total >= 0.6
                            ? '<span class="mp-badge-recommend text-[10px] px-1.5 py-0.5 rounded block mb-1">推荐</span>'
                            : '<span class="text-[10px] text-fg-tertiary block mb-1">候选</span>') +
                    '<button class="mp-btn mp-btn-primary mp-btn-sm w-full" data-mp-action="create-referral" data-lawyer-id="' +
                    esc(l.lawyer_id) +
                    '">' +
                    '<iconify-icon icon="mdi:share-variant" class="text-xs"></iconify-icon> 转介绍' +
                    '</button>' +
                    '<button class="mp-btn mp-btn-secondary mp-btn-sm w-full mt-1" data-mp-action="invite-co-counsel" data-lawyer-id="' +
                    esc(l.lawyer_id) +
                    '">' +
                    '<iconify-icon icon="mdi:account-multiple-plus-outline" class="text-xs"></iconify-icon> 协同' +
                    '</button>' +
                    '</div>' +
                    '</div>' +
                    '</div>'
                );
            })
            .join('');

        // 绑定按钮
        listEl.querySelectorAll('[data-mp-action]').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                var action = btn.getAttribute('data-mp-action');
                var lawyerId = btn.getAttribute('data-lawyer-id');
                if (action === 'create-referral') {
                    if (typeof window.switchView === 'function') {
                        window.switchView('marketplace-referrals');
                        setTimeout(function () {
                            openCreateReferralModal(lawyerId);
                        }, 100);
                    }
                } else if (action === 'invite-co-counsel') {
                    if (typeof window.switchView === 'function') {
                        window.switchView('marketplace-cases');
                        setTimeout(function () {
                            openCreateCaseModal(lawyerId);
                        }, 100);
                    }
                }
            });
        });
    }

    function applyLawyerFilter(root) {
        var search = (root.querySelector('#mp-lawyer-search').value || '').toLowerCase();
        var caseType = root.querySelector('#mp-lawyer-case-type').value;
        var region = root.querySelector('#mp-lawyer-region').value;

        var pool = MarketplaceState.lawyerPool.slice();
        if (search) {
            pool = pool.filter(function (l) {
                return (
                    (l.name && l.name.toLowerCase().indexOf(search) >= 0) ||
                    (l.firm_id && l.firm_id.toLowerCase().indexOf(search) >= 0) ||
                    (l.bio && l.bio.toLowerCase().indexOf(search) >= 0)
                );
            });
        }
        if (caseType) {
            pool = pool.filter(function (l) {
                return l.specialties && l.specialties.indexOf(caseType) >= 0;
            });
        }
        if (region) {
            pool = pool.filter(function (l) {
                return l.region && l.region.indexOf(region) >= 0;
            });
        }
        renderLawyersList(root, pool);
    }

    // ========================================================================
    // 11. 页面 2: Cases 初始化
    // ========================================================================

    function initCasesView() {
        var root = document.getElementById('view-marketplace-cases');
        if (!root) return;
        console.log('[Marketplace] init cases view');
        renderCasesList(root, DEMO_CASES);
        bindCasesFilter(root);
        bindCreateCaseButton(root);
    }

    function renderCasesList(root, cases) {
        var listEl = root.querySelector('#mp-cases-list');
        if (!listEl) return;
        if (!cases || cases.length === 0) {
            listEl.innerHTML =
                '<div class="mp-empty"><iconify-icon icon="mdi:briefcase-off-outline" class="mp-empty-icon"></iconify-icon><div>暂无协同办案案件</div><div class="text-[11px] mt-1">点击"发布协同办案"开始</div></div>';
            return;
        }
        listEl.innerHTML = cases
            .map(function (c) {
                var state = findState(c.state);
                var type = CASE_TYPES.find(function (t) {
                    return t.value === c.case_type;
                });
                return (
                    '' +
                    '<div class="bg-white rounded-lg p-4 mb-3 mp-fade-in border border-bg-border mp-row cursor-pointer hover:shadow-md transition-shadow" data-case-id="' +
                    esc(c.case_id) +
                    '" onclick="MarketplaceFn.openCaseDetail(\'' +
                    esc(c.case_id) +
                    '\')">' +
                    '<div class="flex items-start justify-between gap-3 mb-3">' +
                    '<div class="flex-1 min-w-0">' +
                    '<div class="flex items-center gap-2 flex-wrap mb-1">' +
                    '<h3 class="text-sm font-semibold">' +
                    esc(c.case_id) +
                    '</h3>' +
                    '<span class="mp-state-pill ' +
                    state.color +
                    '">' +
                    state.label +
                    '</span>' +
                    '<span class="text-[10px] px-1.5 py-0.5 rounded bg-bg-subtle text-fg-secondary">' +
                    esc(type ? type.label : c.case_type) +
                    '</span>' +
                    '</div>' +
                    '<p class="text-[12px] text-fg-secondary mb-2">' +
                    esc(c.case_description || '') +
                    '</p>' +
                    '<div class="text-[11px] text-fg-tertiary flex flex-wrap gap-3">' +
                    '<span>律师 A: <strong class="text-fg-secondary">' +
                    esc(c.lawyer_a_id) +
                    '</strong></span>' +
                    (c.lawyer_b_id
                        ? '<span>律师 B: <strong class="text-fg-secondary">' + esc(c.lawyer_b_id) + '</strong></span>'
                        : '<span class="text-warning">律师 B: 待接</span>') +
                    (c.firm_id ? '<span>律所: ' + esc(c.firm_id) + '</span>' : '') +
                    '</div>' +
                    '</div>' +
                    '<div class="text-right flex-shrink-0">' +
                    '<div class="text-lg font-bold text-fg-primary">' +
                    fmtMoney(c.fee) +
                    '</div>' +
                    '<div class="text-[10px] text-fg-tertiary">律师费</div>' +
                    '<div class="text-[11px] text-urgent mt-1">分账 ' +
                    ((c.split_ratio || 0) * 100).toFixed(0) +
                    '% / ' +
                    ((1 - (c.split_ratio || 0)) * 100).toFixed(0) +
                    '%</div>' +
                    '<div class="text-[11px] text-brand">Marketplace 抽 ' +
                    ((c.marketplace_commission_rate || 0) * 100).toFixed(0) +
                    '%</div>' +
                    '</div>' +
                    '</div>' +
                    '<div class="bg-bg-subtle rounded-md p-3">' +
                    renderStateStepBar(c.state) +
                    '</div>' +
                    (c.history && c.history.length > 0
                        ? '<details class="mt-2"><summary class="text-[11px] text-fg-tertiary cursor-pointer hover:text-brand">查看 ' +
                          c.history.length +
                          ' 条历史</summary>' +
                          '<div class="mt-2 mp-timeline">' +
                          c.history
                              .map(function (h) {
                                  return (
                                      '<div class="mp-timeline-item">' +
                                      '<span class="mp-timeline-dot completed"></span>' +
                                      '<div class="mp-timeline-title">' +
                                      esc(h.from) +
                                      ' → ' +
                                      esc(h.to) +
                                      '</div>' +
                                      '<div class="mp-timeline-meta">' +
                                      esc(h.actor) +
                                      ' · ' +
                                      esc(h.reason) +
                                      ' · ' +
                                      fmtDate(h.ts) +
                                      '</div>' +
                                      '</div>'
                                  );
                              })
                              .join('') +
                          '</div>' +
                          '</details>'
                        : '') +
                    '</div>'
                );
            })
            .join('');
    }

    function bindCasesFilter(root) {
        var stateSel = root.querySelector('#mp-cases-state');
        if (stateSel)
            stateSel.addEventListener('change', function () {
                applyCasesFilter(root);
            });
    }

    function applyCasesFilter(root) {
        var stateVal = root.querySelector('#mp-cases-state').value;
        var list = DEMO_CASES.slice();
        if (stateVal)
            list = list.filter(function (c) {
                return c.state === stateVal;
            });
        renderCasesList(root, list);
    }

    function bindCreateCaseButton(root) {
        var btn = root.querySelector('#mp-cases-create-btn');
        if (btn)
            btn.addEventListener('click', function () {
                openCreateCaseModal(null);
            });
    }

    // ========================================================================
    // 12. 页面 3: Referrals 初始化
    // ========================================================================

    function initReferralsView() {
        var root = document.getElementById('view-marketplace-referrals');
        if (!root) return;
        console.log('[Marketplace] init referrals view');
        renderReferralsTimeline(root, DEMO_REFERRALS);
        renderReferralsList(root, DEMO_REFERRALS);
        bindReferralsFilter(root);
        bindCreateReferralButton(root);
    }

    function renderReferralsTimeline(root, referrals) {
        var tlEl = root.querySelector('#mp-referrals-timeline');
        if (!tlEl) return;
        var byStatus = { pending: 0, accepted: 0, completed: 0, settled: 0, cancelled: 0 };
        (referrals || []).forEach(function (r) {
            if (byStatus[r.status] !== undefined) byStatus[r.status]++;
        });

        var total = referrals.length;
        var totalCommission = 0;
        (referrals || []).forEach(function (r) {
            if (r.referrer_commission) totalCommission += r.referrer_commission;
        });

        tlEl.innerHTML =
            '' +
            '<div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">' +
            ['pending', 'accepted', 'completed', 'settled', 'cancelled']
                .map(function (s) {
                    var status = findReferralStatus(s);
                    return (
                        '<div class="bg-white rounded-md p-3 border border-bg-border text-center">' +
                        '<div class="text-2xl font-bold ' +
                        status.color +
                        '">' +
                        byStatus[s] +
                        '</div>' +
                        '<div class="text-[11px] text-fg-tertiary mt-1">' +
                        status.label +
                        '</div>' +
                        '</div>'
                    );
                })
                .join('') +
            '</div>' +
            '<div class="bg-gradient-to-r from-brand to-wiki text-white rounded-lg p-4 mb-4">' +
            '<div class="flex items-center justify-between flex-wrap gap-2">' +
            '<div>' +
            '<div class="text-[11px] opacity-80">累计转介绍</div>' +
            '<div class="text-2xl font-bold mp-score-big">' +
            total +
            ' <span class="text-sm font-normal">次</span></div>' +
            '</div>' +
            '<div>' +
            '<div class="text-[11px] opacity-80">累计抽成</div>' +
            '<div class="text-2xl font-bold mp-score-big">' +
            fmtMoney(totalCommission) +
            '</div>' +
            '</div>' +
            '<div>' +
            '<div class="text-[11px] opacity-80">完成率</div>' +
            '<div class="text-2xl font-bold mp-score-big">' +
            (total > 0 ? ((byStatus.settled / total) * 100).toFixed(0) : 0) +
            '<span class="text-sm font-normal">%</span></div>' +
            '</div>' +
            '</div>' +
            '</div>';
    }

    function renderReferralsList(root, referrals) {
        var listEl = root.querySelector('#mp-referrals-list');
        if (!listEl) return;
        if (!referrals || referrals.length === 0) {
            listEl.innerHTML =
                '<div class="mp-empty"><iconify-icon icon="mdi:share-variant-outline" class="mp-empty-icon"></iconify-icon><div>暂无转介绍记录</div></div>';
            return;
        }
        listEl.innerHTML = referrals
            .map(function (r) {
                var status = findReferralStatus(r.status);
                var type = CASE_TYPES.find(function (t) {
                    return t.value === r.case_type;
                });
                return (
                    '' +
                    '<div class="bg-white rounded-lg p-4 mb-3 mp-fade-in border border-bg-border mp-row cursor-pointer hover:shadow-md transition-shadow" data-referral-id="' +
                    esc(r.referral_id) +
                    '" onclick="MarketplaceFn.openReferralDetail(\'' +
                    esc(r.referral_id) +
                    '\')">' +
                    '<div class="flex items-start gap-3">' +
                    '<div class="w-10 h-10 rounded-full bg-brand-tint flex items-center justify-center flex-shrink-0">' +
                    '<iconify-icon icon="mdi:share-variant" class="text-brand text-lg"></iconify-icon>' +
                    '</div>' +
                    '<div class="flex-1 min-w-0">' +
                    '<div class="flex items-center gap-2 flex-wrap mb-1">' +
                    '<span class="text-sm font-semibold">' +
                    esc(r.referral_id) +
                    '</span>' +
                    '<span class="text-[11px] ' +
                    status.color +
                    '">● ' +
                    status.label +
                    '</span>' +
                    (type
                        ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-bg-subtle text-fg-secondary">' +
                          esc(type.label) +
                          '</span>'
                        : '') +
                    '</div>' +
                    '<p class="text-[12px] text-fg-secondary mb-2">' +
                    esc(r.case_description || '') +
                    '</p>' +
                    '<div class="text-[11px] text-fg-tertiary flex flex-wrap gap-3">' +
                    '<span>推荐人: <strong class="text-fg-secondary">' +
                    esc(r.referrer_id) +
                    '</strong></span>' +
                    '<span>被推荐: <strong class="text-fg-secondary">' +
                    esc(r.target_lawyer_id) +
                    '</strong></span>' +
                    (r.match_score
                        ? '<span>匹配分: <strong class="text-brand">' +
                          (r.match_score * 100).toFixed(0) +
                          '</strong></span>'
                        : '') +
                    '<span>' +
                    fmtDate(r.created_at) +
                    '</span>' +
                    '</div>' +
                    '</div>' +
                    '<div class="text-right flex-shrink-0">' +
                    '<div class="text-[11px] text-fg-tertiary">预期 / 实际</div>' +
                    '<div class="text-sm font-semibold text-fg-primary">' +
                    fmtMoney(r.expected_fee) +
                    '</div>' +
                    (r.actual_fee
                        ? '<div class="text-[10px] text-success">实 ' + fmtMoney(r.actual_fee) + '</div>'
                        : '') +
                    (r.referrer_commission
                        ? '<div class="text-[11px] text-urgent mt-1">抽成 ' + fmtMoney(r.referrer_commission) + '</div>'
                        : '') +
                    '<div class="text-[10px] text-fg-tertiary mt-1">5% 抽成 (Marketplace 不抽)</div>' +
                    '</div>' +
                    '</div>' +
                    '</div>'
                );
            })
            .join('');
    }

    function bindReferralsFilter(root) {
        var statusSel = root.querySelector('#mp-referrals-status');
        if (statusSel)
            statusSel.addEventListener('change', function () {
                applyReferralsFilter(root);
            });
    }

    function applyReferralsFilter(root) {
        var statusVal = root.querySelector('#mp-referrals-status').value;
        var list = DEMO_REFERRALS.slice();
        if (statusVal)
            list = list.filter(function (r) {
                return r.status === statusVal;
            });
        renderReferralsList(root, list);
    }

    function bindCreateReferralButton(root) {
        var btn = root.querySelector('#mp-referrals-create-btn');
        if (btn)
            btn.addEventListener('click', function () {
                openCreateReferralModal(null);
            });
    }

    // ========================================================================
    // 13. 页面 4: Cross-border 初始化
    // ========================================================================

    function initCrossBorderView() {
        var root = document.getElementById('view-marketplace-cross-border');
        if (!root) return;
        console.log('[Marketplace] init cross-border view');
        renderCrossBorderList(root, DEMO_CROSS_BORDER_JOBS);
        renderCrossBorderPricing(root);
        bindCrossBorderFilter(root);
        bindCreateCrossBorderButton(root);
    }

    function renderCrossBorderList(root, jobs) {
        var listEl = root.querySelector('#mp-cb-list');
        if (!listEl) return;
        if (!jobs || jobs.length === 0) {
            listEl.innerHTML =
                '<div class="mp-empty"><iconify-icon icon="mdi:earth" class="mp-empty-icon"></iconify-icon><div>暂无跨境文件订单</div><div class="text-[11px] mt-1">W31 正式启用, 40 律所合作</div></div>';
            return;
        }
        listEl.innerHTML = jobs
            .map(function (j) {
                var docType = findDocType(j.doc_type);
                var lang = findLanguage(j.language);
                return (
                    '' +
                    '<div class="bg-white rounded-lg p-4 mb-3 mp-fade-in border border-bg-border mp-row cursor-pointer hover:shadow-md transition-shadow" data-job-id="' +
                    esc(j.job_id) +
                    '" onclick="MarketplaceFn.openCrossBorderDetail(\'' +
                    esc(j.job_id) +
                    '\')">' +
                    '<div class="flex items-start gap-3">' +
                    '<div class="w-10 h-10 rounded-full bg-wiki-tint flex items-center justify-center flex-shrink-0">' +
                    '<iconify-icon icon="mdi:earth" class="text-wiki text-lg"></iconify-icon>' +
                    '</div>' +
                    '<div class="flex-1 min-w-0">' +
                    '<div class="flex items-center gap-2 flex-wrap mb-1">' +
                    '<span class="text-sm font-semibold">' +
                    esc(j.job_id) +
                    '</span>' +
                    '<span class="text-[10px] px-1.5 py-0.5 rounded ' +
                    lang.cls +
                    '">' +
                    esc(lang.label) +
                    '</span>' +
                    '<span class="text-[10px] px-1.5 py-0.5 rounded bg-bg-subtle text-fg-secondary">' +
                    esc(docType.label) +
                    '</span>' +
                    '<span class="mp-jur-tag">' +
                    esc(j.jurisdiction) +
                    '</span>' +
                    (j.arbitration_institution
                        ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-urgent-tint text-urgent">' +
                          esc(j.arbitration_institution) +
                          '</span>'
                        : '') +
                    '</div>' +
                    '<p class="text-[12px] text-fg-secondary mb-2">律师 ' +
                    esc(j.lawyer_id) +
                    ' → 客户 ' +
                    esc(j.client_id) +
                    '</p>' +
                    '<div class="text-[11px] text-fg-tertiary flex flex-wrap gap-3">' +
                    '<span>状态: <strong class="text-fg-secondary">' +
                    esc(j.status) +
                    '</strong></span>' +
                    (j.template_id
                        ? '<span>模板: <code class="text-fg-secondary">' + esc(j.template_id) + '</code></span>'
                        : '') +
                    '<span>' +
                    fmtDate(j.created_at) +
                    '</span>' +
                    '</div>' +
                    '</div>' +
                    '<div class="text-right flex-shrink-0">' +
                    '<div class="mp-doc-price">' +
                    '<span class="mp-doc-price-cur">¥</span>' +
                    '<span class="mp-doc-price-num">' +
                    (j.price || 0) +
                    '</span>' +
                    '</div>' +
                    '<div class="mp-doc-commission">Marketplace 抽 ¥' +
                    (j.marketplace_commission || 0).toFixed(1) +
                    ' (30%)</div>' +
                    '<div class="text-[11px] text-success mt-1">律师得 ¥' +
                    ((j.price || 0) - (j.marketplace_commission || 0)).toFixed(1) +
                    '</div>' +
                    (j.document_url
                        ? '<a class="text-[11px] text-brand hover:underline block mt-1" href="' +
                          esc(j.document_url) +
                          '">下载文件</a>'
                        : '<span class="text-[11px] text-fg-tertiary block mt-1">生成中</span>') +
                    '</div>' +
                    '</div>' +
                    '</div>'
                );
            })
            .join('');
    }

    function renderCrossBorderPricing(root) {
        var tbl = root.querySelector('#mp-cb-pricing');
        if (!tbl) return;
        var html =
            '<table class="w-full text-[12px]">' +
            '<thead><tr class="border-b border-bg-border text-fg-tertiary"><th class="text-left py-2 px-2">文档类型</th>';
        LANGUAGES.forEach(function (l) {
            html += '<th class="text-right py-2 px-2">' + esc(l.label) + '</th>';
        });
        html += '</tr></thead><tbody>';
        CROSS_BORDER_DOC_TYPES.forEach(function (dt) {
            html +=
                '<tr class="border-b border-bg-border mp-row">' +
                '<td class="py-2 px-2 font-medium">' +
                esc(dt.label) +
                '</td>';
            LANGUAGES.forEach(function (l) {
                var price = dt.basePrice[l.value] || 0;
                html +=
                    '<td class="py-2 px-2 text-right">' +
                    '<div class="mp-doc-price justify-end">' +
                    '<span class="mp-doc-price-cur">¥</span>' +
                    '<span class="font-semibold">' +
                    price +
                    '</span>' +
                    '</div>' +
                    '</td>';
            });
            html += '</tr>';
        });
        html += '</tbody></table>';
        tbl.innerHTML = html;
    }

    function bindCrossBorderFilter(root) {
        var docSel = root.querySelector('#mp-cb-doc-type');
        var langSel = root.querySelector('#mp-cb-language');
        if (docSel)
            docSel.addEventListener('change', function () {
                applyCrossBorderFilter(root);
            });
        if (langSel)
            langSel.addEventListener('change', function () {
                applyCrossBorderFilter(root);
            });
    }

    function applyCrossBorderFilter(root) {
        var docVal = root.querySelector('#mp-cb-doc-type').value;
        var langVal = root.querySelector('#mp-cb-language').value;
        var list = DEMO_CROSS_BORDER_JOBS.slice();
        if (docVal)
            list = list.filter(function (j) {
                return j.doc_type === docVal;
            });
        if (langVal)
            list = list.filter(function (j) {
                return j.language === langVal;
            });
        renderCrossBorderList(root, list);
    }

    function bindCreateCrossBorderButton(root) {
        var btn = root.querySelector('#mp-cb-create-btn');
        if (btn)
            btn.addEventListener('click', function () {
                openCreateCrossBorderModal();
            });
    }

    // ========================================================================
    // 14. 页面 5: Metrics 初始化
    // ========================================================================

    function initMetricsView() {
        var root = document.getElementById('view-marketplace-metrics');
        if (!root) return;
        console.log('[Marketplace] init metrics view');
        loadMetrics(function (err, data) {
            if (err) {
                console.warn('[Marketplace] load metrics failed, demo:', err);
                data = DEMO_METRICS;
            }
            renderMetricsCards(root, data);
            renderMetricsBreakdown(root, data);
        });

        // 刷新按钮
        var refresh = root.querySelector('#mp-metrics-refresh');
        if (refresh) {
            refresh.addEventListener('click', function () {
                refresh.classList.add('icon-spin');
                MarketplaceState.metricsLoadedAt = 0;
                initMetricsView();
                setTimeout(function () {
                    refresh.classList.remove('icon-spin');
                }, 800);
            });
        }
    }

    function loadMetrics(cb) {
        var now = Date.now();
        if (MarketplaceState.metrics && now - MarketplaceState.metricsLoadedAt < MarketplaceState.cacheTtlMs) {
            return cb(null, MarketplaceState.metrics);
        }
        MarketplaceAPI.getMetrics()
            .then(function (res) {
                if (res.ok && res.data) {
                    MarketplaceState.metrics = res.data;
                    MarketplaceState.metricsLoadedAt = now;
                    cb(null, res.data);
                } else {
                    cb(new Error('Marketplace API metrics failed: ' + (res.status || 'no status')));
                }
            })
            .catch(function (err) {
                cb(err);
            });
    }

    function renderMetricsCards(root, data) {
        var cards = root.querySelector('#mp-metrics-cards');
        if (!cards) return;
        cards.innerHTML =
            '' +
            // 律师参与方
            '<div class="mp-metric-card mp-metric-participants border rounded-lg p-4">' +
            '<div class="mp-metric-label">律师参与方</div>' +
            '<div class="mp-metric-num">' +
            (data.lawyer_participants || 0) +
            '</div>' +
            '<div class="mp-metric-delta up mt-1">Marketplace 参与方律师总数</div>' +
            '</div>' +
            // 月接案数
            '<div class="mp-metric-card mp-metric-cases border rounded-lg p-4">' +
            '<div class="mp-metric-label">月接案数</div>' +
            '<div class="mp-metric-num">' +
            (data.cases_completed_monthly || 0) +
            '</div>' +
            '<div class="mp-metric-delta up mt-1">协同 + 转介绍 + 跨境 合计</div>' +
            '</div>' +
            // 月营收
            '<div class="mp-metric-card mp-metric-revenue border rounded-lg p-4">' +
            '<div class="mp-metric-label">月营收</div>' +
            '<div class="mp-metric-num">' +
            fmtMoney(data.revenue_monthly || 0) +
            '</div>' +
            '<div class="mp-metric-delta up mt-1">累计流水</div>' +
            '</div>' +
            // 跨境案件月单量
            '<div class="mp-metric-card mp-metric-crossborder border rounded-lg p-4">' +
            '<div class="mp-metric-label">跨境案件月单量</div>' +
            '<div class="mp-metric-num">' +
            (data.cross_border_orders_monthly || 0) +
            '</div>' +
            '<div class="mp-metric-delta up mt-1">W25 Skill 3 v3.0 模板复用</div>' +
            '</div>' +
            // 律师满意度
            '<div class="mp-metric-card mp-metric-rating border rounded-lg p-4">' +
            '<div class="mp-metric-label">律师满意度</div>' +
            '<div class="mp-metric-num">' +
            (data.avg_lawyer_rating || 0).toFixed(2) +
            ' <span class="text-base text-urgent">★</span></div>' +
            '<div class="mp-metric-delta flat mt-1">仅 marketplace_active 律师</div>' +
            '</div>';
    }

    function renderMetricsBreakdown(root, data) {
        var breakdown = root.querySelector('#mp-metrics-breakdown');
        if (!breakdown) return;
        var total =
            (data.referral_count_total || 0) +
            (data.co_counsel_count_total || 0) +
            (data.cross_border_count_total || 0);
        breakdown.innerHTML =
            '' +
            '<div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">' +
            '<div class="bg-white rounded-md p-3 border border-bg-border">' +
            '<div class="text-[11px] text-fg-tertiary">累计转介绍</div>' +
            '<div class="text-xl font-bold text-brand">' +
            (data.referral_count_total || 0) +
            ' <span class="text-xs text-fg-tertiary">次</span></div>' +
            '</div>' +
            '<div class="bg-white rounded-md p-3 border border-bg-border">' +
            '<div class="text-[11px] text-fg-tertiary">累计协同办案</div>' +
            '<div class="text-xl font-bold text-success">' +
            (data.co_counsel_count_total || 0) +
            ' <span class="text-xs text-fg-tertiary">件</span></div>' +
            '</div>' +
            '<div class="bg-white rounded-md p-3 border border-bg-border">' +
            '<div class="text-[11px] text-fg-tertiary">累计跨境文件</div>' +
            '<div class="text-xl font-bold text-wiki">' +
            (data.cross_border_count_total || 0) +
            ' <span class="text-xs text-fg-tertiary">份</span></div>' +
            '</div>' +
            '</div>' +
            '<div class="bg-white rounded-md p-4 border border-bg-border mb-4">' +
            '<div class="flex items-center justify-between mb-3">' +
            '<h3 class="text-sm font-semibold">抽成结算</h3>' +
            '<span class="text-[11px] text-fg-tertiary">T+7 结算, 复用 W28 PRD § 3.5</span>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3">' +
            '<div class="text-center">' +
            '<div class="text-[11px] text-fg-tertiary">待结算</div>' +
            '<div class="text-lg font-bold text-warning">' +
            fmtMoney(data.commission_pending || 0) +
            '</div>' +
            '</div>' +
            '<div class="text-center">' +
            '<div class="text-[11px] text-fg-tertiary">已结算</div>' +
            '<div class="text-lg font-bold text-success">' +
            fmtMoney(data.commission_settled || 0) +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>' +
            (data.trajectory
                ? '<div class="bg-white rounded-md p-4 border border-bg-border">' +
                  '<h3 class="text-sm font-semibold mb-2">性能 + 统计 (后端返回 trajectory)</h3>' +
                  '<div class="grid grid-cols-3 gap-3 text-[11px]">' +
                  '<div><span class="text-fg-tertiary">周期:</span> <strong>' +
                  (data.trajectory.period_days || 30) +
                  ' 天</strong></div>' +
                  '<div><span class="text-fg-tertiary">律师池:</span> <strong>' +
                  (data.trajectory.lawyer_pool_size || 0) +
                  '</strong></div>' +
                  '<div><span class="text-fg-tertiary">延迟:</span> <strong>' +
                  (data.trajectory.latency_ms || '-') +
                  ' ms</strong></div>' +
                  '</div>' +
                  '</div>'
                : '');
    }

    // ========================================================================
    // 14.5. 弹窗: 律师详情
    // ========================================================================

    var _closeLawyerDetail = null;
    var _closeCaseDetail = null;
    var _closeReferralDetail = null;
    var _closeCrossBorderDetail = null;

    function openLawyerDetail(lawyerId) {
        var lawyer = null;
        var pool = MarketplaceState.lawyerPool.length > 0 ? MarketplaceState.lawyerPool : DEMO_LAWYERS;
        for (var i = 0; i < pool.length; i++) {
            if (pool[i].lawyer_id === lawyerId) {
                lawyer = pool[i];
                break;
            }
        }
        if (!lawyer) {
            toast('未找到律师 ' + lawyerId, 'warning');
            return;
        }
        var score = computeMatchScore(lawyer, [], '');
        var availability =
            AVAILABILITY.find(function (a) {
                return a.value === lawyer.availability;
            }) || AVAILABILITY[0];

        var content =
            '<div class="space-y-4">' +
            '<div class="flex items-start gap-4 p-3 bg-bg-subtle rounded-xl">' +
            '<div class="w-16 h-16 rounded-full bg-gradient-to-br from-brand to-wiki flex items-center justify-center text-white text-xl font-bold flex-shrink-0">' +
            esc(lawyer.name ? lawyer.name.substring(0, 1) : '?') +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-center gap-2 flex-wrap mb-1">' +
            '<h3 class="text-base font-semibold text-fg-primary">' +
            esc(lawyer.name) +
            '</h3>' +
            (lawyer.cross_border_capable
                ? '<span class="mp-badge-strong text-[10px] px-1.5 py-0.5 rounded">跨境</span>'
                : '') +
            '</div>' +
            '<p class="text-xs text-fg-tertiary mb-1">' +
            esc(lawyer.firm_id || '独立律师') +
            '</p>' +
            '<div class="flex items-center gap-3 text-[11px] text-fg-tertiary flex-wrap">' +
            '<span class="flex items-center gap-1"><span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:' +
            availability.dot +
            '"></span>' +
            esc(availability.label) +
            '</span>' +
            '<span><iconify-icon icon="mdi:map-marker-outline" class="text-xs"></iconify-icon> ' +
            esc(lawyer.region || '-') +
            '</span>' +
            '<span><iconify-icon icon="mdi:briefcase-outline" class="text-xs"></iconify-icon> ' +
            (lawyer.experience_years || 0) +
            ' 年</span>' +
            '<span><iconify-icon icon="mdi:star" class="text-xs text-urgent"></iconify-icon> ' +
            (lawyer.rating || 0).toFixed(1) +
            '</span>' +
            '</div>' +
            '</div>' +
            '<div class="text-right flex-shrink-0">' +
            '<div class="text-2xl font-bold text-brand">' +
            (score.total * 100).toFixed(0) +
            '</div>' +
            '<div class="text-[10px] text-fg-tertiary">综合分</div>' +
            '</div>' +
            '</div>' +
            '<div class="space-y-2">' +
            '<p class="text-xs font-medium text-fg-secondary">专业领域</p>' +
            '<div class="flex flex-wrap gap-1">' +
            (lawyer.specialties || [])
                .map(function (s) {
                    var t = CASE_TYPES.find(function (c) {
                        return c.value === s;
                    });
                    return (
                        '<span class="text-[11px] px-2 py-1 rounded bg-bg-subtle text-fg-secondary">' +
                        esc(t ? t.label : s) +
                        '</span>'
                    );
                })
                .join('') +
            '</div>' +
            '</div>' +
            '<div class="space-y-2">' +
            '<p class="text-xs font-medium text-fg-secondary">5 维评分</p>' +
            renderDimBars(score) +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">累计办案</p>' +
            '<p class="text-sm font-semibold text-fg-primary">' +
            (lawyer.completed_cases || 0) +
            ' 件</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">司法辖区</p>' +
            '<p class="text-sm font-semibold text-fg-primary">' +
            (lawyer.jurisdictions || []).length +
            ' 个</p>' +
            '</div>' +
            '</div>' +
            (lawyer.languages && lawyer.languages.length > 0
                ? '<div class="space-y-2"><p class="text-xs font-medium text-fg-secondary">语言能力</p><div class="flex flex-wrap gap-1">' +
                  lawyer.languages
                      .map(function (lg) {
                          var lang = LANGUAGES.find(function (x) {
                              return x.value === lg;
                          });
                          return (
                              '<span class="text-[11px] px-2 py-1 rounded ' +
                              (lang ? lang.cls : 'bg-bg-subtle text-fg-secondary') +
                              '">' +
                              esc(lang ? lang.label : lg) +
                              '</span>'
                          );
                      })
                      .join('') +
                  '</div></div>'
                : '') +
            '<div class="p-3 bg-bg-subtle rounded-xl">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">个人简介</p>' +
            '<p class="text-sm text-fg-primary leading-relaxed">' +
            esc(lawyer.bio || '暂无简介') +
            '</p>' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="mp-btn mp-btn-ghost" onclick="MarketplaceFn.closeLawyerDetail()">关闭</button>' +
            '<button class="mp-btn mp-btn-secondary" onclick="MarketplaceFn.closeLawyerDetail(); openCreateReferralModal(\'' +
            esc(lawyer.lawyer_id) +
            '\')">' +
            '<iconify-icon icon="mdi:share-variant" class="text-xs"></iconify-icon> 转介绍' +
            '</button>' +
            '<button class="mp-btn mp-btn-primary" onclick="MarketplaceFn.closeLawyerDetail(); openCreateCaseModal(\'' +
            esc(lawyer.lawyer_id) +
            '\')">' +
            '<iconify-icon icon="mdi:account-multiple-plus-outline" class="text-xs"></iconify-icon> 协同办案' +
            '</button>';

        if (_closeLawyerDetail) _closeLawyerDetail();
        _closeLawyerDetail = Utils.showModal({
            id: 'mp-lawyer-detail-modal',
            title: '律师详情',
            icon: 'mdi:account-tie',
            content: content,
            footer: footer,
            size: 'md'
        });
    }

    function closeLawyerDetail() {
        if (_closeLawyerDetail) {
            _closeLawyerDetail();
            _closeLawyerDetail = null;
        }
    }

    // ========================================================================
    // 14.6. 弹窗: 协同办案详情
    // ========================================================================

    function openCaseDetail(caseId) {
        var c = null;
        for (var i = 0; i < DEMO_CASES.length; i++) {
            if (DEMO_CASES[i].case_id === caseId) {
                c = DEMO_CASES[i];
                break;
            }
        }
        if (!c) {
            toast('未找到案件 ' + caseId, 'warning');
            return;
        }
        var state = findState(c.state);
        var type = CASE_TYPES.find(function (t) {
            return t.value === c.case_type;
        });

        var content =
            '<div class="space-y-4">' +
            '<div class="p-3 bg-bg-subtle rounded-xl">' +
            '<div class="flex items-center gap-2 flex-wrap mb-2">' +
            '<h3 class="text-sm font-semibold font-mono text-fg-primary">' +
            esc(c.case_id) +
            '</h3>' +
            '<span class="mp-state-pill ' +
            state.color +
            '">' +
            state.label +
            '</span>' +
            (type
                ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-bg-subtle text-fg-secondary">' +
                  esc(type.label) +
                  '</span>'
                : '') +
            '</div>' +
            '<p class="text-[12px] text-fg-secondary">' +
            esc(c.case_description || '') +
            '</p>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">律师 A</p>' +
            '<p class="text-sm font-semibold text-fg-primary">' +
            esc(c.lawyer_a_id) +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">律师 B</p>' +
            '<p class="text-sm font-semibold ' +
            (c.lawyer_b_id ? 'text-fg-primary' : 'text-warning') +
            '">' +
            esc(c.lawyer_b_id || '待接') +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">律师费</p>' +
            '<p class="text-sm font-semibold text-fg-primary">' +
            fmtMoney(c.fee) +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">分账比例</p>' +
            '<p class="text-sm font-semibold text-urgent">A ' +
            ((c.split_ratio || 0) * 100).toFixed(0) +
            '% / B ' +
            ((1 - (c.split_ratio || 0)) * 100).toFixed(0) +
            '%</p>' +
            '</div>' +
            '</div>' +
            (c.deadline
                ? '<div class="p-3 bg-wiki-tint rounded-xl"><p class="text-[11px] text-wiki mb-1">截止日期</p><p class="text-sm font-semibold text-wiki">' +
                  esc(c.deadline) +
                  '</p></div>'
                : '') +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-2">Marketplace 抽成</p>' +
            '<div class="flex items-center justify-between">' +
            '<span class="text-sm font-semibold text-brand">' +
            ((c.marketplace_commission_rate || 0) * 100).toFixed(0) +
            '%</span>' +
            '<span class="text-xs text-fg-tertiary">约 ' +
            fmtMoney((c.fee || 0) * (c.marketplace_commission_rate || 0)) +
            '</span>' +
            '</div>' +
            '</div>' +
            '<div class="bg-bg-subtle rounded-md p-3">' +
            renderStateStepBar(c.state) +
            '</div>' +
            (c.history && c.history.length > 0
                ? '<div class="space-y-2"><p class="text-xs font-medium text-fg-secondary">流程历史 (' +
                  c.history.length +
                  ' 条)</p><div class="mp-timeline">' +
                  c.history
                      .map(function (h) {
                          return (
                              '<div class="mp-timeline-item">' +
                              '<span class="mp-timeline-dot completed"></span>' +
                              '<div class="mp-timeline-title">' +
                              esc(h.from) +
                              ' → ' +
                              esc(h.to) +
                              '</div>' +
                              '<div class="mp-timeline-meta">' +
                              esc(h.actor) +
                              ' · ' +
                              esc(h.reason) +
                              ' · ' +
                              fmtDate(h.ts) +
                              '</div>' +
                              '</div>'
                          );
                      })
                      .join('') +
                  '</div></div>'
                : '') +
            '</div>';

        var footer =
            '<button class="mp-btn mp-btn-ghost" onclick="MarketplaceFn.closeCaseDetail()">关闭</button>' +
            '<button class="mp-btn mp-btn-primary" onclick="MarketplaceFn.closeCaseDetail(); openCreateCaseModal()">发布新协同</button>';

        if (_closeCaseDetail) _closeCaseDetail();
        _closeCaseDetail = Utils.showModal({
            id: 'mp-case-detail-modal',
            title: '协同办案详情',
            icon: 'mdi:briefcase',
            content: content,
            footer: footer,
            size: 'md'
        });
    }

    function closeCaseDetail() {
        if (_closeCaseDetail) {
            _closeCaseDetail();
            _closeCaseDetail = null;
        }
    }

    // ========================================================================
    // 14.7. 弹窗: 转介绍详情
    // ========================================================================

    function openReferralDetail(referralId) {
        var r = null;
        for (var i = 0; i < DEMO_REFERRALS.length; i++) {
            if (DEMO_REFERRALS[i].referral_id === referralId) {
                r = DEMO_REFERRALS[i];
                break;
            }
        }
        if (!r) {
            toast('未找到转介绍 ' + referralId, 'warning');
            return;
        }
        var status = findReferralStatus(r.status);
        var type = CASE_TYPES.find(function (t) {
            return t.value === r.case_type;
        });

        var content =
            '<div class="space-y-4">' +
            '<div class="p-3 bg-bg-subtle rounded-xl">' +
            '<div class="flex items-center gap-2 flex-wrap mb-2">' +
            '<span class="text-sm font-semibold font-mono text-fg-primary">' +
            esc(r.referral_id) +
            '</span>' +
            '<span class="text-[11px] ' +
            status.color +
            ' font-medium">● ' +
            status.label +
            '</span>' +
            (type
                ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-bg-subtle text-fg-secondary">' +
                  esc(type.label) +
                  '</span>'
                : '') +
            '</div>' +
            '<p class="text-[12px] text-fg-secondary">' +
            esc(r.case_description || '') +
            '</p>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">推荐人</p>' +
            '<p class="text-sm font-semibold text-fg-primary">' +
            esc(r.referrer_id) +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">被推荐律师</p>' +
            '<p class="text-sm font-semibold text-fg-primary">' +
            esc(r.target_lawyer_id) +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">预期律师费</p>' +
            '<p class="text-sm font-semibold text-fg-primary">' +
            fmtMoney(r.expected_fee) +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">实际律师费</p>' +
            '<p class="text-sm font-semibold ' +
            (r.actual_fee ? 'text-success' : 'text-fg-tertiary') +
            '">' +
            (r.actual_fee ? fmtMoney(r.actual_fee) : '待结算') +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-brand-tint rounded-lg">' +
            '<p class="text-[11px] text-brand mb-1">推荐人抽成</p>' +
            '<p class="text-sm font-semibold text-brand">' +
            (r.referrer_commission ? fmtMoney(r.referrer_commission) : '-') +
            '</p>' +
            '<p class="text-[10px] text-brand/70">费率 ' +
            ((r.commission_rate || 0) * 100).toFixed(0) +
            '%</p>' +
            '</div>' +
            '<div class="p-3 bg-wiki-tint rounded-lg">' +
            '<p class="text-[11px] text-wiki mb-1">Marketplace 抽成</p>' +
            '<p class="text-sm font-semibold text-wiki">' +
            fmtMoney(r.marketplace_commission || 0) +
            '</p>' +
            '<p class="text-[10px] text-wiki/70">平台不抽</p>' +
            '</div>' +
            '</div>' +
            (r.match_score
                ? '<div class="p-3 bg-white border border-bg-border rounded-lg"><div class="flex items-center justify-between"><span class="text-[11px] text-fg-tertiary">匹配评分</span><span class="text-lg font-bold text-brand">' +
                  (r.match_score * 100).toFixed(0) +
                  ' 分</span></div></div>'
                : '') +
            '<div class="text-[11px] text-fg-tertiary flex items-center justify-between">' +
            '<span>创建时间: ' +
            fmtDate(r.created_at) +
            '</span>' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="mp-btn mp-btn-ghost" onclick="MarketplaceFn.closeReferralDetail()">关闭</button>' +
            '<button class="mp-btn mp-btn-primary" onclick="MarketplaceFn.closeReferralDetail(); openCreateReferralModal()">新建转介绍</button>';

        if (_closeReferralDetail) _closeReferralDetail();
        _closeReferralDetail = Utils.showModal({
            id: 'mp-referral-detail-modal',
            title: '转介绍详情',
            icon: 'mdi:share-variant',
            content: content,
            footer: footer,
            size: 'md'
        });
    }

    function closeReferralDetail() {
        if (_closeReferralDetail) {
            _closeReferralDetail();
            _closeReferralDetail = null;
        }
    }

    // ========================================================================
    // 14.8. 弹窗: 跨境文件订单详情
    // ========================================================================

    function openCrossBorderDetail(jobId) {
        var j = null;
        for (var i = 0; i < DEMO_CROSS_BORDER_JOBS.length; i++) {
            if (DEMO_CROSS_BORDER_JOBS[i].job_id === jobId) {
                j = DEMO_CROSS_BORDER_JOBS[i];
                break;
            }
        }
        if (!j) {
            toast('未找到跨境订单 ' + jobId, 'warning');
            return;
        }
        var docType = findDocType(j.doc_type);
        var lang = findLanguage(j.language);
        var lawyerFee = (j.price || 0) - (j.marketplace_commission || 0);

        var statusBadge = '';
        if (j.status === 'completed')
            statusBadge = '<span class="text-[11px] text-success font-medium">● 已完成</span>';
        else if (j.status === 'in_progress')
            statusBadge = '<span class="text-[11px] text-brand font-medium">● 进行中</span>';
        else statusBadge = '<span class="text-[11px] text-fg-secondary font-medium">● ' + esc(j.status) + '</span>';

        var fieldsHtml = '';
        if (j.fields && Object.keys(j.fields).length > 0) {
            fieldsHtml =
                '<div class="p-3 bg-bg-subtle rounded-xl"><p class="text-[11px] text-fg-tertiary mb-2">文档字段</p><div class="space-y-1">';
            Object.keys(j.fields).forEach(function (k) {
                fieldsHtml +=
                    '<div class="flex items-center justify-between text-[12px]"><span class="text-fg-tertiary">' +
                    esc(k) +
                    '</span><span class="text-fg-primary font-medium">' +
                    esc(j.fields[k]) +
                    '</span></div>';
            });
            fieldsHtml += '</div></div>';
        }

        var content =
            '<div class="space-y-4">' +
            '<div class="p-3 bg-bg-subtle rounded-xl">' +
            '<div class="flex items-center gap-2 flex-wrap mb-2">' +
            '<span class="text-sm font-semibold font-mono text-fg-primary">' +
            esc(j.job_id) +
            '</span>' +
            statusBadge +
            '<span class="text-[10px] px-1.5 py-0.5 rounded ' +
            lang.cls +
            '">' +
            esc(lang.label) +
            '</span>' +
            '<span class="text-[10px] px-1.5 py-0.5 rounded bg-bg-subtle text-fg-secondary">' +
            esc(docType.label) +
            '</span>' +
            '</div>' +
            '<p class="text-[12px] text-fg-secondary">律师 ' +
            esc(j.lawyer_id) +
            ' → 客户 ' +
            esc(j.client_id) +
            '</p>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">司法辖区</p>' +
            '<p class="text-sm font-semibold text-fg-primary">' +
            esc(j.jurisdiction) +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">仲裁机构</p>' +
            '<p class="text-sm font-semibold text-urgent">' +
            esc(j.arbitration_institution || '-') +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">订单价格</p>' +
            '<div class="text-lg font-bold text-wiki">¥' +
            (j.price || 0) +
            '</div>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">律师所得</p>' +
            '<div class="text-lg font-bold text-success">¥' +
            lawyerFee.toFixed(1) +
            '</div>' +
            '</div>' +
            '</div>' +
            '<div class="p-3 bg-wiki-tint rounded-xl">' +
            '<div class="flex items-center justify-between mb-1">' +
            '<span class="text-[11px] text-wiki">Marketplace 抽成 (30%)</span>' +
            '<span class="text-sm font-semibold text-wiki">¥' +
            (j.marketplace_commission || 0).toFixed(1) +
            '</span>' +
            '</div>' +
            '<div class="flex items-center justify-between">' +
            '<span class="text-[11px] text-wiki/70">Skill 3 v3.0 模板</span>' +
            '<span class="text-xs font-mono text-wiki">' +
            esc(j.template_id || '-') +
            '</span>' +
            '</div>' +
            '</div>' +
            fieldsHtml +
            (j.document_url
                ? '<a class="flex items-center justify-between p-3 bg-brand-tint rounded-xl hover:bg-brand/10 transition-colors" href="' +
                  esc(j.document_url) +
                  '">' +
                  '<div class="flex items-center gap-2">' +
                  '<iconify-icon icon="mdi:file-document-outline" class="text-brand text-lg"></iconify-icon>' +
                  '<span class="text-sm font-medium text-brand">下载生成文件</span>' +
                  '</div>' +
                  '<iconify-icon icon="mdi:download" class="text-brand"></iconify-icon>' +
                  '</a>'
                : '<div class="p-3 bg-bg-subtle rounded-xl text-center"><iconify-icon icon="mdi:clock-outline" class="text-fg-tertiary text-lg mb-1"></iconify-icon><p class="text-[11px] text-fg-tertiary">文件生成中, 请稍候...</p></div>') +
            '<div class="text-[11px] text-fg-tertiary">' +
            '创建时间: ' +
            fmtDate(j.created_at) +
            '</div>' +
            '</div>';

        var footer =
            '<button class="mp-btn mp-btn-ghost" onclick="MarketplaceFn.closeCrossBorderDetail()">关闭</button>' +
            '<button class="mp-btn mp-btn-primary" onclick="MarketplaceFn.closeCrossBorderDetail(); openCreateCrossBorderModal()">新建订单</button>';

        if (_closeCrossBorderDetail) _closeCrossBorderDetail();
        _closeCrossBorderDetail = Utils.showModal({
            id: 'mp-cb-detail-modal',
            title: '跨境文件订单详情',
            icon: 'mdi:earth',
            content: content,
            footer: footer,
            size: 'md'
        });
    }

    function closeCrossBorderDetail() {
        if (_closeCrossBorderDetail) {
            _closeCrossBorderDetail();
            _closeCrossBorderDetail = null;
        }
    }

    // ========================================================================
    // 15. 弹窗: 创建转介绍 (复用 modal 模板)
    // ========================================================================

    function openCreateReferralModal(prefilledLawyerId) {
        var modal = document.getElementById('mp-referral-modal');
        if (!modal) {
            // 动态插入
            modal = document.createElement('div');
            modal.id = 'mp-referral-modal';
            modal.className = 'fixed inset-0 z-[1000] flex items-center justify-center bg-black/40 hidden';
            modal.innerHTML =
                '' +
                '<div class="bg-white rounded-xl w-full max-w-md mx-4 shadow-2xl">' +
                '<div class="p-5 border-b border-bg-border flex items-center justify-between">' +
                '<h3 class="text-base font-semibold flex items-center gap-2">' +
                '<iconify-icon icon="mdi:share-variant" class="text-brand"></iconify-icon>' +
                '创建转介绍' +
                '</h3>' +
                '<button class="text-fg-tertiary hover:text-fg-primary" onclick="document.getElementById(\'mp-referral-modal\').classList.add(\'hidden\')">' +
                '<iconify-icon icon="mdi:close" class="text-lg"></iconify-icon>' +
                '</button>' +
                '</div>' +
                '<div class="p-5 space-y-3">' +
                '<div><label class="mp-label">被推荐律师 ID</label><input id="mp-modal-referral-target" class="mp-input" placeholder="L006" value="' +
                esc(prefilledLawyerId || '') +
                '"></div>' +
                '<div><label class="mp-label">案件类型</label><select id="mp-modal-referral-case-type" class="mp-input">' +
                CASE_TYPES.map(function (t) {
                    return '<option value="' + t.value + '">' + t.label + '</option>';
                }).join('') +
                '</select></div>' +
                '<div><label class="mp-label">案件描述</label><textarea id="mp-modal-referral-desc" class="mp-input" rows="3" placeholder="客户跨境仲裁案, 推荐给吴律师"></textarea></div>' +
                '<div><label class="mp-label">预期律师费 (¥)</label><input id="mp-modal-referral-fee" type="number" class="mp-input" placeholder="50000"></div>' +
                '</div>' +
                '<div class="p-4 border-t border-bg-border flex items-center justify-end gap-2">' +
                '<button class="mp-btn mp-btn-ghost" onclick="document.getElementById(\'mp-referral-modal\').classList.add(\'hidden\')">取消</button>' +
                '<button class="mp-btn mp-btn-primary" id="mp-modal-referral-submit">提交</button>' +
                '</div>' +
                '</div>';
            document.body.appendChild(modal);
            modal.querySelector('#mp-modal-referral-submit').addEventListener('click', function () {
                var body = {
                    referrer_id: MarketplaceState.currentLawyerId || 'L001',
                    target_lawyer_id: modal.querySelector('#mp-modal-referral-target').value.trim(),
                    case_type: modal.querySelector('#mp-modal-referral-case-type').value,
                    case_description: modal.querySelector('#mp-modal-referral-desc').value.trim(),
                    expected_fee: parseFloat(modal.querySelector('#mp-modal-referral-fee').value) || 0
                };
                if (!body.target_lawyer_id || !body.case_description || !body.expected_fee) {
                    toast('请填写完整信息', 'warning');
                    return;
                }
                MarketplaceAPI.createReferral(body).then(function (res) {
                    if (res.ok) {
                        toast('转介绍创建成功, referral_id=' + (res.data && res.data.referral_id), 'success');
                        modal.classList.add('hidden');
                    } else {
                        toast(
                            '创建失败: ' + ((res.data && (res.data.detail || res.data.error)) || res.status),
                            'error'
                        );
                    }
                });
            });
        }
        modal.classList.remove('hidden');
    }

    // ========================================================================
    // 16. 弹窗: 创建协同办案
    // ========================================================================

    function openCreateCaseModal(prefilledLawyerId) {
        var modal = document.getElementById('mp-case-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'mp-case-modal';
            modal.className = 'fixed inset-0 z-[1000] flex items-center justify-center bg-black/40 hidden';
            modal.innerHTML =
                '' +
                '<div class="bg-white rounded-xl w-full max-w-md mx-4 shadow-2xl">' +
                '<div class="p-5 border-b border-bg-border flex items-center justify-between">' +
                '<h3 class="text-base font-semibold flex items-center gap-2">' +
                '<iconify-icon icon="mdi:account-multiple-plus-outline" class="text-brand"></iconify-icon>' +
                '发布协同办案' +
                '</h3>' +
                '<button class="text-fg-tertiary hover:text-fg-primary" onclick="document.getElementById(\'mp-case-modal\').classList.add(\'hidden\')">' +
                '<iconify-icon icon="mdi:close" class="text-lg"></iconify-icon>' +
                '</button>' +
                '</div>' +
                '<div class="p-5 space-y-3">' +
                '<div><label class="mp-label">邀请律师 B (可选)</label><input id="mp-modal-case-lawyer-b" class="mp-input" placeholder="L006" value="' +
                esc(prefilledLawyerId || '') +
                '"></div>' +
                '<div><label class="mp-label">案件类型</label><select id="mp-modal-case-type" class="mp-input">' +
                CASE_TYPES.map(function (t) {
                    return '<option value="' + t.value + '">' + t.label + '</option>';
                }).join('') +
                '</select></div>' +
                '<div><label class="mp-label">案件描述</label><textarea id="mp-modal-case-desc" class="mp-input" rows="3" placeholder="跨境合同纠纷, 标的 ¥500,000"></textarea></div>' +
                '<div class="grid grid-cols-2 gap-3">' +
                '<div><label class="mp-label">律师费 (¥)</label><input id="mp-modal-case-fee" type="number" class="mp-input" placeholder="50000"></div>' +
                '<div><label class="mp-label">分账比例 A/B</label><input id="mp-modal-case-split" type="number" min="0" max="100" class="mp-input" placeholder="60" value="60"></div>' +
                '</div>' +
                '<div><label class="mp-label">截止日期 (可选)</label><input id="mp-modal-case-deadline" type="date" class="mp-input"></div>' +
                '</div>' +
                '<div class="p-4 border-t border-bg-border flex items-center justify-end gap-2">' +
                '<button class="mp-btn mp-btn-ghost" onclick="document.getElementById(\'mp-case-modal\').classList.add(\'hidden\')">取消</button>' +
                '<button class="mp-btn mp-btn-primary" id="mp-modal-case-submit">发布</button>' +
                '</div>' +
                '</div>';
            document.body.appendChild(modal);
            modal.querySelector('#mp-modal-case-submit').addEventListener('click', function () {
                var splitPct = parseFloat(modal.querySelector('#mp-modal-case-split').value) || 50;
                var body = {
                    lawyer_a_id: MarketplaceState.currentLawyerId || 'L001',
                    lawyer_b_id: modal.querySelector('#mp-modal-case-lawyer-b').value.trim() || null,
                    case_type: modal.querySelector('#mp-modal-case-type').value,
                    case_description: modal.querySelector('#mp-modal-case-desc').value.trim(),
                    fee: parseFloat(modal.querySelector('#mp-modal-case-fee').value) || 0,
                    split_ratio: splitPct / 100,
                    deadline: modal.querySelector('#mp-modal-case-deadline').value || null
                };
                if (!body.case_description || !body.fee) {
                    toast('请填写案件描述和律师费', 'warning');
                    return;
                }
                MarketplaceAPI.createCase(body).then(function (res) {
                    if (res.ok) {
                        toast('协同办案发布成功, case_id=' + (res.data && res.data.case_id), 'success');
                        modal.classList.add('hidden');
                    } else {
                        toast(
                            '发布失败: ' + ((res.data && (res.data.detail || res.data.error)) || res.status),
                            'error'
                        );
                    }
                });
            });
        }
        modal.classList.remove('hidden');
    }

    // ========================================================================
    // 17. 弹窗: 创建跨境文件订单
    // ========================================================================

    function openCreateCrossBorderModal() {
        var modal = document.getElementById('mp-cb-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'mp-cb-modal';
            modal.className = 'fixed inset-0 z-[1000] flex items-center justify-center bg-black/40 hidden';
            modal.innerHTML =
                '' +
                '<div class="bg-white rounded-xl w-full max-w-md mx-4 shadow-2xl">' +
                '<div class="p-5 border-b border-bg-border flex items-center justify-between">' +
                '<h3 class="text-base font-semibold flex items-center gap-2">' +
                '<iconify-icon icon="mdi:earth" class="text-wiki"></iconify-icon>' +
                '创建跨境文件订单' +
                '</h3>' +
                '<button class="text-fg-tertiary hover:text-fg-primary" onclick="document.getElementById(\'mp-cb-modal\').classList.add(\'hidden\')">' +
                '<iconify-icon icon="mdi:close" class="text-lg"></iconify-icon>' +
                '</button>' +
                '</div>' +
                '<div class="p-5 space-y-3">' +
                '<div><label class="mp-label">国际客户 ID</label><input id="mp-modal-cb-client" class="mp-input" placeholder="client-us-001"></div>' +
                '<div><label class="mp-label">文档类型</label><select id="mp-modal-cb-doc-type" class="mp-input">' +
                CROSS_BORDER_DOC_TYPES.map(function (t) {
                    return '<option value="' + t.value + '">' + t.label + '</option>';
                }).join('') +
                '</select></div>' +
                '<div><label class="mp-label">语言</label><select id="mp-modal-cb-language" class="mp-input">' +
                LANGUAGES.map(function (l) {
                    return '<option value="' + l.value + '">' + l.label + '</option>';
                }).join('') +
                '</select></div>' +
                '<div><label class="mp-label">司法管辖区</label><select id="mp-modal-cb-jurisdiction" class="mp-input">' +
                JURISDICTIONS.map(function (j) {
                    return '<option value="' + j.value + '">' + j.label + '</option>';
                }).join('') +
                '</select></div>' +
                '<div><label class="mp-label">Skill 3 v3.0 模板 ID (可选)</label><input id="mp-modal-cb-template" class="mp-input" placeholder="skill3-letter-v3-en"></div>' +
                '<div class="mp-disclaimer-short">跨境文件 30% Marketplace 抽成, 70% 律师得</div>' +
                '</div>' +
                '<div class="p-4 border-t border-bg-border flex items-center justify-end gap-2">' +
                '<button class="mp-btn mp-btn-ghost" onclick="document.getElementById(\'mp-cb-modal\').classList.add(\'hidden\')">取消</button>' +
                '<button class="mp-btn mp-btn-primary" id="mp-modal-cb-submit">提交</button>' +
                '</div>' +
                '</div>';
            document.body.appendChild(modal);
            modal.querySelector('#mp-modal-cb-submit').addEventListener('click', function () {
                var body = {
                    lawyer_id: MarketplaceState.currentLawyerId || 'L001',
                    client_id: modal.querySelector('#mp-modal-cb-client').value.trim(),
                    doc_type: modal.querySelector('#mp-modal-cb-doc-type').value,
                    language: modal.querySelector('#mp-modal-cb-language').value,
                    jurisdiction: modal.querySelector('#mp-modal-cb-jurisdiction').value,
                    template_id: modal.querySelector('#mp-modal-cb-template').value.trim() || null,
                    fields: { recipient: '', amount: 0 }
                };
                if (!body.client_id) {
                    toast('请填写国际客户 ID', 'warning');
                    return;
                }
                MarketplaceAPI.createCrossBorder(body).then(function (res) {
                    if (res.ok) {
                        toast(
                            '跨境文件订单创建成功, job_id=' +
                                (res.data && res.data.job_id) +
                                ', 价格 ¥' +
                                (res.data && res.data.price),
                            'success'
                        );
                        modal.classList.add('hidden');
                    } else {
                        toast(
                            '创建失败: ' + ((res.data && (res.data.detail || res.data.error)) || res.status),
                            'error'
                        );
                    }
                });
            });
        }
        modal.classList.remove('hidden');
    }

    // ========================================================================
    // 18. 暴露到全局 (IIFE 双绑定模式, 跟 W11 router.js / contract-review.js 一致)
    // ========================================================================

    globalThis.MarketplaceAPI = MarketplaceAPI;
    globalThis.MarketplaceState = MarketplaceState;
    globalThis.MarketplaceData = {
        CASE_TYPES: CASE_TYPES,
        CO_COUNSEL_STATES: CO_COUNSEL_STATES,
        REFERRAL_STATUSES: REFERRAL_STATUSES,
        CROSS_BORDER_DOC_TYPES: CROSS_BORDER_DOC_TYPES,
        LANGUAGES: LANGUAGES,
        JURISDICTIONS: JURISDICTIONS,
        AVAILABILITY: AVAILABILITY
    };
    globalThis.MarketplaceFn = {
        initLawyersView: initLawyersView,
        initCasesView: initCasesView,
        initReferralsView: initReferralsView,
        initCrossBorderView: initCrossBorderView,
        initMetricsView: initMetricsView,
        initMatchView: initMatchView,
        openLawyerDetail: openLawyerDetail,
        closeLawyerDetail: closeLawyerDetail,
        openCaseDetail: openCaseDetail,
        closeCaseDetail: closeCaseDetail,
        openReferralDetail: openReferralDetail,
        closeReferralDetail: closeReferralDetail,
        openCrossBorderDetail: openCrossBorderDetail,
        closeCrossBorderDetail: closeCrossBorderDetail,
        openCreateReferralModal: openCreateReferralModal,
        openCreateCaseModal: openCreateCaseModal,
        openCreateCrossBorderModal: openCreateCrossBorderModal,
        openMatchDetail: openMatchDetail,
        closeMatchDetail: closeMatchDetail,
        computeMatchScore: computeMatchScore,
        rankLawyers: rankLawyers,
        renderStateStepBar: renderStateStepBar,
        renderDimBars: renderDimBars,
        matchLawyersV2: matchLawyersV2,
        getMatchExplanationV2: getMatchExplanationV2,
        renderMatchResults: renderMatchResults,
        renderMatchResultCard: renderMatchResultCard,
        renderMatchRadarChart: renderMatchRadarChart,
        renderMatchDimensionBars: renderMatchDimensionBars,
        retryMatchSearch: retryMatchSearch,
        goToMatchPage: goToMatchPage
    };
})();
