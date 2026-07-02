'use strict';

const assert = require('assert');
const { describe, it } = require('node:test');

// ===== 从 schedule.js 提取的纯函数逻辑（全局函数无法直接 require，复制核心算法测试） =====
// 对应 assets/js/schedule.js: parseDateStr / formatDate / formatDateLabel / getFutureDate / checkScheduleConflict / getScheduleFilterPredicate

// 把 'YYYY-MM-DD' 解析成 Date (本地时间), 空值返回当前时间
function parseDateStr(s) {
    if (!s) return new Date();
    var parts = s.split('-');
    return new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
}

// Date -> 'YYYY-MM-DD'
function formatDate(d) {
    return (
        d.getFullYear() +
        '-' +
        String(d.getMonth() + 1).padStart(2, '0') +
        '-' +
        String(d.getDate()).padStart(2, '0')
    );
}

// 'YYYY-MM-DD' -> 'YYYY年M月D日' (去掉前导零)
function formatDateLabel(dateStr) {
    var parts = dateStr.split('-');
    return parts[0] + '年' + parseInt(parts[1]) + '月' + parseInt(parts[2]) + '日';
}

// 今天 + N 天后的 'YYYY-MM-DD'
function getFutureDate(days) {
    var d = new Date();
    d.setDate(d.getDate() + days);
    return formatDate(d);
}

// 日程冲突检测: 同一天, 给定时间落在某日程 [time, endTime) 区间内
function checkScheduleConflict(date, time, scheduleData) {
    if (!date || !time) return null;
    var conflicts = scheduleData.filter(function (item) {
        if (item.date !== date) return false;
        if (time >= item.time && time < item.endTime) return true;
        return false;
    });
    return conflicts.length > 0 ? conflicts : null;
}

// 过滤谓词: pending 未完成 / completed 已完成 / all 全部
function getScheduleFilterPredicate(filter) {
    if (filter === 'pending')
        return function (s) {
            return !s.completed;
        };
    if (filter === 'completed')
        return function (s) {
            return !!s.completed;
        };
    return function () {
        return true;
    };
}

// ===== 测试 =====

describe('schedule.js - parseDateStr', function () {
    it('should parse YYYY-MM-DD into local Date', function () {
        var d = parseDateStr('2026-07-02');
        assert.strictEqual(d.getFullYear(), 2026);
        assert.strictEqual(d.getMonth(), 6); // 0-indexed
        assert.strictEqual(d.getDate(), 2);
    });

    it('should handle single-digit month/day', function () {
        var d = parseDateStr('2026-1-5');
        assert.strictEqual(d.getMonth(), 0);
        assert.strictEqual(d.getDate(), 5);
    });

    it('should return current Date for empty input', function () {
        var before = Date.now();
        var d = parseDateStr('');
        var after = Date.now();
        assert.ok(d.getTime() >= before && d.getTime() <= after);
    });

    it('should return current Date for null/undefined', function () {
        var d1 = parseDateStr(null);
        var d2 = parseDateStr(undefined);
        assert.ok(d1 instanceof Date);
        assert.ok(d2 instanceof Date);
    });
});

describe('schedule.js - formatDate', function () {
    it('should format Date as YYYY-MM-DD with zero padding', function () {
        assert.strictEqual(formatDate(new Date(2026, 0, 5)), '2026-01-05');
        assert.strictEqual(formatDate(new Date(2026, 11, 31)), '2026-12-31');
    });

    it('should not pad double-digit month/day', function () {
        assert.strictEqual(formatDate(new Date(2026, 10, 15)), '2026-11-15');
    });
});

describe('schedule.js - formatDateLabel', function () {
    it('should format as YYYY年M月D日 without leading zeros', function () {
        assert.strictEqual(formatDateLabel('2026-01-05'), '2026年1月5日');
        assert.strictEqual(formatDateLabel('2026-12-31'), '2026年12月31日');
    });

    it('should handle single-digit parts', function () {
        assert.strictEqual(formatDateLabel('2026-3-9'), '2026年3月9日');
    });
});

describe('schedule.js - getFutureDate', function () {
    it('should return date N days in future as YYYY-MM-DD', function () {
        var today = new Date();
        var expected = new Date();
        expected.setDate(today.getDate() + 7);
        var expectedStr =
            expected.getFullYear() +
            '-' +
            String(expected.getMonth() + 1).padStart(2, '0') +
            '-' +
            String(expected.getDate()).padStart(2, '0');
        assert.strictEqual(getFutureDate(7), expectedStr);
    });

    it('should handle negative delta (past)', function () {
        var result = getFutureDate(-1);
        // 确保是有效的 YYYY-MM-DD 格式
        assert.ok(/^\d{4}-\d{2}-\d{2}$/.test(result));
    });

    it('should return valid date string format', function () {
        assert.ok(/^\d{4}-\d{2}-\d{2}$/.test(getFutureDate(0)));
    });
});

describe('schedule.js - checkScheduleConflict', function () {
    var scheduleData = [
        { date: '2026-07-02', time: '09:00', endTime: '11:00', title: '开庭' },
        { date: '2026-07-02', time: '14:00', endTime: '16:00', title: '会议' },
        { date: '2026-07-03', time: '10:00', endTime: '12:00', title: '调解' }
    ];

    it('should detect conflict when time falls within existing slot', function () {
        var conflicts = checkScheduleConflict('2026-07-02', '10:00', scheduleData);
        assert.ok(conflicts);
        assert.strictEqual(conflicts.length, 1);
        assert.strictEqual(conflicts[0].title, '开庭');
    });

    it('should detect conflict at boundary start time (inclusive)', function () {
        var conflicts = checkScheduleConflict('2026-07-02', '09:00', scheduleData);
        assert.ok(conflicts);
        assert.strictEqual(conflicts[0].title, '开庭');
    });

    it('should not conflict at boundary end time (exclusive)', function () {
        var conflicts = checkScheduleConflict('2026-07-02', '11:00', scheduleData);
        assert.strictEqual(conflicts, null);
    });

    it('should return null when no conflict', function () {
        var conflicts = checkScheduleConflict('2026-07-02', '12:30', scheduleData);
        assert.strictEqual(conflicts, null);
    });

    it('should return null when date has no schedules', function () {
        var conflicts = checkScheduleConflict('2026-12-25', '10:00', scheduleData);
        assert.strictEqual(conflicts, null);
    });

    it('should return null for empty date or time', function () {
        assert.strictEqual(checkScheduleConflict('', '10:00', scheduleData), null);
        assert.strictEqual(checkScheduleConflict('2026-07-02', '', scheduleData), null);
        assert.strictEqual(checkScheduleConflict(null, null, scheduleData), null);
    });

    it('should detect multiple conflicts on same date', function () {
        var data = [
            { date: '2026-07-02', time: '09:00', endTime: '12:00', title: 'A' },
            { date: '2026-07-02', time: '10:00', endTime: '13:00', title: 'B' }
        ];
        var conflicts = checkScheduleConflict('2026-07-02', '10:30', data);
        assert.strictEqual(conflicts.length, 2);
    });
});

describe('schedule.js - getScheduleFilterPredicate', function () {
    it('should return predicate filtering pending (not completed)', function () {
        var pred = getScheduleFilterPredicate('pending');
        assert.strictEqual(pred({ completed: false }), true);
        assert.strictEqual(pred({ completed: true }), false);
        assert.strictEqual(pred({}), true); // undefined completed
    });

    it('should return predicate filtering completed', function () {
        var pred = getScheduleFilterPredicate('completed');
        assert.strictEqual(pred({ completed: true }), true);
        assert.strictEqual(pred({ completed: false }), false);
        assert.strictEqual(pred({}), false);
    });

    it('should return predicate matching all for "all" or unknown filter', function () {
        var predAll = getScheduleFilterPredicate('all');
        assert.strictEqual(predAll({ completed: true }), true);
        assert.strictEqual(predAll({ completed: false }), true);

        var predUnknown = getScheduleFilterPredicate('xyz');
        assert.strictEqual(predUnknown({ completed: true }), true);
        assert.strictEqual(predUnknown({ completed: false }), true);
    });

    it('returned predicate should be usable with Array.filter', function () {
        var items = [
            { id: 1, completed: false },
            { id: 2, completed: true },
            { id: 3, completed: false }
        ];
        var pending = items.filter(getScheduleFilterPredicate('pending'));
        assert.strictEqual(pending.length, 2);
        var completed = items.filter(getScheduleFilterPredicate('completed'));
        assert.strictEqual(completed.length, 1);
        var all = items.filter(getScheduleFilterPredicate('all'));
        assert.strictEqual(all.length, 3);
    });
});
