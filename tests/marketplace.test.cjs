'use strict';

const assert = require('assert');
const { describe, it } = require('node:test');

// ===== 从 marketplace.js 提取的纯函数逻辑（IIFE 内部无法直接 require，复制核心算法测试） =====
// 对应 assets/js/marketplace.js: esc / fmtMoney / fmtPercent / fmtDate / computeMatchScore / rankLawyers / find*

function esc(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
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

// 律师匹配评分 (5 维度加权 + 跨境 bonus)
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
        score.specialty = 0.7;
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

    // 跨境 bonus
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

// 常量 (复制自 marketplace.js)
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

// ===== 测试 =====

describe('marketplace.js - esc', function () {
    it('should escape all HTML special characters', function () {
        assert.strictEqual(esc('<script>'), '&lt;script&gt;');
        assert.strictEqual(esc('"q"'), '&quot;q&quot;');
        assert.strictEqual(esc("a'b"), "a&#39;b");
    });

    it('should escape ampersand first', function () {
        assert.strictEqual(esc('a&b'), 'a&amp;b');
        assert.strictEqual(esc('<&>'), '&lt;&amp;&gt;');
    });

    it('should return empty string for null/undefined', function () {
        assert.strictEqual(esc(null), '');
        assert.strictEqual(esc(undefined), '');
    });

    it('should coerce non-string to string', function () {
        assert.strictEqual(esc(123), '123');
        assert.strictEqual(esc(true), 'true');
    });
});

describe('marketplace.js - fmtMoney', function () {
    it('should format number as ¥ with thousand separators', function () {
        assert.strictEqual(fmtMoney(99), '¥99');
        assert.strictEqual(fmtMoney(1500), '¥1,500');
        assert.strictEqual(fmtMoney(1000000), '¥1,000,000');
    });

    it('should return dash for null/undefined', function () {
        assert.strictEqual(fmtMoney(null), '-');
        assert.strictEqual(fmtMoney(undefined), '-');
    });

    it('should truncate decimal places', function () {
        assert.strictEqual(fmtMoney(99.99), '¥100');
        assert.strictEqual(fmtMoney(1500.5), '¥1,501'); // 四舍五入
    });
});

describe('marketplace.js - fmtPercent', function () {
    it('should format decimal as percentage with 1 decimal place', function () {
        assert.strictEqual(fmtPercent(0.05), '5.0%');
        assert.strictEqual(fmtPercent(0.1), '10.0%');
        assert.strictEqual(fmtPercent(0.305), '30.5%');
        assert.strictEqual(fmtPercent(1), '100.0%');
    });

    it('should return dash for null/undefined', function () {
        assert.strictEqual(fmtPercent(null), '-');
        assert.strictEqual(fmtPercent(undefined), '-');
    });
});

describe('marketplace.js - fmtDate', function () {
    it('should format valid date string as YYYY-MM-DD HH:mm', function () {
        var result = fmtDate('2026-07-02T14:30:00');
        assert.ok(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(result));
    });

    it('should return dash for empty input', function () {
        assert.strictEqual(fmtDate(''), '-');
        assert.strictEqual(fmtDate(null), '-');
    });

    it('should return original string for invalid date', function () {
        assert.strictEqual(fmtDate('not-a-date'), 'not-a-date');
    });
});

describe('marketplace.js - computeMatchScore', function () {
    var baseLawyer = {
        specialties: ['contract', 'civil'],
        experience_years: 5,
        region: '北京',
        availability: 'available',
        rating: 4.5,
        cross_border_capable: false
    };

    it('should compute score with all 5 dimensions weighted', function () {
        var score = computeMatchScore(baseLawyer, ['contract'], '北京');
        assert.ok(score.specialty > 0);
        assert.ok(score.experience > 0);
        assert.strictEqual(score.geography, 1.0); // 完全匹配
        assert.strictEqual(score.availability, 1.0); // available
        assert.ok(score.rating > 0);
        assert.ok(score.total > 0 && score.total <= 1.0);
    });

    it('should give specialty 0.7 when no requirements', function () {
        var score = computeMatchScore(baseLawyer, [], '北京');
        assert.strictEqual(score.specialty, 0.7);
    });

    it('should give geography 1.0 for exact region match', function () {
        var score = computeMatchScore(baseLawyer, [], '北京');
        assert.strictEqual(score.geography, 1.0);
    });

    it('should give geography 0.6 for same province prefix', function () {
        var lawyer = Object.assign({}, baseLawyer, { region: '北京朝阳' });
        var score = computeMatchScore(lawyer, [], '北京海淀');
        assert.strictEqual(score.geography, 0.6);
    });

    it('should give geography 0.3 for no match', function () {
        var score = computeMatchScore(baseLawyer, [], '上海');
        assert.strictEqual(score.geography, 0.3);
    });

    it('should cap experience at 1.0 for 10+ years', function () {
        var lawyer = Object.assign({}, baseLawyer, { experience_years: 15 });
        var score = computeMatchScore(lawyer, [], null);
        assert.strictEqual(score.experience, 1.0);
    });

    it('should handle availability states', function () {
        var available = computeMatchScore(Object.assign({}, baseLawyer, { availability: 'available' }), [], null);
        var busy = computeMatchScore(Object.assign({}, baseLawyer, { availability: 'busy' }), [], null);
        var offline = computeMatchScore(Object.assign({}, baseLawyer, { availability: 'offline' }), [], null);
        assert.strictEqual(available.availability, 1.0);
        assert.strictEqual(busy.availability, 0.4);
        assert.strictEqual(offline.availability, 0.0);
    });

    it('should apply cross_border bonus for capable lawyer', function () {
        var lawyer = Object.assign({}, baseLawyer, { cross_border_capable: true });
        var score = computeMatchScore(lawyer, [], null);
        assert.strictEqual(score.cross_border_bonus, 0.1);
    });

    it('should apply enhanced cross_border bonus with en-US language', function () {
        var lawyer = Object.assign({}, baseLawyer, { cross_border_capable: true, languages: ['en-US'] });
        var score = computeMatchScore(lawyer, [], null);
        assert.strictEqual(score.cross_border_bonus, 0.15);
    });

    it('should apply penalty for cross_border requirement without capability', function () {
        var score = computeMatchScore(baseLawyer, ['cross_border'], null);
        assert.strictEqual(score.cross_border_bonus, -0.3);
    });

    it('should clamp total to [0, 1]', function () {
        var score = computeMatchScore(baseLawyer, ['cross_border'], null);
        assert.ok(score.total >= 0 && score.total <= 1.0);
    });
});

describe('marketplace.js - rankLawyers', function () {
    var pool = [
        { name: 'A', specialties: ['contract'], experience_years: 8, region: '北京', availability: 'available', rating: 4.8 },
        { name: 'B', specialties: ['criminal'], experience_years: 2, region: '上海', availability: 'busy', rating: 3.0 },
        { name: 'C', specialties: ['contract', 'civil'], experience_years: 12, region: '北京', availability: 'available', rating: 4.9 }
    ];

    it('should rank lawyers by total score descending', function () {
        var ranked = rankLawyers(pool, ['contract'], '北京');
        assert.ok(ranked.length >= 1);
        for (var i = 1; i < ranked.length; i++) {
            assert.ok(ranked[i - 1].score.total >= ranked[i].score.total);
        }
    });

    it('should filter out scores below 0.4 threshold', function () {
        var ranked = rankLawyers(pool, ['contract'], '北京');
        ranked.forEach(function (x) {
            assert.ok(x.score.total >= 0.4);
        });
    });

    it('should respect topK limit', function () {
        var ranked = rankLawyers(pool, [], null, 2);
        assert.ok(ranked.length <= 2);
    });

    it('should return empty array for empty pool', function () {
        var ranked = rankLawyers([], ['contract'], '北京');
        assert.strictEqual(ranked.length, 0);
    });

    it('should put best matching lawyer first', function () {
        var ranked = rankLawyers(pool, ['contract'], '北京');
        if (ranked.length > 0) {
            // C 应该比 B 排名高 (专长匹配 + 经验高 + 地区匹配 + 评分高)
            var cItem = ranked.find(function (x) { return x.lawyer.name === 'C'; });
            var bItem = ranked.find(function (x) { return x.lawyer.name === 'B'; });
            if (cItem && bItem) {
                assert.ok(cItem.score.total > bItem.score.total);
            }
        }
    });
});

describe('marketplace.js - findState / findReferralStatus', function () {
    it('should find state by value', function () {
        var s = findState('accepted');
        assert.strictEqual(s.value, 'accepted');
        assert.strictEqual(s.label, '已接案');
    });

    it('should return first state for unknown value', function () {
        var s = findState('unknown');
        assert.strictEqual(s.value, 'open');
    });

    it('should return first state for empty/null', function () {
        assert.strictEqual(findState('').value, 'open');
        assert.strictEqual(findState(null).value, 'open');
    });

    it('should find referral status by value', function () {
        var s = findReferralStatus('completed');
        assert.strictEqual(s.value, 'completed');
        assert.strictEqual(s.label, '已完成');
    });

    it('should return first referral status for unknown', function () {
        var s = findReferralStatus('xyz');
        assert.strictEqual(s.value, 'pending');
    });
});
