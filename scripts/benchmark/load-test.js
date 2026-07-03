/**
 * 负载测试 - 模拟真实用户场景
 * 模拟多用户并发访问典型业务流程
 *
 * 用法: node scripts/benchmark/load-test.js [options]
 */

'use strict';

var http = require('http');
var https = require('https');
var url = require('url');
var fs = require('fs');
var path = require('path');

var DEFAULT_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:3847';
var DEFAULT_USERS = 50;
var DEFAULT_DURATION = 60;
var DEFAULT_RAMP_UP = 10;

var userScenarios = [
    {
        name: 'case-browsing',
        weight: 30,
        steps: [
            { method: 'GET', path: '/api/cases?limit=20', thinkTime: 1000 },
            { method: 'GET', path: '/api/cases?limit=20&cause_category=合同纠纷', thinkTime: 2000 },
            { method: 'POST', path: '/api/search', body: JSON.stringify({
                query: '借款合同',
                index: 'cases',
                page: 1,
                size: 20
            }), headers: { 'Content-Type': 'application/json' }, thinkTime: 3000 }
        ]
    },
    {
        name: 'law-research',
        weight: 20,
        steps: [
            { method: 'GET', path: '/api/laws?limit=20', thinkTime: 1500 },
            { method: 'GET', path: '/api/laws?law_type=法律&limit=20', thinkTime: 2000 }
        ]
    },
    {
        name: 'company-search',
        weight: 15,
        steps: [
            { method: 'GET', path: '/api/companies?limit=20', thinkTime: 1000 },
            { method: 'GET', path: '/api/companies?name=科技&limit=20', thinkTime: 2000 }
        ]
    },
    {
        name: 'health-check',
        weight: 35,
        steps: [
            { method: 'GET', path: '/api/health', thinkTime: 500 }
        ]
    }
];

function LoadTest(options) {
    this.baseUrl = options.baseUrl || DEFAULT_BASE_URL;
    this.users = options.users || DEFAULT_USERS;
    this.duration = options.duration || DEFAULT_DURATION;
    this.rampUp = options.rampUp || DEFAULT_RAMP_UP;
    this.stats = {
        totalRequests: 0,
        totalSuccess: 0,
        totalErrors: 0,
        totalLatency: 0,
        minLatency: Infinity,
        maxLatency: 0,
        latencies: [],
        statusCodes: {},
        scenarioStats: {},
        startTime: 0,
        endTime: 0
    };
    this.activeUsers = 0;
    this.stopped = false;
}

LoadTest.prototype.run = function () {
    var self = this;
    console.log('========================================');
    console.log('  LexPrime 负载测试');
    console.log('========================================');
    console.log('目标地址:', self.baseUrl);
    console.log('虚拟用户数:', self.users);
    console.log('测试时长:', self.duration, '秒');
    console.log('爬升时间:', self.rampUp, '秒');
    console.log('');

    self.stats.startTime = Date.now();
    self.startRampUp();

    setTimeout(function () {
        console.log('\n[停止测试中...]');
        self.stopped = true;
        setTimeout(function () {
            self.stats.endTime = Date.now();
            self.printSummary();
        }, 5000);
    }, self.duration * 1000);
};

LoadTest.prototype.startRampUp = function () {
    var self = this;
    var usersPerSecond = self.users / self.rampUp;
    var added = 0;
    var interval = setInterval(function () {
        var toAdd = Math.min(Math.floor(usersPerSecond), self.users - added);
        for (var i = 0; i < toAdd; i++) {
            self.addUser();
            added++;
        }
        if (added >= self.users) {
            clearInterval(interval);
            console.log('[爬升完成] 所有 ' + self.users + ' 个用户已启动');
        }
    }, 1000);
};

LoadTest.prototype.addUser = function () {
    var self = this;
    self.activeUsers++;
    var scenario = self.pickScenario();
    self.runUserScenario(scenario);
};

LoadTest.prototype.pickScenario = function () {
    var totalWeight = userScenarios.reduce(function (sum, s) {
        return sum + s.weight;
    }, 0);
    var rand = Math.random() * totalWeight;
    var cumulative = 0;
    for (var i = 0; i < userScenarios.length; i++) {
        cumulative += userScenarios[i].weight;
        if (rand < cumulative) {
            return userScenarios[i];
        }
    }
    return userScenarios[0];
};

LoadTest.prototype.runUserScenario = function (scenario) {
    var self = this;
    var stepIndex = 0;

    if (!self.stats.scenarioStats[scenario.name]) {
        self.stats.scenarioStats[scenario.name] = {
            requests: 0,
            success: 0,
            errors: 0
        };
    }

    function nextStep() {
        if (self.stopped) {
            self.activeUsers--;
            return;
        }

        if (stepIndex >= scenario.steps.length) {
            stepIndex = 0;
            setTimeout(nextStep, 2000);
            return;
        }

        var step = scenario.steps[stepIndex++];
        self.makeRequest(step, scenario.name, function () {
            setTimeout(nextStep, step.thinkTime || 1000);
        });
    }

    nextStep();
};

LoadTest.prototype.makeRequest = function (step, scenarioName, callback) {
    var self = this;
    var parsed = url.parse(self.baseUrl + step.path);
    var isHttps = parsed.protocol === 'https:';
    var lib = isHttps ? https : http;

    var options = {
        hostname: parsed.hostname,
        port: parsed.port || (isHttps ? 443 : 80),
        path: parsed.path,
        method: step.method,
        headers: step.headers || {}
    };

    var reqStart = Date.now();
    var req = lib.request(options, function (res) {
        var chunks = [];
        res.on('data', function (chunk) {
            chunks.push(chunk);
        });
        res.on('end', function () {
            var latency = Date.now() - reqStart;
            self.recordStats(true, latency, res.statusCode, scenarioName);
            callback();
        });
    });

    req.on('error', function (err) {
        self.recordStats(false, 0, 0, scenarioName);
        callback();
    });

    if (step.body) {
        req.write(step.body);
    }
    req.end();
};

LoadTest.prototype.recordStats = function (success, latency, statusCode, scenarioName) {
    var self = this;
    self.stats.totalRequests++;

    var scStats = self.stats.scenarioStats[scenarioName];
    if (scStats) {
        scStats.requests++;
    }

    if (success) {
        self.stats.totalSuccess++;
        self.stats.totalLatency += latency;
        self.stats.minLatency = Math.min(self.stats.minLatency, latency);
        self.stats.maxLatency = Math.max(self.stats.maxLatency, latency);
        self.stats.latencies.push(latency);
        self.stats.statusCodes[statusCode] = (self.stats.statusCodes[statusCode] || 0) + 1;
        if (scStats) {
            scStats.success++;
        }
    } else {
        self.stats.totalErrors++;
        if (scStats) {
            scStats.errors++;
        }
    }
};

LoadTest.prototype.percentile = function (sortedArr, p) {
    if (sortedArr.length === 0) {
        return 0;
    }
    var index = Math.ceil(p / 100 * sortedArr.length) - 1;
    return sortedArr[Math.max(0, Math.min(index, sortedArr.length - 1))];
};

LoadTest.prototype.printSummary = function () {
    var self = this;
    var stats = self.stats;
    var duration = (stats.endTime - stats.startTime) / 1000;

    stats.latencies.sort(function (a, b) { return a - b; });

    console.log('\n========================================');
    console.log('  负载测试总结');
    console.log('========================================');
    console.log('测试时长: ' + duration.toFixed(2) + ' 秒');
    console.log('活跃用户峰值: ' + self.users);
    console.log('');
    console.log('总请求数: ' + stats.totalRequests);
    console.log('成功: ' + stats.totalSuccess + ', 失败: ' + stats.totalErrors);
    console.log('成功率: ' + (stats.totalRequests > 0 ? (stats.totalSuccess / stats.totalRequests * 100).toFixed(2) : 0) + '%');
    console.log('吞吐量: ' + (stats.totalRequests / duration).toFixed(2) + ' req/s');
    console.log('');
    console.log('延迟统计:');
    console.log('  最小: ' + (stats.minLatency === Infinity ? 0 : stats.minLatency) + 'ms');
    console.log('  平均: ' + (stats.totalSuccess > 0 ? (stats.totalLatency / stats.totalSuccess).toFixed(2) : 0) + 'ms');
    console.log('  最大: ' + stats.maxLatency + 'ms');
    console.log('  P50: ' + self.percentile(stats.latencies, 50) + 'ms');
    console.log('  P95: ' + self.percentile(stats.latencies, 95) + 'ms');
    console.log('  P99: ' + self.percentile(stats.latencies, 99) + 'ms');
    console.log('');
    console.log('HTTP 状态码分布: ' + JSON.stringify(stats.statusCodes));
    console.log('');
    console.log('场景统计:');
    Object.keys(stats.scenarioStats).forEach(function (name) {
        var s = stats.scenarioStats[name];
        console.log('  ' + name + ': ' + s.requests + ' 请求, 成功率 ' +
            (s.requests > 0 ? (s.success / s.requests * 100).toFixed(2) : 0) + '%');
    });

    var reportPath = path.join(__dirname, 'reports', 'load-test-' + Date.now() + '.json');
    try {
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify({
            baseUrl: self.baseUrl,
            users: self.users,
            duration: self.duration,
            rampUp: self.rampUp,
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
        } else if (arg === '--users' && args[i + 1]) {
            options.users = parseInt(args[++i], 10);
        } else if (arg === '--duration' && args[i + 1]) {
            options.duration = parseInt(args[++i], 10);
        } else if (arg === '--ramp-up' && args[i + 1]) {
            options.rampUp = parseInt(args[++i], 10);
        } else if (arg === '--help' || arg === '-h') {
            console.log('用法: node scripts/benchmark/load-test.js [options]');
            console.log('');
            console.log('选项:');
            console.log('  --url <url>          API 基础地址 (默认: http://127.0.0.1:3847)');
            console.log('  --users <n>          虚拟用户数 (默认: 50)');
            console.log('  --duration <seconds> 测试时长 (默认: 60)');
            console.log('  --ramp-up <seconds>  爬升时间 (默认: 10)');
            console.log('  --help, -h           显示帮助');
            process.exit(0);
        }
    }

    return options;
}

if (require.main === module) {
    var options = parseArgs();
    var test = new LoadTest(options);
    test.run();
}

module.exports = LoadTest;
