/**
 * 混沌实验运行器
 * 编排和管理混沌工程实验，支持多种故障类型组合
 *
 * 用法: node scripts/chaos/chaos-runner.js [options]
 */

'use strict';

var fs = require('fs');
var path = require('path');

var LatencyInjector = require('./latency-injector');
var ErrorInjector = require('./error-injector');
var CpuStressor = require('./cpu-stressor');
var MemoryStressor = require('./memory-stressor');

var DEFAULT_DURATION = 120;
var DEFAULT_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:3847';

var experimentPresets = {
    gentle: {
        name: '温和实验',
        description: '低强度故障注入，适合生产环境验证',
        duration: 60,
        latency: { enabled: true, min: 50, max: 200, rate: 0.1 },
        error: { enabled: true, rate: 0.05 },
        cpu: { enabled: false, percent: 20, cores: 1 },
        memory: { enabled: false, mb: 64, rate: 5 }
    },
    moderate: {
        name: '中等实验',
        description: '中等强度故障注入，模拟常见故障场景',
        duration: 90,
        latency: { enabled: true, min: 100, max: 1000, rate: 0.2 },
        error: { enabled: true, rate: 0.1 },
        cpu: { enabled: true, percent: 40, cores: 2 },
        memory: { enabled: false, mb: 128, rate: 10 }
    },
    aggressive: {
        name: '激进实验',
        description: '高强度故障注入，测试系统极限容错能力',
        duration: 120,
        latency: { enabled: true, min: 500, max: 3000, rate: 0.4 },
        error: { enabled: true, rate: 0.25 },
        cpu: { enabled: true, percent: 70, cores: 4 },
        memory: { enabled: true, mb: 512, rate: 20 }
    },
    latency_only: {
        name: '仅延迟',
        description: '仅注入网络延迟',
        duration: 60,
        latency: { enabled: true, min: 200, max: 2000, rate: 0.5 },
        error: { enabled: false, rate: 0 },
        cpu: { enabled: false, percent: 0, cores: 0 },
        memory: { enabled: false, mb: 0, rate: 0 }
    },
    error_only: {
        name: '仅错误',
        description: '仅注入服务错误',
        duration: 60,
        latency: { enabled: false, min: 0, max: 0, rate: 0 },
        error: { enabled: true, rate: 0.3 },
        cpu: { enabled: false, percent: 0, cores: 0 },
        memory: { enabled: false, mb: 0, rate: 0 }
    },
    resource_pressure: {
        name: '资源压力',
        description: 'CPU + 内存高负载',
        duration: 90,
        latency: { enabled: false, min: 0, max: 0, rate: 0 },
        error: { enabled: false, rate: 0 },
        cpu: { enabled: true, percent: 60, cores: 4 },
        memory: { enabled: true, mb: 256, rate: 15 }
    }
};

function ChaosRunner(options) {
    this.baseUrl = options.baseUrl || DEFAULT_BASE_URL;
    this.preset = options.preset || 'gentle';
    this.duration = options.duration || null;
    this.experiment = null;
    this.results = {};
    this.activeExperiments = [];
}

ChaosRunner.prototype.run = function () {
    var self = this;
    var preset = experimentPresets[self.preset];

    if (!preset) {
        console.error('错误: 未知的实验预设:', self.preset);
        console.log('可用预设:', Object.keys(experimentPresets).join(', '));
        process.exit(1);
    }

    if (self.duration) {
        preset.duration = self.duration;
    }

    self.experiment = preset;

    console.log('========================================');
    console.log('  LexPrime 混沌工程 - 实验运行器');
    console.log('========================================');
    console.log('实验名称:', preset.name);
    console.log('实验描述:', preset.description);
    console.log('实验时长:', preset.duration, '秒');
    console.log('目标地址:', self.baseUrl);
    console.log('');
    console.log('故障组件:');
    console.log('  延迟注入:', preset.latency.enabled ? '是 (' + (preset.latency.rate * 100) + '%)' : '否');
    console.log('  错误注入:', preset.error.enabled ? '是 (' + (preset.error.rate * 100) + '%)' : '否');
    console.log('  CPU 压力:', preset.cpu.enabled ? '是 (' + preset.cpu.percent + '%)' : '否');
    console.log('  内存压力:', preset.memory.enabled ? '是 (' + preset.memory.mb + ' MB)' : '否');
    console.log('');
    console.log('[实验开始]');
    console.log('');

    var started = 0;
    var totalExperiments = 0;

    if (preset.latency.enabled) { totalExperiments++; }
    if (preset.error.enabled) { totalExperiments++; }
    if (preset.cpu.enabled) { totalExperiments++; }
    if (preset.memory.enabled) { totalExperiments++; }

    function checkAllDone() {
        started++;
        if (started >= totalExperiments) {
            setTimeout(function () {
                self.printSummary();
            }, 500);
        }
    }

    if (preset.latency.enabled) {
        console.log('[启动] 延迟注入...');
        var latencyInjector = new LatencyInjector({
            baseUrl: self.baseUrl,
            duration: preset.duration,
            minLatency: preset.latency.min,
            maxLatency: preset.latency.max,
            injectionRate: preset.latency.rate
        });
        latencyInjector.printSummary = function () {
            self.results.latency = this.stats;
            console.log('[完成] 延迟注入');
            checkAllDone();
        };
        latencyInjector.run();
        self.activeExperiments.push(latencyInjector);
    }

    if (preset.error.enabled) {
        console.log('[启动] 错误注入...');
        var errorInjector = new ErrorInjector({
            baseUrl: self.baseUrl,
            duration: preset.duration,
            errorRate: preset.error.rate
        });
        errorInjector.printSummary = function () {
            self.results.error = this.stats;
            console.log('[完成] 错误注入');
            checkAllDone();
        };
        errorInjector.run();
        self.activeExperiments.push(errorInjector);
    }

    if (preset.cpu.enabled) {
        console.log('[启动] CPU 压力...');
        var cpuStressor = new CpuStressor({
            duration: preset.duration,
            cpuPercent: preset.cpu.percent,
            cores: preset.cpu.cores
        });
        cpuStressor.printSummary = function () {
            self.results.cpu = this.stats;
            console.log('[完成] CPU 压力');
            checkAllDone();
        };
        cpuStressor.run();
        self.activeExperiments.push(cpuStressor);
    }

    if (preset.memory.enabled) {
        console.log('[启动] 内存压力...');
        var memStressor = new MemoryStressor({
            duration: preset.duration,
            memoryMB: preset.memory.mb,
            growthRate: preset.memory.rate
        });
        memStressor.printSummary = function () {
            self.results.memory = this.stats;
            console.log('[完成] 内存压力');
            checkAllDone();
        };
        memStressor.run();
        self.activeExperiments.push(memStressor);
    }

    if (totalExperiments === 0) {
        console.log('没有启用任何故障组件');
        process.exit(0);
    }
};

ChaosRunner.prototype.printSummary = function () {
    var self = this;
    console.log('');
    console.log('========================================');
    console.log('  混沌实验总结报告');
    console.log('========================================');
    console.log('实验名称: ' + self.experiment.name);
    console.log('实验时长: ' + self.experiment.duration + ' 秒');
    console.log('');

    var resilienceScore = self.calculateResilienceScore();
    console.log('系统韧性评分: ' + resilienceScore + '/100');
    console.log('');

    console.log('--- 各组件结果:');
    if (self.results.latency) {
        var lat = self.results.latency;
        console.log('  延迟注入:');
        console.log('    总请求: ' + lat.totalRequests);
        console.log('    错误率: ' + (lat.totalRequests > 0
            ? (lat.errors / lat.totalRequests * 100).toFixed(2)
            : 0) + '%');
    }
    if (self.results.error) {
        var err = self.results.error;
        console.log('  错误注入:');
        console.log('    总请求: ' + err.totalRequests);
        console.log('    成功率: ' + (err.totalRequests > 0
            ? (err.successfulRequests / err.totalRequests * 100).toFixed(2)
            : 0) + '%');
    }
    if (self.results.cpu) {
        console.log('  CPU 压力: 已执行');
    }
    if (self.results.memory) {
        console.log('  内存压力: 已执行');
    }

    console.log('\n--- 改进建议:');
    self.printRecommendations(resilienceScore);

    var reportPath = path.join(__dirname, 'reports', 'chaos-experiment-' + Date.now() + '.json');
    try {
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify({
            preset: self.preset,
            experiment: self.experiment,
            baseUrl: self.baseUrl,
            timestamp: new Date().toISOString(),
            resilienceScore: resilienceScore,
            results: self.results
        }, null, 2));
        console.log('\n详细报告已保存: ' + reportPath);
    } catch (e) {
        console.warn('保存报告失败:', e.message);
    }

    console.log('\n实验完成!');
};

ChaosRunner.prototype.calculateResilienceScore = function () {
    var score = 100;

    if (this.results.latency && this.results.latency.totalRequests > 0) {
        var errorRate = this.results.latency.errors / this.results.latency.totalRequests;
        score -= Math.min(30, errorRate * 100);
    }

    if (this.results.error && this.results.error.totalRequests > 0) {
        var failRate = this.results.error.errorRequests / this.results.error.totalRequests;
        score -= Math.min(30, failRate * 50);
    }

    return Math.max(0, Math.round(score));
};

ChaosRunner.prototype.printRecommendations = function (score) {
    var recs = [];

    if (score >= 80) {
        recs.push('系统韧性良好，继续保持');
    } else if (score >= 50) {
        recs.push('建议加强容错机制，增加重试和降级策略');
        recs.push('实施熔断器模式，防止故障扩散');
    } else {
        recs.push('系统韧性不足，需要重点改进');
        recs.push('添加服务降级和熔断机制');
        recs.push('优化超时控制和资源隔离');
        recs.push('加强监控和告警系统');
    }

    if (this.results.latency && this.results.latency.errors > 0) {
        recs.push('延迟场景下存在错误，建议增加超时重试机制');
    }

    recs.forEach(function (rec, i) {
        console.log('  ' + (i + 1) + '. ' + rec);
    });
};

function parseArgs() {
    var args = process.argv.slice(2);
    var options = {};

    for (var i = 0; i < args.length; i++) {
        var arg = args[i];
        if (arg === '--preset' && args[i + 1]) {
            options.preset = args[++i];
        } else if (arg === '--url' && args[i + 1]) {
            options.baseUrl = args[++i];
        } else if (arg === '--duration' && args[i + 1]) {
            options.duration = parseInt(args[++i], 10);
        } else if (arg === '--list' || arg === '-l') {
            console.log('可用实验预设:');
            Object.keys(experimentPresets).forEach(function (key) {
                var p = experimentPresets[key];
                console.log('  ' + key + ' - ' + p.name + ': ' + p.description);
            });
            process.exit(0);
        } else if (arg === '--help' || arg === '-h') {
            console.log('用法: node scripts/chaos/chaos-runner.js [options]');
            console.log('');
            console.log('选项:');
            console.log('  --preset <name>    实验预设 (默认: gentle)');
            console.log('  --url <url>        API 基础地址');
            console.log('  --duration <sec>   实验时长（覆盖预设）');
            console.log('  --list, -l         列出所有预设');
            console.log('  --help, -h         显示帮助');
            console.log('');
            console.log('预设: gentle, moderate, aggressive, latency_only, error_only, resource_pressure');
            process.exit(0);
        }
    }

    return options;
}

if (require.main === module) {
    var options = parseArgs();
    var runner = new ChaosRunner(options);
    runner.run();
}

module.exports = ChaosRunner;
