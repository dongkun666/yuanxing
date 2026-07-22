/**
 * 延迟注入工具
 * 在 API 请求中注入随机延迟，模拟网络波动和服务降级
 *
 * 用法: node scripts/chaos/latency-injector.js [options]
 */

'use strict';

var http = require('http');
var https = require('https');
var url = require('url');
var fs = require('fs');
var path = require('path');

var DEFAULT_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:3847';
var DEFAULT_DURATION = 60;
var DEFAULT_MIN_LATENCY = 100;
var DEFAULT_MAX_LATENCY = 2000;
var DEFAULT_INJECTION_RATE = 0.3;

var testEndpoints = [
    { method: 'GET', path: '/api/health', name: 'health-check' },
    { method: 'GET', path: '/api/cases?limit=20', name: 'cases-list' },
    { method: 'GET', path: '/api/laws?limit=20', name: 'laws-list' },
    { method: 'POST', path: '/api/search', name: 'search', body: JSON.stringify({
        query: '合同',
        index: 'cases',
        page: 1,
        size: 20
    }), headers: { 'Content-Type': 'application/json' } }
];

function LatencyInjector(options) {
    this.baseUrl = options.baseUrl || DEFAULT_BASE_URL;
    this.duration = options.duration || DEFAULT_DURATION;
    this.minLatency = options.minLatency || DEFAULT_MIN_LATENCY;
    this.maxLatency = options.maxLatency || DEFAULT_MAX_LATENCY;
    this.injectionRate = options.injectionRate || DEFAULT_INJECTION_RATE;
    this.stats = {
        totalRequests: 0,
        injectedRequests: 0,
        normalRequests: 0,
        totalLatency: 0,
        minObserved: Infinity,
        maxObserved: 0,
        errors: 0,
        startTime: 0,
        endTime: 0
    };
    this.stopped = false;
    this.activeRequests = 0;
}

LatencyInjector.prototype.run = function () {
    var self = this;
    console.log('========================================');
    console.log('  LexPrime 混沌工程 - 延迟注入');
    console.log('========================================');
    console.log('目标地址:', self.baseUrl);
    console.log('测试时长:', self.duration, '秒');
    console.log('延迟范围:', self.minLatency + 'ms - ' + self.maxLatency + 'ms');
    console.log('注入概率:', (self.injectionRate * 100).toFixed(0) + '%');
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

LatencyInjector.prototype.startSending = function () {
    var self = this;

    function sendLoop() {
        if (self.stopped) {
            return;
        }

        if (self.activeRequests < 20) {
            var endpoint = testEndpoints[Math.floor(Math.random() * testEndpoints.length)];
            self.sendRequest(endpoint);
        }

        setTimeout(sendLoop, 50 + Math.random() * 100);
    }

    sendLoop();
};

LatencyInjector.prototype.sendRequest = function (endpoint) {
    var self = this;
    var shouldInject = Math.random() < self.injectionRate;
    var injectedLatency = shouldInject
        ? Math.floor(self.minLatency + Math.random() * (self.maxLatency - self.minLatency))
        : 0;

    if (shouldInject) {
        self.simulateLatency(injectedLatency);
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

    var reqStart = Date.now();
    self.stats.totalRequests++;
    self.activeRequests++;

    var req = lib.request(options, function (res) {
        var chunks = [];
        res.on('data', function (chunk) {
            chunks.push(chunk);
        });
        res.on('end', function () {
            var actualLatency = Date.now() - reqStart;
            var totalLatency = actualLatency + injectedLatency;

            if (shouldInject) {
                self.stats.injectedRequests++;
            } else {
                self.stats.normalRequests++;
            }

            self.stats.totalLatency += totalLatency;
            self.stats.minObserved = Math.min(self.stats.minObserved, totalLatency);
            self.stats.maxObserved = Math.max(self.stats.maxObserved, totalLatency);

            self.activeRequests--;
        });
    });

    req.on('error', function (err) {
        self.stats.errors++;
        self.activeRequests--;
    });

    if (endpoint.body) {
        req.write(endpoint.body);
    }
    req.end();
};

LatencyInjector.prototype.simulateLatency = function (ms) {
    var start = Date.now();
    while (Date.now() - start < ms) {
        // 忙等待模拟延迟（仅用于测试）
    }
};

LatencyInjector.prototype.printSummary = function () {
    var self = this;
    var stats = self.stats;
    var duration = (stats.endTime - stats.startTime) / 1000;

    console.log('\n========================================');
    console.log('  延迟注入实验总结');
    console.log('========================================');
    console.log('实验时长: ' + duration.toFixed(2) + ' 秒');
    console.log('');
    console.log('总请求数: ' + stats.totalRequests);
    console.log('注入延迟请求: ' + stats.injectedRequests + ' (' +
        (stats.totalRequests > 0 ? (stats.injectedRequests / stats.totalRequests * 100).toFixed(1) : 0) + '%)');
    console.log('正常请求: ' + stats.normalRequests);
    console.log('错误请求: ' + stats.errors);
    console.log('');
    console.log('延迟统计:');
    console.log('  注入范围: ' + self.minLatency + 'ms - ' + self.maxLatency + 'ms');
    console.log('  最小观测: ' + (stats.minObserved === Infinity ? 0 : stats.minObserved) + 'ms');
    console.log('  最大观测: ' + stats.maxObserved + 'ms');
    console.log('  平均延迟: ' + (stats.totalRequests > 0
        ? (stats.totalLatency / stats.totalRequests).toFixed(2)
        : 0) + 'ms');
    console.log('');
    console.log('系统表现:');
    console.log('  吞吐量: ' + (stats.totalRequests / duration).toFixed(2) + ' req/s');
    console.log('  错误率: ' + (stats.totalRequests > 0
        ? (stats.errors / stats.totalRequests * 100).toFixed(2)
        : 0) + '%');

    var reportPath = path.join(__dirname, 'reports', 'latency-injection-' + Date.now() + '.json');
    try {
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify({
            baseUrl: self.baseUrl,
            duration: self.duration,
            minLatency: self.minLatency,
            maxLatency: self.maxLatency,
            injectionRate: self.injectionRate,
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
        } else if (arg === '--min' && args[i + 1]) {
            options.minLatency = parseInt(args[++i], 10);
        } else if (arg === '--max' && args[i + 1]) {
            options.maxLatency = parseInt(args[++i], 10);
        } else if (arg === '--rate' && args[i + 1]) {
            options.injectionRate = parseFloat(args[++i]);
        } else if (arg === '--help' || arg === '-h') {
            console.log('用法: node scripts/chaos/latency-injector.js [options]');
            console.log('');
            console.log('选项:');
            console.log('  --url <url>          API 基础地址 (默认: http://127.0.0.1:3847)');
            console.log('  --duration <seconds> 实验时长 (默认: 60)');
            console.log('  --min <ms>           最小延迟 (默认: 100)');
            console.log('  --max <ms>           最大延迟 (默认: 2000)');
            console.log('  --rate <0-1>         注入概率 (默认: 0.3)');
            console.log('  --help, -h           显示帮助');
            process.exit(0);
        }
    }

    return options;
}

if (require.main === module) {
    var options = parseArgs();
    var injector = new LatencyInjector(options);
    injector.run();
}

module.exports = LatencyInjector;
