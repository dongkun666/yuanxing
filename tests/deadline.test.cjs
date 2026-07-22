'use strict';

const assert = require('assert');
const { describe, it } = require('node:test');

// ===== 从 deadline.js 提取的纯函数逻辑（IIFE 内部无法直接 require，复制核心算法测试） =====

function addDays(date, days) {
    var d = new Date(date);
    d.setDate(d.getDate() + days);
    return d;
}

function addMonths(date, months) {
    var d = new Date(date);
    var targetMonth = d.getMonth() + months;
    d.setMonth(targetMonth);
    if (d.getMonth() !== (targetMonth % 12 + 12) % 12) {
        d.setDate(0);
    }
    return d;
}

function addYears(date, years) {
    var d = new Date(date);
    d.setFullYear(d.getFullYear() + years);
    return d;
}

function calculateDeadline(rule, baseDate) {
    var result;
    if (rule.unit === 'day') {
        result = addDays(baseDate, rule.days);
    } else if (rule.unit === 'month') {
        result = addMonths(baseDate, rule.days);
    } else if (rule.unit === 'year') {
        result = addYears(baseDate, rule.days);
    }
    return result;
}

function formatDate(date) {
    var d = new Date(date);
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var dd = String(d.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + dd;
}

function getDeadlineStatus(deadlineDate, today) {
    if (!deadlineDate) return 'unknown';
    var diffMs = new Date(deadlineDate) - today;
    var diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays < 0) return 'overdue';
    if (diffDays === 0) return 'today';
    if (diffDays <= 3) return 'urgent';
    if (diffDays <= 7) return 'critical';
    if (diffDays <= 30) return 'warning';
    return 'normal';
}

function getStatusConfig(status) {
    var map = {
        'overdue': { label: '已过期', cls: 'bg-red-100 text-red-700 border-red-200', icon: 'mdi:alert-circle', color: 'red' },
        'today': { label: '今天到期', cls: 'bg-red-100 text-red-700 border-red-200', icon: 'mdi:alarm', color: 'red' },
        'urgent': { label: '3 天内', cls: 'bg-orange-100 text-orange-700 border-orange-200', icon: 'mdi:clock-alert', color: 'orange' },
        'critical': { label: '一周内', cls: 'bg-amber-100 text-amber-700 border-amber-200', icon: 'mdi:clock', color: 'amber' },
        'warning': { label: '一月内', cls: 'bg-blue-100 text-blue-700 border-blue-200', icon: 'mdi:clock-outline', color: 'blue' },
        'normal': { label: '远期', cls: 'bg-gray-100 text-gray-600 border-gray-200', icon: 'mdi:calendar-outline', color: 'gray' },
        'unknown': { label: '未知', cls: 'bg-gray-100 text-gray-500 border-gray-200', icon: 'mdi:help', color: 'gray' }
    };
    return map[status] || map['normal'];
}

// ===== 测试 =====

describe('deadline.js - addDays', function() {
    it('should add days correctly', function() {
        var base = new Date('2026-06-15');
        var result = addDays(base, 15);
        assert.strictEqual(formatDate(result), '2026-06-30');
    });

    it('should add days across month boundary', function() {
        var base = new Date('2026-06-20');
        var result = addDays(base, 15);
        assert.strictEqual(formatDate(result), '2026-07-05');
    });

    it('should add zero days', function() {
        var base = new Date('2026-06-15');
        var result = addDays(base, 0);
        assert.strictEqual(formatDate(result), '2026-06-15');
    });
});

describe('deadline.js - addMonths', function() {
    it('should add months correctly', function() {
        var base = new Date('2026-01-15');
        var result = addMonths(base, 6);
        assert.strictEqual(formatDate(result), '2026-07-15');
    });

    it('should handle month-end overflow (Jan 31 + 1 month = Feb 28)', function() {
        var base = new Date('2026-01-31');
        var result = addMonths(base, 1);
        assert.strictEqual(formatDate(result), '2026-02-28');
    });

    it('should handle month-end overflow (Mar 31 + 1 month = Apr 30)', function() {
        var base = new Date('2026-03-31');
        var result = addMonths(base, 1);
        assert.strictEqual(formatDate(result), '2026-04-30');
    });

    it('should add months across year boundary', function() {
        var base = new Date('2026-10-15');
        var result = addMonths(base, 6);
        assert.strictEqual(formatDate(result), '2027-04-15');
    });
});

describe('deadline.js - addYears', function() {
    it('should add years correctly', function() {
        var base = new Date('2026-06-15');
        var result = addYears(base, 2);
        assert.strictEqual(formatDate(result), '2028-06-15');
    });

    it('should add 5 years', function() {
        var base = new Date('2026-06-15');
        var result = addYears(base, 5);
        assert.strictEqual(formatDate(result), '2031-06-15');
    });

    it('should add years for normal dates', function() {
        var base = new Date('2026-06-15');
        var result = addYears(base, 10);
        assert.strictEqual(formatDate(result), '2036-06-15');
    });
});

describe('deadline.js - calculateDeadline', function() {
    it('should calculate day-unit deadline', function() {
        var rule = { days: 15, unit: 'day' };
        var base = new Date('2026-06-15');
        var result = calculateDeadline(rule, base);
        assert.strictEqual(formatDate(result), '2026-06-30');
    });

    it('should calculate month-unit deadline', function() {
        var rule = { days: 6, unit: 'month' };
        var base = new Date('2026-01-15');
        var result = calculateDeadline(rule, base);
        assert.strictEqual(formatDate(result), '2026-07-15');
    });

    it('should calculate year-unit deadline', function() {
        var rule = { days: 2, unit: 'year' };
        var base = new Date('2026-06-15');
        var result = calculateDeadline(rule, base);
        assert.strictEqual(formatDate(result), '2028-06-15');
    });

    it('should calculate zero-day deadline (immediate)', function() {
        var rule = { days: 0, unit: 'day' };
        var base = new Date('2026-06-15');
        var result = calculateDeadline(rule, base);
        assert.strictEqual(formatDate(result), '2026-06-15');
    });
});

describe('deadline.js - getDeadlineStatus', function() {
    it('should return "overdue" for past deadline', function() {
        var deadline = new Date('2026-01-01');
        var today = new Date('2026-06-15');
        assert.strictEqual(getDeadlineStatus(deadline, today), 'overdue');
    });

    it('should return "today" for same-day deadline', function() {
        var deadline = new Date('2026-06-15');
        var today = new Date('2026-06-15');
        assert.strictEqual(getDeadlineStatus(deadline, today), 'today');
    });

    it('should return "urgent" for deadline within 3 days', function() {
        var deadline = new Date('2026-06-18');
        var today = new Date('2026-06-15');
        assert.strictEqual(getDeadlineStatus(deadline, today), 'urgent');
    });

    it('should return "critical" for deadline within 7 days', function() {
        var deadline = new Date('2026-06-22');
        var today = new Date('2026-06-15');
        assert.strictEqual(getDeadlineStatus(deadline, today), 'critical');
    });

    it('should return "warning" for deadline within 30 days', function() {
        var deadline = new Date('2026-07-10');
        var today = new Date('2026-06-15');
        assert.strictEqual(getDeadlineStatus(deadline, today), 'warning');
    });

    it('should return "normal" for far future deadline', function() {
        var deadline = new Date('2026-12-15');
        var today = new Date('2026-06-15');
        assert.strictEqual(getDeadlineStatus(deadline, today), 'normal');
    });

    it('should return "unknown" for null deadline', function() {
        assert.strictEqual(getDeadlineStatus(null, new Date()), 'unknown');
    });
});

describe('deadline.js - getStatusConfig', function() {
    it('should return config for each known status', function() {
        var statuses = ['overdue', 'today', 'urgent', 'critical', 'warning', 'normal', 'unknown'];
        statuses.forEach(function(status) {
            var cfg = getStatusConfig(status);
            assert.ok(cfg.label, 'status "' + status + '" should have a label');
            assert.ok(cfg.cls, 'status "' + status + '" should have a cls');
            assert.ok(cfg.icon, 'status "' + status + '" should have an icon');
            assert.ok(cfg.color, 'status "' + status + '" should have a color');
        });
    });

    it('should return "normal" config for unknown status string', function() {
        var cfg = getStatusConfig('nonexistent');
        assert.strictEqual(cfg.label, '远期');
    });
});

describe('deadline.js - formatDate', function() {
    it('should format date as YYYY-MM-DD', function() {
        var d = new Date('2026-01-05');
        assert.strictEqual(formatDate(d), '2026-01-05');
    });

    it('should pad single-digit month and day', function() {
        var d = new Date('2026-03-09');
        assert.strictEqual(formatDate(d), '2026-03-09');
    });
});

describe('deadline.js - globalThis exposure', function() {
    it('should expose core functions to globalThis after loading module', function() {
        globalThis.document = {
            getElementById: function() { return null; },
            querySelector: function() { return null; },
            querySelectorAll: function() { return []; },
            body: { observe: function() {} },
            addEventListener: function() {},
            removeEventListener: function() {}
        };
        globalThis.window = { location: {} };
        globalThis.MutationObserver = function() { return { observe: function() {} }; };
        // navigator 在 Node 中为只读属性, 使用 Object.defineProperty 覆盖
        Object.defineProperty(globalThis, 'navigator', {
            value: { clipboard: null },
            writable: true,
            configurable: true
        });
        globalThis.console = { error: function() {}, log: function() {} };
        globalThis.escapeHtml = function(s) { return s; };
        globalThis.showToast = function() {};

        require('../assets/js/deadline.js');

        assert.ok(typeof globalThis.selectDeadlineCaseType === 'function', 'selectDeadlineCaseType should be a function');
        assert.ok(typeof globalThis.setDeadlineDate === 'function', 'setDeadlineDate should be a function');
        assert.ok(typeof globalThis.recalculateDeadlines === 'function', 'recalculateDeadlines should be a function');
        assert.ok(typeof globalThis.copyDeadlineDate === 'function', 'copyDeadlineDate should be a function');
        assert.ok(typeof globalThis.initDeadlineView === 'function', 'initDeadlineView should be a function');
    });
});
