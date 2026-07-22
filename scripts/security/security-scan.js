/**
 * 综合安全扫描
 * 整合所有安全测试，生成综合安全报告
 *
 * 用法: node scripts/security/security-scan.js [options]
 */

'use strict';

var fs = require('fs');
var path = require('path');
var http = require('http');
var https = require('https');
var urlModule = require('url');

var XssTester = require('./xss-test');
var CsrfTester = require('./csrf-test');
var SqlInjectionTester = require('./sql-injection-test');
var AuthBypassTester = require('./auth-bypass-test');

var DEFAULT_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:3847';

var securityHeadersChecks = [
    { header: 'X-Frame-Options', description: '防止点击劫持', recommended: 'DENY or SAMEORIGIN' },
    { header: 'X-Content-Type-Options', description: 'MIME 类型嗅探防护', recommended: 'nosniff' },
    { header: 'X-XSS-Protection', description: 'XSS 防护', recommended: '1; mode=block' },
    { header: 'Strict-Transport-Security', description: '强制 HTTPS', recommended: 'max-age=31536000' },
    { header: 'Content-Security-Policy', description: '内容安全策略', recommended: '设置适当的 CSP' },
    { header: 'Referrer-Policy', description: 'Referrer 策略', recommended: 'strict-origin-when-cross-origin' },
    { header: 'Permissions-Policy', description: '权限策略', recommended: '限制敏感功能' }
];

var infoDisclosureChecks = [
    { pattern: 'server:', name: 'Server 头信息泄露' },
    { pattern: 'x-powered-by', name: 'X-Powered-By 泄露' },
    { pattern: 'stack trace', name: '堆栈跟踪泄露' },
    { pattern: 'debug', name: '调试信息泄露' }
];

function SecurityScanner(options) {
    this.baseUrl = options.baseUrl || DEFAULT_BASE_URL;
    this.results = {
        xss: null,
        csrf: null,
        sqlInjection: null,
        authBypass: null,
        headers: null,
        infoDisclosure: null
    };
    this.totalVulnerabilities = 0;
}

SecurityScanner.prototype.run = function () {
    var self = this;
    console.log('========================================');
    console.log('  LexPrime 综合安全扫描');
    console.log('========================================');
    console.log('目标地址:', self.baseUrl);
    console.log('扫描时间:', new Date().toISOString());
    console.log('');

    self.checkSecurityHeaders(function () {
        self.checkInformationDisclosure(function () {
            console.log('\n[1/4] 运行 XSS 测试...');
            var xssTester = new XssTester({ baseUrl: self.baseUrl });
            var origXssPrint = xssTester.printSummary;
            xssTester.printSummary = function () {
                self.results.xss = {
                    total: this.results.length,
                    vulnerabilities: this.vulnerabilities.length,
                    details: this.vulnerabilities
                };
                self.totalVulnerabilities += this.vulnerabilities.length;
                console.log('  XSS 测试完成: ' + this.vulnerabilities.length + ' 个漏洞');

                console.log('\n[2/4] 运行 CSRF 测试...');
                var csrfTester = new CsrfTester({ baseUrl: self.baseUrl });
                var origCsrfPrint = csrfTester.printSummary;
                csrfTester.printSummary = function () {
                    self.results.csrf = {
                        total: this.results.length,
                        vulnerabilities: this.findings.length,
                        details: this.findings
                    };
                    self.totalVulnerabilities += this.findings.length;
                    console.log('  CSRF 测试完成: ' + this.findings.length + ' 个风险');

                    console.log('\n[3/4] 运行 SQL 注入测试...');
                    var sqlTester = new SqlInjectionTester({ baseUrl: self.baseUrl });
                    var origSqlPrint = sqlTester.printSummary;
                    sqlTester.printSummary = function () {
                        self.results.sqlInjection = {
                            total: this.results.length,
                            vulnerabilities: this.vulnerabilities.length,
                            details: this.vulnerabilities
                        };
                        self.totalVulnerabilities += this.vulnerabilities.length;
                        console.log('  SQL 注入测试完成: ' + this.vulnerabilities.length + ' 个漏洞');

                        console.log('\n[4/4] 运行认证绕过测试...');
                        var authTester = new AuthBypassTester({ baseUrl: self.baseUrl });
                        var origAuthPrint = authTester.printSummary;
                        authTester.printSummary = function () {
                            self.results.authBypass = {
                                total: this.results.length,
                                vulnerabilities: this.vulnerabilities.length,
                                details: this.vulnerabilities
                            };
                            self.totalVulnerabilities += this.vulnerabilities.length;
                            console.log('  认证绕过测试完成: ' + this.vulnerabilities.length + ' 个漏洞');

                            self.generateReport();
                        };
                        authTester.printSummary = origAuthPrint.bind(authTester);
                        authTester.run();
                    };
                    sqlTester.printSummary = origSqlPrint.bind(sqlTester);
                    sqlTester.run();
                };
                csrfTester.printSummary = origCsrfPrint.bind(csrfTester);
                csrfTester.run();
            };
            xssTester.printSummary = origXssPrint.bind(xssTester);
            xssTester.run();
        });
    });
};

SecurityScanner.prototype.checkSecurityHeaders = function (callback) {
    var self = this;
    console.log('[0/4] 检查安全响应头...');

    var parsed = urlModule.parse(self.baseUrl + '/api/health');
    var isHttps = parsed.protocol === 'https:';
    var lib = isHttps ? https : http;

    var options = {
        hostname: parsed.hostname,
        port: parsed.port || (isHttps ? 443 : 80),
        path: parsed.path,
        method: 'GET',
        headers: { 'User-Agent': 'SecurityScanner/1.0' }
    };

    var req = lib.request(options, function (res) {
        var missingHeaders = [];
        var presentHeaders = [];

        securityHeadersChecks.forEach(function (check) {
            var headerLower = check.header.toLowerCase();
            if (res.headers[headerLower]) {
                presentHeaders.push({
                    header: check.header,
                    value: res.headers[headerLower],
                    description: check.description
                });
            } else {
                missingHeaders.push({
                    header: check.header,
                    description: check.description,
                    recommended: check.recommended
                });
            }
        });

        self.results.headers = {
            present: presentHeaders,
            missing: missingHeaders,
            total: securityHeadersChecks.length,
            score: Math.round(presentHeaders.length / securityHeadersChecks.length * 100)
        };

        console.log('  安全头得分: ' + self.results.headers.score + '%');
        console.log('  已设置: ' + presentHeaders.length + '/' + securityHeadersChecks.length);

        callback();
    });

    req.on('error', function (err) {
        console.log('  安全头检查失败:', err.message);
        self.results.headers = { present: [], missing: [], total: 0, score: 0 };
        callback();
    });

    req.setTimeout(5000, function () {
        req.abort();
    });

    req.end();
};

SecurityScanner.prototype.checkInformationDisclosure = function (callback) {
    var self = this;
    console.log('\n[0/4] 检查信息泄露...');

    var parsed = urlModule.parse(self.baseUrl + '/api/health');
    var isHttps = parsed.protocol === 'https:';
    var lib = isHttps ? https : http;

    var options = {
        hostname: parsed.hostname,
        port: parsed.port || (isHttps ? 443 : 80),
        path: parsed.path,
        method: 'GET',
        headers: { 'User-Agent': 'SecurityScanner/1.0' }
    };

    var req = lib.request(options, function (res) {
        var chunks = [];
        res.on('data', function (chunk) {
            chunks.push(chunk);
        });
        res.on('end', function () {
            var body = Buffer.concat(chunks).toString().toLowerCase();
            var findings = [];

            infoDisclosureChecks.forEach(function (check) {
                var headerLower = check.pattern.toLowerCase();
                var headerMatch = Object.keys(res.headers).some(function (h) {
                    return h.toLowerCase().indexOf(headerLower) !== -1;
                });
                var bodyMatch = body.indexOf(headerLower) !== -1;
                if (headerMatch || bodyMatch) {
                    findings.push(check.name);
                }
            });

            var serverHeader = res.headers['server'] || res.headers['x-powered-by'];

            self.results.infoDisclosure = {
                findings: findings,
                serverHeader: serverHeader || null,
                count: findings.length
            };

            console.log('  发现信息泄露: ' + findings.length + ' 项');
            callback();
        });
    });

    req.on('error', function (err) {
        console.log('  信息泄露检查失败:', err.message);
        self.results.infoDisclosure = { findings: [], serverHeader: null, count: 0 };
        callback();
    });

    req.setTimeout(5000, function () {
        req.abort();
    });

    req.end();
};

SecurityScanner.prototype.generateReport = function () {
    var self = this;
    console.log('\n\n========================================');
    console.log('  综合安全扫描报告');
    console.log('========================================');

    var overallScore = self.calculateOverallScore();
    var riskLevel = overallScore >= 80 ? '低' : (overallScore >= 50 ? '中' : '高');

    console.log('目标地址: ' + self.baseUrl);
    console.log('扫描时间: ' + new Date().toISOString());
    console.log('');
    console.log('总体安全评分: ' + overallScore + '/100');
    console.log('风险等级: ' + riskLevel);
    console.log('总漏洞数: ' + self.totalVulnerabilities);
    console.log('');

    console.log('--- 各模块得分:');
    console.log('  XSS 防护: ' + self.getModuleScore('xss') + '/100');
    console.log('  CSRF 防护: ' + self.getModuleScore('csrf') + '/100');
    console.log('  SQL 注入防护: ' + self.getModuleScore('sqlInjection') + '/100');
    console.log('  认证安全: ' + self.getModuleScore('authBypass') + '/100');
    console.log('  安全响应头: ' + (self.results.headers ? self.results.headers.score : 0) + '/100');

    console.log('\n--- 安全建议:');
    self.printRecommendations();

    var reportPath = path.join(__dirname, 'reports', 'security-scan-' + Date.now() + '.json');
    try {
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify({
            baseUrl: self.baseUrl,
            timestamp: new Date().toISOString(),
            overallScore: overallScore,
            riskLevel: riskLevel,
            totalVulnerabilities: self.totalVulnerabilities,
            results: self.results
        }, null, 2));
        console.log('\n详细报告已保存: ' + reportPath);
    } catch (e) {
        console.warn('保存报告失败:', e.message);
    }

    console.log('\n扫描完成!');
};

SecurityScanner.prototype.calculateOverallScore = function () {
    var scores = [
        this.getModuleScore('xss'),
        this.getModuleScore('csrf'),
        this.getModuleScore('sqlInjection'),
        this.getModuleScore('authBypass'),
        this.results.headers ? this.results.headers.score : 0
    ];
    var sum = scores.reduce(function (a, b) { return a + b; }, 0);
    return Math.round(sum / scores.length);
};

SecurityScanner.prototype.getModuleScore = function (module) {
    var result = this.results[module];
    if (!result || !result.total) {
        return 100;
    }
    if (result.vulnerabilities === 0) {
        return 100;
    }
    var ratio = 1 - (result.vulnerabilities / result.total);
    return Math.max(0, Math.round(ratio * 100));
};

SecurityScanner.prototype.printRecommendations = function () {
    var recs = [];

    if (this.results.headers && this.results.headers.missing.length > 0) {
        recs.push('添加缺失的安全响应头: ' + this.results.headers.missing.map(function (m) { return m.header; }).join(', '));
    }
    if (this.results.xss && this.results.xss.vulnerabilities > 0) {
        recs.push('修复 XSS 漏洞，实施输入验证和输出编码');
    }
    if (this.results.csrf && this.results.csrf.vulnerabilities > 0) {
        recs.push('加强 CSRF 防护，使用 CSRF Token 和 Origin 验证');
    }
    if (this.results.sqlInjection && this.results.sqlInjection.vulnerabilities > 0) {
        recs.push('修复 SQL 注入漏洞，使用参数化查询');
    }
    if (this.results.authBypass && this.results.authBypass.vulnerabilities > 0) {
        recs.push('加强认证授权机制，实施细粒度权限控制');
    }
    if (this.results.infoDisclosure && this.results.infoDisclosure.count > 0) {
        recs.push('修复信息泄露问题，隐藏服务器版本信息');
    }

    if (recs.length === 0) {
        console.log('  所有检查项均通过 ✓');
    } else {
        recs.forEach(function (rec, i) {
            console.log('  ' + (i + 1) + '. ' + rec);
        });
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
            console.log('用法: node scripts/security/security-scan.js [options]');
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
    var scanner = new SecurityScanner(options);
    scanner.run();
}

module.exports = SecurityScanner;
