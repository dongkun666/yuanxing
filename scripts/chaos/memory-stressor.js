/**
 * 内存压力工具
 * 模拟内存高负载场景，测试系统在内存紧张时的表现
 *
 * 用法: node scripts/chaos/memory-stressor.js [options]
 */

'use strict';

var os = require('os');
var fs = require('fs');
var path = require('path');

var DEFAULT_DURATION = 60;
var DEFAULT_MEMORY_MB = 256;
var DEFAULT_GROWTH_RATE = 10;

function MemoryStressor(options) {
    this.duration = options.duration || DEFAULT_DURATION;
    this.targetMemoryMB = options.memoryMB || DEFAULT_MEMORY_MB;
    this.growthRate = options.growthRate || DEFAULT_GROWTH_RATE;
    this.memoryChunks = [];
    this.stats = {
        startTime: 0,
        endTime: 0,
        targetMemoryMB: this.targetMemoryMB,
        peakMemoryMB: 0,
        samples: []
    };
    this.stopped = false;
}

MemoryStressor.prototype.run = function () {
    var self = this;
    var totalMemMB = Math.round(os.totalmem() / 1024 / 1024);
    var freeMemMB = Math.round(os.freemem() / 1024 / 1024);

    console.log('========================================');
    console.log('  LexPrime 混沌工程 - 内存压力测试');
    console.log('========================================');
    console.log('系统总内存:', totalMemMB, 'MB');
    console.log('系统空闲内存:', freeMemMB, 'MB');
    console.log('目标占用内存:', this.targetMemoryMB, 'MB');
    console.log('增长速率:', this.growthRate, 'MB/秒');
    console.log('测试时长:', this.duration, '秒');
    console.log('');

    self.stats.startTime = Date.now();
    self.startMemoryGrowth();
    self.startMonitoring();

    setTimeout(function () {
        console.log('\n[停止压力测试中...]');
        self.stopped = true;
        self.releaseMemory();
        setTimeout(function () {
            self.stats.endTime = Date.now();
            self.printSummary();
        }, 1000);
    }, self.duration * 1000);
};

MemoryStressor.prototype.startMemoryGrowth = function () {
    var self = this;
    var currentMB = 0;

    function growMemory() {
        if (self.stopped || currentMB >= self.targetMemoryMB) {
            if (currentMB >= self.targetMemoryMB) {
                console.log('[内存已达目标] ' + currentMB + ' MB');
            }
            return;
        }

        var chunkSize = self.growthRate * 1024 * 1024;
        var chunk = Buffer.alloc(chunkSize, 'x');
        self.memoryChunks.push(chunk);
        currentMB += self.growthRate;

        var memUsage = process.memoryUsage();
        self.stats.peakMemoryMB = Math.max(
            self.stats.peakMemoryMB,
            Math.round(memUsage.heapUsed / 1024 / 1024)
        );

        setTimeout(growMemory, 1000);
    }

    growMemory();
    console.log('[内存增长已启动] 目标 ' + self.targetMemoryMB + ' MB');
};

MemoryStressor.prototype.releaseMemory = function () {
    var self = this;
    self.memoryChunks = [];
    if (global.gc) {
        try {
            global.gc();
        } catch (e) {
            // ignore
        }
    }
    console.log('[内存已释放]');
};

MemoryStressor.prototype.startMonitoring = function () {
    var self = this;
    var sampleInterval = setInterval(function () {
        if (self.stopped) {
            clearInterval(sampleInterval);
            return;
        }

        var memUsage = process.memoryUsage();
        var freeMem = os.freemem();

        self.stats.samples.push({
            timestamp: Date.now(),
            heapUsedMB: Math.round(memUsage.heapUsed / 1024 / 1024),
            heapTotalMB: Math.round(memUsage.heapTotal / 1024 / 1024),
            rssMB: Math.round(memUsage.rss / 1024 / 1024),
            systemFreeMB: Math.round(freeMem / 1024 / 1024),
            allocatedChunks: self.memoryChunks.length
        });
    }, 2000);
};

MemoryStressor.prototype.printSummary = function () {
    var self = this;
    var stats = self.stats;
    var duration = (stats.endTime - stats.startTime) / 1000;

    console.log('\n========================================');
    console.log('  内存压力测试总结');
    console.log('========================================');
    console.log('实验时长: ' + duration.toFixed(2) + ' 秒');
    console.log('目标内存: ' + stats.targetMemoryMB + ' MB');
    console.log('峰值内存: ' + stats.peakMemoryMB + ' MB');
    console.log('');

    if (stats.samples.length > 0) {
        var firstSample = stats.samples[0];
        var lastSample = stats.samples[stats.samples.length - 1];

        console.log('内存使用:');
        console.log('  起始 Heap: ' + firstSample.heapUsedMB + ' MB');
        console.log('  结束 Heap: ' + lastSample.heapUsedMB + ' MB');
        console.log('  峰值 Heap: ' + stats.peakMemoryMB + ' MB');
        console.log('  结束 RSS: ' + lastSample.rssMB + ' MB');
        console.log('');
        console.log('系统内存:');
        console.log('  起始空闲: ' + firstSample.systemFreeMB + ' MB');
        console.log('  结束空闲: ' + lastSample.systemFreeMB + ' MB');
    }

    var reportPath = path.join(__dirname, 'reports', 'memory-stressor-' + Date.now() + '.json');
    try {
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify({
            duration: self.duration,
            targetMemoryMB: self.targetMemoryMB,
            growthRate: self.growthRate,
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
        } else if (arg === '--memory' && args[i + 1]) {
            options.memoryMB = parseInt(args[++i], 10);
        } else if (arg === '--rate' && args[i + 1]) {
            options.growthRate = parseInt(args[++i], 10);
        } else if (arg === '--help' || arg === '-h') {
            console.log('用法: node scripts/chaos/memory-stressor.js [options]');
            console.log('');
            console.log('选项:');
            console.log('  --duration <seconds>  测试时长 (默认: 60)');
            console.log('  --memory <mb>         目标内存占用 (默认: 256)');
            console.log('  --rate <mb/s>         增长速率 (默认: 10)');
            console.log('  --help, -h            显示帮助');
            process.exit(0);
        }
    }

    return options;
}

if (require.main === module) {
    var options = parseArgs();
    var stressor = new MemoryStressor(options);
    stressor.run();
}

module.exports = MemoryStressor;
