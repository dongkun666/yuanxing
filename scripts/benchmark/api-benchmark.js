/**
 * API 性能基准测试
 * 用于测量 API 端点的基础性能指标
 *
 * 用法: node scripts/benchmark/api-benchmark.js [options]
 */

'use strict';

var http = require('http');
var https = require('https');
var url = require('url');
var fs = require('fs');
var path = require('path');

var DEFAULT_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:3847';
var DEFAULT_DURATION = 10;
var DEFAULT_CONNECTIONS = 10;
var DEFAULT_PIPELINING = 1;

var endpoints = [
    { method: 'GET', path: '/api/health', name: 'health-check' },
    { method: 'GET', path: '/api/cases?limit=20', name: 'cases-list' },
    { method: 'GET', path: '/api/laws?limit=20', name: 'laws-list' },
    { method: 'GET', path: '/api/companies?limit=20', name: 'companies-list' },
    { method: 'POST', path: '/api/search', name: 'search-cases', body: JSON.stringify({
        query: '合同纠纷',
        index: 'cases',
        page: 1,
        size: 20
    }), headers: { 'Content-Type': 'application/json' } }
];

function BenchmarkRunner(options) {
    this.baseUrl = options.baseUrl || DEFAULT_BASE_URL;
    this.duration = options.duration || DEFAULT_DURATION;
    this.connections = options.connections || DEFAULT_CONNECTIONS;
    this.pipelining = options.pipelining || DEFAULT_PIPELINING;
    this.results = [];
}

BenchmarkRunner.prototype.run = function () {
    var self = this;
    console.log('========================================');
    console.log('  LexPrime API 性能基准测试');
    console.log('========================================');
    console.log('目标地址:', self.baseUrl);
    console.log('测试时长:', self.duration, '秒');
    console.log('并发连接:', self.connections);
    console.log('');

    var index = 0;
    function next() {
        if (index >= endpoints.length) {
            self.printSummary();
            return;
        }
        var endpoint = endpoints[index++];
        self.testEndpoint(endpoint, function () {
            setTimeout(next, 1000);
        });
    }
    next();
};

BenchmarkRunner.prototype.testEndpoint = function (endpoint, callback) {
    var self = this;
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

    var stats = {
        name: endpoint.name,
        method: endpoint.method,
        path: endpoint.path,
        requests: 0,
        success: 0,
        errors: 0,
        totalLatency: 0,
        minLatency: Infinity,
        maxLatency: 0,
        latencies: [],
        statusCodes: {},
        startTime: Date.now(),
        endTime: 0
    };

    var activeRequests = 0;
    var stopped = false;

    function makeRequest() {
        if (stopped) {
            return;
        }

        var reqStart = Date.now();
        var req = lib.request(options, function (res) {
            var chunks = [];
            res.on('data', function (chunk) {
                chunks.push(chunk);
            });
            res.on('end', function () {
                var latency = Date.now() - reqStart;
                stats.requests++;
                stats.success++;
                stats.totalLatency += latency;
                stats.minLatency = Math.min(stats.minLatency, latency);
                stats.maxLatency = Math.max(stats.maxLatency, latency);
                stats.latencies.push(latency);
                stats.statusCodes[res.statusCode] = (stats.statusCodes[res.statusCode] || 0) + 1;
                activeRequests--;
                if (!stopped) {
                    makeRequest();
                }
            });
        });

        req.on('error', function (err) {
            stats.requests++;
            stats.errors++;
            activeRequests--;
            if (!stopped) {
                makeRequest();
            }
        });

        if (endpoint.body) {
            req.write(endpoint.body);
        }
        req.end();
        activeRequests++;
    }

    for (var i = 0; i < self.connections; i++) {
        makeRequest();
    }

    setTimeout(function () {
        stopped = true;
        stats.endTime = Date.now();
        stats.duration = (stats.endTime - stats.startTime) / 1000;
        stats.avgLatency = stats.success > 0 ? stats.totalLatency / stats.success : 0;
        stats.rps = stats.requests / stats.duration;
        stats.latencies.sort(function (a, b) { return a - b; });
        stats.p50 = self.percentile(stats.latencies, 50);
        stats.p95 = self.percentile(stats.latencies, 95);
        stats.p99 = self.percentile(stats.latencies, 99);

        self.results.push(stats);
        self.printEndpointResult(stats);
        callback();
    }, self.duration * 1000);
};

BenchmarkRunner.prototype.percentile = function (sortedArr, p) {
    if (sortedArr.length === 0) {
        return 0;
    }
    var index = Math.ceil(p / 100 * sortedArr.length) - 1;
    return sortedArr[Math.max(0, Math.min(index, sortedArr.length - 1))];
};

BenchmarkRunner.prototype.printEndpointResult = function (stats) {
    console.log('--- ' + stats.name + ' (' + stats.method + ' ' + stats.path + ') ---');
    console.log('  请求总数: ' + stats.requests);
    console.log('  成功: ' + stats.success + ', 失败: ' + stats.errors);
    console.log('  成功率: ' + (stats.requests > 0 ? (stats.success / stats.requests * 100).toFixed(2) : 0) + '%');
    console.log('  RPS: ' + stats.rps.toFixed(2));
    console.log('  延迟 - 最小: ' + stats.minLatency + 'ms, 平均: ' + stats.avgLatency.toFixed(2) + 'ms, 最大: ' + stats.maxLatency + 'ms');
    console.log('  P50: ' + stats.p50 + 'ms, P95: ' + stats.p95 + 'ms, P99: ' + stats.p99 + 'ms');
    console.log('  状态码: ' + JSON.stringify(stats.statusCodes));
    console.log('');
};

BenchmarkRunner.prototype.printSummary = function () {
    var self = this;
    console.log('========================================');
    console.log('  测试总结');
    console.log('========================================');

    var totalRequests = 0;
    var totalSuccess = 0;
    var totalErrors = 0;

    self.results.forEach(function (r) {
        totalRequests += r.requests;
        totalSuccess += r.success;
        totalErrors += r.errors;
    });

    console.log('总请求数: ' + totalRequests);
    console.log('总成功: ' + totalSuccess);
    console.log('总失败: ' + totalErrors);
    console.log('总成功率: ' + (totalRequests > 0 ? (totalSuccess / totalRequests * 100).toFixed(2) : 0) + '%');
    console.log('');

    var reportPath = path.join(__dirname, 'reports', 'benchmark-' + Date.now() + '.json');
    try {
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify({
            baseUrl: self.baseUrl,
            duration: self.duration,
            connections: self.connections,
            timestamp: new Date().toISOString(),
            results: self.results
        }, null, 2));
        console.log('报告已保存: ' + reportPath);
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
        } else if (arg === '--connections' && args[i + 1]) {
            options.connections = parseInt(args[++i], 10);
        } else if (arg === '--help' || arg === '-h') {
            console.log('用法: node scripts/benchmark/api-benchmark.js [options]');
            console.log('');
            console.log('选项:');
            console.log('  --url <url>           API 基础地址 (默认: http://127.0.0.1:3847)');
            console.log('  --duration <seconds>  测试时长 (默认: 10)');
            console.log('  --connections <n>     并发连接数 (默认: 10)');
            console.log('  --help, -h            显示帮助');
            process.exit(0);
        }
    }

    return options;
}

if (require.main === module) {
    var options = parseArgs();
    var runner = new BenchmarkRunner(options);
    runner.run();
}

module.exports = BenchmarkRunner;
