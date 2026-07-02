'use strict';

const assert = require('assert');
const { describe, it } = require('node:test');

// ===== 从 archive.js 提取的纯逻辑（数据过滤算法） =====

var _archiveData = [
    { id: 0, caseNum: '(2025)京01民终456号', cause: '房屋买卖合同纠纷', plaintiff: '陈某某', defendant: '某某房地产公司', archiveDate: '2025-12-15', year: '2025', type: '民事' },
    { id: 1, caseNum: '(2025)京02民终789号', cause: '借款合同纠纷', plaintiff: '赵某某', defendant: '王某某', archiveDate: '2025-11-20', year: '2025', type: '商事' },
    { id: 2, caseNum: '(2024)京01民终123号', cause: '劳动争议', plaintiff: '孙某某', defendant: '某某科技公司', archiveDate: '2024-12-01', year: '2024', type: '劳动争议' },
    { id: 3, caseNum: '(2024)京03民初567号', cause: '股权转让纠纷', plaintiff: '李某某', defendant: '某某投资公司', archiveDate: '2024-10-15', year: '2024', type: '商事' },
    { id: 4, caseNum: '(2026)京01民初100号', cause: '建设工程合同纠纷', plaintiff: '某某建筑公司', defendant: '某某房地产公司', archiveDate: '2026-01-20', year: '2026', type: '民事' }
];

// 模拟 getFilteredData 内部的过滤逻辑
function filterArchiveData(data, searchText, yearValue, typeValue) {
    return data.filter(function(item) {
        var matchSearch = !searchText ||
            item.caseNum.toLowerCase().indexOf(searchText) > -1 ||
            item.cause.toLowerCase().indexOf(searchText) > -1 ||
            item.plaintiff.toLowerCase().indexOf(searchText) > -1 ||
            item.defendant.toLowerCase().indexOf(searchText) > -1;
        var matchYear = !yearValue || item.year === yearValue;
        var matchType = !typeValue || item.type.indexOf(typeValue) > -1;
        return matchSearch && matchYear && matchType;
    });
}

// 模拟 restoreArchive/deleteArchive 的数据移除逻辑
function removeArchiveItem(data, id) {
    return data.filter(function(x) { return x.id !== id; });
}

// 模拟 openArchiveDetail 的数据查找逻辑
function findArchiveItem(data, id) {
    return data.find(function(x) { return x.id === id; });
}

// ===== 测试 =====

describe('archive.js - filterArchiveData (数据过滤逻辑)', function() {
    it('should return all data when no filters applied', function() {
        var result = filterArchiveData(_archiveData, '', '', '');
        assert.strictEqual(result.length, 5);
    });

    it('should filter by search text matching caseNum', function() {
        var result = filterArchiveData(_archiveData, '456', '', '');
        assert.strictEqual(result.length, 1);
        assert.strictEqual(result[0].id, 0);
    });

    it('should filter by search text matching cause', function() {
        var result = filterArchiveData(_archiveData, '劳动', '', '');
        assert.strictEqual(result.length, 1);
        assert.strictEqual(result[0].id, 2);
    });

    it('should filter by search text matching plaintiff', function() {
        var result = filterArchiveData(_archiveData, '赵某某', '', '');
        assert.strictEqual(result.length, 1);
        assert.strictEqual(result[0].id, 1);
    });

    it('should filter by year', function() {
        var result = filterArchiveData(_archiveData, '', '2024', '');
        assert.strictEqual(result.length, 2);
        assert.strictEqual(result[0].year, '2024');
    });

    it('should filter by type', function() {
        var result = filterArchiveData(_archiveData, '', '', '商事');
        assert.strictEqual(result.length, 2);
    });

    it('should combine search + year + type filters', function() {
        var result = filterArchiveData(_archiveData, '纠纷', '2025', '商事');
        assert.strictEqual(result.length, 1);
        assert.strictEqual(result[0].id, 1);
    });

    it('should return empty when no match', function() {
        var result = filterArchiveData(_archiveData, '不存在的案件', '', '');
        assert.strictEqual(result.length, 0);
    });
});

describe('archive.js - removeArchiveItem (还原/删除逻辑)', function() {
    it('should remove item by id', function() {
        var result = removeArchiveItem(_archiveData, 2);
        assert.strictEqual(result.length, 4);
        assert.ok(!result.find(function(x) { return x.id === 2; }), 'item with id 2 should be removed');
    });

    it('should not modify original when removing', function() {
        var originalLen = _archiveData.length;
        removeArchiveItem(_archiveData, 0);
        assert.strictEqual(_archiveData.length, originalLen);
    });

    it('should return same array when removing non-existent id', function() {
        var result = removeArchiveItem(_archiveData, 99);
        assert.strictEqual(result.length, 5);
    });
});

describe('archive.js - findArchiveItem (查找逻辑)', function() {
    it('should find item by id', function() {
        var item = findArchiveItem(_archiveData, 0);
        assert.ok(item, 'should find item with id 0');
        assert.strictEqual(item.caseNum, '(2025)京01民终456号');
    });

    it('should return undefined for non-existent id', function() {
        var item = findArchiveItem(_archiveData, 99);
        assert.strictEqual(item, undefined);
    });
});

describe('archive.js - globalThis exposure', function() {
    it('should expose all functions to globalThis after loading module', function() {
        globalThis.document = {
            getElementById: function() { return null; },
            querySelector: function() { return null; },
            querySelectorAll: function() { return []; },
            createElement: function() {
                return {
                    className: '', textContent: '', value: '', innerHTML: '',
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
        globalThis.Utils = { showModal: function() { return function() {}; } };
        globalThis.clearTimeout = function() {};
        globalThis.setTimeout = function(fn) { return 0; };

        require('../assets/js/archive.js');

        var expectedFns = [
            'filterArchiveList', 'toggleAllArchive',
            'openArchiveDetail', 'closeArchiveDetail',
            'restoreArchive', 'deleteArchive', 'initArchive'
        ];
        expectedFns.forEach(function(name) {
            assert.ok(typeof globalThis[name] === 'function', name + ' should be a function on globalThis');
        });
    });
});
