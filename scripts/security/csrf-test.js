/**
 * CSRF 测试
 * 测试应用程序对跨站请求伪造攻击的防护能力
 *
 * 用法: node scripts/security/csrf-test.js [options]
 */

'use strict';

var http = require('http');
var https = require('https');
var url = require('url');
var fs = require('fs');
var path = require('path');

var DEFAULT_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:3847';

var csrfTestCases = [
    {
        name: 'no-referer',
        description: '无 Referer 头的 POST 请求',
        method: 'POST',
        path: '/api/search',
        body: JSON.stringify({ query: 'test', index: 'cases', page: 1, size: 20 }),
        headers: { 'Content-Type': 'application/json' },
        removeHeaders: ['referer', 'origin']
    },
    {
        name: 'evil-origin',
        description: '恶意 Origin 头的请求',
        method: 'POST',
        path: '/api/search',
        body: JSON.stringify({ query: 'test', index: 'cases', page: 1, size: 20 }),
        headers: {
            'Content-Type': 'application/json',
            'Origin': 'https://evil-attacker.com'
        }
    },
    {
        name: 'cross-origin-referer',
        description: '跨站 Referer',
        method: 'POST',
        path: '/api/search',
        body: JSON.stringify({ query: 'test', index: 'cases', page: 1, size: 20 }),
        headers: {
            'Content-Type': 'application/json',
            'Referer': 'https://evil-attacker.com/malicious.html'
        }
    },
    {
        name: 'no-csrf-token',
        description: '无 CSRF Token 的状态变更请求',
        method: 'POST',
        path: '/api/firm/time-entries?firm_id=TEST',
        body: JSON.stringify({
            lawyer_id: 'L001',
            entry_date: '2026-01-01',
            hours: 1,
            description: 'test'
        }),
        headers: { 'Content-Type': 'application/json' },
        checkStatusChange: true
    },
    {
        name: 'csrf-with-get',
        description: 'GET 请求执行状态变更',
        method: 'GET',
        path: '/api/firm/time-entries?firm_id=TEST&lawyer_id=L001&hours=1',
        headers: {}
    }
];

function CsrfTester(options) {
    this.baseUrl = options.baseUrl || DEFAULT_BASE_URL;
    this.results = [];
    this.findings = [];
}

CsrfTester.prototype.run = function () {
    var self = this;
    console.log('========================================');
    console.log('  LexPrime CSRF 测试');
    console.log('========================================');
    console.log('目标地址:', self.baseUrl);
    console.log('测试用例数量:', csrfTestCases.length);
    console.log('');

    var index = 0;

    function nextTest() {
        if (index >= csrfTestCases.length) {
            self.printSummary();
            return;
        }

        var testCase = csrfTestCases[index++];
        self.testCsrfCase(testCase, function () {
            setTimeout(nextTest, 200);
        });
    }

    nextTest();
};

CsrfTester.prototype.testCsrfCase = function (testCase, callback) {
    var self = this;
    var fullUrl = self.baseUrl + testCase.path;
    var parsed = url.parse(fullUrl);
    var isHttps = parsed.protocol === 'https:';
    var lib = isHttps ? https : http;

    var headers = {};
    for (var key in testCase.headers) {
        if (testCase.headers.hasOwnProperty(key)) {
            headers[key] = testCase.headers[key];
        }
    }

    if (testCase.removeHeaders) {
        testCase.removeHeaders.forEach(function (h) {
            delete headers[h];
        });
    }

    headers['User-Agent'] = 'Mozilla/5.0 (compatible; SecurityScanner/1.0)';

    var options = {
        hostname: parsed.hostname,
        port: parsed.port || (isHttps ? 443 : 80),
        path: parsed.path,
        method: testCase.method,
        headers: headers
    };

    var startTime = Date.now();
    var req = lib.request(options, function (res) {
        var chunks = [];
        res.on('data', function (chunk) {
            chunks.push(chunk);
        });
        res.on('end', function () {
            var body = Buffer.concat(chunks).toString();
            var latency = Date.now() - startTime;
            var isVulnerable = self.analyzeCsrfResult(res, body, testCase);

            var result = {
                testName: testCase.name,
                description: testCase.description,
                endpoint: testCase.method + ' ' + testCase.path,
                statusCode: res.statusCode,
                latency: latency,
                vulnerable: isVulnerable,
                responseHeaders: {
                    'content-type': res.headers['content-type'],
                    'access-control-allow-origin': res.headers['access-control-allow-origin'],
                    'x-frame-options': res.headers['x-frame-options']
                }
            };

            self.results.push(result);

            if (isVulnerable) {
                self.findings.push(result);
                console.log('[!] CSRF 风险: ' + testCase.name);
            } else {
                console.log('[✓] 安全: ' + testCase.name);
            }

            callback();
        });
    });

    req.on('error', function (err) {
        self.results.push({
            testName: testCase.name,
            description: testCase.description,
            endpoint: testCase.method + ' ' + testCase.path,
            statusCode: 0,
            latency: 0,
            vulnerable: false,
            error: err.message
        });
        console.log('[x] 请求失败: ' + testCase.name + ' - ' + err.message);
        callback();
    });

    req.setTimeout(5000, function () {
        req.abort();
    });

    if (testCase.body) {
        req.write(testCase.body);
    }
    req.end();
};

CsrfTester.prototype.analyzeCsrfResult = function (res, body, testCase) {
    var statusCode = res.statusCode;

    if (statusCode === 403 || statusCode === 401 || statusCode === 405) {
        return false;
    }

    if (testCase.name === 'evil-origin' || testCase.name === 'cross-origin-referer') {
        var acao = res.headers['access-control-allow-origin'];
        if (acao === '*' || (acao && acao.indexOf('evil') !== -1)) {
            return true;
        }
    }

    if (testCase.checkStatusChange && statusCode >= 200 && statusCode < 300) {
        return true;
    }

    if (testCase.name === 'no-referer' && statusCode >= 200 && statusCode < 300) {
        return false;
    }

    return false;
};

CsrfTester.prototype.printSummary = function () {
    var self = this;
    console.log('');
    console.log('========================================');
    console.log('  CSRF 测试总结');
    console.log('========================================');
    console.log('总测试数:', self.results.length);
    console.log('发现风险:', self.findings.length);
    console.log('通过测试:', self.results.length - self.findings.length);
    console.log('');

    if (self.findings.length > 0) {
        console.log('风险详情:');
        self.findings.forEach(function (f, i) {
            console.log('  ' + (i + 1) + '. ' + f.testName);
            console.log('     ' + f.description);
            console.log('     端点: ' + f.endpoint);
            console.log('     状态码: ' + f.statusCode);
        });
    } else {
        console.log('未发现 CSRF 风险 ✓');
    }

    console.log('\n安全建议:');
    console.log('  1. 验证 Origin/Referer 头');
    console.log('  2. 使用 CSRF Token');
    console.log('  3. 实施 SameSite Cookie');
    console.log('  4. 设置合理的 CORS 策略');

    var reportPath = path.join(__dirname, 'reports', 'csrf-test-' + Date.now() + '.json');
    try {
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify({
            baseUrl: self.baseUrl,
            timestamp: new Date().toISOString(),
            totalTests: self.results.length,
            findings: self.findings.length,
            results: self.results,
            findings_detail: self.findings
        }, null, 2));
        console.log('\n报告已保存: ' + reportPath);
    } catch (e) {
        console.warn('保存报告失败:', e.message);
    }
};

function parseArgs() {
    var args = process.argv.slice(2);
    var options = {};

    for (var i = 0; i < args.length; i++) {
        var arg = args[i];
        if (arg === '--url' && args[i + 1]) {
            options.baseUrl = args[++i];
        } else if (arg === '--help' || arg === '-h') {
            console.log('用法: node scripts/security/csrf-test.js [options]');
            console.log('');
            console.log('选项:');
            console.log('  --url <url>  API 基础地址 (默认: http://127.0.0.1:3847)');
            console.log('  --help, -h   显示帮助');
            process.exit(0);
        }
    }

    return options;
}

if (require.main === module) {
    var options = parseArgs();
    var tester = new CsrfTester(options);
    tester.run();
}

module.exports = CsrfTester;
