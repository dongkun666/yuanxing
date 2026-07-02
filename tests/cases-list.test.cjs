'use strict';

const assert = require('assert');
const { describe, it } = require('node:test');

// ===== 从 cases-list.js 提取的纯逻辑（数据过滤匹配算法） =====

// 模拟 filterCaseList 内部的行匹配逻辑
function matchRow(searchText, statusValue, typeValue, caseNum, caseType, party, lawyer, rowStatus, rowType) {
    var matchSearch = !searchText ||
        caseNum.includes(searchText) ||
        caseType.includes(searchText) ||
        party.includes(searchText) ||
        lawyer.includes(searchText);

    var matchStatus = !statusValue || rowStatus === statusValue;
    var matchType = !typeValue || rowType.includes(typeValue) || caseType.includes(typeValue);

    return matchSearch && matchStatus && matchType;
}

// 模拟 archiveCase 内部的 localStorage 归档逻辑
function addToArchive(localStorageData, idx) {
    var archived = JSON.parse(localStorageData || '[]');
    if (archived.indexOf(idx) === -1) {
        archived.push(idx);
    }
    return archived;
}

// 模拟 restoreArchive/deleteArchive 内部的 localStorage 移除逻辑
function removeFromArchive(localStorageData, idx) {
    var archived = JSON.parse(localStorageData || '[]');
    return archived.filter(function(x) { return x !== idx; });
}

// 分页计算逻辑
function calcPagination(totalItems, pageSize, currentPage) {
    var totalPages = Math.ceil(totalItems / pageSize) || 1;
    if (currentPage > totalPages) currentPage = totalPages;
    var startIdx = (currentPage - 1) * pageSize;
    var endIdx = startIdx + pageSize;
    return { totalPages: totalPages, startIdx: startIdx, endIdx: endIdx, currentPage: currentPage };
}

// ===== 测试 =====

describe('cases-list.js - matchRow (搜索/筛选逻辑)', function() {
    it('should match when no filters applied', function() {
        assert.strictEqual(matchRow('', '', '', '案号1', '民事', '原告甲', '律师A', '进行中', 'civil'), true);
    });

    it('should match by case number search', function() {
        assert.strictEqual(matchRow('案号1', '', '', '案号1', '民事', '原告甲', '律师A', '进行中', 'civil'), true);
        assert.strictEqual(matchRow('案号2', '', '', '案号1', '民事', '原告甲', '律师A', '进行中', 'civil'), false);
    });

    it('should match by party name search', function() {
        assert.strictEqual(matchRow('原告甲', '', '', '案号1', '民事', '原告甲', '律师A', '进行中', 'civil'), true);
        assert.strictEqual(matchRow('原告乙', '', '', '案号1', '民事', '原告甲', '律师A', '进行中', 'civil'), false);
    });

    it('should match by status filter', function() {
        assert.strictEqual(matchRow('', '进行中', '', '案号1', '民事', '原告甲', '律师A', '进行中', 'civil'), true);
        assert.strictEqual(matchRow('', '已结案', '', '案号1', '民事', '原告甲', '律师A', '进行中', 'civil'), false);
    });

    it('should match by type filter (checks both rowType and caseType)', function() {
        assert.strictEqual(matchRow('', '', '民事', '案号1', '民事', '原告甲', '律师A', '进行中', 'civil'), true);
        assert.strictEqual(matchRow('', '', '商事', '案号1', '民事', '原告甲', '律师A', '进行中', 'civil'), false);
    });

    it('should combine search and filter', function() {
        assert.strictEqual(matchRow('甲', '进行中', '', '案号1', '民事', '原告甲', '律师A', '进行中', 'civil'), true);
        assert.strictEqual(matchRow('甲', '已结案', '', '案号1', '民事', '原告甲', '律师A', '进行中', 'civil'), false);
    });
});

describe('cases-list.js - addToArchive (归档逻辑)', function() {
    it('should add index to empty archive', function() {
        var result = addToArchive('[]', 2);
        assert.deepStrictEqual(result, [2]);
    });

    it('should add index to existing archive', function() {
        var result = addToArchive('[1,3]', 2);
        assert.deepStrictEqual(result, [1, 3, 2]);
    });

    it('should not add duplicate index', function() {
        var result = addToArchive('[1,2,3]', 2);
        assert.deepStrictEqual(result, [1, 2, 3]);
    });
});

describe('cases-list.js - removeFromArchive (恢复/删除逻辑)', function() {
    it('should remove index from archive', function() {
        var result = removeFromArchive('[1,2,3]', 2);
        assert.deepStrictEqual(result, [1, 3]);
    });

    it('should handle removing non-existent index', function() {
        var result = removeFromArchive('[1,3]', 5);
        assert.deepStrictEqual(result, [1, 3]);
    });

    it('should handle empty archive', function() {
        var result = removeFromArchive('[]', 0);
        assert.deepStrictEqual(result, []);
    });
});

describe('cases-list.js - calcPagination (分页计算)', function() {
    it('should calculate pagination for first page', function() {
        var result = calcPagination(25, 10, 1);
        assert.strictEqual(result.totalPages, 3);
        assert.strictEqual(result.startIdx, 0);
        assert.strictEqual(result.endIdx, 10);
        assert.strictEqual(result.currentPage, 1);
    });

    it('should calculate pagination for last page', function() {
        var result = calcPagination(25, 10, 3);
        assert.strictEqual(result.totalPages, 3);
        assert.strictEqual(result.startIdx, 20);
        assert.strictEqual(result.endIdx, 30);
        assert.strictEqual(result.currentPage, 3);
    });

    it('should handle empty list', function() {
        var result = calcPagination(0, 10, 1);
        assert.strictEqual(result.totalPages, 1);
        assert.strictEqual(result.currentPage, 1);
    });

    it('should clamp currentPage to totalPages', function() {
        var result = calcPagination(5, 10, 99);
        assert.strictEqual(result.totalPages, 1);
        assert.strictEqual(result.currentPage, 1);
    });
});

describe('cases-list.js - globalThis exposure', function() {
    it('should expose all functions to globalThis after loading module', function() {
        var archivedData = '[]';
        globalThis.localStorage = {
            getItem: function(key) { return archivedData; },
            setItem: function(key, val) { archivedData = val; }
        };
        globalThis.document = {
            getElementById: function() { return null; },
            querySelector: function() { return null; },
            querySelectorAll: function() { return []; },
            createElement: function() {
                return {
                    className: '', textContent: '', value: '',
                    setAttribute: function() {}, addEventListener: function() {},
                    appendChild: function() {}, classList: { add: function() {}, remove: function() {} }
                };
            }
        };
        globalThis.window = { location: {} };
        globalThis.console = { error: function() {}, log: function() {} };
        globalThis.confirm = function() { return false; };
        globalThis.showToast = function() {};
        globalThis.escapeHtml = function(s) { return s; };

        require('../assets/js/cases-list.js');

        var expectedFns = [
            'filterCaseList', 'goToCasePage', 'archiveCase',
            'editCaseTitle', 'deleteCase',
            'openNewCaseModal', 'closeNewCaseModal', 'submitNewCase',
            'openArchiveDetail', 'restoreArchive', 'deleteArchive',
            'filterArchiveList', 'toggleAllArchive'
        ];
        expectedFns.forEach(function(name) {
            assert.ok(typeof globalThis[name] === 'function', name + ' should be a function on globalThis');
        });
    });
});
