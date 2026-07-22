/**
 * XSS 注入测试
 * 测试应用程序对跨站脚本攻击的防护能力
 *
 * 用法: node scripts/security/xss-test.js [options]
 */

'use strict';

var http = require('http');
var https = require('https');
var url = require('url');
var fs = require('fs');
var path = require('path');

var DEFAULT_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:3847';

var xssPayloads = [
    { name: 'basic-script', payload: '<script>alert(1)</script>', type: 'reflected' },
    { name: 'img-onerror', payload: '<img src=x onerror=alert(1)>', type: 'reflected' },
    { name: 'svg-onload', payload: '<svg onload=alert(1)>', type: 'reflected' },
    { name: 'javascript-uri', payload: 'javascript:alert(1)', type: 'reflected' },
    { name: 'event-handler', payload: '" onmouseover="alert(1)" x="', type: 'reflected' },
    { name: 'html-injection', payload: '</textarea><script>alert(1)</script>', type: 'reflected' },
    { name: 'base64-encoded', payload: 'PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==', type: 'stored' },
    { name: 'unicode-encoded', payload: '\\u003cscript\\u003ealert(1)\\u003c/script\\u003e', type: 'stored' },
    { name: 'polyglot', payload: 'jaVasCript:/*-/*`/*\\`/*\'/*"/**/(/* */oNcliCk=alert()//', type: 'stored' },
    { name: 'mutation-xss', payload: '<iframe/src=javascript&colon;alert&lpar;&rpar;>', type: 'stored' }
];

var testEndpoints = [
    { method: 'GET', path: '/api/cases?query=', param: 'query' },
    { method: 'GET', path: '/api/search?query=', param: 'query' },
    { method: 'GET', path: '/api/laws?law_type=', param: 'law_type' },
    { method: 'GET', path: '/api/companies?name=', param: 'name' }
];

function XssTester(options) {
    this.baseUrl = options.baseUrl || DEFAULT_BASE_URL;
    this.results = [];
    this.vulnerabilities = [];
}

XssTester.prototype.run = function () {
    var self = this;
    console.log('========================================');
    console.log('  LexPrime XSS 注入测试');
    console.log('========================================');
    console.log('目标地址:', self.baseUrl);
    console.log('测试 Payload 数量:', xssPayloads.length);
    console.log('测试端点数量:', testEndpoints.length);
    console.log('');

    var payloadIndex = 0;
    var endpointIndex = 0;

    function nextTest() {
        if (endpointIndex >= testEndpoints.length) {
            self.printSummary();
            return;
        }

        if (payloadIndex >= xssPayloads.length) {
            payloadIndex = 0;
            endpointIndex++;
            setTimeout(nextTest, 200);
            return;
        }

        var endpoint = testEndpoints[endpointIndex];
        var payload = xssPayloads[payloadIndex++];

        self.testPayload(endpoint, payload, function () {
            setTimeout(nextTest, 100);
        });
    }

    nextTest();
};

XssTester.prototype.testPayload = function (endpoint, payload, callback) {
    var self = this;
    var parsed = url.parse(self.baseUrl + endpoint.path + encodeURIComponent(payload.payload));
    var isHttps = parsed.protocol === 'https:';
    var lib = isHttps ? https : http;

    var options = {
        hostname: parsed.hostname,
        port: parsed.port || (isHttps ? 443 : 80),
        path: parsed.path,
        method: endpoint.method,
        headers: {
            'User-Agent': 'Mozilla/5.0 (compatible; SecurityScanner/1.0)'
        }
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
            var isVulnerable = self.checkXssReflection(body, payload.payload);

            var result = {
                endpoint: endpoint.method + ' ' + endpoint.path,
                payloadName: payload.name,
                payloadType: payload.type,
                statusCode: res.statusCode,
                latency: latency,
                vulnerable: isVulnerable,
                contentType: res.headers['content-type'] || ''
            };

            self.results.push(result);

            if (isVulnerable) {
                self.vulnerabilities.push(result);
                console.log('[!] 发现 XSS 漏洞: ' + payload.name + ' @ ' + endpoint.path);
            } else {
                console.log('[✓] 安全: ' + payload.name + ' @ ' + endpoint.path);
            }

            callback();
        });
    });

    req.on('error', function (err) {
        self.results.push({
            endpoint: endpoint.method + ' ' + endpoint.path,
            payloadName: payload.name,
            payloadType: payload.type,
            statusCode: 0,
            latency: 0,
            vulnerable: false,
            error: err.message
        });
        console.log('[x] 请求失败: ' + endpoint.path + ' - ' + err.message);
        callback();
    });

    req.setTimeout(5000, function () {
        req.abort();
    });

    req.end();
};

XssTester.prototype.checkXssReflection = function (body, payload) {
    if (!body || body.length === 0) {
        return false;
    }

    var lowerBody = body.toLowerCase();
    var lowerPayload = payload.toLowerCase();

    if (lowerBody.indexOf(lowerPayload) !== -1) {
        return true;
    }

    var decodedPayload = payload
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&amp;/g, '&');

    if (decodedPayload !== payload && lowerBody.indexOf(decodedPayload.toLowerCase()) !== -1) {
        return true;
    }

    return false;
};

XssTester.prototype.printSummary = function () {
    var self = this;
    console.log('');
    console.log('========================================');
    console.log('  XSS 测试总结');
    console.log('========================================');
    console.log('总测试数:', self.results.length);
    console.log('发现漏洞:', self.vulnerabilities.length);
    console.log('安全测试:', self.results.length - self.vulnerabilities.length);
    console.log('');

    if (self.vulnerabilities.length > 0) {
        console.log('漏洞详情:');
        self.vulnerabilities.forEach(function (v, i) {
            console.log('  ' + (i + 1) + '. ' + v.payloadName + ' - ' + v.endpoint);
            console.log('     类型: ' + v.payloadType);
            console.log('     状态码: ' + v.statusCode);
        });
    } else {
        console.log('未发现 XSS 漏洞 ✓');
    }

    var reportPath = path.join(__dirname, 'reports', 'xss-test-' + Date.now() + '.json');
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
            console.log('用法: node scripts/security/xss-test.js [options]');
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
    var tester = new XssTester(options);
    tester.run();
}

module.exports = XssTester;
