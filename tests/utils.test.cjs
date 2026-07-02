'use strict';

const assert = require('assert');
const { describe, it } = require('node:test');

describe('Utils.showModal', function() {
    it('should create modal with basic options', function() {
        globalThis.document = {
            getElementById: function() { return null; },
            createElement: function(type) {
                return {
                    id: '',
                    className: '',
                    setAttribute: function() {},
                    addEventListener: function() {},
                    innerHTML: '',
                    appendChild: function() {},
                    classList: { add: function() {}, remove: function() {} }
                };
            },
            body: { appendChild: function() {} },
            addEventListener: function() {},
            removeEventListener: function() {}
        };
        globalThis.window = { location: {} };
        globalThis.console = { error: function() {}, log: function() {} };

        require('../assets/js/utils.js');

        assert.ok(typeof Utils.showModal === 'function', 'showModal should be a function');

        var close = Utils.showModal({
            id: 'test-modal',
            title: 'Test Title',
            content: '<div>Test Content</div>',
            footer: '<button>Close</button>'
        });

        assert.ok(typeof close === 'function', 'showModal should return close function');
    });
});

describe('Utils.escapeHtml', function() {
    it('should escape HTML special characters', function() {
        var mockDiv;
        globalThis.document = {
            createElement: function(type) {
                mockDiv = {
                    textContent: '',
                    get innerHTML() {
                        var s = this.textContent;
                        return s.replace(/&/g, '&amp;')
                                .replace(/</g, '&lt;')
                                .replace(/>/g, '&gt;')
                                .replace(/"/g, '&quot;')
                                .replace(/'/g, '&#39;');
                    }
                };
                return mockDiv;
            }
        };
        require('../assets/js/utils.js');
        assert.strictEqual(Utils.escapeHtml('<script>alert(1)</script>'), '&lt;script&gt;alert(1)&lt;/script&gt;');
        assert.strictEqual(Utils.escapeHtml('"test"'), '&quot;test&quot;');
        assert.strictEqual(Utils.escapeHtml("'test'"), '&#39;test&#39;');
        assert.strictEqual(Utils.escapeHtml('&test'), '&amp;test');
    });
});

describe('Utils.debounce', function() {
    it('should debounce function calls', function() {
        require('../assets/js/utils.js');
        var count = 0;
        var fn = Utils.debounce(function() { count++; }, 100);
        fn(); fn(); fn();
        assert.strictEqual(count, 0);
    });
});

describe('Utils.formatDate', function() {
    it('should format dates correctly', function() {
        require('../assets/js/utils.js');
        assert.ok(Utils.formatDate(new Date('2026-01-15'), 'YYYY-MM-DD') === '2026-01-15');
    });
});