/**
 * Router 模块 - 视图路由 + 视图缓存 + 动态加载
 * 拆分自 script.js + schedule.js (2026-06-28 IIFE 拆分计划)
 *
 * 加载顺序: 在 app-state.js 之后, schedule.js 之前
 * 依赖: AppState (app-state.js)
 *
 * 暴露: viewCache, viewFileMap, isDevMode, loadView, switchView, switchSidebarTab
 * 全部 globalThis 双绑定, 兼容 HTML inline onclick (router.someFunc)
 */

(function() {
    'use strict';

    // ===== 视图缓存管理 =====
    var viewCache = {};

    // ===== 视图文件名映射 =====
    var viewFileMap = {
        'login': 'login.html',
        'workstation': 'workstation.html',
        'schedule-list': 'schedule-list.html',
        'attention-list': 'attention-list.html',
        'case-list': 'case-list.html',
        'case-analysis': 'case-analysis.html',
        'schedule-calendar': 'schedule-calendar.html',
        'case-dynamics': 'case-dynamics.html',
        'attachment-list': 'attachment-list.html',
        'case': 'case-detail.html',
        'client': 'client.html',
        'client-detail': 'client-detail.html',
        'template': 'template.html',
        'knowledge': 'knowledge.html',
        'ai': 'ai.html',
        'subscription': 'subscription.html',
        'payment': 'payment.html',
        'payment-success': 'payment-success.html',
        'orders': 'orders.html',
        'member-center': 'member-center.html',
        'account-settings': 'account-settings.html',
        'archive': 'archive.html',
        'notifications': 'notifications.html',
        'deadline': 'deadline.html',
        'zhixing': 'zhixing.html',
        'case-progress': 'case-progress.html',
        'ai-doc': 'ai-doc.html',
        'firm': 'firm.html',
        'cases-db': 'cases-db.html',
        'laws-db': 'laws-db.html',
        'companies-db': 'companies-db.html',
        // Skill 2 合同风险审查 (W5 lex-coder)
        'contract-review-upload': 'contract-review/contract-review-upload.html',
        'contract-review-result': 'contract-review/contract-review-result.html',
        'contract-review-suggestion': 'contract-review/contract-review-suggestion.html',
        'contract-review-negotiation': 'contract-review/contract-review-negotiation.html',
        'contract-review-export': 'contract-review/contract-review-export.html',
        // W6 (2026-06-29 lex-coder) 律师评审 Score App
        'review-score-app': 'review/score-app.html',
        // W7 (2026-06-29 lex-coder) 评审数据看板
        'review-board': 'review/board.html',
        // W8 (2026-06-29 lex-coder) PRD backlog 总览 (A2)
        'backlog': 'backlog/index.html',
        // W9 (2026-06-29 lex-coder) Skill 3 文书生成 (C1: 起诉状/答辩状/合同/律师函)
        'doc-gen': 'doc-gen/index.html',
        // W12 A2 (2026-06-30 lex-coder) 双审工作流 (5 状态机 + 4 文书风险标注 + 客户签字)
        'doc-review': 'doc-review/index.html',
        // W10 (2026-06-30 lex-bd) 创始体验官招募页 (B2: 80 席剩余 + 6 模块 + 2 track event)
        'founding': 'founding/index.html',
        // W13 (2026-06-30 lex-coder) 运营 dashboard (4 业务 + 3 创史专属 + 7 SQL + 3 图表 + 5min 刷新)
        'dashboard': 'dashboard/index.html'
    };

    // ===== Dev 模式检测 (URL 含 ?dev=1 或 dev=N 非 0) =====
    var isDevMode = window.location.search.indexOf('dev=1') !== -1 ||
                     window.location.search.indexOf('dev=') !== -1 && /dev=(\d+)/.test(window.location.search) && RegExp.$1 !== '0';

    /**
     * 动态加载视图 HTML, 已缓存直接复用
     * (从 schedule.js 搬过来, schedule.js 不该有视图加载基础设施)
     *
     * 注意: insertAdjacentHTML('beforeend', html) 不执行 <script>, 必须手动提取 + 重建执行
     * (W9 A2 已知 bug fix, W13 C1 dashboard 需要 IIFE 跑才能初始化 chart + 倒计时 + track event)
     */
    function loadView(viewId, callback) {
        if (!isDevMode && viewCache[viewId]) {
            if (callback) callback(viewCache[viewId]);
            return;
        }
        var fileName = viewFileMap[viewId];
        if (!fileName) {
            console.error('未知的视图ID:', viewId);
            return;
        }
        var url = 'templates/views/' + fileName + '?_t=' + Date.now();
        fetch(url)
            .then(function(response) { response.text().then(function(html) {
                viewCache[viewId] = html;
                // W13 C1 fix: 提取 <script> 重建执行 (insertAdjacentHTML 不跑 innerHTML <script>)
                var scripts = [];
                var stripped = html.replace(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi, function(_match, attrs, body) {
                    scripts.push({ attrs: attrs, body: body });
                    return '';
                });
                var mainContent = document.getElementById('main-content');
                if (mainContent) {
                    mainContent.insertAdjacentHTML('beforeend', stripped);
                    scripts.forEach(function(s) {
                        try {
                            var scriptEl = document.createElement('script');
                            // 提取 src / type 等 attrs
                            var attrRegex = /([a-zA-Z\-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/g;
                            var match;
                            while ((match = attrRegex.exec(s.attrs)) !== null) {
                                var name = match[1];
                                var val = match[2] || match[3] || match[4] || '';
                                if (name && val) scriptEl.setAttribute(name, val);
                            }
                            scriptEl.textContent = s.body;
                            document.body.appendChild(scriptEl);
                        } catch (e) {
                            console.error('[loadView] 执行 view script 失败:', viewId, e);
                        }
                    });
                }
                if (callback) callback(html);
            }); })
            .catch(function(err) { console.error('加载视图失败:', viewId, err); });
    }

    /**
     * 切换视图: 已加载直接显示, 未加载动态 fetch 后插入
     */
    function switchView(viewId, el) {
        var target = document.getElementById('view-' + viewId);
        if (target) {
            document.querySelectorAll('.view-content').forEach(function(view) { view.classList.add('hidden'); });
            target.classList.remove('hidden');
            if (viewId === 'schedule-list' || viewId === 'attention-list') {
                target.classList.add('flex-col');
            }
            if (viewId === 'template') {
                if (typeof fixTemplateViewDOM === 'function') fixTemplateViewDOM();
                setTimeout(function() {
                    if (typeof renderPersonalTemplates === 'function') renderPersonalTemplates();
                }, 50);
            }
            if (viewId === 'schedule-calendar' || viewId === 'schedule-list') {
                setTimeout(function() {
                    if (typeof window.renderScheduleList === 'function') window.renderScheduleList();
                    if (typeof window.filterScheduleByDate === 'function') window.filterScheduleByDate();
                }, 50);
            }
            if (viewId === 'notifications') {
                setTimeout(function() {
                    if (typeof window.setNotificationsFilter === 'function') window.setNotificationsFilter(AppState.notificationsFilter || 'all');
                }, 50);
            }
            if (viewId === 'review-board') {
                setTimeout(function() {
                    if (typeof window.__loadReviewBoard === 'function') window.__loadReviewBoard();
                }, 50);
            }
            if (viewId === 'backlog') {
                setTimeout(function() {
                    if (typeof window.__loadBacklogBoard === 'function') window.__loadBacklogBoard();
                }, 50);
            }
            if (viewId === 'doc-gen') {
                setTimeout(function() {
                    if (typeof window.__loadDocGenHealth === 'function') window.__loadDocGenHealth();
                }, 50);
            }
            if (viewId === 'founding') {
                // founding 招募页是公开 landing, 由 founding/index.html 自带 track stub + DOMContentLoaded; 这里无需额外调用, 但保留 setTimeout 以防未来加健康检查
                setTimeout(function() {
                    if (typeof window.__loadFoundingView === 'function') window.__loadFoundingView();
                }, 50);
            }
            if (viewId === 'founding') {
                // founding 招募页是公开 landing, 由 founding/index.html 自带 track stub + DOMContentLoaded; 这里无需额外调用, 但保留 setTimeout 以防未来加健康检查
                setTimeout(function() {
                    if (typeof window.__loadFoundingView === 'function') window.__loadFoundingView();
                }, 50);
            }
            if (viewId === 'founding') {
                // W10 B2 创始体验官招募页: 倒计时由 view 内部 setInterval 处理, 表单提交由 view 内部处理
                // track event founding_viewed 在 view 加载时自动上报 (view 内 trackEvent 函数)
                // 这里无需额外初始化, 但确保倒计时元素存在时再触发
                setTimeout(function() {
                    var cdDays = document.getElementById('cd-days');
                    if (cdDays && typeof window.__initFoundingCountdown === 'function') {
                        window.__initFoundingCountdown();
                    }
                }, 50);
            }
            if (viewId === 'dashboard') {
                // W13 C1 dashboard: chart 已在 view 内部初始化 (DOMContentLoaded), 重新可见时重建 chart
                setTimeout(function() {
                    if (typeof window.__loadDashboardView === 'function') window.__loadDashboardView();
                }, 50);
            }
        } else {
            loadView(viewId, function(html) {
                document.getElementById('main-content').insertAdjacentHTML('beforeend', html);
                var newTarget = document.getElementById('view-' + viewId);
                if (newTarget) {
                    document.querySelectorAll('.view-content').forEach(function(view) { view.classList.add('hidden'); });
                    newTarget.classList.remove('hidden');
                    if (viewId === 'schedule-list' || viewId === 'attention-list') {
                        newTarget.classList.add('flex-col');
                    }
                    if (viewId === 'template') {
                        setTimeout(fixTemplateViewDOM, 100);
                        setTimeout(fixTemplateViewDOM, 500);
                        setTimeout(function() {
                            if (typeof renderPersonalTemplates === 'function') renderPersonalTemplates();
                        }, 50);
                    }
                    if (viewId === 'schedule-calendar' || viewId === 'schedule-list') {
                        setTimeout(function() {
                            if (typeof window.renderScheduleList === 'function') window.renderScheduleList();
                            if (typeof window.filterScheduleByDate === 'function') window.filterScheduleByDate();
                        }, 50);
                    }
                    if (viewId === 'notifications') {
                        setTimeout(function() {
                            if (typeof window.setNotificationsFilter === 'function') window.setNotificationsFilter(AppState.notificationsFilter || 'all');
                        }, 50);
                    }
                    if (viewId === 'review-board') {
                        setTimeout(function() {
                            if (typeof window.__loadReviewBoard === 'function') window.__loadReviewBoard();
                        }, 50);
                    }
                    if (viewId === 'backlog') {
                        setTimeout(function() {
                            if (typeof window.__loadBacklogBoard === 'function') window.__loadBacklogBoard();
                        }, 50);
                    }
                    if (viewId === 'doc-gen') {
                        setTimeout(function() {
                            if (typeof window.__loadDocGenHealth === 'function') window.__loadDocGenHealth();
                        }, 50);
                    }
                    if (viewId === 'founding') {
                        setTimeout(function() {
                            if (typeof window.__loadFoundingView === 'function') window.__loadFoundingView();
                        }, 50);
                    }
                    if (viewId === 'founding') {
                        setTimeout(function() {
                            if (typeof window.__loadFoundingView === 'function') window.__loadFoundingView();
                        }, 50);
                    }
                    if (viewId === 'founding') {
                        // W10 B2 创始体验官招募页: view 内部自包含倒计时 + 表单 + track event
                        setTimeout(function() {
                            var cdDays = document.getElementById('cd-days');
                            if (cdDays && typeof window.__initFoundingCountdown === 'function') {
                                window.__initFoundingCountdown();
                            }
                        }, 50);
                    }
                    if (viewId === 'dashboard') {
                        // W13 C1 dashboard 首次加载: view 内部 DOMContentLoaded 会触发 chart 初始化
                        // 这里额外调一次确保 chart 在视图可见时重建
                        setTimeout(function() {
                            if (typeof window.__loadDashboardView === 'function') window.__loadDashboardView();
                        }, 100);
                    }
                }
            });
        }

        // 更新侧边栏状态
        if (el) {
            document.querySelectorAll('.sidebar-item').forEach(function(item) { item.classList.remove('active'); });
            el.classList.add('active');
        }

        // 切换 workstation 时刷新今日日程角标 + 日期控件
        if (viewId === 'workstation') {
            setTimeout(function() {
                if (typeof window.updateTodayScheduleBadge === 'function') window.updateTodayScheduleBadge();
                if (typeof window.renderTodayScheduleDateControls === 'function') window.renderTodayScheduleDateControls();
                if (typeof window.renderTodaySchedule === 'function') window.renderTodaySchedule();
            }, 50);
        }
    }

    /**
     * 侧边栏 tab 切换 (工作 / AI 对话)
     */
    function switchSidebarTab(tab) {
        var tabWork = document.getElementById('sidebarTabWork');
        var tabAI = document.getElementById('sidebarTabAI');
        var btns = document.querySelectorAll('.sidebar-tab-btn');

        btns.forEach(function(btn) { btn.classList.remove('active'); });

        if (tab === 'work') {
            if (tabWork) tabWork.classList.remove('hidden');
            if (tabAI) tabAI.classList.add('hidden');
            if (btns[0]) btns[0].classList.add('active');

            var viewAI = document.getElementById('view-ai');
            if (viewAI) viewAI.classList.add('hidden');
            var ws = document.getElementById('view-workstation');
            if (ws) ws.classList.remove('hidden');
        } else {
            if (tabWork) tabWork.classList.add('hidden');
            if (tabAI) tabAI.classList.remove('hidden');
            if (btns[1]) btns[1].classList.add('active');

            document.querySelectorAll('.sidebar-item').forEach(function(item) { item.classList.remove('active'); });
            document.querySelectorAll('.view-content').forEach(function(v) { v.classList.add('hidden'); });

            var viewAI = document.getElementById('view-ai');
            if (!viewAI) {
                loadView('ai', function(html) {
                    document.getElementById('main-content').insertAdjacentHTML('beforeend', html);
                    var newViewAI = document.getElementById('view-ai');
                    if (newViewAI) newViewAI.classList.remove('hidden');
                    var aiViewChat = document.getElementById('aiViewChat');
                    if (aiViewChat) aiViewChat.classList.remove('hidden');
                });
            } else {
                viewAI.classList.remove('hidden');
                var aiViewChat = document.getElementById('aiViewChat');
                if (aiViewChat) aiViewChat.classList.remove('hidden');
                var aiViewSkills = document.getElementById('aiViewSkills');
                if (aiViewSkills) aiViewSkills.classList.add('hidden');
                var aiViewHistory = document.getElementById('aiViewHistory');
                if (aiViewHistory) aiViewHistory.classList.add('hidden');
            }
        }
    }

    // ===== 双绑定 (globalThis) =====
    globalThis.viewCache = viewCache;
    globalThis.viewFileMap = viewFileMap;
    globalThis.isDevMode = isDevMode;
    globalThis.loadView = loadView;
    globalThis.switchView = switchView;
    globalThis.switchSidebarTab = switchSidebarTab;

    // ===== 全局 click 监听: 关菜单 + 关通知面板 =====
    document.addEventListener('click', function(e) {
        var menuWork = document.getElementById('moreMenuWork');
        var menuAI = document.getElementById('moreMenuAI');
        var isClickInBtn = e.target.closest('[onclick*="toggleMoreMenu"]');
        if (!isClickInBtn) {
            if (menuWork) menuWork.classList.add('hidden');
            if (menuAI) menuAI.classList.add('hidden');
        }

        var panel = document.getElementById('notificationPanel');
        var notifBtn = document.querySelector('[onclick*="toggleNotifications"]');
        if (panel && notifBtn && !panel.contains(e.target) && !notifBtn.contains(e.target)) {
            panel.classList.add('hidden');
        }
    });

    // ===== window.onload 占位 (原 script.js 留空, 保留以防未来用) =====
    window.onload = function() {
        // 页面加载完毕
    };
})();