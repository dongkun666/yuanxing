'use strict';

const assert = require('assert');
const { describe, it } = require('node:test');

// ===== 从 templates.js 提取的纯函数逻辑（全局函数无法直接 require，复制核心算法测试） =====
// 对应 assets/js/templates.js 中的 escapeHtml / personalCategoryColor / parseTime

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function personalCategoryColor(c) {
    var colorCls = {
        诉状类: 'bg-brand-tint text-brand',
        答辩类: 'bg-wiki-tint text-wiki',
        合同类: 'bg-warning-tint text-warning',
        申请类: 'bg-success-tint text-success'
    };
    return colorCls[c] || 'bg-bg-subtle text-fg-secondary';
}

// parseTime: 从 tr 的第 4 列 td 读取时间字符串, 转为时间戳; 无效返回 0
function parseTime(tr) {
    var tds = tr.querySelectorAll('td');
    var timeStr = tds.length >= 4 ? (tds[3].textContent || '').trim() : '';
    var d = new Date(timeStr.replace(/-/g, '/'));
    return isNaN(d.getTime()) ? 0 : d.getTime();
}

// buildUploadCategoryOptions 核心逻辑: 从 .personal-category-tab 读取分类(排除 all), 拼 <option>
function buildUploadCategoryOptions(tabs) {
    var html = '';
    tabs.forEach(function (tab) {
        var name = tab.getAttribute('data-category');
        if (name && name !== 'all') {
            html += '<option value="' + escapeHtml(name) + '">' + escapeHtml(name) + '</option>';
        }
    });
    return html;
}

// ===== 测试 =====

describe('templates.js - escapeHtml', function () {
    it('should escape HTML special characters', function () {
        assert.strictEqual(escapeHtml('<script>'), '&lt;script&gt;');
        assert.strictEqual(escapeHtml('"q"'), '&quot;q&quot;');
        assert.strictEqual(escapeHtml("'a'"), '&#39;a&#39;');
        assert.strictEqual(escapeHtml('a&b'), 'a&amp;b');
    });

    it('should return empty string for null/undefined', function () {
        assert.strictEqual(escapeHtml(null), '');
        assert.strictEqual(escapeHtml(undefined), '');
    });

    it('should coerce non-string to string', function () {
        assert.strictEqual(escapeHtml(123), '123');
        assert.strictEqual(escapeHtml(true), 'true');
    });
});

describe('templates.js - personalCategoryColor', function () {
    it('should return mapped color for known categories', function () {
        assert.strictEqual(personalCategoryColor('诉状类'), 'bg-brand-tint text-brand');
        assert.strictEqual(personalCategoryColor('答辩类'), 'bg-wiki-tint text-wiki');
        assert.strictEqual(personalCategoryColor('合同类'), 'bg-warning-tint text-warning');
        assert.strictEqual(personalCategoryColor('申请类'), 'bg-success-tint text-success');
    });

    it('should return default color for unknown category', function () {
        assert.strictEqual(
            personalCategoryColor('未知分类'),
            'bg-bg-subtle text-fg-secondary'
        );
        assert.strictEqual(
            personalCategoryColor(''),
            'bg-bg-subtle text-fg-secondary'
        );
    });
});

describe('templates.js - parseTime', function () {
    function mockTr(textContent, tdsCount) {
        var tds = [];
        for (var i = 0; i < (tdsCount || 4); i++) {
            tds.push({ textContent: i === 3 ? textContent : '' });
        }
        return {
            querySelectorAll: function () { return tds; }
        };
    }

    it('should parse valid datetime string from 4th td', function () {
        var tr = mockTr('2026-06-15 14:30');
        var ts = parseTime(tr);
        assert.ok(ts > 0, 'should return positive timestamp');
        var d = new Date(ts);
        assert.strictEqual(d.getFullYear(), 2026);
        assert.strictEqual(d.getMonth(), 5); // 0-indexed
        assert.strictEqual(d.getDate(), 15);
    });

    it('should return 0 for empty time string', function () {
        var tr = mockTr('');
        assert.strictEqual(parseTime(tr), 0);
    });

    it('should return 0 for invalid date string', function () {
        var tr = mockTr('not-a-date');
        assert.strictEqual(parseTime(tr), 0);
    });

    it('should return 0 when fewer than 4 tds', function () {
        var tr = {
            querySelectorAll: function () { return [{ textContent: 'x' }, { textContent: 'y' }]; }
        };
        assert.strictEqual(parseTime(tr), 0);
    });
});

describe('templates.js - buildUploadCategoryOptions', function () {
    function mockTab(category) {
        return { getAttribute: function (attr) { return attr === 'data-category' ? category : null; } };
    }

    it('should build option HTML for each category excluding "all"', function () {
        var tabs = [mockTab('all'), mockTab('诉状类'), mockTab('合同类')];
        var html = buildUploadCategoryOptions(tabs);
        assert.ok(html.indexOf('<option value="诉状类">诉状类</option>') >= 0);
        assert.ok(html.indexOf('<option value="合同类">合同类</option>') >= 0);
        assert.ok(html.indexOf('all') < 0, 'should exclude "all" category');
    });

    it('should escape special chars in category name', function () {
        var tabs = [mockTab('a&b<c>')];
        var html = buildUploadCategoryOptions(tabs);
        assert.ok(html.indexOf('a&amp;b&lt;c&gt;') >= 0);
    });

    it('should return empty string when no tabs', function () {
        assert.strictEqual(buildUploadCategoryOptions([]), '');
    });

    it('should skip tabs with null/empty category', function () {
        var tabs = [
            { getAttribute: function () { return null; } },
            { getAttribute: function () { return ''; } },
            mockTab('有效类')
        ];
        var html = buildUploadCategoryOptions(tabs);
        assert.ok(html.indexOf('有效类') >= 0);
        assert.strictEqual(html.match(/<option/g).length, 1);
    });
});
