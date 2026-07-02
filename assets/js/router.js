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

(function () {
    'use strict';

    // ===== 视图缓存管理 =====
    var viewCache = {};

    // ===== 视图文件名映射 =====
    var viewFileMap = {
        login: 'login.html',
        workstation: 'workstation.html',
        'schedule-list': 'schedule-list.html',
        'attention-list': 'attention-list.html',
        'case-list': 'case-list.html',
        'case-analysis': 'case-analysis.html',
        'schedule-calendar': 'schedule-calendar.html',
        'case-dynamics': 'case-dynamics.html',
        'attachment-list': 'attachment-list.html',
        case: 'case-detail.html',
        client: 'client.html',
        'client-detail': 'client-detail.html',
        template: 'template.html',
        knowledge: 'knowledge.html',
        ai: 'ai.html',
        subscription: 'subscription.html',
        payment: 'payment.html',
        'payment-success': 'payment-success.html',
        orders: 'orders.html',
        'member-center': 'member-center.html',
        'account-settings': 'account-settings.html',
        archive: 'archive.html',
        notifications: 'notifications.html',
        deadline: 'deadline.html',
        zhixing: 'zhixing.html',
        'case-progress': 'case-progress.html',
        'ai-doc': 'ai-doc.html',
        firm: 'firm.html',
        'cases-db': 'cases-db.html',
        'laws-db': 'laws-db.html',
        'companies-db': 'companies-db.html',
        'contract-review-upload': 'contract-review/contract-review-upload.html',
        'contract-review-result': 'contract-review/contract-review-result.html',
        'contract-review-suggestion': 'contract-review/contract-review-suggestion.html',
        'contract-review-negotiation': 'contract-review/contract-review-negotiation.html',
        'contract-review-export': 'contract-review/contract-review-export.html',
        'review-score-app': 'review/score-app.html',
        'review-board': 'review/board.html',
        backlog: 'backlog/index.html',
        'doc-gen': 'doc-gen/index.html',
        'doc-review': 'doc-review/index.html',
        founding: 'founding/index.html',
        dashboard: 'dashboard/index.html',
        'marketplace-lawyers': 'marketplace/lawyers.html',
        'marketplace-cases': 'marketplace/cases.html',
        'marketplace-referrals': 'marketplace/referrals.html',
        'marketplace-cross-border': 'marketplace/cross-border.html',
        'marketplace-metrics': 'marketplace/metrics.html',
        onboarding: 'onboarding.html',
        pricing: 'pricing.html'
    };

    // ===== 视图初始化函数映射 (优化: 避免重复的 if-else setTimeout 代码) =====
    var viewInitMap = {
        template: function () {
            if (typeof fixTemplateViewDOM === 'function') fixTemplateViewDOM();
            setTimeout(function () {
                if (typeof renderPersonalTemplates === 'function') renderPersonalTemplates();
            }, 50);
        },
        'schedule-calendar': function () {
            setTimeout(function () {
                if (typeof window.renderScheduleList === 'function') window.renderScheduleList();
                if (typeof window.filterScheduleByDate === 'function') window.filterScheduleByDate();
            }, 50);
        },
        'schedule-list': function () {
            setTimeout(function () {
                if (typeof window.renderScheduleList === 'function') window.renderScheduleList();
                if (typeof window.filterScheduleByDate === 'function') window.filterScheduleByDate();
            }, 50);
        },
        notifications: function () {
            setTimeout(function () {
                if (typeof window.setNotificationsFilter === 'function')
                    window.setNotificationsFilter(AppState.notificationsFilter || 'all');
            }, 50);
        },
        'review-board': function () {
            setTimeout(function () {
                if (typeof window.__loadReviewBoard === 'function') window.__loadReviewBoard();
            }, 50);
        },
        backlog: function () {
            setTimeout(function () {
                if (typeof window.__loadBacklogBoard === 'function') window.__loadBacklogBoard();
            }, 50);
        },
        'doc-gen': function () {
            setTimeout(function () {
                if (typeof window.__loadDocGenHealth === 'function') window.__loadDocGenHealth();
            }, 50);
        },
        founding: function () {
            setTimeout(function () {
                if (typeof window.__loadFoundingView === 'function') window.__loadFoundingView();
                var cdDays = document.getElementById('cd-days');
                if (cdDays && typeof window.__initFoundingCountdown === 'function') {
                    window.__initFoundingCountdown();
                }
            }, 50);
        },
        'attachment-list': function () {
            setTimeout(function () {
                if (typeof window.initAttachmentList === 'function') window.initAttachmentList();
            }, 50);
        },
        'attention-list': function () {
            setTimeout(function () {
                if (typeof window.initAttentionList === 'function') window.initAttentionList();
            }, 50);
        },
        archive: function () {
            setTimeout(function () {
                if (typeof window.initArchive === 'function') window.initArchive();
            }, 50);
        },
        'member-center': function () {
            setTimeout(function () {
                if (typeof window.initMemberCenter === 'function') window.initMemberCenter();
            }, 50);
        },
        firm: function () {
            setTimeout(function () {
                if (typeof window.initFirm === 'function') window.initFirm();
            }, 50);
        },
        orders: function () {
            setTimeout(function () {
                if (typeof window.initOrders === 'function') window.initOrders();
            }, 50);
        },
        'case-dynamics': function () {
            setTimeout(function () {
                if (typeof window.switchDynamicsView === 'function') window.switchDynamicsView('list');
                if (typeof window.initCaseDynamics === 'function') window.initCaseDynamics();
            }, 50);
        },
        'companies-db': function () {
            setTimeout(function () {
                if (typeof window.initCompaniesDb === 'function') window.initCompaniesDb();
            }, 50);
        },
        'cases-db': function () {
            setTimeout(function () {
                if (typeof window.initCasesDb === 'function') window.initCasesDb();
            }, 50);
        },
        zhixing: function () {
            setTimeout(function () {
                if (typeof window.initZhixing === 'function') window.initZhixing();
            }, 50);
        },
        'laws-db': function () {
            setTimeout(function () {
                if (typeof window.initLawsDb === 'function') window.initLawsDb();
            }, 50);
        },
        deadline: function () {
            setTimeout(function () {
                if (typeof window.initDeadlineView === 'function') window.initDeadlineView();
            }, 50);
        },
        'ai-doc': function () {
            setTimeout(function () {
                if (typeof window.initAIDocView === 'function') window.initAIDocView();
            }, 50);
        },
        'case-progress': function () {
            setTimeout(function () {
                if (typeof window.initCaseProgress === 'function') window.initCaseProgress();
            }, 50);
        },
        dashboard: function () {
            setTimeout(function () {
                if (typeof window.__loadDashboardView === 'function') window.__loadDashboardView();
            }, 50);
        },
        client: function () {
            setTimeout(function () {
                if (typeof window.initClientsView === 'function') window.initClientsView();
            }, 50);
        }
    };

    // ===== Marketplace 视图初始化映射 =====
    var marketplaceInitMap = {
        'marketplace-lawyers': 'initLawyersView',
        'marketplace-cases': 'initCasesView',
        'marketplace-referrals': 'initReferralsView',
        'marketplace-cross-border': 'initCrossBorderView',
        'marketplace-metrics': 'initMetricsView'
    };

    // ===== Dev 模式检测 (URL 含 ?dev=1 或 dev=N 非 0) =====
    var isDevMode =
        window.location.search.indexOf('dev=1') !== -1 ||
        (window.location.search.indexOf('dev=') !== -1 &&
            /dev=(\d+)/.test(window.location.search) &&
            RegExp.$1 !== '0');

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
            .then(function (response) {
                response.text().then(function (html) {
                    viewCache[viewId] = html;
                    // W13 C1 fix: 提取 <script> 重建执行 (insertAdjacentHTML 不跑 innerHTML <script>)
                    var scripts = [];
                    var stripped = html.replace(
                        /<script\b([^>]*)>([\s\S]*?)<\/script>/gi,
                        function (_match, attrs, body) {
                            scripts.push({ attrs: attrs, body: body });
                            return '';
                        }
                    );
                    var mainContent = document.getElementById('main-content');
                    if (mainContent) {
                        mainContent.insertAdjacentHTML('beforeend', stripped);
                        scripts.forEach(function (s) {
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
                });
            })
            .catch(function (err) {
                console.error('加载视图失败:', viewId, err);
            });
    }

    /**
     * 统一初始化视图 (性能优化: 使用映射表替代大量 if-else)
     */
    function initView(viewId) {
        if (viewId === 'template') {
            if (typeof fixTemplateViewDOM === 'function') fixTemplateViewDOM();
            setTimeout(fixTemplateViewDOM, 100);
            setTimeout(fixTemplateViewDOM, 500);
        }

        if (viewInitMap[viewId]) {
            try {
                viewInitMap[viewId]();
            } catch (e) {
                console.warn('[initView] 初始化视图失败:', viewId, e);
            }
        }

        if (viewId.indexOf('marketplace-') === 0) {
            setTimeout(function () {
                var fn = marketplaceInitMap[viewId];
                if (
                    fn &&
                    typeof window.MarketplaceFn !== 'undefined' &&
                    typeof window.MarketplaceFn[fn] === 'function'
                ) {
                    window.MarketplaceFn[fn]();
                }
            }, 50);
        }
    }

    /**
     * 初始化视图动画
     * 调用 Animations.initPageAnimations 扫描 [data-animate] 元素
     */
    function initViewAnimations(scope) {
        if (typeof Animations !== 'undefined' && typeof Animations.initPageAnimations === 'function') {
            setTimeout(function () {
                try {
                    Animations.initPageAnimations(scope);
                } catch (e) {
                    console.warn('[initViewAnimations] 初始化动画失败:', e);
                }
            }, 30);
        }
    }

    /**
     * 切换视图: 已加载直接显示, 未加载动态 fetch 后插入
     */
    function switchView(viewId, el) {
        if (typeof Utils !== 'undefined' && typeof Utils.closeAllModals === 'function') {
            Utils.closeAllModals();
        }

        var target = document.getElementById('view-' + viewId);
        if (target) {
            document.querySelectorAll('.view-content').forEach(function (view) {
                view.classList.add('hidden');
            });
            target.classList.remove('hidden');
            if (viewId === 'schedule-list' || viewId === 'attention-list') {
                target.classList.add('flex-col');
            }
            initView(viewId);
            initViewAnimations(target);
        } else {
            loadView(viewId, function () {
                var newTarget = document.getElementById('view-' + viewId);
                if (newTarget) {
                    document.querySelectorAll('.view-content').forEach(function (view) {
                        view.classList.add('hidden');
                    });
                    newTarget.classList.remove('hidden');
                    if (viewId === 'schedule-list' || viewId === 'attention-list') {
                        newTarget.classList.add('flex-col');
                    }
                    initView(viewId);
                    initViewAnimations(newTarget);
                }
            });
        }

        if (el) {
            document.querySelectorAll('.sidebar-item').forEach(function (item) {
                item.classList.remove('active');
            });
            el.classList.add('active');
        }

        if (viewId === 'workstation') {
            setTimeout(function () {
                if (typeof window.updateTodayScheduleBadge === 'function') window.updateTodayScheduleBadge();
                if (typeof window.renderTodayScheduleDateControls === 'function')
                    window.renderTodayScheduleDateControls();
                if (typeof window.renderTodaySchedule === 'function') window.renderTodaySchedule();
            }, 50);
        }

        updateMobileTab(viewId);
    }

    /**
     * 侧边栏 tab 切换 (工作 / AI 对话)
     */
    function switchSidebarTab(tab) {
        var tabWork = document.getElementById('sidebarTabWork');
        var tabAI = document.getElementById('sidebarTabAI');
        var btns = document.querySelectorAll('.sidebar-tab-btn');
        var viewAI;

        btns.forEach(function (btn) {
            btn.classList.remove('active');
        });

        if (tab === 'work') {
            if (tabWork) tabWork.classList.remove('hidden');
            if (tabAI) tabAI.classList.add('hidden');
            if (btns[0]) btns[0].classList.add('active');

            viewAI = document.getElementById('view-ai');
            if (viewAI) viewAI.classList.add('hidden');
            var ws = document.getElementById('view-workstation');
            if (ws) ws.classList.remove('hidden');
        } else {
            if (tabWork) tabWork.classList.add('hidden');
            if (tabAI) tabAI.classList.remove('hidden');
            if (btns[1]) btns[1].classList.add('active');

            document.querySelectorAll('.sidebar-item').forEach(function (item) {
                item.classList.remove('active');
            });
            document.querySelectorAll('.view-content').forEach(function (v) {
                v.classList.add('hidden');
            });

            viewAI = document.getElementById('view-ai');
            if (!viewAI) {
                loadView('ai', function (html) {
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

    function updateMobileTab(viewId) {
        var tabMap = {
            workstation: 'workstation',
            'case-list': 'cases',
            'cases-db': 'cases',
            knowledge: 'knowledge',
            'laws-db': 'knowledge',
            'companies-db': 'knowledge',
            'marketplace-lawyers': 'market',
            'marketplace-cases': 'market',
            'marketplace-referrals': 'market',
            'marketplace-cross-border': 'market',
            'member-center': 'profile',
            orders: 'profile',
            firm: 'profile',
            'account-settings': 'profile'
        };
        var tabId = tabMap[viewId];
        if (tabId) {
            var tabBtn = document.querySelector('[data-mobile-tab="' + tabId + '"]');
            if (tabBtn && typeof setMobileTabActive === 'function') {
                setMobileTabActive(tabBtn);
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
    document.addEventListener('click', function (e) {
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
    window.onload = function () {
        // 页面加载完毕
    };
})();
