/**
 * 压力测试 - 极限压测
 * 逐步增加负载直到系统达到极限，找出系统瓶颈
 *
 * 用法: node scripts/benchmark/stress-test.js [options]
 */

'use strict';

var http = require('http');
var https = require('https');
var url = require('url');
var fs = require('fs');
var path = require('path');

var DEFAULT_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:3847';
var DEFAULT_START_CONNECTIONS = 10;
var DEFAULT_MAX_CONNECTIONS = 1000;
var DEFAULT_STEP_DURATION = 30;
var DEFAULT_STEP_INCREMENT = 50;
var DEFAULT_ERROR_THRESHOLD = 5;

var targetEndpoint = {
    method: 'GET',
    path: '/api/health',
    name: 'health-check'
};

function StressTest(options) {
    this.baseUrl = options.baseUrl || DEFAULT_BASE_URL;
    this.startConnections = options.startConnections || DEFAULT_START_CONNECTIONS;
    this.maxConnections = options.maxConnections || DEFAULT_MAX_CONNECTIONS;
    this.stepDuration = options.stepDuration || DEFAULT_STEP_DURATION;
    this.stepIncrement = options.stepIncrement || DEFAULT_STEP_INCREMENT;
    this.errorThreshold = options.errorThreshold || DEFAULT_ERROR_THRESHOLD;
    this.results = [];
    this.stopped = false;
}

StressTest.prototype.run = function () {
    var self = this;
    console.log('========================================');
    console.log('  LexPrime 压力测试 (极限压测)');
    console.log('========================================');
    console.log('目标地址:', self.baseUrl);
    console.log('起始并发:', self.startConnections);
    console.log('最大并发:', self.maxConnections);
    console.log('每阶时长:', self.stepDuration, '秒');
    console.log('步进增量:', self.stepIncrement);
    console.log('错误阈值:', self.errorThreshold + '%');
    console.log('目标端点:', targetEndpoint.method + ' ' + targetEndpoint.path);
    console.log('');

    var currentConnections = self.startConnections;
    var totalTime = 0;

    function nextStep() {
        if (self.stopped || currentConnections > self.maxConnections) {
            self.printSummary();
            return;
        }

        console.log('[阶段 ' + (self.results.length + 1) + '] 并发连接: ' + currentConnections);
        self.runStep(currentConnections, function (result) {
            self.results.push(result);
            self.printStepResult(result);

            var errorRate = result.requests > 0 ? (result.errors / result.requests * 100) : 0;
            if (errorRate > self.errorThreshold) {
                console.log('\n[警告] 错误率 (' + errorRate.toFixed(2) + '%) 超过阈值 (' + self.errorThreshold + '%)，停止测试');
                self.stopped = true;
                self.printSummary();
                return;
            }

            currentConnections += self.stepIncrement;
            totalTime += self.stepDuration;
            setTimeout(nextStep, 2000);
        });
    }

    nextStep();
};

StressTest.prototype.runStep = function (connections, callback) {
    var self = this;
    var parsed = url.parse(self.baseUrl + targetEndpoint.path);
    var isHttps = parsed.protocol === 'https:';
    var lib = isHttps ? https : http;

    var options = {
        hostname: parsed.hostname,
        port: parsed.port || (isHttps ? 443 : 80),
        path: parsed.path,
        method: targetEndpoint.method,
        headers: targetEndpoint.headers || {}
    };

    var stats = {
        connections: connections,
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

        req.end();
        activeRequests++;
    }

    for (var i = 0; i < connections; i++) {
        makeRequest();
    }

    setTimeout(function () {
        stopped = true;
        stats.endTime = Date.now();
        stats.duration = (stats.endTime - stats.startTime) / 1000;
        stats.avgLatency = stats.success > 0 ? stats.totalLatency / stats.success : 0;
        stats.rps = stats.requests / stats.duration;
        stats.errorRate = stats.requests > 0 ? (stats.errors / stats.requests * 100) : 0;
        stats.latencies.sort(function (a, b) { return a - b; });
        stats.p50 = self.percentile(stats.latencies, 50);
        stats.p95 = self.percentile(stats.latencies, 95);
        stats.p99 = self.percentile(stats.latencies, 99);

        callback(stats);
    }, self.stepDuration * 1000);
};

StressTest.prototype.percentile = function (sortedArr, p) {
    if (sortedArr.length === 0) {
        return 0;
    }
    var index = Math.ceil(p / 100 * sortedArr.length) - 1;
    return sortedArr[Math.max(0, Math.min(index, sortedArr.length - 1))];
};

StressTest.prototype.printStepResult = function (stats) {
    console.log('  请求数: ' + stats.requests + ', RPS: ' + stats.rps.toFixed(2));
    console.log('  成功: ' + stats.success + ', 失败: ' + stats.errors +
        ', 错误率: ' + stats.errorRate.toFixed(2) + '%');
    console.log('  延迟: 平均 ' + stats.avgLatency.toFixed(2) + 'ms, P95 ' + stats.p95 + 'ms, P99 ' + stats.p99 + 'ms');
    console.log('');
};

StressTest.prototype.printSummary = function () {
    var self = this;
    console.log('========================================');
    console.log('  压力测试总结');
    console.log('========================================');
    console.log('测试阶段数: ' + self.results.length);
    console.log('');

    if (self.results.length > 0) {
        var maxRps = 0;
        var maxRpsStep = null;
        var breakingPoint = null;

        self.results.forEach(function (r) {
            if (r.rps > maxRps) {
                maxRps = r.rps;
                maxRpsStep = r;
            }
            if (breakingPoint === null && r.errorRate > self.errorThreshold) {
                breakingPoint = r;
            }
        });

        console.log('峰值吞吐量: ' + maxRps.toFixed(2) + ' req/s');
        if (maxRpsStep) {
            console.log('  发生在并发 ' + maxRpsStep.connections + ' 时');
        }
        console.log('');

        if (breakingPoint) {
            console.log('系统临界点:');
            console.log('  并发连接: ' + breakingPoint.connections);
            console.log('  错误率: ' + breakingPoint.errorRate.toFixed(2) + '%');
            console.log('  吞吐量: ' + breakingPoint.rps.toFixed(2) + ' req/s');
        } else {
            console.log('在最大并发 (' + self.maxConnections + ') 下系统仍稳定运行');
        }
        console.log('');

        console.log('各阶段详情:');
        self.results.forEach(function (r, i) {
            console.log('  阶段 ' + (i + 1) + ' (并发 ' + r.connections + '): ' +
                r.rps.toFixed(2) + ' req/s, ' +
                'P95: ' + r.p95 + 'ms, ' +
                '错误率: ' + r.errorRate.toFixed(2) + '%');
        });
    }

    var reportPath = path.join(__dirname, 'reports', 'stress-test-' + Date.now() + '.json');
    try {
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify({
            baseUrl: self.baseUrl,
            startConnections: self.startConnections,
            maxConnections: self.maxConnections,
            stepDuration: self.stepDuration,
            stepIncrement: self.stepIncrement,
            errorThreshold: self.errorThreshold,
            timestamp: new Date().toISOString(),
            results: self.results
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
        } else if (arg === '--start' && args[i + 1]) {
            options.startConnections = parseInt(args[++i], 10);
        } else if (arg === '--max' && args[i + 1]) {
            options.maxConnections = parseInt(args[++i], 10);
        } else if (arg === '--step-duration' && args[i + 1]) {
            options.stepDuration = parseInt(args[++i], 10);
        } else if (arg === '--step-increment' && args[i + 1]) {
            options.stepIncrement = parseInt(args[++i], 10);
        } else if (arg === '--error-threshold' && args[i + 1]) {
            options.errorThreshold = parseFloat(args[++i]);
        } else if (arg === '--help' || arg === '-h') {
            console.log('用法: node scripts/benchmark/stress-test.js [options]');
            console.log('');
            console.log('选项:');
            console.log('  --url <url>             API 基础地址 (默认: http://127.0.0.1:3847)');
            console.log('  --start <n>             起始并发数 (默认: 10)');
            console.log('  --max <n>               最大并发数 (默认: 1000)');
            console.log('  --step-duration <sec>   每阶时长 (默认: 30)');
            console.log('  --step-increment <n>    步进增量 (默认: 50)');
            console.log('  --error-threshold <%>   错误率阈值 (默认: 5)');
            console.log('  --help, -h              显示帮助');
            process.exit(0);
        }
    }

    return options;
}

if (require.main === module) {
    var options = parseArgs();
    var test = new StressTest(options);
    test.run();
}

module.exports = StressTest;
