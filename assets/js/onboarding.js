/**
 * Onboarding 引导组件
 * 提供首次使用引导、功能 Tour、步骤指示器等功能
 *
 * 暴露: Onboarding.startTour(), Onboarding.showWelcome(), Onboarding.resetProgress()
 */
(function () {
    'use strict';

    var STORAGE_PREFIX = 'lexprime.onboarding.';
    var _activeTour = null;
    var _tourRegistry = {};

    function _getStorageKey(tourId) {
        return STORAGE_PREFIX + tourId + '.completed';
    }

    function _isTourCompleted(tourId) {
        try {
            return localStorage.getItem(_getStorageKey(tourId)) === 'true';
        } catch (e) {
            return false;
        }
    }

    function _markTourCompleted(tourId) {
        try {
            localStorage.setItem(_getStorageKey(tourId), 'true');
        } catch (e) {
            console.warn('[Onboarding] 保存进度失败:', e.message);
        }
    }

    function _resetTourProgress(tourId) {
        try {
            localStorage.removeItem(_getStorageKey(tourId));
        } catch (e) {
            console.warn('[Onboarding] 重置进度失败:', e.message);
        }
    }

    function registerTour(tourId, config) {
        if (!tourId || !config || !config.steps || !config.steps.length) {
            console.warn('[Onboarding] 无效的 Tour 配置');
            return false;
        }
        _tourRegistry[tourId] = {
            id: tourId,
            title: config.title || '功能引导',
            steps: config.steps,
            onComplete: config.onComplete || null,
            onSkip: config.onSkip || null,
            overlayColor: config.overlayColor || 'rgba(0, 0, 0, 0.7)',
            highlightPadding: config.highlightPadding || 8
        };
        return true;
    }

    function startTour(tourId, options) {
        options = options || {};
        var tour = _tourRegistry[tourId];
        if (!tour) {
            console.warn('[Onboarding] 未找到 Tour:', tourId);
            return null;
        }

        if (_activeTour) {
            _activeTour.close();
        }

        var currentStep = 0;
        var overlay = null;
        var highlightBox = null;
        var tooltip = null;
        var isAnimating = false;

        function _createOverlay() {
            overlay = document.createElement('div');
            overlay.className = 'onboarding-overlay';
            overlay.style.cssText =
                'position:fixed;top:0;left:0;width:100%;height:100%;' +
                'background:' + tour.overlayColor + ';' +
                'z-index:9998;opacity:0;transition:opacity 0.3s ease;' +
                'pointer-events:none;';

            highlightBox = document.createElement('div');
            highlightBox.className = 'onboarding-highlight';
            highlightBox.style.cssText =
                'position:absolute;border-radius:8px;' +
                'box-shadow:0 0 0 9999px ' + tour.overlayColor + ';' +
                'transition:all 0.3s ease;' +
                'z-index:9999;pointer-events:none;';

            tooltip = document.createElement('div');
            tooltip.className = 'onboarding-tooltip';
            tooltip.style.cssText =
                'position:absolute;z-index:10000;max-width:320px;' +
                'background:#fff;border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,0.3);' +
                'padding:20px;transition:all 0.3s ease;opacity:0;';

            document.body.appendChild(overlay);
            document.body.appendChild(highlightBox);
            document.body.appendChild(tooltip);

            requestAnimationFrame(function () {
                overlay.style.opacity = '1';
            });
        }

        function _getElement(selector) {
            if (!selector) return null;
            if (typeof selector === 'string') {
                return document.querySelector(selector);
            }
            return selector;
        }

        function _getElementRect(el) {
            if (!el) return null;
            var rect = el.getBoundingClientRect();
            var padding = tour.highlightPadding;
            return {
                top: rect.top - padding + window.scrollY,
                left: rect.left - padding + window.scrollX,
                width: rect.width + padding * 2,
                height: rect.height + padding * 2
            };
        }

        function _positionTooltip(step, rect) {
            var tooltipWidth = tooltip.offsetWidth || 300;
            var tooltipHeight = tooltip.offsetHeight || 200;
            var gap = 16;
            var top = 0;
            var left = 0;
            var placement = step.placement || 'bottom';

            if (rect) {
                switch (placement) {
                    case 'top':
                        top = rect.top - tooltipHeight - gap;
                        left = rect.left + rect.width / 2 - tooltipWidth / 2;
                        break;
                    case 'bottom':
                        top = rect.top + rect.height + gap;
                        left = rect.left + rect.width / 2 - tooltipWidth / 2;
                        break;
                    case 'left':
                        top = rect.top + rect.height / 2 - tooltipHeight / 2;
                        left = rect.left - tooltipWidth - gap;
                        break;
                    case 'right':
                        top = rect.top + rect.height / 2 - tooltipHeight / 2;
                        left = rect.left + rect.width + gap;
                        break;
                    default:
                        top = rect.top + rect.height + gap;
                        left = rect.left + rect.width / 2 - tooltipWidth / 2;
                }

                var viewportWidth = window.innerWidth;
                var viewportHeight = window.innerHeight;
                var scrollY = window.scrollY;
                var scrollX = window.scrollX;

                if (left < 16 + scrollX) left = 16 + scrollX;
                if (left + tooltipWidth > viewportWidth - 16 + scrollX) {
                    left = viewportWidth - tooltipWidth - 16 + scrollX;
                }
                if (top < 16 + scrollY) top = 16 + scrollY;
                if (top + tooltipHeight > viewportHeight - 16 + scrollY) {
                    top = viewportHeight - tooltipHeight - 16 + scrollY;
                }
            } else {
                top = '50%';
                left = '50%';
                tooltip.style.transform = 'translate(-50%, -50%)';
            }

            tooltip.style.top = typeof top === 'number' ? top + 'px' : top;
            tooltip.style.left = typeof left === 'number' ? left + 'px' : left;
        }

        function _renderStep(stepIndex) {
            if (stepIndex < 0 || stepIndex >= tour.steps.length) return;
            var step = tour.steps[stepIndex];
            var el = _getElement(step.target);

            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }

            isAnimating = true;
            tooltip.style.opacity = '0';

            setTimeout(function () {
                var rect = el ? _getElementRect(el) : null;

                if (rect && highlightBox) {
                    highlightBox.style.top = rect.top + 'px';
                    highlightBox.style.left = rect.left + 'px';
                    highlightBox.style.width = rect.width + 'px';
                    highlightBox.style.height = rect.height + 'px';
                    highlightBox.style.display = 'block';
                } else if (highlightBox) {
                    highlightBox.style.display = 'none';
                }

                var progressPercent = ((stepIndex + 1) / tour.steps.length) * 100;
                var iconHtml = step.icon
                    ? '<div class="onboarding-step-icon w-12 h-12 rounded-xl bg-gradient-to-br from-brand to-wiki flex items-center justify-center mb-4 mx-auto">' +
                      '<iconify-icon icon="' + step.icon + '" class="text-xl text-white"></iconify-icon>' +
                      '</div>'
                    : '';

                tooltip.innerHTML =
                    '<div class="text-center">' +
                    iconHtml +
                    '<div class="flex items-center justify-between mb-3">' +
                    '<span class="text-xs font-semibold text-brand">' +
                    tour.title +
                    '</span>' +
                    '<span class="text-[11px] text-fg-tertiary">' +
                    (stepIndex + 1) +
                    ' / ' +
                    tour.steps.length +
                    '</span>' +
                    '</div>' +
                    '<div class="h-1 bg-bg rounded-full mb-4 overflow-hidden">' +
                    '<div class="h-full bg-gradient-to-r from-brand to-wiki rounded-full transition-all duration-300" style="width:' +
                    progressPercent +
                    '%"></div>' +
                    '</div>' +
                    '<h4 class="text-base font-bold text-fg-primary mb-2">' +
                    Utils.escapeHtml(step.title || '') +
                    '</h4>' +
                    '<p class="text-sm text-fg-secondary leading-relaxed mb-5">' +
                    Utils.escapeHtml(step.description || '') +
                    '</p>' +
                    '<div class="flex items-center justify-between gap-2">' +
                    '<button class="onboarding-skip-btn px-3 py-2 text-xs text-fg-tertiary hover:text-fg-secondary transition-colors rounded-lg hover:bg-bg-subtle">' +
                    '跳过' +
                    '</button>' +
                    '<div class="flex items-center gap-2">' +
                    (stepIndex > 0
                        ? '<button class="onboarding-prev-btn px-4 py-2 text-xs font-medium text-fg-secondary bg-bg hover:bg-bg-hover rounded-lg transition-colors">上一步</button>'
                        : '') +
                    '<button class="onboarding-next-btn px-5 py-2 text-xs font-semibold text-white bg-gradient-to-r from-brand to-brand-hover hover:shadow-lg hover:shadow-brand/30 rounded-lg transition-all">' +
                    (stepIndex === tour.steps.length - 1 ? '完成' : '下一步') +
                    '</button>' +
                    '</div>' +
                    '</div>' +
                    '</div>';

                _positionTooltip(step, rect);

                var skipBtn = tooltip.querySelector('.onboarding-skip-btn');
                if (skipBtn) {
                    skipBtn.addEventListener('click', _onSkip);
                }

                var prevBtn = tooltip.querySelector('.onboarding-prev-btn');
                if (prevBtn) {
                    prevBtn.addEventListener('click', _onPrev);
                }

                var nextBtn = tooltip.querySelector('.onboarding-next-btn');
                if (nextBtn) {
                    nextBtn.addEventListener('click', _onNext);
                }

                requestAnimationFrame(function () {
                    tooltip.style.opacity = '1';
                    isAnimating = false;
                });
            }, 300);
        }

        function _onNext() {
            if (isAnimating) return;
            if (currentStep < tour.steps.length - 1) {
                currentStep++;
                _renderStep(currentStep);
            } else {
                _onComplete();
            }
        }

        function _onPrev() {
            if (isAnimating) return;
            if (currentStep > 0) {
                currentStep--;
                _renderStep(currentStep);
            }
        }

        function _onSkip() {
            if (tour.onSkip) {
                try {
                    tour.onSkip();
                } catch (e) {
                    console.error('[Onboarding] Skip 回调失败:', e);
                }
            }
            close();
        }

        function _onComplete() {
            _markTourCompleted(tourId);
            if (tour.onComplete) {
                try {
                    tour.onComplete();
                } catch (e) {
                    console.error('[Onboarding] Complete 回调失败:', e);
                }
            }
            Utils.showToast({
                type: 'success',
                message: '引导完成！开始探索更多功能吧',
                duration: 3000
            });
            close();
        }

        function _onKeyDown(e) {
            if (e.key === 'Escape') {
                _onSkip();
            } else if (e.key === 'ArrowRight' || e.key === 'Enter') {
                _onNext();
            } else if (e.key === 'ArrowLeft') {
                _onPrev();
            }
        }

        function _onResize() {
            if (!isAnimating && currentStep >= 0 && currentStep < tour.steps.length) {
                var step = tour.steps[currentStep];
                var el = _getElement(step.target);
                var rect = el ? _getElementRect(el) : null;
                if (rect && highlightBox) {
                    highlightBox.style.top = rect.top + 'px';
                    highlightBox.style.left = rect.left + 'px';
                    highlightBox.style.width = rect.width + 'px';
                    highlightBox.style.height = rect.height + 'px';
                }
                _positionTooltip(step, rect);
            }
        }

        function close() {
            if (overlay) {
                overlay.style.opacity = '0';
            }
            if (tooltip) {
                tooltip.style.opacity = '0';
            }
            if (highlightBox) {
                highlightBox.style.opacity = '0';
            }

            setTimeout(function () {
                if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay);
                if (highlightBox && highlightBox.parentNode) highlightBox.parentNode.removeChild(highlightBox);
                if (tooltip && tooltip.parentNode) tooltip.parentNode.removeChild(tooltip);
                overlay = null;
                highlightBox = null;
                tooltip = null;
            }, 300);

            document.removeEventListener('keydown', _onKeyDown);
            window.removeEventListener('resize', Utils.debounce(_onResize, 150));

            _activeTour = null;
        }

        _createOverlay();
        _renderStep(0);

        document.addEventListener('keydown', _onKeyDown);
        window.addEventListener('resize', Utils.debounce(_onResize, 150));

        _activeTour = {
            close: close,
            next: _onNext,
            prev: _onPrev,
            getCurrentStep: function () {
                return currentStep;
            }
        };

        return _activeTour;
    }

    function showWelcome() {
        var modalId = 'onboarding-welcome-modal';
        var content =
            '<div class="text-center">' +
            '<div class="w-20 h-20 mx-auto mb-5 rounded-2xl bg-gradient-to-br from-brand via-wiki to-ai flex items-center justify-center relative">' +
            '<div class="absolute inset-0 rounded-2xl bg-gradient-to-br from-brand/20 to-wiki/20 animate-pulse-soft"></div>' +
            '<iconify-icon icon="mdi:hand-wave-outline" class="text-4xl text-white relative z-10"></iconify-icon>' +
            '</div>' +
            '<h3 class="text-xl font-bold bg-gradient-to-r from-brand to-wiki bg-clip-text text-transparent mb-2">欢迎使用 LexPrime</h3>' +
            '<p class="text-sm text-fg-secondary mb-6 max-w-sm mx-auto leading-relaxed">' +
            '您的智能法律助手已准备就绪。让我们花 1 分钟了解核心功能，帮助您快速上手。' +
            '</p>' +
            '<div class="grid grid-cols-3 gap-3 mb-6">' +
            '<div class="p-3 rounded-xl bg-brand-tint/30">' +
            '<iconify-icon icon="mdi:book-search-outline" class="text-xl text-brand mb-1"></iconify-icon>' +
            '<p class="text-[11px] font-medium text-fg-primary">类案检索</p>' +
            '</div>' +
            '<div class="p-3 rounded-xl bg-wiki-tint/30">' +
            '<iconify-icon icon="mdi:file-document-edit-outline" class="text-xl text-wiki mb-1"></iconify-icon>' +
            '<p class="text-[11px] font-medium text-fg-primary">合同审查</p>' +
            '</div>' +
            '<div class="p-3 rounded-xl bg-ai-tint/30">' +
            '<iconify-icon icon="mdi:robot-outline" class="text-xl text-ai mb-1"></iconify-icon>' +
            '<p class="text-[11px] font-medium text-fg-primary">AI 助手</p>' +
            '</div>' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="px-4 py-2 text-sm font-medium text-fg-secondary bg-bg hover:bg-bg-hover rounded-lg transition-colors" data-onboarding-later>稍后再说</button>' +
            '<button class="px-5 py-2 text-sm font-semibold text-white bg-gradient-to-r from-brand to-brand-hover hover:shadow-lg hover:shadow-brand/30 rounded-lg transition-all" data-onboarding-start>开始引导 →</button>';

        var closeFn = Utils.showModal({
            id: modalId,
            title: '',
            content: content,
            footer: footer,
            size: 'md',
            escClose: true,
            onClose: function () {
                _markTourCompleted('welcome_shown');
            }
        });

        setTimeout(function () {
            var modal = document.getElementById(modalId);
            if (!modal) return;

            var laterBtn = modal.querySelector('[data-onboarding-later]');
            if (laterBtn) {
                laterBtn.addEventListener('click', function () {
                    closeFn();
                });
            }

            var startBtn = modal.querySelector('[data-onboarding-start]');
            if (startBtn) {
                startBtn.addEventListener('click', function () {
                    closeFn();
                    setTimeout(function () {
                        startTour('workstation-intro');
                    }, 300);
                });
            }
        }, 50);
    }

    function checkFirstVisit() {
        var hasVisited = false;
        try {
            hasVisited = localStorage.getItem(STORAGE_PREFIX + 'has_visited') === 'true';
        } catch (e) {
            hasVisited = false;
        }

        if (!hasVisited) {
            try {
                localStorage.setItem(STORAGE_PREFIX + 'has_visited', 'true');
            } catch (e) {
                console.warn('[Onboarding] 保存访问记录失败:', e.message);
            }
            return true;
        }
        return false;
    }

    function resetAllProgress() {
        try {
            var keys = [];
            for (var i = 0; i < localStorage.length; i++) {
                var key = localStorage.key(i);
                if (key && key.indexOf(STORAGE_PREFIX) === 0) {
                    keys.push(key);
                }
            }
            keys.forEach(function (key) {
                localStorage.removeItem(key);
            });
            return true;
        } catch (e) {
            console.warn('[Onboarding] 重置所有进度失败:', e.message);
            return false;
        }
    }

    function _initDefaultTours() {
        registerTour('workstation-intro', {
            title: '工作台引导',
            steps: [
                {
                    target: '#sidebar-nav',
                    placement: 'right',
                    icon: 'mdi:view-sidebar-outline',
                    title: '侧边导航栏',
                    description: '这里是您的功能导航，包含案件管理、合同审查、AI助手等核心功能模块。'
                },
                {
                    target: 'header input[type="text"]',
                    placement: 'bottom',
                    icon: 'mdi:magnify',
                    title: '全局搜索',
                    description: '快速搜索案件、法规、企业信息，支持关键词全文检索。'
                },
                {
                    target: '.quick-actions',
                    placement: 'bottom',
                    icon: 'mdi:lightning-bolt-outline',
                    title: '快捷操作',
                    description: '一键新建案件、上传合同、预约日程，提升工作效率。'
                },
                {
                    target: '#case-list-section',
                    placement: 'top',
                    icon: 'mdi:briefcase-outline',
                    title: '我的案件',
                    description: '查看和管理您的所有案件，支持多维度筛选和排序。'
                },
                {
                    target: '#ai-assistant-section',
                    placement: 'left',
                    icon: 'mdi:robot-outline',
                    title: 'AI 助手',
                    description: '智能法律助手随时为您提供案件分析、文书润色、法律问答服务。'
                }
            ],
            onComplete: function () {
                console.log('[Onboarding] 工作台引导完成');
            }
        });

        registerTour('case-management', {
            title: '案件管理',
            steps: [
                {
                    target: '.new-case-btn',
                    placement: 'bottom',
                    icon: 'mdi:plus-circle-outline',
                    title: '新建案件',
                    description: '点击创建新案件，填写基本信息后即可开始管理。'
                },
                {
                    target: '.case-filter',
                    placement: 'bottom',
                    icon: 'mdi:filter-variant',
                    title: '筛选与排序',
                    description: '按案由、状态、时间等维度筛选案件，快速定位目标。'
                },
                {
                    target: '.case-card',
                    placement: 'right',
                    icon: 'mdi:file-document-outline',
                    title: '案件卡片',
                    description: '点击案件卡片查看详情，包含文书、证据、日程等完整信息。'
                }
            ]
        });
    }

    _initDefaultTours();

    globalThis.Onboarding = {
        registerTour: registerTour,
        startTour: startTour,
        showWelcome: showWelcome,
        checkFirstVisit: checkFirstVisit,
        resetTourProgress: _resetTourProgress,
        resetAllProgress: resetAllProgress,
        isTourCompleted: _isTourCompleted
    };
})();
