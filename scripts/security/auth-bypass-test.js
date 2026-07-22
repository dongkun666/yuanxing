/**
 * 认证绕过测试
 * 测试应用程序认证和授权机制的安全性
 *
 * 用法: node scripts/security/auth-bypass-test.js [options]
 */

'use strict';

var http = require('http');
var https = require('https');
var url = require('url');
var fs = require('fs');
var path = require('path');

var DEFAULT_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:3847';

var authBypassTests = [
    {
        name: 'no-auth-header',
        description: '无认证头访问受保护端点',
        method: 'GET',
        path: '/api/users',
        headers: {},
        expectedStatus: 401,
        risk: 'high'
    },
    {
        name: 'invalid-token',
        description: '无效 Token 访问',
        method: 'GET',
        path: '/api/users',
        headers: { 'Authorization': 'Bearer invalid_token_12345' },
        expectedStatus: 401,
        risk: 'high'
    },
    {
        name: 'expired-token',
        description: '过期 Token 访问',
        method: 'GET',
        path: '/api/users',
        headers: {
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjEwMDAwMDAwMDB9.invalid'
        },
        expectedStatus: 401,
        risk: 'high'
    },
    {
        name: 'basic-auth-bypass',
        description: '基础认证绕过',
        method: 'GET',
        path: '/api/users',
        headers: { 'Authorization': 'Basic YWRtaW46YWRtaW4=' },
        expectedStatus: 401,
        risk: 'medium'
    },
    {
        name: 'path-traversal',
        description: '路径遍历尝试',
        method: 'GET',
        path: '/api/../etc/passwd',
        headers: {},
        expectedStatus: 404,
        risk: 'medium'
    },
    {
        name: 'admin-endpoint',
        description: '管理端点未授权访问',
        method: 'GET',
        path: '/api/growth/overview',
        headers: {},
        expectedStatus: 401,
        risk: 'high'
    },
    {
        name: 'weak-password-test',
        description: '弱密码测试',
        method: 'POST',
        path: '/api/users',
        body: JSON.stringify({ email: 'admin@example.com', password: 'admin' }),
        headers: { 'Content-Type': 'application/json' },
        expectedStatus: 401,
        risk: 'high'
    },
    {
        name: 'api-key-missing',
        description: '缺少 API Key',
        method: 'GET',
        path: '/api/developer/keys',
        headers: {},
        expectedStatus: 401,
        risk: 'medium'
    },
    {
        name: 'session-fixation',
        description: '会话固定测试',
        method: 'GET',
        path: '/api/health',
        headers: { 'Cookie': 'sessionid=fake_session_id' },
        expectedStatus: 200,
        risk: 'low'
    },
    {
        name: 'privilege-escalation',
        description: '权限提升尝试',
        method: 'GET',
        path: '/api/settings',
        headers: { 'Authorization': 'Bearer user_token' },
        expectedStatus: 403,
        risk: 'high'
    }
];

function AuthBypassTester(options) {
    this.baseUrl = options.baseUrl || DEFAULT_BASE_URL;
    this.results = [];
    this.vulnerabilities = [];
}

AuthBypassTester.prototype.run = function () {
    var self = this;
    console.log('========================================');
    console.log('  LexPrime 认证绕过测试');
    console.log('========================================');
    console.log('目标地址:', self.baseUrl);
    console.log('测试用例数量:', authBypassTests.length);
    console.log('');

    var index = 0;

    function nextTest() {
        if (index >= authBypassTests.length) {
            self.printSummary();
            return;
        }

        var testCase = authBypassTests[index++];
        self.testAuthBypass(testCase, function () {
            setTimeout(nextTest, 200);
        });
    }

    nextTest();
};

AuthBypassTester.prototype.testAuthBypass = function (testCase, callback) {
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
    headers['User-Agent'] = 'SecurityScanner/1.0';

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

            var isVulnerable = self.analyzeAuthResult(res, body, testCase);

            var result = {
                testName: testCase.name,
                description: testCase.description,
                endpoint: testCase.method + ' ' + testCase.path,
                statusCode: res.statusCode,
                expectedStatus: testCase.expectedStatus,
                latency: latency,
                vulnerable: isVulnerable,
                risk: testCase.risk
            };

            self.results.push(result);

            if (isVulnerable) {
                self.vulnerabilities.push(result);
                console.log('[!] 认证风险 (' + testCase.risk + '): ' + testCase.name);
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
            expectedStatus: testCase.expectedStatus,
            latency: 0,
            vulnerable: false,
            risk: testCase.risk,
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

AuthBypassTester.prototype.analyzeAuthResult = function (res, body, testCase) {
    var statusCode = res.statusCode;
    var expected = testCase.expectedStatus;

    if (expected === 401 || expected === 403) {
        if (statusCode >= 200 && statusCode < 300) {
            return true;
        }
    }

    if (expected === 404) {
        if (statusCode === 200) {
            return true;
        }
    }

    if (testCase.name === 'no-auth-header' && statusCode === 200) {
        return true;
    }

    if (testCase.name === 'invalid-token' && statusCode === 200) {
        return true;
    }

    if (testCase.name === 'admin-endpoint' && statusCode === 200) {
        return true;
    }

    return false;
};

AuthBypassTester.prototype.printSummary = function () {
    var self = this;
    console.log('');
    console.log('========================================');
    console.log('  认证绕过测试总结');
    console.log('========================================');
    console.log('总测试数:', self.results.length);
    console.log('发现漏洞:', self.vulnerabilities.length);
    console.log('通过测试:', self.results.length - self.vulnerabilities.length);
    console.log('');

    if (self.vulnerabilities.length > 0) {
        console.log('漏洞详情:');
        self.vulnerabilities.forEach(function (v, i) {
            console.log('  ' + (i + 1) + '. [' + v.risk.toUpperCase() + '] ' + v.testName);
            console.log('     ' + v.description);
            console.log('     端点: ' + v.endpoint);
            console.log('     实际状态码: ' + v.statusCode + ' (预期: ' + v.expectedStatus + ')');
        });
    } else {
        console.log('未发现认证绕过漏洞 ✓');
    }

    console.log('\n安全建议:');
    console.log('  1. 实施强 JWT 认证');
    console.log('  2. 细粒度权限控制');
    console.log('  3. Token 过期和刷新机制');
    console.log('  4. 登录失败锁定策略');
    console.log('  5. 敏感操作二次验证');

    var reportPath = path.join(__dirname, 'reports', 'auth-bypass-test-' + Date.now() + '.json');
    try {
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify({
            baseUrl: self.baseUrl,
            timestamp: new Date().toISOString(),
            totalTests: self.results.length,
            vulnerabilities: self.vulnerabilities.length,
            results: self.results,
            vulnerabilities_detail: self.vulnerabilities
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
            console.log('用法: node scripts/security/auth-bypass-test.js [options]');
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
    var tester = new AuthBypassTester(options);
    tester.run();
}

module.exports = AuthBypassTester;
