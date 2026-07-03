/**
 * 错误注入工具
 * 模拟服务错误，测试系统的容错能力
 *
 * 用法: node scripts/chaos/error-injector.js [options]
 */

'use strict';

var http = require('http');
var https = require('https');
var url = require('url');
var fs = require('fs');
var path = require('path');

var DEFAULT_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:3847';
var DEFAULT_DURATION = 60;
var DEFAULT_ERROR_RATE = 0.2;

var errorTypes = [
    { code: 500, name: 'internal_server_error', description: '500 内部服务器错误' },
    { code: 502, name: 'bad_gateway', description: '502 网关错误' },
    { code: 503, name: 'service_unavailable', description: '503 服务不可用' },
    { code: 504, name: 'gateway_timeout', description: '504 网关超时' },
    { code: 429, name: 'too_many_requests', description: '429 请求过多' },
    { code: 0, name: 'connection_error', description: '连接错误（模拟断开）' }
];

var testEndpoints = [
    { method: 'GET', path: '/api/health', name: 'health-check' },
    { method: 'GET', path: '/api/cases?limit=20', name: 'cases-list' },
    { method: 'POST', path: '/api/search', name: 'search', body: JSON.stringify({
        query: 'test',
        index: 'cases',
        page: 1,
        size: 20
    }), headers: { 'Content-Type': 'application/json' } }
];

function ErrorInjector(options) {
    this.baseUrl = options.baseUrl || DEFAULT_BASE_URL;
    this.duration = options.duration || DEFAULT_DURATION;
    this.errorRate = options.errorRate || DEFAULT_ERROR_RATE;
    this.stats = {
        totalRequests: 0,
        successfulRequests: 0,
        errorRequests: 0,
        errorDistribution: {},
        errorTypeDetails: {},
        startTime: 0,
        endTime: 0
    };
    this.stopped = false;
    this.activeRequests = 0;
}

ErrorInjector.prototype.run = function () {
    var self = this;
    console.log('========================================');
    console.log('  LexPrime 混沌工程 - 错误注入');
    console.log('========================================');
    console.log('目标地址:', self.baseUrl);
    console.log('测试时长:', self.duration, '秒');
    console.log('错误注入率:', (self.errorRate * 100).toFixed(0) + '%');
    console.log('错误类型:', errorTypes.map(function (e) { return e.name; }).join(', '));
    console.log('');

    self.stats.startTime = Date.now();
    self.startSending();

    setTimeout(function () {
        console.log('\n[停止注入中...]');
        self.stopped = true;
        setTimeout(function () {
            self.stats.endTime = Date.now();
            self.printSummary();
        }, 2000);
    }, self.duration * 1000);
};

ErrorInjector.prototype.startSending = function () {
    var self = this;

    function sendLoop() {
        if (self.stopped) {
            return;
        }

        if (self.activeRequests < 30) {
            var endpoint = testEndpoints[Math.floor(Math.random() * testEndpoints.length)];
            self.sendRequest(endpoint);
        }

        setTimeout(sendLoop, 30 + Math.random() * 70);
    }

    sendLoop();
};

ErrorInjector.prototype.sendRequest = function (endpoint) {
    var self = this;
    var shouldInjectError = Math.random() < self.errorRate;
    var selectedError = null;

    if (shouldInjectError) {
        selectedError = errorTypes[Math.floor(Math.random() * errorTypes.length)];
    }

    var parsed = url.parse(self.baseUrl + endpoint.path);
    var isHttps = parsed.protocol === 'https:';
    var lib = isHttps ? https : http;

    var options = {
        hostname: parsed.hostname,
        port: parsed.port || (isHttps ? 443 : 80),
        path: parsed.path,
        method: endpoint.method,
        headers: endpoint.headers || {}
    };

    self.stats.totalRequests++;
    self.activeRequests++;

    if (shouldInjectError && selectedError.code === 0) {
        setTimeout(function () {
            self.recordError(selectedError);
            self.activeRequests--;
        }, 100);
        return;
    }

    var req = lib.request(options, function (res) {
        var chunks = [];
        res.on('data', function (chunk) {
            chunks.push(chunk);
        });
        res.on('end', function () {
            if (res.statusCode >= 500) {
                self.stats.errorRequests++;
                var codeStr = String(res.statusCode);
                self.stats.errorDistribution[codeStr] = (self.stats.errorDistribution[codeStr] || 0) + 1;
            } else {
                self.stats.successfulRequests++;
            }
            self.activeRequests--;
        });
    });

    req.on('error', function (err) {
        self.stats.errorRequests++;
        self.stats.errorDistribution['connection_error'] = (self.stats.errorDistribution['connection_error'] || 0) + 1;
        self.activeRequests--;
    });

    req.setTimeout(5000, function () {
        req.abort();
    });

    if (endpoint.body) {
        req.write(endpoint.body);
    }
    req.end();
};

ErrorInjector.prototype.recordError = function (errorType) {
    this.stats.errorRequests++;
    var key = errorType.name;
    this.stats.errorDistribution[key] = (this.stats.errorDistribution[key] || 0) + 1;

    if (!this.stats.errorTypeDetails[key]) {
        this.stats.errorTypeDetails[key] = {
            count: 0,
            description: errorType.description,
            code: errorType.code
        };
    }
    this.stats.errorTypeDetails[key].count++;
};

ErrorInjector.prototype.printSummary = function () {
    var self = this;
    var stats = self.stats;
    var duration = (stats.endTime - stats.startTime) / 1000;

    console.log('\n========================================');
    console.log('  错误注入实验总结');
    console.log('========================================');
    console.log('实验时长: ' + duration.toFixed(2) + ' 秒');
    console.log('');
    console.log('总请求数: ' + stats.totalRequests);
    console.log('成功请求: ' + stats.successfulRequests);
    console.log('错误请求: ' + stats.errorRequests + ' (' +
        (stats.totalRequests > 0 ? (stats.errorRequests / stats.totalRequests * 100).toFixed(1) : 0) + '%)');
    console.log('');
    console.log('错误分布:');
    Object.keys(stats.errorDistribution).forEach(function (key) {
        var count = stats.errorDistribution[key];
        var pct = stats.errorRequests > 0 ? (count / stats.errorRequests * 100).toFixed(1) : 0;
        console.log('  ' + key + ': ' + count + ' (' + pct + '%)');
    });
    console.log('');
    console.log('系统表现:');
    console.log('  吞吐量: ' + (stats.totalRequests / duration).toFixed(2) + ' req/s');
    console.log('  成功率: ' + (stats.totalRequests > 0
        ? (stats.successfulRequests / stats.totalRequests * 100).toFixed(2)
        : 0) + '%');

    var reportPath = path.join(__dirname, 'reports', 'error-injection-' + Date.now() + '.json');
    try {
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify({
            baseUrl: self.baseUrl,
            duration: self.duration,
            errorRate: self.errorRate,
            timestamp: new Date().toISOString(),
            stats: stats
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
        } else if (arg === '--duration' && args[i + 1]) {
            options.duration = parseInt(args[++i], 10);
        } else if (arg === '--rate' && args[i + 1]) {
            options.errorRate = parseFloat(args[++i]);
        } else if (arg === '--help' || arg === '-h') {
            console.log('用法: node scripts/chaos/error-injector.js [options]');
            console.log('');
            console.log('选项:');
            console.log('  --url <url>          API 基础地址 (默认: http://127.0.0.1:3847)');
            console.log('  --duration <seconds> 实验时长 (默认: 60)');
            console.log('  --rate <0-1>         错误注入率 (默认: 0.2)');
            console.log('  --help, -h           显示帮助');
            process.exit(0);
        }
    }

    return options;
}

if (require.main === module) {
    var options = parseArgs();
    var injector = new ErrorInjector(options);
    injector.run();
}

module.exports = ErrorInjector;
