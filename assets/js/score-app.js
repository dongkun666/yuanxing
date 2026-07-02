/**
 * W6 评审 Score App - 前端核心模块 (lex-coder · 2026-06-29)
 *
 * 覆盖范围:
 * 1. 加载 5 测试合同 (从 /api/review/contracts, 复用 W5 fixtures)
 * 2. 加载律师下拉 (5 评审律师 L1-L5)
 * 3. 合同 Tab 切换
 * 4. 5 维度滑块 (致命准确率 / 建议实用性 / 策略可执行 / 中立性 / UI 流程) 0-10 分
 * 5. 5 维度 文字评论 textarea
 * 6. 综合评分自动聚合 (算术平均)
 * 7. 提交按钮 → POST /api/review/submit-score
 * 8. localStorage 断网 fallback + 重连后自动补传
 * 9. 历史评分列表 (从 localStorage + 后端 GET)
 * 10. mobile-responsive (<768px 单栏堆叠, >768px 双栏)
 * 11. 键盘可达 + ARIA
 * 12. online/offline 事件监听
 *
 * 加载: 在 contract-review.js 之后 (2026-06-29)
 * 依赖: switchView/showToast (router.js + script.js)
 *
 * API:
 * - GET  /api/review/contracts      返回 5 测试合同
 * - POST /api/review/submit-score   提交评分
 * - GET  /api/review/my-scores      律师历史评分 (auth 集成)
 * - GET  /api/review/summary        团队汇总 (评审完开放)
 *
 * Demo: 直接打开页面, 默认 5 律师 + 5 合同, 无 auth 要求
 */

(function() {
    'use strict';

    // ====== 5 评分维度 (从 W4 scoring-rubric.md §1.1 沿用, 展示名按任务 prompt) ======
    var DIMENSIONS = [
        {
            id: 'fatal_accuracy',
            label: 'D1 · 致命准确率',
            short: '致命准确',
            description: '致命/重大/建议 三级风险识别的准确率 (W5 rubric §2)',
            hint: '对比 baseline 5 份合同标记的 fatal/major/advisory, 评估 LLM 检出率',
            color: 'danger',
            icon: 'mdi:alert-octagon-outline'
        },
        {
            id: 'suggestion_practicality',
            label: 'D2 · 建议实用性',
            short: '建议实用',
            description: 'AI 修改建议的可执行性 + 法条准确 + 表述清晰 (W5 rubric §3)',
            hint: '是否给出具体表述 + 法条引用 + 数值范围 + modified_clause_template',
            color: 'warning',
            icon: 'mdi:lightbulb-on-outline'
        },
        {
            id: 'strategy_executability',
            label: 'D3 · 策略可执行',
            short: '策略执行',
            description: '谈判策略的可执行性 + 立场感知 (W5 rubric §4)',
            hint: 'priority_clauses 排序 / leverage_points / trade_off / walk_away_signals',
            color: 'urgent',
            icon: 'mdi:strategy'
        },
        {
            id: 'neutrality',
            label: 'D4 · 中立性',
            short: '中立性',
            description: 'LLM 输出的中立性 (硬门槛, 一票否决 · W5 rubric §5)',
            hint: '是否含"必败/必胜"等确定性预测, 法条引用是否准确, disclaimer 是否显示',
            color: 'brand',
            icon: 'mdi:scale-balance'
        },
        {
            id: 'ui_flow',
            label: 'D5 · UI 流程',
            short: 'UI 流程',
            description: '整体可用性 (UI 易用 + 风险高亮 + 加载速度 + 导出格式 · W5 rubric §6)',
            hint: '5 步内完成审查 + 红黄绿灯清晰 + 加载 P95 < 2s + 3 种导出格式',
            color: 'success',
            icon: 'mdi:cellphone-link'
        }
    ];

    // ====== 5 评审律师 (W4 schedule.md §8.1 + W5 lex-pm 待定) ======
    var LAWYERS = [
        {id: 'L1', name: 'L1 单飞律师 · 民商', type: '单飞', venue: '评审 #1 · 7/19'},
        {id: 'L2', name: 'L2 小所律师 · 民商', type: '小所', venue: '评审 #1 · 7/19'},
        {id: 'L3', name: 'L3 小所律师 · 婚姻家事', type: '小所', venue: '评审 #1 · 7/19'},
        {id: 'L4', name: 'L4 中所律师 · 金融', type: '中所', venue: '评审 #2 · 7/26'},
        {id: 'L5', name: 'L5 企业法务 · 合规', type: '企业法务', venue: '评审 #2 · 7/26'}
    ];

    // ====== 全局状态 ======
    var SA = {
        apiBase: 'http://127.0.0.1:8000/api/review',
        contracts: [],          // 5 测试合同 (从后端加载)
        currentContract: null,  // 当前合同对象
        currentLawyerId: null,  // L1-L5
        scores: {},             // {fatal_accuracy: 7, ...}
        comments: {},           // {fatal_accuracy: "评论", ...}
        submittedCache: [],     // localStorage 已提交但未上传 (断网 fallback)
        history: [],            // 已提交历史 (从 localStorage + 后端)
        isOnline: navigator.onLine
    };

    // ====== HTML 转义 ======
    function esc(s) {
        if (s === null || s === undefined) return '';
        return String(s).replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', '\'':'&#39;'}[c];
        });
    }

    // ====== Toast (复用 contract-review.js 兼容模式) ======
    function toast(msg, type) {
        type = type || 'info';
        if (typeof window.showToast === 'function') {
            window.showToast(msg, type);
            return;
        }
        var el = document.createElement('div');
        el.className = 'fixed top-4 left-1/2 -translate-x-1/2 z-[9999] px-4 py-2 rounded-lg shadow-lg text-sm flex items-center gap-1.5 ' +
            (type === 'success' ? 'bg-success text-white' :
                type === 'warning' ? 'bg-warning text-white' :
                    type === 'error' ? 'bg-danger text-white' :
                        'bg-brand text-white');
        el.textContent = msg;
        document.body.appendChild(el);
        setTimeout(function() { el.remove(); }, 2500);
    }

    // ====== 加载 5 测试合同 (从 /api/review/contracts) ======
    function loadContracts() {
        fetch(SA.apiBase + '/contracts')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                SA.contracts = data.contracts || [];
                renderContractTabs();
                // 默认选中第 1 份
                if (SA.contracts.length > 0) {
                    selectContract(SA.contracts[0].contract_id);
                }
            })
            .catch(function(err) {
                console.warn('[/api/review/contracts] 加载失败, 使用 fallback:', err);
                // Fallback: 直接给前端内嵌 5 合同 (W5 fixture 摘要, 不含全文)
                SA.contracts = [
                    {contract_id: 'demo-rental-beijing-2026', contract_type: '房屋租赁', contract_title: '北京市朝阳区望京 SOHO T3 写字楼租赁合同 (2026)', icon: 'mdi:home-city-outline', risk_count: '7 条款 / 1fatal+3major+1advisory', amount: '¥98万', stance: '乙方'},
                    {contract_id: 'demo-loan-shanghai-2026', contract_type: '借款合同', contract_title: '上海市浦东新区民间借贷合同 (2026)', icon: 'mdi:cash-multiple', risk_count: '6 条款 / 1fatal+2major+2advisory', amount: '¥50万', stance: '乙方'},
                    {contract_id: 'demo-labor-fulltime-2026', contract_type: '劳动合同', contract_title: '北京市某科技公司劳动合同 (2026)', icon: 'mdi:briefcase-account-outline', risk_count: '8 条款 / 0fatal+0major+5advisory', amount: '面议', stance: '乙方'},
                    {contract_id: 'demo-service-tech-2026', contract_type: '服务合同', contract_title: '上海市某 IT 服务采购合同 (2026)', icon: 'mdi:laptop', risk_count: '6 条款 / 1fatal+0major+4advisory', amount: '面议', stance: '乙方'},
                    {contract_id: 'demo-sales-goods-2026', contract_type: '销售合同', contract_title: '广东省某货物销售合同 (2026)', icon: 'mdi:cart-outline', risk_count: '6 条款 / 1fatal+0major+4advisory', amount: '面议', stance: '乙方'}
                ];
                renderContractTabs();
                selectContract(SA.contracts[0].contract_id);
            });
    }

    // ====== 渲染合同 Tab + 详情 ======
    function renderContractTabs() {
        var tabs = document.getElementById('contract-tabs');
        if (!tabs) return;
        tabs.innerHTML = SA.contracts.map(function(c) {
            var active = (SA.currentContract && SA.currentContract.contract_id === c.contract_id) ? 'active' : '';
            var colorMap = {
                '房屋租赁': 'bg-brand text-white border-brand shadow-sm',
                '借款合同': 'bg-danger text-white border-danger shadow-sm',
                '劳动合同': 'bg-warning text-white border-warning shadow-sm',
                '服务合同': 'bg-success text-white border-success shadow-sm',
                '销售合同': 'bg-urgent text-white border-urgent shadow-sm'
            };
            var activeClass = active ? colorMap[c.contract_type] || 'bg-fg-primary text-white border-fg-primary' : 'bg-white text-fg-secondary border-bg-border hover:border-brand hover:text-brand';
            return '<button class="contract-tab flex-shrink-0 px-3 py-2 rounded-md text-xs font-medium border transition-all ' + activeClass + ' ' + active + '" data-contract-id="' + esc(c.contract_id) + '">'
                + '<iconify-icon icon="' + esc(c.icon || 'mdi:file-document-outline') + '" class="text-sm align-middle mr-0.5"></iconify-icon>'
                + '<span>' + esc(c.contract_type) + '</span></button>';
        }).join('');
        // 绑定事件
        tabs.querySelectorAll('.contract-tab').forEach(function(btn) {
            btn.addEventListener('click', function() {
                selectContract(btn.getAttribute('data-contract-id'));
            });
        });
    }

    function selectContract(contractId) {
        var c = SA.contracts.find(function(x) { return x.contract_id === contractId; });
        if (!c) return;
        SA.currentContract = c;
        renderContractTabs();
        renderCurrentContractInfo();
        updateProgress();
        // 触发 current contract change 事件
        document.dispatchEvent(new CustomEvent('scoreApp:contractChanged', {detail: c}));
    }

    function renderCurrentContractInfo() {
        var info = document.getElementById('current-contract-info');
        var c = SA.currentContract;
        if (!info || !c) return;
        info.classList.remove('hidden');
        // 当前合同 tag
        var tag = document.getElementById('score-current-contract-tag');
        if (tag) tag.textContent = c.contract_type;
        // 合同标题 + meta
        document.getElementById('contract-title').textContent = c.contract_title || c.contract_type;
        document.getElementById('contract-meta').textContent = '当事人: ' + (c.party_a || '—') + ' / ' + (c.party_b || '—')
            + ' · 金额: ' + (c.amount || '面议') + ' · 推荐立场: ' + (c.stance || '审查方');
        // 风险标签
        var risksEl = document.getElementById('contract-risks');
        risksEl.innerHTML = (c.expected_risks || {}).fatal
            ? '<span class="text-[10px] px-1.5 py-0.5 bg-danger-tint text-danger rounded-sm">'
                + c.expected_risks.fatal.length + ' 致命</span>'
            : '';
        if (c.expected_risks && c.expected_risks.major) {
            risksEl.innerHTML += '<span class="text-[10px] px-1.5 py-0.5 bg-warning-tint text-warning rounded-sm">'
                + c.expected_risks.major.length + ' 重大</span>';
        }
        if (c.expected_risks && c.expected_risks.advisory) {
            risksEl.innerHTML += '<span class="text-[10px] px-1.5 py-0.5 bg-brand-tint text-brand rounded-sm">'
                + c.expected_risks.advisory.length + ' 建议</span>';
        }
        // 合同全文预览 (如果有)
        var preview = document.getElementById('contract-text-preview');
        if (preview) preview.textContent = c.contract_text || '（合同全文从后端 contract_review/fixtures 接口获取, 此处仅显示摘要）';
    }

    // ====== 渲染 5 维度滑块 + 评论 ======
    function renderDimensions() {
        var container = document.getElementById('score-dimensions');
        if (!container) return;
        container.innerHTML = DIMENSIONS.map(function(d, idx) {
            var colorMap = {
                danger: 'text-danger',
                warning: 'text-warning',
                urgent: 'text-urgent',
                brand: 'text-brand',
                success: 'text-success'
            };
            return '<div class="space-y-2" data-dim-id="' + esc(d.id) + '">'
                + '<div class="flex items-start justify-between gap-2">'
                + '  <div class="flex-1 min-w-0">'
                + '    <label class="text-sm font-medium text-fg-primary flex items-center gap-1.5">'
                + '      <span class="w-5 h-5 rounded-full bg-' + d.color + '-tint text-' + d.color + ' flex items-center justify-center text-[10px] font-bold">' + (idx + 1) + '</span>'
                + '      <iconify-icon icon="' + d.icon + '" class="' + colorMap[d.color] + '"></iconify-icon>'
                + '      <span>' + esc(d.label) + '</span>'
                + '    </label>'
                + '    <p class="text-[11px] text-fg-tertiary mt-0.5 leading-relaxed">' + esc(d.description) + '</p>'
                + '    <p class="text-[10px] text-fg-tertiary mt-1 italic">' + esc(d.hint) + '</p>'
                + '  </div>'
                + '  <div class="flex flex-col items-end flex-shrink-0">'
                + '    <span class="text-3xl font-bold score-number ' + colorMap[d.color] + '" data-dim-display="' + esc(d.id) + '">5</span>'
                + '    <span class="text-[10px] text-fg-tertiary">/ 10 分</span>'
                + '  </div>'
                + '</div>'
                + '<div class="flex items-center gap-3">'
                + '  <span class="text-[10px] text-fg-tertiary w-4 text-right">0</span>'
                + '  <input type="range" min="0" max="10" step="1" value="5" '
                + '    class="score-slider flex-1" data-dim-slider="' + esc(d.id) + '" '
                + '    aria-label="' + esc(d.label) + '评分 0-10">'
                + '  <span class="text-[10px] text-fg-tertiary w-6">10</span>'
                + '</div>'
                + '<textarea class="w-full px-3 py-2 text-xs bg-bg-subtle border border-bg-border rounded-md resize-none focus:bg-white focus:border-brand focus:ring-2 focus:ring-brand/20 outline-none transition-all" '
                + '  rows="2" maxlength="200" placeholder="评论 (≤200 字, 可选)" '
                + '  data-dim-comment="' + esc(d.id) + '" '
                + '  aria-label="' + esc(d.label) + '评论"></textarea>'
                + '</div>';
        }).join('');
        // 绑定滑块事件
        container.querySelectorAll('[data-dim-slider]').forEach(function(slider) {
            slider.addEventListener('input', function() {
                var dimId = slider.getAttribute('data-dim-slider');
                var value = parseInt(slider.value, 10);
                SA.scores[dimId] = value;
                // 更新数字显示
                var display = container.querySelector('[data-dim-display="' + dimId + '"]');
                if (display) display.textContent = value;
                updateAggregate();
            });
        });
        // 绑定评论事件
        container.querySelectorAll('[data-dim-comment]').forEach(function(area) {
            area.addEventListener('input', function() {
                var dimId = area.getAttribute('data-dim-comment');
                SA.comments[dimId] = area.value;
            });
        });
        // 初始化默认 5 分
        DIMENSIONS.forEach(function(d) { SA.scores[d.id] = 5; });
        updateAggregate();
    }

    // ====== 综合评分聚合 ======
    function updateAggregate() {
        var sum = 0;
        var count = 0;
        DIMENSIONS.forEach(function(d) {
            if (typeof SA.scores[d.id] === 'number') {
                sum += SA.scores[d.id];
                count++;
            }
        });
        var avg = count > 0 ? (sum / count) : 0;
        var display = document.getElementById('score-aggregate-display');
        var meta = document.getElementById('score-aggregate-meta');
        var bar = document.getElementById('score-summary-bar');
        if (display) display.textContent = avg.toFixed(1);
        if (meta) meta.textContent = '满分 10 分 · 律师: ' + (SA.currentLawyerId || '—');
        if (bar) bar.classList.remove('hidden');
        // 进度
        updateProgress();
    }

    // ====== 进度条 (5 合同 5 律师子集已完成数 / 总数 5) ======
    function updateProgress() {
        var scored = SA.history.length;
        var current = document.getElementById('score-progress-current');
        var total = document.getElementById('score-progress-total');
        var bar = document.getElementById('score-progress-bar');
        var pill = document.getElementById('score-progress-pill');
        if (current) current.textContent = scored;
        if (total) total.textContent = 5;
        if (bar) bar.style.width = Math.min((scored / 5) * 100, 100) + '%';
        if (pill) pill.classList.toggle('hidden', scored === 0);
        // 历史卡
        renderHistory();
    }

    // ====== 律师下拉渲染 ======
    function renderLawyerOptions() {
        var sel = document.getElementById('lawyer-select');
        if (!sel) return;
        sel.innerHTML = '<option value="">— 选择律师 / 评审编号 —</option>'
            + LAWYERS.map(function(l) {
                return '<option value="' + esc(l.id) + '">' + esc(l.name) + ' · ' + esc(l.venue) + '</option>';
            }).join('');
        sel.addEventListener('change', function() {
            SA.currentLawyerId = sel.value;
            updateAggregate();
        });
    }

    // ====== 提交按钮 ======
    function initSubmit() {
        var btn = document.getElementById('score-submit-btn');
        if (!btn) return;
        btn.addEventListener('click', function() {
            submitScore();
        });
    }

    function submitScore() {
        var status = document.getElementById('score-submit-status');
        // 校验
        if (!SA.currentLawyerId) {
            showStatus('error', '请先选择律师身份 (评审编号)');
            return;
        }
        if (!SA.currentContract) {
            showStatus('error', '请先选择测试合同');
            return;
        }
        var payload = {
            lawyer_id: SA.currentLawyerId,
            contract_id: SA.currentContract.contract_id,
            contract_type: SA.currentContract.contract_type,
            scores: SA.scores,
            comments: SA.comments,
            submitted_at: new Date().toISOString()
        };
        // 提交到后端
        fetch(SA.apiBase + '/submit-score', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.detail) throw new Error(data.detail);
                showStatus('success', '已提交评分 (score_id=' + (data.score_id || '—') + ')');
                toast('已提交 ✓', 'success');
                // 记录到历史 (前端)
                SA.history.push({
                    lawyer_id: SA.currentLawyerId,
                    contract_id: SA.currentContract.contract_id,
                    contract_type: SA.currentContract.contract_type,
                    contract_title: SA.currentContract.contract_title,
                    aggregate_score: parseFloat(document.getElementById('score-aggregate-display').textContent || 0),
                    submitted_at: payload.submitted_at,
                    score_id: data.score_id
                });
                saveHistory();
                updateProgress();
            })
            .catch(function(err) {
            // 断网 fallback: 暂存 localStorage
                console.warn('提交失败, 触发 localStorage fallback:', err);
                SA.submittedCache.push(payload);
                saveCache();
                SA.history.push({
                    lawyer_id: SA.currentLawyerId,
                    contract_id: SA.currentContract.contract_id,
                    contract_type: SA.currentContract.contract_type,
                    contract_title: SA.currentContract.contract_title,
                    aggregate_score: parseFloat(document.getElementById('score-aggregate-display').textContent || 0),
                    submitted_at: payload.submitted_at,
                    score_id: null,
                    cached: true
                });
                saveHistory();
                updateProgress();
                showStatus('warning', '已暂存 localStorage (网络异常, 重连后自动补传)');
                toast('已暂存 (离线)', 'warning');
            });
    }

    function showStatus(type, msg) {
        var status = document.getElementById('score-submit-status');
        if (!status) return;
        status.classList.remove('hidden', 'text-success', 'text-warning', 'text-danger');
        var colorMap = {success: 'text-success', warning: 'text-warning', error: 'text-danger'};
        status.classList.add(colorMap[type] || 'text-fg-secondary');
        var iconMap = {success: 'mdi:check-circle', warning: 'mdi:alert-circle', error: 'mdi:close-circle'};
        status.innerHTML = '<iconify-icon icon="' + iconMap[type] + '" class="text-sm align-middle"></iconify-icon> ' + esc(msg);
    }

    function initClear() {
        var btn = document.getElementById('score-clear-btn');
        if (!btn) return;
        btn.addEventListener('click', function() {
            if (!confirm('确认清空当前 5 维度评分 + 文字评论? (不影响已提交历史)')) return;
            DIMENSIONS.forEach(function(d) {
                SA.scores[d.id] = 5;
                SA.comments[d.id] = '';
                var slider = document.querySelector('[data-dim-slider="' + d.id + '"]');
                var display = document.querySelector('[data-dim-display="' + d.id + '"]');
                var area = document.querySelector('[data-dim-comment="' + d.id + '"]');
                if (slider) slider.value = 5;
                if (display) display.textContent = 5;
                if (area) area.value = '';
            });
            updateAggregate();
            toast('已清空当前评分', 'info');
        });
    }

    // ====== localStorage fallback 管理 ======
    function loadCache() {
        try {
            var raw = localStorage.getItem('w6_score_cache_v1');
            SA.submittedCache = raw ? JSON.parse(raw) : [];
        } catch (e) { SA.submittedCache = []; }
        try {
            var raw2 = localStorage.getItem('w6_score_history_v1');
            SA.history = raw2 ? JSON.parse(raw2) : [];
        } catch (e) { SA.history = []; }
    }

    function saveCache() {
        try { localStorage.setItem('w6_score_cache_v1', JSON.stringify(SA.submittedCache)); } catch (e) {}
    }

    function saveHistory() {
        try { localStorage.setItem('w6_score_history_v1', JSON.stringify(SA.history)); } catch (e) {}
    }

    // ====== 重连后自动补传 ======
    function flushCache() {
        if (!SA.isOnline || SA.submittedCache.length === 0) return;
        var failed = [];
        var completed = 0;
        SA.submittedCache.forEach(function(payload) {
            fetch(SA.apiBase + '/submit-score', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.score_id) {
                        completed++;
                        console.log('[ScoreApp] 补传成功:', payload.contract_id);
                    }
                })
                .catch(function() {
                    failed.push(payload);
                })
                .finally(function() {
                    SA.submittedCache = failed;
                    saveCache();
                    if (completed > 0) {
                        toast('已自动补传 ' + completed + ' 条评分 (断网前暂存)', 'success');
                    }
                });
        });
    }

    // ====== online/offline 事件 ======
    function initOnlineListener() {
        var banner = document.getElementById('score-offline-banner');
        function updateBanner() {
            SA.isOnline = navigator.onLine;
            if (banner) {
                if (SA.isOnline) {
                    banner.classList.add('hidden');
                } else {
                    banner.classList.remove('hidden');
                }
            }
        }
        window.addEventListener('online', function() {
            updateBanner();
            console.log('[ScoreApp] 网络恢复, 触发补传');
            flushCache();
        });
        window.addEventListener('offline', function() {
            updateBanner();
            toast('网络断开 - 评分将自动暂存到 localStorage', 'warning');
        });
        updateBanner();
    }

    // ====== 渲染历史列表 ======
    function renderHistory() {
        var card = document.getElementById('score-history-card');
        var list = document.getElementById('score-history-list');
        var count = document.getElementById('score-history-count');
        if (!card || !list) return;
        if (SA.history.length === 0) {
            card.classList.add('hidden');
            return;
        }
        card.classList.remove('hidden');
        count.textContent = SA.history.length;
        list.innerHTML = SA.history.slice().reverse().map(function(h) {
            var dt = new Date(h.submitted_at);
            var dtStr = dt.toLocaleString('zh-CN', {hour12: false});
            var cachedTag = h.cached ? '<span class="text-[9px] px-1 py-0.5 bg-warning-tint text-warning rounded-sm ml-1">已暂存</span>' : '';
            var scoreColor = h.aggregate_score >= 7 ? 'text-success' : h.aggregate_score >= 4 ? 'text-warning' : 'text-danger';
            return '<div class="flex items-center justify-between gap-2 px-3 py-2 bg-bg-subtle rounded-md border border-bg-border">'
                + '<div class="flex items-center gap-2 min-w-0 flex-1">'
                + '  <iconify-icon icon="mdi:check-circle" class="text-success flex-shrink-0"></iconify-icon>'
                + '  <div class="min-w-0 flex-1">'
                + '    <div class="text-xs font-medium truncate">' + esc(h.contract_type) + ' · ' + esc(h.lawyer_id) + cachedTag + '</div>'
                + '    <div class="text-[10px] text-fg-tertiary truncate">' + esc(dtStr) + ' · ' + esc(h.contract_title || h.contract_id || '') + '</div>'
                + '  </div>'
                + '</div>'
                + '<span class="text-base font-bold ' + scoreColor + ' score-number">' + h.aggregate_score.toFixed(1) + '</span>'
                + '</div>';
        }).join('');
    }

    // ====== 帮助 Modal (Utils.showModal 统一管理) ======
    var _closeScoreHelpModal = null;
    function initHelpModal() {
        var open = document.getElementById('score-help-btn');
        if (!open) return;
        open.addEventListener('click', function() {
            var content =
                '<div class="space-y-3 text-sm text-fg-secondary">' +
                '<div>' +
                '<p class="font-medium text-fg-primary mb-1">Step 1 · 选择律师身份</p>' +
                '<p class="text-xs text-fg-tertiary">选择你的评审编号 (L1-L5) + 姓名 (下拉可选). 评审后端按律师维度聚合.</p>' +
                '</div>' +
                '<div>' +
                '<p class="font-medium text-fg-primary mb-1">Step 2 · 切换 5 份测试合同</p>' +
                '<p class="text-xs text-fg-tertiary">5 合同覆盖 PRD § 3.12.2 必备 5 大类 (房屋租赁/借款/劳动/服务/销售). 每份合同需独立评分一次.</p>' +
                '</div>' +
                '<div>' +
                '<p class="font-medium text-fg-primary mb-1">Step 3 · 5 维度 0-10 分评分</p>' +
                '<p class="text-xs text-fg-tertiary">D1 致命准确 / D2 建议实用 / D3 策略可执行 / D4 中立性 / D5 UI 流程. 每维度 100 字以内文字评论.</p>' +
                '</div>' +
                '<div>' +
                '<p class="font-medium text-fg-primary mb-1">Step 4 · 提交 (自动断网 fallback)</p>' +
                '<p class="text-xs text-fg-tertiary">提交后立即落库 review_scores. 断网时自动暂存 localStorage, 顶部出现 "离线" 角标, 重连后自动补传.</p>' +
                '</div>' +
                '<div class="bg-warning-tint border-l-4 border-warning rounded-md p-3">' +
                '<p class="text-xs text-fg-secondary"><strong>提示</strong>: 5 律师 × 5 合同 = 25 条评分. 评审结束后, 团队汇总视图将自动生成 prd-feedback v1.0.</p>' +
                '</div>' +
                '</div>';
            if (_closeScoreHelpModal) _closeScoreHelpModal();
            _closeScoreHelpModal = Utils.showModal({
                id: 'score-help-modal',
                title: '使用说明',
                icon: 'mdi:help-circle-outline',
                content: content,
                footer: '<button class="px-4 py-2 text-sm font-medium text-white bg-brand hover:bg-brand-hover rounded-lg transition-colors" onclick="closeScoreHelpModal()">知道了</button>',
                size: 'md'
            });
        });
    }

    // 暴露给 onclick 调用
    globalThis.closeScoreHelpModal = function() {
        if (_closeScoreHelpModal) {
            _closeScoreHelpModal();
            _closeScoreHelpModal = null;
        }
    };

    // ====== 视图切换: 切换到 score-app 时重新初始化 ======
    function initViewHook() {
        document.addEventListener('scoreApp:visible', function() {
            renderLawyerOptions();
            loadContracts();
            loadCache();
            initOnlineListener();
            flushCache();
        });
    }

    function patchRouter() {
        // 重写 switchView: 当切换到 score-app 视图时触发可见事件
        var orig = window.switchView;
        if (typeof orig !== 'function') return;
        if (orig.__w6_patched) return;
        globalThis.switchView = function(viewId, el) {
            orig.call(this, viewId, el);
            if (viewId === 'review-score-app') {
                setTimeout(function() {
                    document.dispatchEvent(new CustomEvent('scoreApp:visible'));
                }, 100);
            }
        };
        globalThis.switchView.__w6_patched = true;
    }

    // ====== 启动 ======
    function boot() {
        renderDimensions();
        renderLawyerOptions();
        loadContracts();
        loadCache();
        initSubmit();
        initClear();
        initOnlineListener();
        initHelpModal();
        initViewHook();
        patchRouter();
        // 移动端优化 (滑块高度)
        if (window.matchMedia('(max-width: 767px)').matches) {
            document.querySelectorAll('input[type=range].score-slider').forEach(function(s) {
                s.style.height = '12px';
            });
        }
        // 启动时若已暂存, 重连后自动补传
        if (navigator.onLine) {
            setTimeout(flushCache, 1500);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

    // 全局暴露 (调试 + 团队汇总视图用)
    globalThis.SA = SA;
    globalThis.ScoreApp = {
        flushCache: flushCache,
        loadContracts: loadContracts,
        submitScore: submitScore,
        history: function() { return SA.history; }
    };
})();
