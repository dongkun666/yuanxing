/**
 * 数据可视化增强组件
 * 提供案件趋势图、胜诉率分析、律师能力画像、案件类型分布、时间分布热力图
 *
 * 依赖: Chart.js (chart.js 4.x)
 * 暴露: Charts.createLineChart, Charts.createPieChart, Charts.createRadarChart,
 *       Charts.createBarChart, Charts.createHeatmap
 */
(function () {
    'use strict';

    var _chartInstances = {};
    var _defaultColors = {
        brand: '#165DFF',
        wiki: '#6C5CE7',
        ai: '#0EA5E9',
        success: '#07C160',
        warning: '#FA8C16',
        danger: '#F53F3F',
        purple: '#722ED1',
        cyan: '#0FC6C2',
        gold: '#FF7D00',
        magenta: '#F5319D'
    };

    var _chartDefaultFont = {
        family: '-apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "Segoe UI", Roboto, sans-serif',
        size: 12
    };

    function _getChartJS() {
        if (typeof Chart !== 'undefined') {
            return Chart;
        }
        console.warn('[Charts] Chart.js 未加载');
        return null;
    }

    function _getColorPalette(count) {
        var palette = [
            _defaultColors.brand,
            _defaultColors.success,
            _defaultColors.warning,
            _defaultColors.wiki,
            _defaultColors.ai,
            _defaultColors.danger,
            _defaultColors.purple,
            _defaultColors.cyan,
            _defaultColors.gold,
            _defaultColors.magenta
        ];
        if (count <= palette.length) {
            return palette.slice(0, count);
        }
        var result = [];
        for (var i = 0; i < count; i++) {
            result.push(palette[i % palette.length]);
        }
        return result;
    }

    function _hexToRgba(hex, alpha) {
        var r = parseInt(hex.slice(1, 3), 16);
        var g = parseInt(hex.slice(3, 5), 16);
        var b = parseInt(hex.slice(5, 7), 16);
        return 'rgba(' + r + ', ' + g + ', ' + b + ', ' + alpha + ')';
    }

    function _destroyChart(chartId) {
        if (_chartInstances[chartId]) {
            try {
                _chartInstances[chartId].destroy();
            } catch (e) {
                console.warn('[Charts] 销毁图表失败:', chartId, e);
            }
            delete _chartInstances[chartId];
        }
    }

    function _getCanvas(container) {
        var el = typeof container === 'string' ? document.querySelector(container) : container;
        if (!el) return null;
        if (el.tagName === 'CANVAS') return el;
        var canvas = el.querySelector('canvas');
        if (!canvas) {
            canvas = document.createElement('canvas');
            el.innerHTML = '';
            el.appendChild(canvas);
        }
        return canvas;
    }

    function _isDarkMode() {
        var theme = document.documentElement.getAttribute('data-theme');
        return theme === 'dark';
    }

    function _getThemeColors() {
        var dark = _isDarkMode();
        return {
            text: dark ? '#E5E6EB' : '#1D2129',
            textSecondary: dark ? '#86909C' : '#86909C',
            grid: dark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
            tooltipBg: dark ? '#1D2129' : '#ffffff',
            tooltipBorder: dark ? '#4E5969' : '#E5E6EB'
        };
    }

    /**
     * 创建折线图 - 案件趋势图
     * @param {string|HTMLElement} container - 容器选择器或元素
     * @param {Object} options - 配置选项
     * @param {string} options.chartId - 图表唯一ID
     * @param {Array} options.labels - X轴标签
     * @param {Array} options.datasets - 数据集
     * @param {string} [options.title] - 标题
     * @param {boolean} [options.fill=true] - 是否填充区域
     * @returns {Object|null} - Chart 实例
     */
    function createLineChart(container, options) {
        var ChartJS = _getChartJS();
        if (!ChartJS) return null;

        options = options || {};
        var chartId = options.chartId || ('line-' + Date.now());
        var canvas = _getCanvas(container);
        if (!canvas) return null;

        _destroyChart(chartId);

        var themeColors = _getThemeColors();
        var colors = _getColorPalette(options.datasets ? options.datasets.length : 1);

        var datasets = (options.datasets || []).map(function (ds, idx) {
            var color = ds.color || colors[idx % colors.length];
            return {
                label: ds.label || ('数据 ' + (idx + 1)),
                data: ds.data || [],
                borderColor: color,
                backgroundColor: options.fill !== false ? _hexToRgba(color, 0.1) : 'transparent',
                borderWidth: 2,
                fill: options.fill !== false,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: color,
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            };
        });

        var chartConfig = {
            type: 'line',
            data: {
                labels: options.labels || [],
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: datasets.length > 1,
                        position: 'top',
                        align: 'end',
                        labels: {
                            font: _chartDefaultFont,
                            color: themeColors.textSecondary,
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 16
                        }
                    },
                    title: {
                        display: !!options.title,
                        text: options.title || '',
                        font: {
                            family: _chartDefaultFont.family,
                            size: 14,
                            weight: '600'
                        },
                        color: themeColors.text,
                        padding: {
                            bottom: 16
                        }
                    },
                    tooltip: {
                        backgroundColor: themeColors.tooltipBg,
                        titleColor: themeColors.text,
                        bodyColor: themeColors.textSecondary,
                        borderColor: themeColors.tooltipBorder,
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12,
                        bodyFont: _chartDefaultFont,
                        titleFont: {
                            family: _chartDefaultFont.family,
                            size: 12,
                            weight: '600'
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: themeColors.textSecondary,
                            font: _chartDefaultFont
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: themeColors.grid
                        },
                        ticks: {
                            color: themeColors.textSecondary,
                            font: _chartDefaultFont
                        }
                    }
                }
            }
        };

        var chart = new ChartJS(canvas.getContext('2d'), chartConfig);
        _chartInstances[chartId] = chart;
        return chart;
    }

    /**
     * 创建饼图/环形图 - 胜诉率分析
     * @param {string|HTMLElement} container - 容器选择器或元素
     * @param {Object} options - 配置选项
     * @param {string} options.chartId - 图表唯一ID
     * @param {Array} options.data - 数据 [{label, value, color}]
     * @param {string} [options.title] - 标题
     * @param {boolean} [options.doughnut=true] - 是否为环形图
     * @param {string} [options.centerText] - 环形图中心文字
     * @returns {Object|null} - Chart 实例
     */
    function createPieChart(container, options) {
        var ChartJS = _getChartJS();
        if (!ChartJS) return null;

        options = options || {};
        var chartId = options.chartId || ('pie-' + Date.now());
        var canvas = _getCanvas(container);
        if (!canvas) return null;

        _destroyChart(chartId);

        var themeColors = _getThemeColors();
        var dataItems = options.data || [];
        var labels = dataItems.map(function (item) { return item.label; });
        var values = dataItems.map(function (item) { return item.value; });
        var colors = dataItems.map(function (item, idx) {
            return item.color || _getColorPalette(dataItems.length)[idx];
        });

        var isDoughnut = options.doughnut !== false;
        var chartType = isDoughnut ? 'doughnut' : 'pie';

        var chartConfig = {
            type: chartType,
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#fff',
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: isDoughnut ? '65%' : '0%',
                plugins: {
                    legend: {
                        display: true,
                        position: 'right',
                        labels: {
                            font: _chartDefaultFont,
                            color: themeColors.textSecondary,
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 12
                        }
                    },
                    title: {
                        display: !!options.title,
                        text: options.title || '',
                        font: {
                            family: _chartDefaultFont.family,
                            size: 14,
                            weight: '600'
                        },
                        color: themeColors.text,
                        padding: {
                            bottom: 16
                        }
                    },
                    tooltip: {
                        backgroundColor: themeColors.tooltipBg,
                        titleColor: themeColors.text,
                        bodyColor: themeColors.textSecondary,
                        borderColor: themeColors.tooltipBorder,
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12,
                        bodyFont: _chartDefaultFont,
                        titleFont: {
                            family: _chartDefaultFont.family,
                            size: 12,
                            weight: '600'
                        },
                        callbacks: {
                            label: function (context) {
                                var total = context.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                                var percentage = total > 0 ? ((context.raw / total) * 100).toFixed(1) : 0;
                                return context.label + ': ' + context.raw + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        };

        var chart = new ChartJS(canvas.getContext('2d'), chartConfig);
        _chartInstances[chartId] = chart;

        if (isDoughnut && options.centerText) {
            var drawCenterText = function (chart) {
                var ctx = chart.ctx;
                var width = chart.width;
                var height = chart.height;
                ctx.restore();
                var fontSize = (height / 114).toFixed(2);
                ctx.font = '600 ' + fontSize + 'em ' + _chartDefaultFont.family;
                ctx.textBaseline = 'middle';
                ctx.textAlign = 'center';
                ctx.fillStyle = themeColors.text;
                var textY = height / 2;
                ctx.fillText(options.centerText, width / 2, textY);
                ctx.save();
            };
            chart.options.plugins.tooltip.callbacks.label = function (context) {
                var total = context.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                var percentage = total > 0 ? ((context.raw / total) * 100).toFixed(1) : 0;
                return context.label + ': ' + context.raw + ' (' + percentage + '%)';
            };
        }

        return chart;
    }

    /**
     * 创建雷达图 - 律师能力画像
     * @param {string|HTMLElement} container - 容器选择器或元素
     * @param {Object} options - 配置选项
     * @param {string} options.chartId - 图表唯一ID
     * @param {Array} options.labels - 能力维度标签
     * @param {Array} options.datasets - 数据集
     * @param {string} [options.title] - 标题
     * @param {number} [options.max=100] - 最大值
     * @returns {Object|null} - Chart 实例
     */
    function createRadarChart(container, options) {
        var ChartJS = _getChartJS();
        if (!ChartJS) return null;

        options = options || {};
        var chartId = options.chartId || ('radar-' + Date.now());
        var canvas = _getCanvas(container);
        if (!canvas) return null;

        _destroyChart(chartId);

        var themeColors = _getThemeColors();
        var colors = _getColorPalette(options.datasets ? options.datasets.length : 1);

        var datasets = (options.datasets || []).map(function (ds, idx) {
            var color = ds.color || colors[idx % colors.length];
            return {
                label: ds.label || ('律师 ' + (idx + 1)),
                data: ds.data || [],
                borderColor: color,
                backgroundColor: _hexToRgba(color, 0.15),
                borderWidth: 2,
                pointBackgroundColor: color,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            };
        });

        var chartConfig = {
            type: 'radar',
            data: {
                labels: options.labels || [],
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: datasets.length > 1,
                        position: 'top',
                        align: 'end',
                        labels: {
                            font: _chartDefaultFont,
                            color: themeColors.textSecondary,
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 16
                        }
                    },
                    title: {
                        display: !!options.title,
                        text: options.title || '',
                        font: {
                            family: _chartDefaultFont.family,
                            size: 14,
                            weight: '600'
                        },
                        color: themeColors.text,
                        padding: {
                            bottom: 16
                        }
                    },
                    tooltip: {
                        backgroundColor: themeColors.tooltipBg,
                        titleColor: themeColors.text,
                        bodyColor: themeColors.textSecondary,
                        borderColor: themeColors.tooltipBorder,
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12,
                        bodyFont: _chartDefaultFont,
                        titleFont: {
                            family: _chartDefaultFont.family,
                            size: 12,
                            weight: '600'
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: options.max || 100,
                        ticks: {
                            stepSize: 20,
                            color: themeColors.textSecondary,
                            backdropColor: 'transparent',
                            font: _chartDefaultFont
                        },
                        grid: {
                            color: themeColors.grid
                        },
                        angleLines: {
                            color: themeColors.grid
                        },
                        pointLabels: {
                            color: themeColors.text,
                            font: {
                                family: _chartDefaultFont.family,
                                size: 12
                            }
                        }
                    }
                }
            }
        };

        var chart = new ChartJS(canvas.getContext('2d'), chartConfig);
        _chartInstances[chartId] = chart;
        return chart;
    }

    /**
     * 创建柱状图 - 案件类型分布
     * @param {string|HTMLElement} container - 容器选择器或元素
     * @param {Object} options - 配置选项
     * @param {string} options.chartId - 图表唯一ID
     * @param {Array} options.labels - X轴标签
     * @param {Array} options.datasets - 数据集
     * @param {string} [options.title] - 标题
     * @param {boolean} [options.horizontal=false] - 是否水平柱状图
     * @returns {Object|null} - Chart 实例
     */
    function createBarChart(container, options) {
        var ChartJS = _getChartJS();
        if (!ChartJS) return null;

        options = options || {};
        var chartId = options.chartId || ('bar-' + Date.now());
        var canvas = _getCanvas(container);
        if (!canvas) return null;

        _destroyChart(chartId);

        var themeColors = _getThemeColors();
        var colors = _getColorPalette(options.datasets ? options.datasets.length : 1);

        var datasets = (options.datasets || []).map(function (ds, idx) {
            var color = ds.color || colors[idx % colors.length];
            return {
                label: ds.label || ('数据 ' + (idx + 1)),
                data: ds.data || [],
                backgroundColor: _hexToRgba(color, 0.8),
                hoverBackgroundColor: color,
                borderRadius: 6,
                borderSkipped: false
            };
        });

        var chartType = options.horizontal ? 'bar' : 'bar';
        var indexAxis = options.horizontal ? 'y' : 'x';

        var chartConfig = {
            type: chartType,
            data: {
                labels: options.labels || [],
                datasets: datasets
            },
            options: {
                indexAxis: indexAxis,
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: datasets.length > 1,
                        position: 'top',
                        align: 'end',
                        labels: {
                            font: _chartDefaultFont,
                            color: themeColors.textSecondary,
                            usePointStyle: true,
                            pointStyle: 'rect',
                            padding: 16
                        }
                    },
                    title: {
                        display: !!options.title,
                        text: options.title || '',
                        font: {
                            family: _chartDefaultFont.family,
                            size: 14,
                            weight: '600'
                        },
                        color: themeColors.text,
                        padding: {
                            bottom: 16
                        }
                    },
                    tooltip: {
                        backgroundColor: themeColors.tooltipBg,
                        titleColor: themeColors.text,
                        bodyColor: themeColors.textSecondary,
                        borderColor: themeColors.tooltipBorder,
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12,
                        bodyFont: _chartDefaultFont,
                        titleFont: {
                            family: _chartDefaultFont.family,
                            size: 12,
                            weight: '600'
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: !options.horizontal,
                            color: themeColors.grid
                        },
                        ticks: {
                            color: themeColors.textSecondary,
                            font: _chartDefaultFont
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            display: options.horizontal,
                            color: themeColors.grid
                        },
                        ticks: {
                            color: themeColors.textSecondary,
                            font: _chartDefaultFont
                        }
                    }
                }
            }
        };

        var chart = new ChartJS(canvas.getContext('2d'), chartConfig);
        _chartInstances[chartId] = chart;
        return chart;
    }

    /**
     * 创建热力图 - 时间分布
     * 使用 canvas 原生绘制，不依赖 Chart.js 热力图插件
     * @param {string|HTMLElement} container - 容器选择器或元素
     * @param {Object} options - 配置选项
     * @param {string} options.chartId - 图表唯一ID
     * @param {Array} options.data - 二维数据数组 [x, y, value]
     * @param {Array} options.xLabels - X轴标签 (如: 周一到周日)
     * @param {Array} options.yLabels - Y轴标签 (如: 0-23点)
     * @param {string} [options.title] - 标题
     * @param {string} [options.colorStart] - 起始颜色
     * @param {string} [options.colorEnd] - 结束颜色
     * @returns {Object|null} - 热力图实例
     */
    function createHeatmap(container, options) {
        options = options || {};
        var chartId = options.chartId || ('heatmap-' + Date.now());

        var el = typeof container === 'string' ? document.querySelector(container) : container;
        if (!el) return null;

        var themeColors = _getThemeColors();
        var colorStart = options.colorStart || '#E8F3FF';
        var colorEnd = options.colorEnd || '#165DFF';

        function _parseColor(hex) {
            var r = parseInt(hex.slice(1, 3), 16);
            var g = parseInt(hex.slice(3, 5), 16);
            var b = parseInt(hex.slice(5, 7), 16);
            return { r: r, g: g, b: b };
        }

        function _interpolateColor(c1, c2, t) {
            return {
                r: Math.round(c1.r + (c2.r - c1.r) * t),
                g: Math.round(c1.g + (c2.g - c1.g) * t),
                b: Math.round(c1.b + (c2.b - c1.b) * t)
            };
        }

        function _rgbToCss(c) {
            return 'rgb(' + c.r + ', ' + c.g + ', ' + c.b + ')';
        }

        var data = options.data || [];
        var xLabels = options.xLabels || [];
        var yLabels = options.yLabels || [];

        var maxValue = 0;
        data.forEach(function (item) {
            if (item[2] > maxValue) maxValue = item[2];
        });

        el.innerHTML = '';
        el.className = (el.className || '') + ' heatmap-container';
        el.style.position = 'relative';

        var titleHtml = '';
        if (options.title) {
            titleHtml =
                '<div class="heatmap-title text-sm font-semibold mb-3" style="color:' +
                themeColors.text +
                '">' +
                Utils.escapeHtml(options.title) +
                '</div>';
        }

        var gridHtml = '<div class="heatmap-grid" style="display:grid;gap:4px;">';
        var xLen = xLabels.length || 7;
        var yLen = yLabels.length || 24;

        var dataMap = {};
        data.forEach(function (item) {
            var key = item[0] + '_' + item[1];
            dataMap[key] = item[2];
        });

        var cStart = _parseColor(colorStart);
        var cEnd = _parseColor(colorEnd);

        gridHtml += '<div style="display:contents;">';
        gridHtml += '<div style="width:40px;"></div>';
        for (var x = 0; x < xLen; x++) {
            gridHtml +=
                '<div class="text-center text-[10px]" style="color:' +
                themeColors.textSecondary +
                ';font-size:11px;">' +
                Utils.escapeHtml(xLabels[x] || ('x' + x)) +
                '</div>';
        }
        gridHtml += '</div>';

        for (var y = 0; y < yLen; y++) {
            gridHtml += '<div style="display:contents;">';
            gridHtml +=
                '<div class="text-right pr-2 text-[11px]" style="color:' +
                themeColors.textSecondary +
                ';line-height:24px;">' +
                Utils.escapeHtml(yLabels[y] || ('y' + y)) +
                '</div>';
            for (var xIdx = 0; xIdx < xLen; xIdx++) {
                var key = xIdx + '_' + y;
                var value = dataMap[key] || 0;
                var ratio = maxValue > 0 ? value / maxValue : 0;
                var bgColor = maxValue > 0
                    ? _rgbToCss(_interpolateColor(cStart, cEnd, ratio))
                    : colorStart;

                gridHtml +=
                    '<div class="heatmap-cell rounded-sm cursor-pointer transition-transform hover:scale-110" ' +
                    'style="background-color:' + bgColor +
                    ';height:24px;"' +
                    'title="' +
                    Utils.escapeHtml(xLabels[xIdx] || '') + ' ' +
                    Utils.escapeHtml(yLabels[y] || '') + ': ' + value +
                    '"' +
                    'data-x="' + xIdx + '"' +
                    'data-y="' + y + '"' +
                    'data-value="' + value + '"' +
                    '></div>';
            }
            gridHtml += '</div>';
        }

        var legendHtml =
            '<div class="heatmap-legend flex items-center gap-2 mt-4 justify-end">' +
            '<span class="text-[11px]" style="color:' + themeColors.textSecondary + ';">少</span>' +
            '<div class="h-3 w-32 rounded" style="background: linear-gradient(to right, ' +
            colorStart + ', ' + colorEnd + ');"></div>' +
            '<span class="text-[11px]" style="color:' + themeColors.textSecondary + ';">多</span>' +
            '</div>';

        el.innerHTML = titleHtml + gridHtml + '</div>' + legendHtml;

        var instance = {
            id: chartId,
            container: el,
            update: function (newData) {
                data = newData || [];
                maxValue = 0;
                data.forEach(function (item) {
                    if (item[2] > maxValue) maxValue = item[2];
                });
                var cells = el.querySelectorAll('.heatmap-cell');
                cells.forEach(function (cell) {
                    var cx = parseInt(cell.getAttribute('data-x'));
                    var cy = parseInt(cell.getAttribute('data-y'));
                    var ckey = cx + '_' + cy;
                    var cvalue = 0;
                    for (var i = 0; i < data.length; i++) {
                        if (data[i][0] === cx && data[i][1] === cy) {
                            cvalue = data[i][2];
                            break;
                        }
                    }
                    var cratio = maxValue > 0 ? cvalue / maxValue : 0;
                    var cbgColor = maxValue > 0
                        ? _rgbToCss(_interpolateColor(cStart, cEnd, cratio))
                        : colorStart;
                    cell.style.backgroundColor = cbgColor;
                    cell.setAttribute('data-value', cvalue);
                    var origTitle = cell.getAttribute('title');
                    if (origTitle) {
                        var parts = origTitle.split(': ');
                        if (parts.length > 0) {
                            cell.title = parts[0] + ': ' + cvalue;
                        }
                    }
                });
            },
            destroy: function () {
                el.innerHTML = '';
                delete _chartInstances[chartId];
            }
        };

        _chartInstances[chartId] = instance;
        return instance;
    }

    /**
     * 更新指定图表数据
     * @param {string} chartId - 图表ID
     * @param {Object} data - 新数据
     */
    function updateChart(chartId, data) {
        var chart = _chartInstances[chartId];
        if (!chart) return;

        if (chart.update && typeof chart.update === 'function' && !(chart instanceof (typeof Chart !== 'undefined' ? Chart : Object))) {
            chart.update(data);
            return;
        }

        if (chart.data && data.datasets) {
            chart.data.datasets = data.datasets;
            if (data.labels) {
                chart.data.labels = data.labels;
            }
            chart.update();
        }
    }

    /**
     * 销毁指定图表
     * @param {string} chartId - 图表ID
     */
    function destroyChart(chartId) {
        _destroyChart(chartId);
    }

    /**
     * 销毁所有图表
     */
    function destroyAllCharts() {
        for (var id in _chartInstances) {
            if (_chartInstances.hasOwnProperty(id)) {
                _destroyChart(id);
            }
        }
    }

    /**
     * 获取图表实例
     * @param {string} chartId - 图表ID
     * @returns {Object|null}
     */
    function getChart(chartId) {
        return _chartInstances[chartId] || null;
    }

    globalThis.Charts = {
        createLineChart: createLineChart,
        createPieChart: createPieChart,
        createRadarChart: createRadarChart,
        createBarChart: createBarChart,
        createHeatmap: createHeatmap,
        updateChart: updateChart,
        destroyChart: destroyChart,
        destroyAllCharts: destroyAllCharts,
        getChart: getChart,
        colors: _defaultColors
    };
})();
