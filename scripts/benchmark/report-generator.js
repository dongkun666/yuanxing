/**
 * 性能报告生成器
 * 从测试结果数据生成 HTML 和 JSON 格式的性能报告
 *
 * 用法: node scripts/benchmark/report-generator.js <result-file> [options]
 */

'use strict';

var fs = require('fs');
var path = require('path');

function ReportGenerator(options) {
    this.options = options || {};
    this.outputDir = options.outputDir || path.join(__dirname, 'reports');
}

ReportGenerator.prototype.generateHtml = function (data, title) {
    var self = this;
    var reportTitle = title || 'LexPrime 性能测试报告';
    var timestamp = new Date().toISOString();
    var summaryHtml = self.generateSummaryHtml(data);
    var chartsHtml = self.generateChartsHtml(data);
    var detailsHtml = self.generateDetailsHtml(data);

    return '<!DOCTYPE html>\n' +
        '<html lang="zh-CN">\n' +
        '<head>\n' +
        '    <meta charset="UTF-8">\n' +
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n' +
        '    <title>' + reportTitle + '</title>\n' +
        '    <style>\n' +
        '        * { margin: 0; padding: 0; box-sizing: border-box; }\n' +
        '        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f7fa; color: #333; padding: 20px; }\n' +
        '        .container { max-width: 1200px; margin: 0 auto; }\n' +
        '        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }\n' +
        '        .header h1 { font-size: 28px; margin-bottom: 10px; }\n' +
        '        .header .meta { opacity: 0.9; font-size: 14px; }\n' +
        '        .section { background: white; border-radius: 10px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }\n' +
        '        .section h2 { font-size: 20px; margin-bottom: 16px; color: #2c3e50; border-bottom: 2px solid #667eea; padding-bottom: 8px; display: inline-block; }\n' +
        '        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }\n' +
        '        .summary-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #667eea; }\n' +
        '        .summary-card .value { font-size: 28px; font-weight: bold; color: #667eea; }\n' +
        '        .summary-card .label { font-size: 14px; color: #666; margin-top: 5px; }\n' +
        '        .summary-card.success { border-left-color: #10b981; }\n' +
        '        .summary-card.success .value { color: #10b981; }\n' +
        '        .summary-card.warning { border-left-color: #f59e0b; }\n' +
        '        .summary-card.warning .value { color: #f59e0b; }\n' +
        '        .summary-card.danger { border-left-color: #ef4444; }\n' +
        '        .summary-card.danger .value { color: #ef4444; }\n' +
        '        table { width: 100%; border-collapse: collapse; margin-top: 10px; }\n' +
        '        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }\n' +
        '        th { background: #f8f9fa; font-weight: 600; color: #374151; }\n' +
        '        tr:hover { background: #f9fafb; }\n' +
        '        .bar-chart { display: flex; align-items: flex-end; height: 200px; gap: 10px; padding: 20px 0; }\n' +
        '        .bar-item { flex: 1; display: flex; flex-direction: column; align-items: center; }\n' +
        '        .bar { width: 100%; background: linear-gradient(to top, #667eea, #764ba2); border-radius: 4px 4px 0 0; transition: height 0.3s; min-height: 2px; }\n' +
        '        .bar-label { margin-top: 8px; font-size: 12px; color: #666; text-align: center; }\n' +
        '        .bar-value { font-size: 11px; color: #999; margin-bottom: 4px; }\n' +
        '        .status-badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 500; }\n' +
        '        .status-pass { background: #d1fae5; color: #065f46; }\n' +
        '        .status-warn { background: #fef3c7; color: #92400e; }\n' +
        '        .status-fail { background: #fee2e2; color: #991b1b; }\n' +
        '        .chart-container { margin: 20px 0; }\n' +
        '        .chart-title { font-size: 16px; font-weight: 600; margin-bottom: 10px; color: #374151; }\n' +
        '    </style>\n' +
        '</head>\n' +
        '<body>\n' +
        '    <div class="container">\n' +
        '        <div class="header">\n' +
        '            <h1>' + reportTitle + '</h1>\n' +
        '            <div class="meta">生成时间: ' + timestamp + '</div>\n' +
        '        </div>\n' +
        summaryHtml +
        chartsHtml +
        detailsHtml +
        '    </div>\n' +
        '</body>\n' +
        '</html>';
};

ReportGenerator.prototype.generateSummaryHtml = function (data) {
    var stats = this.calculateStats(data);
    return '<div class="section">' +
        '<h2>总览</h2>' +
        '<div class="summary-grid">' +
        '    <div class="summary-card">' +
        '        <div class="value">' + stats.totalRequests + '</div>' +
        '        <div class="label">总请求数</div>' +
        '    </div>' +
        '    <div class="summary-card success">' +
        '        <div class="value">' + stats.successRate.toFixed(2) + '%</div>' +
        '        <div class="label">成功率</div>' +
        '    </div>' +
        '    <div class="summary-card ' + (stats.avgLatency > 500 ? 'warning' : '') + '">' +
        '        <div class="value">' + stats.avgLatency.toFixed(2) + 'ms</div>' +
        '        <div class="label">平均延迟</div>' +
        '    </div>' +
        '    <div class="summary-card">' +
        '        <div class="value">' + stats.avgRps.toFixed(2) + '</div>' +
        '        <div class="label">平均 RPS</div>' +
        '    </div>' +
        '    <div class="summary-card ' + (stats.p95Latency > 1000 ? 'danger' : 'warning') + '">' +
        '        <div class="value">' + stats.p95Latency + 'ms</div>' +
        '        <div class="label">P95 延迟</div>' +
        '    </div>' +
        '    <div class="summary-card">' +
        '        <div class="value">' + stats.p99Latency + 'ms</div>' +
        '        <div class="label">P99 延迟</div>' +
        '    </div>' +
        '</div>' +
        '</div>';
};

ReportGenerator.prototype.generateChartsHtml = function (data) {
    var self = this;
    var results = data.results || [data];
    if (!results.length) {
        return '';
    }

    var maxRps = 0;
    var maxLatency = 0;
    results.forEach(function (r) {
        if (r.rps > maxRps) { maxRps = r.rps; }
        if ((r.p95 || r.avgLatency || 0) > maxLatency) { maxLatency = r.p95 || r.avgLatency || 0; }
    });

    var rpsBars = '';
    var latencyBars = '';
    results.forEach(function (r) {
        var label = r.name || ('并发' + r.connections);
        var rpsHeight = maxRps > 0 ? (r.rps / maxRps * 180) : 0;
        var latValue = r.p95 || r.avgLatency || 0;
        var latHeight = maxLatency > 0 ? (latValue / maxLatency * 180) : 0;
        rpsBars += '<div class="bar-item">' +
            '<div class="bar-value">' + r.rps.toFixed(0) + '</div>' +
            '<div class="bar" style="height: ' + rpsHeight + 'px;"></div>' +
            '<div class="bar-label">' + label + '</div>' +
            '</div>';
        latencyBars += '<div class="bar-item">' +
            '<div class="bar-value">' + latValue + 'ms</div>' +
            '<div class="bar" style="height: ' + latHeight + 'px; background: linear-gradient(to top, #f59e0b, #ef4444);"></div>' +
            '<div class="bar-label">' + label + '</div>' +
            '</div>';
    });

    return '<div class="section">' +
        '<h2>性能图表</h2>' +
        '<div class="chart-container">' +
        '    <div class="chart-title">吞吐量 (RPS)</div>' +
        '    <div class="bar-chart">' + rpsBars + '</div>' +
        '</div>' +
        '<div class="chart-container">' +
        '    <div class="chart-title">P95 延迟 (ms)</div>' +
        '    <div class="bar-chart">' + latencyBars + '</div>' +
        '</div>' +
        '</div>';
};

ReportGenerator.prototype.generateDetailsHtml = function (data) {
    var results = data.results || [data];
    var rows = '';

    results.forEach(function (r, i) {
        var errorRate = r.requests > 0 ? (r.errors / r.requests * 100) : 0;
        var statusClass = errorRate < 1 ? 'status-pass' : (errorRate < 5 ? 'status-warn' : 'status-fail');
        var statusText = errorRate < 1 ? '通过' : (errorRate < 5 ? '警告' : '失败');
        rows += '<tr>' +
            '<td>' + (i + 1) + '</td>' +
            '<td>' + (r.name || r.method + ' ' + (r.path || '')) + '</td>' +
            '<td>' + r.requests + '</td>' +
            '<td>' + r.success + '</td>' +
            '<td>' + r.errors + '</td>' +
            '<td><span class="status-badge ' + statusClass + '">' + statusText + ' (' + errorRate.toFixed(2) + '%)</span></td>' +
            '<td>' + r.rps.toFixed(2) + '</td>' +
            '<td>' + (r.avgLatency || 0).toFixed(2) + 'ms</td>' +
            '<td>' + (r.p50 || 0) + 'ms</td>' +
            '<td>' + (r.p95 || 0) + 'ms</td>' +
            '<td>' + (r.p99 || 0) + 'ms</td>' +
            '</tr>';
    });

    return '<div class="section">' +
        '<h2>详细数据</h2>' +
        '<table>' +
        '    <thead>' +
        '        <tr>' +
        '            <th>#</th>' +
        '            <th>端点/阶段</th>' +
        '            <th>请求数</th>' +
        '            <th>成功</th>' +
        '            <th>失败</th>' +
        '            <th>状态</th>' +
        '            <th>RPS</th>' +
        '            <th>平均延迟</th>' +
        '            <th>P50</th>' +
        '            <th>P95</th>' +
        '            <th>P99</th>' +
        '        </tr>' +
        '    </thead>' +
        '    <tbody>' + rows + '</tbody>' +
        '</table>' +
        '</div>';
};

ReportGenerator.prototype.calculateStats = function (data) {
    var results = data.results || [data];
    var totalRequests = 0;
    var totalSuccess = 0;
    var totalErrors = 0;
    var totalLatency = 0;
    var allLatencies = [];
    var totalRps = 0;

    results.forEach(function (r) {
        totalRequests += r.requests || 0;
        totalSuccess += r.success || 0;
        totalErrors += r.errors || 0;
        totalLatency += r.totalLatency || 0;
        totalRps += r.rps || 0;
        if (r.latencies && r.latencies.length) {
            allLatencies = allLatencies.concat(r.latencies);
        }
    });

    allLatencies.sort(function (a, b) { return a - b; });

    return {
        totalRequests: totalRequests,
        totalSuccess: totalSuccess,
        totalErrors: totalErrors,
        successRate: totalRequests > 0 ? (totalSuccess / totalRequests * 100) : 0,
        avgLatency: totalSuccess > 0 ? totalLatency / totalSuccess : 0,
        avgRps: results.length > 0 ? totalRps / results.length : 0,
        p50Latency: this.percentile(allLatencies, 50),
        p95Latency: this.percentile(allLatencies, 95),
        p99Latency: this.percentile(allLatencies, 99)
    };
};

ReportGenerator.prototype.percentile = function (sortedArr, p) {
    if (!sortedArr || sortedArr.length === 0) {
        return 0;
    }
    var index = Math.ceil(p / 100 * sortedArr.length) - 1;
    return sortedArr[Math.max(0, Math.min(index, sortedArr.length - 1))];
};

ReportGenerator.prototype.saveReport = function (data, format, title) {
    var self = this;
    var timestamp = Date.now();
    var fileName, content;

    if (format === 'html') {
        fileName = 'report-' + timestamp + '.html';
        content = self.generateHtml(data, title);
    } else {
        fileName = 'report-' + timestamp + '.json';
        content = JSON.stringify(data, null, 2);
    }

    var filePath = path.join(self.outputDir, fileName);
    fs.mkdirSync(self.outputDir, { recursive: true });
    fs.writeFileSync(filePath, content);
    return filePath;
};

function parseArgs() {
    var args = process.argv.slice(2);
    var options = {
        inputFile: null,
        format: 'html',
        outputDir: path.join(__dirname, 'reports'),
        title: 'LexPrime 性能测试报告'
    };

    for (var i = 0; i < args.length; i++) {
        var arg = args[i];
        if (arg === '--format' && args[i + 1]) {
            options.format = args[++i];
        } else if (arg === '--output' && args[i + 1]) {
            options.outputDir = args[++i];
        } else if (arg === '--title' && args[i + 1]) {
            options.title = args[++i];
        } else if (arg === '--help' || arg === '-h') {
            console.log('用法: node scripts/benchmark/report-generator.js <result-file> [options]');
            console.log('');
            console.log('选项:');
            console.log('  --format <html|json>  输出格式 (默认: html)');
            console.log('  --output <dir>        输出目录');
            console.log('  --title <title>       报告标题');
            console.log('  --help, -h            显示帮助');
            process.exit(0);
        } else if (!options.inputFile && !arg.startsWith('--')) {
            options.inputFile = arg;
        }
    }

    return options;
}

if (require.main === module) {
    var options = parseArgs();

    if (!options.inputFile) {
        console.error('错误: 请指定输入文件路径');
        console.log('用法: node scripts/benchmark/report-generator.js <result-file>');
        process.exit(1);
    }

    try {
        var rawData = fs.readFileSync(options.inputFile, 'utf-8');
        var data = JSON.parse(rawData);

        var generator = new ReportGenerator({ outputDir: options.outputDir });
        var reportPath = generator.saveReport(data, options.format, options.title);
        console.log('报告已生成: ' + reportPath);
    } catch (e) {
        console.error('生成报告失败:', e.message);
        process.exit(1);
    }
}

module.exports = ReportGenerator;
