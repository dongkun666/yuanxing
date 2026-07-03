/**
 * SQL 注入测试
 * 测试应用程序对 SQL 注入攻击的防护能力
 *
 * 用法: node scripts/security/sql-injection-test.js [options]
 */

'use strict';

var http = require('http');
var https = require('https');
var url = require('url');
var fs = require('fs');
var path = require('path');

var DEFAULT_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:3847';

var sqlInjectionPayloads = [
    { name: 'single-quote', payload: "'", type: 'error-based', description: '单引号测试' },
    { name: 'or-1-1', payload: "' OR '1'='1", type: 'boolean-based', description: 'OR 1=1 恒真' },
    { name: 'union-select', payload: "' UNION SELECT 1,2,3--", type: 'union-based', description: 'UNION 注入' },
    { name: 'sleep-injection', payload: "'; SLEEP(5)--", type: 'time-based', description: '时间盲注' },
    { name: 'boolean-blind', payload: "' AND 1=1--", type: 'boolean-based', description: '布尔盲注 - 真' },
    { name: 'boolean-blind-false', payload: "' AND 1=2--", type: 'boolean-based', description: '布尔盲注 - 假' },
    { name: 'stacked-queries', payload: "'; DROP TABLE users--", type: 'stacked', description: '堆叠查询' },
    { name: 'comment-injection', payload: "test'--", type: 'comment', description: '注释注入' },
    { name: 'hex-injection', payload: "0x414243", type: 'hex', description: '十六进制注入' },
    { name: 'like-injection', payload: "%' OR '1'='1", type: 'like', description: 'LIKE 注入' },
    { name: 'numeric-injection', payload: "1 OR 1=1", type: 'numeric', description: '数字型注入' },
    { name: 'second-order', payload: "test');--", type: 'second-order', description: '二阶注入' }
];

var injectionPoints = [
    { method: 'GET', path: '/api/cases', param: 'cause', description: '案由参数' },
    { method: 'GET', path: '/api/cases', param: 'court', description: '法院参数' },
    { method: 'GET', path: '/api/laws', param: 'law_type', description: '法规类型参数' },
    { method: 'GET', path: '/api/companies', param: 'name', description: '企业名称参数' },
    { method: 'GET', path: '/api/companies', param: 'region', description: '地区参数' }
];

function SqlInjectionTester(options) {
    this.baseUrl = options.baseUrl || DEFAULT_BASE_URL;
    this.results = [];
    this.vulnerabilities = [];
    this.normalResponses = {};
}

SqlInjectionTester.prototype.run = function () {
    var self = this;
    console.log('========================================');
    console.log('  LexPrime SQL 注入测试');
    console.log('========================================');
    console.log('目标地址:', self.baseUrl);
    console.log('测试 Payload 数量:', sqlInjectionPayloads.length);
    console.log('注入点数量:', injectionPoints.length);
    console.log('');

    self.collectBaseline(function () {
        var pointIndex = 0;
        var payloadIndex = 0;

        function nextTest() {
            if (pointIndex >= injectionPoints.length) {
                self.printSummary();
                return;
            }

            if (payloadIndex >= sqlInjectionPayloads.length) {
                payloadIndex = 0;
                pointIndex++;
                setTimeout(nextTest, 200);
                return;
            }

            var point = injectionPoints[pointIndex];
            var payload = sqlInjectionPayloads[payloadIndex++];

            self.testInjection(point, payload, function () {
                setTimeout(nextTest, 100);
            });
        }

        nextTest();
    });
};

SqlInjectionTester.prototype.collectBaseline = function (callback) {
    var self = this;
    var completed = 0;
    var total = injectionPoints.length;

    injectionPoints.forEach(function (point) {
        var fullUrl = self.baseUrl + point.path + '?' + point.param + '=normal_test_value';
        var parsed = url.parse(fullUrl);
        var isHttps = parsed.protocol === 'https:';
        var lib = isHttps ? https : http;

        var options = {
            hostname: parsed.hostname,
            port: parsed.port || (isHttps ? 443 : 80),
            path: parsed.path,
            method: point.method,
            headers: { 'User-Agent': 'SecurityScanner/1.0' }
        };

        var req = lib.request(options, function (res) {
            var chunks = [];
            res.on('data', function (chunk) {
                chunks.push(chunk);
            });
            res.on('end', function () {
                var body = Buffer.concat(chunks).toString();
                self.normalResponses[point.path + '?' + point.param] = {
                    statusCode: res.statusCode,
                    bodyLength: body.length,
                    body: body.substring(0, 500)
                };
                completed++;
                if (completed >= total) {
                    callback();
                }
            });
        });

        req.on('error', function () {
            completed++;
            if (completed >= total) {
                callback();
            }
        });

        req.setTimeout(5000, function () {
            req.abort();
        });

        req.end();
    });
};

SqlInjectionTester.prototype.testInjection = function (point, payload, callback) {
    var self = this;
    var fullUrl = self.baseUrl + point.path + '?' + point.param + '=' + encodeURIComponent(payload.payload);
    var parsed = url.parse(fullUrl);
    var isHttps = parsed.protocol === 'https:';
    var lib = isHttps ? https : http;

    var options = {
        hostname: parsed.hostname,
        port: parsed.port || (isHttps ? 443 : 80),
        path: parsed.path,
        method: point.method,
        headers: { 'User-Agent': 'SecurityScanner/1.0' }
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

            var isVulnerable = self.checkSqlInjection(res, body, latency, point, payload);

            var result = {
                injectionPoint: point.description + ' (' + point.param + ')',
                payloadName: payload.name,
                payloadType: payload.type,
                payload: payload.payload,
                statusCode: res.statusCode,
                latency: latency,
                bodyLength: body.length,
                vulnerable: isVulnerable
            };

            self.results.push(result);

            if (isVulnerable) {
                self.vulnerabilities.push(result);
                console.log('[!] SQL 注入漏洞: ' + payload.name + ' @ ' + point.param);
            } else {
                console.log('[✓] 安全: ' + payload.name + ' @ ' + point.param);
            }

            callback();
        });
    });

    req.on('error', function (err) {
        self.results.push({
            injectionPoint: point.description + ' (' + point.param + ')',
            payloadName: payload.name,
            payloadType: payload.type,
            payload: payload.payload,
            statusCode: 0,
            latency: 0,
            vulnerable: false,
            error: err.message
        });
        console.log('[x] 请求失败: ' + point.param + ' - ' + err.message);
        callback();
    });

    req.setTimeout(10000, function () {
        req.abort();
    });

    req.end();
};

SqlInjectionTester.prototype.checkSqlInjection = function (res, body, latency, point, payload) {
    var statusCode = res.statusCode;
    var key = point.path + '?' + point.param;
    var normal = this.normalResponses[key];

    if (statusCode >= 500) {
        var errorPatterns = [
            'sql', 'syntax', 'error', 'mysql', 'postgresql',
            'sqlite', 'ORA-', 'PG::', 'Warning: mysql',
            'unclosed quotation', 'syntax error',
            'invalid query', 'database error'
        ];
        var lowerBody = body.toLowerCase();
        for (var i = 0; i < errorPatterns.length; i++) {
            if (lowerBody.indexOf(errorPatterns[i]) !== -1) {
                return true;
            }
        }
    }

    if (payload.type === 'time-based' && latency > 4000) {
        return true;
    }

    if (normal && normal.statusCode === statusCode) {
        var diff = Math.abs(body.length - normal.bodyLength);
        if (diff > normal.bodyLength * 0.5 && payload.type === 'boolean-based') {
            return true;
        }
    }

    return false;
};

SqlInjectionTester.prototype.printSummary = function () {
    var self = this;
    console.log('');
    console.log('========================================');
    console.log('  SQL 注入测试总结');
    console.log('========================================');
    console.log('总测试数:', self.results.length);
    console.log('发现漏洞:', self.vulnerabilities.length);
    console.log('通过测试:', self.results.length - self.vulnerabilities.length);
    console.log('');

    if (self.vulnerabilities.length > 0) {
        console.log('漏洞详情:');
        self.vulnerabilities.forEach(function (v, i) {
            console.log('  ' + (i + 1) + '. ' + v.payloadName + ' - ' + v.injectionPoint);
            console.log('     类型: ' + v.payloadType);
            console.log('     状态码: ' + v.statusCode);
        });
    } else {
        console.log('未发现 SQL 注入漏洞 ✓');
    }

    console.log('\n安全建议:');
    console.log('  1. 使用参数化查询/预编译语句');
    console.log('  2. 输入验证和过滤');
    console.log('  3. ORM 框架');
    console.log('  4. 最小权限原则');
    console.log('  5. Web 应用防火墙 (WAF)');

    var reportPath = path.join(__dirname, 'reports', 'sql-injection-test-' + Date.now() + '.json');
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
            console.log('用法: node scripts/security/sql-injection-test.js [options]');
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
    var tester = new SqlInjectionTester(options);
    tester.run();
}

module.exports = SqlInjectionTester;
