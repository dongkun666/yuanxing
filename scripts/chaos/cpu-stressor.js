/**
 * CPU 压力工具
 * 模拟 CPU 高负载场景，测试系统在资源紧张时的表现
 *
 * 用法: node scripts/chaos/cpu-stressor.js [options]
 */

'use strict';

var os = require('os');
var fs = require('fs');
var path = require('path');

var DEFAULT_DURATION = 60;
var DEFAULT_CPU_PERCENT = 50;
var DEFAULT_CORES = os.cpus().length;

function CpuStressor(options) {
    this.duration = options.duration || DEFAULT_DURATION;
    this.cpuPercent = options.cpuPercent || DEFAULT_CPU_PERCENT;
    this.cores = options.cores || Math.min(DEFAULT_CORES, 4);
    this.workers = [];
    this.stats = {
        startTime: 0,
        endTime: 0,
        targetCpuPercent: this.cpuPercent,
        coresUsed: this.cores,
        samples: []
    };
    this.stopped = false;
}

CpuStressor.prototype.run = function () {
    var self = this;
    console.log('========================================');
    console.log('  LexPrime 混沌工程 - CPU 压力测试');
    console.log('========================================');
    console.log('系统 CPU 核心数:', DEFAULT_CORES);
    console.log('使用核心数:', this.cores);
    console.log('目标 CPU 使用率:', this.cpuPercent + '%');
    console.log('测试时长:', this.duration, '秒');
    console.log('');

    self.stats.startTime = Date.now();
    self.startStress();
    self.startMonitoring();

    setTimeout(function () {
        console.log('\n[停止压力测试中...]');
        self.stopped = true;
        self.stopStress();
        setTimeout(function () {
            self.stats.endTime = Date.now();
            self.printSummary();
        }, 1000);
    }, self.duration * 1000);
};

CpuStressor.prototype.startStress = function () {
    var self = this;

    for (var i = 0; i < self.cores; i++) {
        (function (coreId) {
            var worker = {
                id: coreId,
                running: true,
                iterations: 0
            };
            self.workers.push(worker);

            function stressLoop() {
                if (!worker.running || self.stopped) {
                    return;
                }

                var workTime = self.cpuPercent / 100 * 100;
                var sleepTime = 100 - workTime;

                var start = Date.now();
                while (Date.now() - start < workTime) {
                    worker.iterations++;
                    Math.sqrt(Math.random() * 1000000);
                    JSON.stringify({ data: new Array(100).fill(0) });
                }

                setTimeout(stressLoop, sleepTime);
            }

            stressLoop();
        })(i);
    }

    console.log('[CPU 压力已启动] 使用 ' + self.cores + ' 个核心，目标 ' + self.cpuPercent + '%');
};

CpuStressor.prototype.stopStress = function () {
    var self = this;
    self.workers.forEach(function (worker) {
        worker.running = false;
    });
    console.log('[CPU 压力已停止]');
};

CpuStressor.prototype.startMonitoring = function () {
    var self = this;
    var sampleInterval = setInterval(function () {
        if (self.stopped) {
            clearInterval(sampleInterval);
            return;
        }

        var load = os.loadavg();
        var memUsage = process.memoryUsage();

        self.stats.samples.push({
            timestamp: Date.now(),
            loadAvg1: load[0],
            loadAvg5: load[1],
            loadAvg15: load[2],
            memoryUsedMB: Math.round(memUsage.heapUsed / 1024 / 1024),
            totalIterations: self.workers.reduce(function (sum, w) { return sum + w.iterations; }, 0)
        });
    }, 5000);
};

CpuStressor.prototype.printSummary = function () {
    var self = this;
    var stats = self.stats;
    var duration = (stats.endTime - stats.startTime) / 1000;

    console.log('\n========================================');
    console.log('  CPU 压力测试总结');
    console.log('========================================');
    console.log('实验时长: ' + duration.toFixed(2) + ' 秒');
    console.log('使用核心数: ' + stats.coresUsed);
    console.log('目标 CPU: ' + stats.targetCpuPercent + '%');
    console.log('');

    if (stats.samples.length > 0) {
        var avgLoad = stats.samples.reduce(function (sum, s) { return sum + s.loadAvg1; }, 0) / stats.samples.length;
        var maxLoad = Math.max.apply(null, stats.samples.map(function (s) { return s.loadAvg1; }));
        var lastSample = stats.samples[stats.samples.length - 1];

        console.log('系统负载:');
        console.log('  平均 1分钟负载: ' + avgLoad.toFixed(2));
        console.log('  峰值 1分钟负载: ' + maxLoad.toFixed(2));
        console.log('  5分钟负载: ' + lastSample.loadAvg5.toFixed(2));
        console.log('  15分钟负载: ' + lastSample.loadAvg15.toFixed(2));
        console.log('');
        console.log('Worker 统计:');
        self.workers.forEach(function (w) {
            console.log('  Core ' + w.id + ': ' + w.iterations + ' 次迭代');
        });
    }

    var reportPath = path.join(__dirname, 'reports', 'cpu-stressor-' + Date.now() + '.json');
    try {
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify({
            duration: self.duration,
            cpuPercent: self.cpuPercent,
            cores: self.cores,
            systemCores: DEFAULT_CORES,
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
        if (arg === '--duration' && args[i + 1]) {
            options.duration = parseInt(args[++i], 10);
        } else if (arg === '--cpu' && args[i + 1]) {
            options.cpuPercent = parseInt(args[++i], 10);
        } else if (arg === '--cores' && args[i + 1]) {
            options.cores = parseInt(args[++i], 10);
        } else if (arg === '--help' || arg === '-h') {
            console.log('用法: node scripts/chaos/cpu-stressor.js [options]');
            console.log('');
            console.log('选项:');
            console.log('  --duration <seconds>  测试时长 (默认: 60)');
            console.log('  --cpu <percent>       目标 CPU 使用率 (默认: 50)');
            console.log('  --cores <n>           使用核心数 (默认: 系统核心数，最多4)');
            console.log('  --help, -h            显示帮助');
            process.exit(0);
        }
    }

    return options;
}

if (require.main === module) {
    var options = parseArgs();
    var stressor = new CpuStressor(options);
    stressor.run();
}

module.exports = CpuStressor;
