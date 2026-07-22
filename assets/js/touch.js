(function () {
    'use strict';

    function TouchHandler(element) {
        this.element = element || document;
        this._listeners = {};
        this._startX = 0;
        this._startY = 0;
        this._currentX = 0;
        this._currentY = 0;
        this._startTime = 0;
        this._longPressTimer = null;
        this._isLongPressTriggered = false;
        this._isScrolling = false;
        this._touchCount = 0;
        this._startDistance = 0;
        this._startAngle = 0;
        this._currentDistance = 0;
        this._currentAngle = 0;
        this._initialScale = 1;
        this._initialRotation = 0;
        this._swipeThreshold = 50;
        this._longPressThreshold = 500;
        this._minSwipeVelocity = 0.3;

        this._bindEvents();
    }

    TouchHandler.prototype._bindEvents = function () {
        var self = this;
        this.element.addEventListener(
            'touchstart',
            function (e) {
                self._onTouchStart(e);
            },
            { passive: true }
        );
        this.element.addEventListener(
            'touchmove',
            function (e) {
                self._onTouchMove(e);
            },
            { passive: false }
        );
        this.element.addEventListener(
            'touchend',
            function (e) {
                self._onTouchEnd(e);
            },
            { passive: true }
        );
        this.element.addEventListener(
            'touchcancel',
            function (e) {
                self._onTouchEnd(e);
            },
            { passive: true }
        );
    };

    TouchHandler.prototype._onTouchStart = function (e) {
        this._touchCount = e.touches.length;

        if (this._touchCount === 1) {
            var touch = e.touches[0];
            this._startX = touch.clientX;
            this._startY = touch.clientY;
            this._currentX = touch.clientX;
            this._currentY = touch.clientY;
            this._startTime = Date.now();
            this._isLongPressTriggered = false;
            this._isScrolling = false;

            this._longPressTimer = setTimeout(
                function () {
                    if (!self._isScrolling && !self._isLongPressTriggered) {
                        self._isLongPressTriggered = true;
                        self._trigger('longpress', {
                            x: self._startX,
                            y: self._startY,
                            target: e.target
                        });
                    }
                }.bind(this),
                this._longPressThreshold
            );
        } else if (this._touchCount === 2) {
            if (this._longPressTimer) {
                clearTimeout(this._longPressTimer);
                this._longPressTimer = null;
            }

            var touch1 = e.touches[0];
            var touch2 = e.touches[1];

            this._startDistance = this._getDistance(touch1, touch2);
            this._startAngle = this._getAngle(touch1, touch2);
            this._currentDistance = this._startDistance;
            this._currentAngle = this._startAngle;
        }

        this._trigger('touchstart', {
            touches: e.touches,
            target: e.target
        });
    };

    TouchHandler.prototype._onTouchMove = function (e) {
        this._touchCount = e.touches.length;

        if (this._touchCount === 1) {
            var touch = e.touches[0];
            var prevX = this._currentX;
            var prevY = this._currentY;
            this._currentX = touch.clientX;
            this._currentY = touch.clientY;

            var deltaX = this._currentX - this._startX;
            var deltaY = this._currentY - this._startY;

            if (Math.abs(deltaX) > 10 || Math.abs(deltaY) > 10) {
                if (this._longPressTimer) {
                    clearTimeout(this._longPressTimer);
                    this._longPressTimer = null;
                }
                this._isScrolling = true;
            }

            this._trigger('touchmove', {
                x: this._currentX,
                y: this._currentY,
                deltaX: deltaX,
                deltaY: deltaY,
                velocityX: this._currentX - prevX,
                velocityY: this._currentY - prevY,
                target: e.target
            });
        } else if (this._touchCount === 2) {
            var touch1 = e.touches[0];
            var touch2 = e.touches[1];

            this._currentDistance = this._getDistance(touch1, touch2);
            this._currentAngle = this._getAngle(touch1, touch2);

            var scale = this._currentDistance / this._startDistance;
            var rotation = this._currentAngle - this._startAngle;

            this._trigger('pinch', {
                scale: scale,
                deltaScale: scale - this._initialScale,
                distance: this._currentDistance,
                startDistance: this._startDistance,
                target: e.target
            });

            this._trigger('rotate', {
                rotation: rotation,
                angle: this._currentAngle,
                startAngle: this._startAngle,
                target: e.target
            });

            if (Math.abs(scale - 1) > 0.01 || Math.abs(rotation) > 2) {
                e.preventDefault();
            }
        }

        this._trigger('touchmove', {
            touches: e.touches,
            target: e.target
        });
    };

    TouchHandler.prototype._onTouchEnd = function (e) {
        if (this._longPressTimer) {
            clearTimeout(this._longPressTimer);
            this._longPressTimer = null;
        }

        if (this._touchCount === 1 && !this._isLongPressTriggered) {
            var deltaX = this._currentX - this._startX;
            var deltaY = this._currentY - this._startY;
            var duration = Date.now() - this._startTime;

            var absDeltaX = Math.abs(deltaX);
            var absDeltaY = Math.abs(deltaY);

            if (Math.max(absDeltaX, absDeltaY) >= this._swipeThreshold) {
                var velocity = Math.max(absDeltaX, absDeltaY) / duration;

                if (velocity >= this._minSwipeVelocity || duration < 300) {
                    var direction;
                    if (absDeltaX > absDeltaY) {
                        direction = deltaX > 0 ? 'right' : 'left';
                    } else {
                        direction = deltaY > 0 ? 'down' : 'up';
                    }

                    this._trigger('swipe', {
                        direction: direction,
                        deltaX: deltaX,
                        deltaY: deltaY,
                        duration: duration,
                        velocity: velocity,
                        x: this._startX,
                        y: this._startY,
                        target: e.target
                    });

                    this._trigger('swipe' + direction.charAt(0).toUpperCase() + direction.slice(1), {
                        deltaX: deltaX,
                        deltaY: deltaY,
                        duration: duration,
                        velocity: velocity,
                        x: this._startX,
                        y: this._startY,
                        target: e.target
                    });
                }
            }
        }

        this._trigger('touchend', {
            touches: e.changedTouches,
            target: e.target
        });

        this._touchCount = 0;
        this._isScrolling = false;
    };

    TouchHandler.prototype._getDistance = function (touch1, touch2) {
        var dx = touch2.clientX - touch1.clientX;
        var dy = touch2.clientY - touch1.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    };

    TouchHandler.prototype._getAngle = function (touch1, touch2) {
        var dx = touch2.clientX - touch1.clientX;
        var dy = touch2.clientY - touch1.clientY;
        return Math.atan2(dy, dx) * (180 / Math.PI);
    };

    TouchHandler.prototype._trigger = function (eventName, data) {
        var listeners = this._listeners[eventName];
        if (!listeners) return;

        for (var i = 0; i < listeners.length; i++) {
            try {
                listeners[i](data);
            } catch (err) {
                console.error('[TouchHandler] 事件回调执行失败:', eventName, err);
            }
        }
    };

    TouchHandler.prototype.on = function (eventName, callback) {
        if (!this._listeners[eventName]) {
            this._listeners[eventName] = [];
        }
        this._listeners[eventName].push(callback);
        return this;
    };

    TouchHandler.prototype.off = function (eventName, callback) {
        var listeners = this._listeners[eventName];
        if (!listeners) return this;

        if (callback) {
            var index = listeners.indexOf(callback);
            if (index !== -1) {
                listeners.splice(index, 1);
            }
        } else {
            this._listeners[eventName] = [];
        }
        return this;
    };

    TouchHandler.prototype.onSwipe = function (callback) {
        return this.on('swipe', callback);
    };

    TouchHandler.prototype.onSwipeLeft = function (callback) {
        return this.on('swipeLeft', callback);
    };

    TouchHandler.prototype.onSwipeRight = function (callback) {
        return this.on('swipeRight', callback);
    };

    TouchHandler.prototype.onSwipeUp = function (callback) {
        return this.on('swipeUp', callback);
    };

    TouchHandler.prototype.onSwipeDown = function (callback) {
        return this.on('swipeDown', callback);
    };

    TouchHandler.prototype.onLongPress = function (callback) {
        return this.on('longpress', callback);
    };

    TouchHandler.prototype.onPinch = function (callback) {
        return this.on('pinch', callback);
    };

    TouchHandler.prototype.onRotate = function (callback) {
        return this.on('rotate', callback);
    };

    TouchHandler.prototype.onTouchStart = function (callback) {
        return this.on('touchstart', callback);
    };

    TouchHandler.prototype.onTouchMove = function (callback) {
        return this.on('touchmove', callback);
    };

    TouchHandler.prototype.onTouchEnd = function (callback) {
        return this.on('touchend', callback);
    };

    TouchHandler.prototype.setSwipeThreshold = function (threshold) {
        this._swipeThreshold = threshold;
        return this;
    };

    TouchHandler.prototype.setLongPressThreshold = function (threshold) {
        this._longPressThreshold = threshold;
        return this;
    };

    TouchHandler.prototype.destroy = function () {
        if (this._longPressTimer) {
            clearTimeout(this._longPressTimer);
        }
        this._listeners = {};
        this.element = null;
    };

    globalThis.TouchHandler = TouchHandler;

    // ========================================================================
    // PullToRefresh - 下拉刷新
    // ========================================================================

    function PullToRefresh(container, options) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        if (!this.container) return;

        this.options = Object.assign({
            threshold: 60,
            maxDistance: 100,
            resistance: 0.5,
            triggerText: '下拉刷新',
            releaseText: '释放刷新',
            loadingText: '正在刷新...',
            successText: '刷新成功',
            autoHide: true,
            hideDelay: 500
        }, options || {});

        this._startY = 0;
        this._currentY = 0;
        this._isPulling = false;
        this._isRefreshing = false;
        this._indicator = null;
        this._onRefresh = null;

        this._init();
    }

    PullToRefresh.prototype._init = function () {
        this._createIndicator();
        this._bindEvents();
    };

    PullToRefresh.prototype._createIndicator = function () {
        var indicator = document.createElement('div');
        indicator.className = 'pull-to-refresh-indicator';
        indicator.style.cssText = [
            'position: absolute',
            'top: 0',
            'left: 0',
            'right: 0',
            'height: 0',
            'overflow: hidden',
            'display: flex',
            'align-items: center',
            'justify-content: center',
            'font-size: 13px',
            'color: var(--fg-secondary, #86909C)',
            'transition: height 0.3s ease',
            'z-index: 100'
        ].join(';');

        var content = document.createElement('div');
        content.className = 'pull-to-refresh-content';
        content.style.cssText = [
            'display: flex',
            'align-items: center',
            'gap: 8px'
        ].join(';');

        var icon = document.createElement('div');
        icon.className = 'pull-to-refresh-icon';
        icon.innerHTML = '<iconify-icon icon="mdi:refresh" class="text-base"></iconify-icon>';
        icon.style.cssText = 'transition: transform 0.2s ease;';

        var text = document.createElement('span');
        text.className = 'pull-to-refresh-text';
        text.textContent = this.options.triggerText;

        content.appendChild(icon);
        content.appendChild(text);
        indicator.appendChild(content);

        if (this.container.style.position === 'static' || !this.container.style.position) {
            this.container.style.position = 'relative';
        }
        this.container.insertBefore(indicator, this.container.firstChild);

        this._indicator = indicator;
        this._indicatorIcon = icon;
        this._indicatorText = text;
    };

    PullToRefresh.prototype._bindEvents = function () {
        var self = this;

        this.container.addEventListener('touchstart', function (e) {
            self._onTouchStart(e);
        }, { passive: true });

        this.container.addEventListener('touchmove', function (e) {
            self._onTouchMove(e);
        }, { passive: false });

        this.container.addEventListener('touchend', function (e) {
            self._onTouchEnd(e);
        }, { passive: true });
    };

    PullToRefresh.prototype._onTouchStart = function (e) {
        if (this._isRefreshing) return;
        if (this.container.scrollTop > 0) return;

        var touch = e.touches[0];
        this._startY = touch.clientY;
        this._currentY = touch.clientY;
        this._isPulling = true;
    };

    PullToRefresh.prototype._onTouchMove = function (e) {
        if (!this._isPulling || this._isRefreshing) return;

        var touch = e.touches[0];
        this._currentY = touch.clientY;

        var delta = this._currentY - this._startY;
        if (delta <= 0) {
            this._resetPosition();
            return;
        }

        e.preventDefault();

        var distance = delta * this.options.resistance;
        if (distance > this.options.maxDistance) {
            distance = this.options.maxDistance;
        }

        this._indicator.style.height = distance + 'px';

        if (distance >= this.options.threshold) {
            this._indicatorText.textContent = this.options.releaseText;
            this._indicatorIcon.style.transform = 'rotate(180deg)';
        } else {
            this._indicatorText.textContent = this.options.triggerText;
            this._indicatorIcon.style.transform = 'rotate(0deg)';
        }
    };

    PullToRefresh.prototype._onTouchEnd = function () {
        if (!this._isPulling || this._isRefreshing) return;

        this._isPulling = false;
        var height = parseFloat(this._indicator.style.height) || 0;

        if (height >= this.options.threshold) {
            this._startRefresh();
        } else {
            this._resetPosition();
        }
    };

    PullToRefresh.prototype._startRefresh = function () {
        var self = this;
        this._isRefreshing = true;
        this._indicator.style.height = this.options.threshold + 'px';
        this._indicatorText.textContent = this.options.loadingText;
        this._indicatorIcon.style.transform = 'rotate(360deg)';
        this._indicatorIcon.style.transition = 'transform 1s linear';
        this._indicatorIcon.style.animation = 'spin 1s linear infinite';

        if (this._onRefresh) {
            this._onRefresh(function () {
                self._finishRefresh();
            });
        } else {
            setTimeout(function () {
                self._finishRefresh();
            }, 1000);
        }
    };

    PullToRefresh.prototype._finishRefresh = function () {
        var self = this;
        this._indicatorText.textContent = this.options.successText;

        if (this.options.autoHide) {
            setTimeout(function () {
                self._resetPosition();
                self._isRefreshing = false;
                self._indicatorIcon.style.animation = '';
                self._indicatorIcon.style.transition = 'transform 0.2s ease';
            }, this.options.hideDelay);
        } else {
            this._isRefreshing = false;
            this._indicatorIcon.style.animation = '';
            this._indicatorIcon.style.transition = 'transform 0.2s ease';
        }
    };

    PullToRefresh.prototype._resetPosition = function () {
        this._indicator.style.height = '0px';
        this._indicatorText.textContent = this.options.triggerText;
        this._indicatorIcon.style.transform = 'rotate(0deg)';
    };

    PullToRefresh.prototype.onRefresh = function (callback) {
        this._onRefresh = callback;
        return this;
    };

    PullToRefresh.prototype.destroy = function () {
        if (this._indicator && this._indicator.parentNode) {
            this._indicator.parentNode.removeChild(this._indicator);
        }
        this.container = null;
        this._indicator = null;
    };

    globalThis.PullToRefresh = PullToRefresh;

    // ========================================================================
    // InfiniteScroll - 上滑加载更多
    // ========================================================================

    function InfiniteScroll(container, options) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        if (!this.container) return;

        this.options = Object.assign({
            threshold: 100,
            loadingText: '加载中...',
            noMoreText: '没有更多了',
            errorText: '加载失败，点击重试',
            autoLoad: true
        }, options || {});

        this._isLoading = false;
        this._hasMore = true;
        this._isError = false;
        this._loader = null;
        this._onLoadMore = null;

        this._init();
    }

    InfiniteScroll.prototype._init = function () {
        this._createLoader();
        this._bindEvents();
    };

    InfiniteScroll.prototype._createLoader = function () {
        var loader = document.createElement('div');
        loader.className = 'infinite-scroll-loader';
        loader.style.cssText = [
            'padding: 20px',
            'text-align: center',
            'font-size: 13px',
            'color: var(--fg-secondary, #86909C)',
            'display: none'
        ].join(';');

        var content = document.createElement('div');
        content.className = 'infinite-scroll-content';
        content.style.cssText = 'display: flex; align-items: center; justify-content: center; gap: 8px;';

        var icon = document.createElement('div');
        icon.className = 'infinite-scroll-icon';
        icon.innerHTML = '<iconify-icon icon="mdi:loading" class="text-base" style="animation: spin 1s linear infinite;"></iconify-icon>';

        var text = document.createElement('span');
        text.className = 'infinite-scroll-text';

        content.appendChild(icon);
        content.appendChild(text);
        loader.appendChild(content);

        this.container.parentNode.insertBefore(loader, this.container.nextSibling);

        this._loader = loader;
        this._loaderIcon = icon;
        this._loaderText = text;
    };

    InfiniteScroll.prototype._bindEvents = function () {
        var self = this;

        this.container.addEventListener('scroll', function () {
            self._checkScroll();
        });

        if (this.options.autoLoad) {
            setTimeout(function () {
                self._checkScroll();
            }, 100);
        }
    };

    InfiniteScroll.prototype._checkScroll = function () {
        if (this._isLoading || !this._hasMore) return;

        var scrollTop = this.container.scrollTop;
        var scrollHeight = this.container.scrollHeight;
        var clientHeight = this.container.clientHeight;

        if (scrollTop + clientHeight >= scrollHeight - this.options.threshold) {
            this._loadMore();
        }
    };

    InfiniteScroll.prototype._loadMore = function () {
        if (this._isLoading) return;

        this._isLoading = true;
        this._isError = false;
        this._showLoader(this.options.loadingText, true);

        var self = this;
        if (this._onLoadMore) {
            this._onLoadMore(function (hasMore, error) {
                self._isLoading = false;
                if (error) {
                    self._isError = true;
                    self._showLoader(self.options.errorText, false);
                } else {
                    self._hasMore = hasMore;
                    if (!hasMore) {
                        self._showLoader(self.options.noMoreText, false);
                    } else {
                        self._hideLoader();
                    }
                }
            });
        } else {
            setTimeout(function () {
                self._isLoading = false;
                self._hasMore = false;
                self._showLoader(self.options.noMoreText, false);
            }, 1000);
        }
    };

    InfiniteScroll.prototype._showLoader = function (text, showIcon) {
        this._loader.style.display = 'block';
        this._loaderText.textContent = text;
        this._loaderIcon.style.display = showIcon ? 'block' : 'none';
    };

    InfiniteScroll.prototype._hideLoader = function () {
        this._loader.style.display = 'none';
    };

    InfiniteScroll.prototype.onLoadMore = function (callback) {
        this._onLoadMore = callback;
        return this;
    };

    InfiniteScroll.prototype.reset = function () {
        this._hasMore = true;
        this._isLoading = false;
        this._isError = false;
        this._hideLoader();
    };

    InfiniteScroll.prototype.setHasMore = function (hasMore) {
        this._hasMore = hasMore;
        if (!hasMore) {
            this._showLoader(this.options.noMoreText, false);
        }
    };

    InfiniteScroll.prototype.retry = function () {
        if (this._isError) {
            this._loadMore();
        }
    };

    InfiniteScroll.prototype.destroy = function () {
        if (this._loader && this._loader.parentNode) {
            this._loader.parentNode.removeChild(this._loader);
        }
        this.container = null;
        this._loader = null;
    };

    globalThis.InfiniteScroll = InfiniteScroll;

    // ========================================================================
    // SideMenu - 侧滑菜单
    // ========================================================================

    function SideMenu(menu, options) {
        this.menu = typeof menu === 'string' ? document.querySelector(menu) : menu;
        if (!this.menu) return;

        this.options = Object.assign({
            side: 'left',
            width: 280,
            threshold: 50,
            duration: 300,
            overlay: true,
            swipeArea: 30,
            closeOnOverlayClick: true
        }, options || {});

        this._isOpen = false;
        this._isAnimating = false;
        this._startX = 0;
        this._startY = 0;
        this._currentX = 0;
        this._isDragging = false;
        this._overlay = null;

        this._init();
    }

    SideMenu.prototype._init = function () {
        this._setupMenu();
        if (this.options.overlay) {
            this._createOverlay();
        }
        this._bindEvents();
    };

    SideMenu.prototype._setupMenu = function () {
        var side = this.options.side;
        this.menu.style.position = 'fixed';
        this.menu.style.top = '0';
        this.menu.style.bottom = '0';
        this.menu.style.width = this.options.width + 'px';
        this.menu.style.zIndex = '1000';
        this.menu.style.transition = 'transform ' + this.options.duration + 'ms ease';
        this.menu.style.transform = side === 'left' ?
            'translateX(-100%)' : 'translateX(100%)';

        if (side === 'left') {
            this.menu.style.left = '0';
        } else {
            this.menu.style.right = '0';
        }
    };

    SideMenu.prototype._createOverlay = function () {
        var overlay = document.createElement('div');
        overlay.className = 'side-menu-overlay';
        overlay.style.cssText = [
            'position: fixed',
            'top: 0',
            'left: 0',
            'right: 0',
            'bottom: 0',
            'background: rgba(0, 0, 0, 0.5)',
            'opacity: 0',
            'visibility: hidden',
            'transition: opacity ' + this.options.duration + 'ms ease, visibility ' + this.options.duration + 'ms ease',
            'z-index: 999'
        ].join(';');

        document.body.appendChild(overlay);
        this._overlay = overlay;

        if (this.options.closeOnOverlayClick) {
            var self = this;
            overlay.addEventListener('click', function () {
                self.close();
            });
        }
    };

    SideMenu.prototype._bindEvents = function () {
        var self = this;

        document.addEventListener('touchstart', function (e) {
            self._onTouchStart(e);
        }, { passive: true });

        document.addEventListener('touchmove', function (e) {
            self._onTouchMove(e);
        }, { passive: false });

        document.addEventListener('touchend', function (e) {
            self._onTouchEnd(e);
        }, { passive: true });
    };

    SideMenu.prototype._onTouchStart = function (e) {
        if (this._isAnimating) return;

        var touch = e.touches[0];
        this._startX = touch.clientX;
        this._startY = touch.clientY;
        this._currentX = touch.clientX;
        this._isDragging = false;

        if (!this._isOpen) {
            if (this.options.side === 'left' && touch.clientX > this.options.swipeArea) {
                return;
            }
            if (this.options.side === 'right' && touch.clientX < window.innerWidth - this.options.swipeArea) {
                return;
            }
        }
    };

    SideMenu.prototype._onTouchMove = function (e) {
        if (this._isAnimating) return;

        var touch = e.touches[0];
        this._currentX = touch.clientX;

        var deltaX = this._currentX - this._startX;
        var deltaY = Math.abs(touch.clientY - this._startY);

        if (!this._isDragging && Math.abs(deltaX) > 10 && Math.abs(deltaX) > deltaY) {
            this._isDragging = true;
            this.menu.style.transition = 'none';
            if (this._overlay) {
                this._overlay.style.transition = 'none';
            }
        }

        if (!this._isDragging) return;

        e.preventDefault();

        var width = this.options.width;
        var currentTranslate;

        if (this.options.side === 'left') {
            if (this._isOpen) {
                currentTranslate = Math.min(0, Math.max(-width, deltaX));
            } else {
                currentTranslate = Math.min(0, Math.max(-width, deltaX - width));
            }
            this.menu.style.transform = 'translateX(' + currentTranslate + 'px)';

            var progress = (width + currentTranslate) / width;
            if (this._overlay) {
                this._overlay.style.opacity = progress * 0.5;
                this._overlay.style.visibility = progress > 0 ? 'visible' : 'hidden';
            }
        } else {
            if (this._isOpen) {
                currentTranslate = Math.max(0, Math.min(width, deltaX));
            } else {
                currentTranslate = Math.max(0, Math.min(width, deltaX + width));
            }
            this.menu.style.transform = 'translateX(' + currentTranslate + 'px)';

            var progress = (width - currentTranslate) / width;
            if (this._overlay) {
                this._overlay.style.opacity = (1 - progress) * 0.5;
                this._overlay.style.visibility = progress < 1 ? 'visible' : 'hidden';
            }
        }
    };

    SideMenu.prototype._onTouchEnd = function () {
        if (!this._isDragging) return;

        this._isDragging = false;
        this.menu.style.transition = 'transform ' + this.options.duration + 'ms ease';
        if (this._overlay) {
            this._overlay.style.transition = 'opacity ' + this.options.duration + 'ms ease, visibility ' + this.options.duration + 'ms ease';
        }

        var deltaX = this._currentX - this._startX;

        if (this._isOpen) {
            if (Math.abs(deltaX) > this.options.threshold) {
                this.close();
            } else {
                this.open();
            }
        } else {
            if (Math.abs(deltaX) > this.options.threshold) {
                this.open();
            } else {
                this.close();
            }
        }
    };

    SideMenu.prototype.open = function () {
        var self = this;
        if (this._isOpen || this._isAnimating) return;

        this._isAnimating = true;
        this._isOpen = true;

        this.menu.style.transform = this.options.side === 'left' ?
            'translateX(0)' : 'translateX(0)';

        if (this._overlay) {
            this._overlay.style.opacity = '0.5';
            this._overlay.style.visibility = 'visible';
        }

        setTimeout(function () {
            self._isAnimating = false;
        }, this.options.duration);
    };

    SideMenu.prototype.close = function () {
        var self = this;
        if (!this._isOpen || this._isAnimating) return;

        this._isAnimating = true;
        this._isOpen = false;

        this.menu.style.transform = this.options.side === 'left' ?
            'translateX(-100%)' : 'translateX(100%)';

        if (this._overlay) {
            this._overlay.style.opacity = '0';
            this._overlay.style.visibility = 'hidden';
        }

        setTimeout(function () {
            self._isAnimating = false;
        }, this.options.duration);
    };

    SideMenu.prototype.toggle = function () {
        if (this._isOpen) {
            this.close();
        } else {
            this.open();
        }
    };

    SideMenu.prototype.destroy = function () {
        if (this._overlay && this._overlay.parentNode) {
            this._overlay.parentNode.removeChild(this._overlay);
        }
        this.menu = null;
        this._overlay = null;
    };

    globalThis.SideMenu = SideMenu;

    // ========================================================================
    // BottomNavigation - 底部导航栏
    // ========================================================================

    function BottomNavigation(container, options) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = Object.assign({
            items: [],
            activeIndex: 0,
            safeArea: true
        }, options || {});

        this._activeIndex = this.options.activeIndex;
        this._nav = null;
        this._onChange = null;

        this._init();
    }

    BottomNavigation.prototype._init = function () {
        this._createNav();
    };

    BottomNavigation.prototype._createNav = function () {
        var nav = document.createElement('div');
        nav.className = 'mobile-bottom-nav';
        nav.style.cssText = [
            'position: fixed',
            'bottom: 0',
            'left: 0',
            'right: 0',
            'height: 56px',
            'background: var(--bg-white, #FFFFFF)',
            'border-top: 1px solid var(--bg-border, #E5E6EB)',
            'display: flex',
            'align-items: center',
            'justify-content: space-around',
            'z-index: 100',
            'padding-bottom: ' + (this.options.safeArea ? 'env(safe-area-inset-bottom, 0)' : '0')
        ].join(';');

        for (var i = 0; i < this.options.items.length; i++) {
            var item = this.options.items[i];
            var btn = this._createItem(item, i);
            nav.appendChild(btn);
        }

        if (this.container) {
            this.container.style.paddingBottom = (56 + (this.options.safeArea ? 20 : 0)) + 'px';
        }

        document.body.appendChild(nav);
        this._nav = nav;
    };

    BottomNavigation.prototype._createItem = function (item, index) {
        var self = this;
        var btn = document.createElement('button');
        btn.className = 'bottom-nav-item' + (index === this._activeIndex ? ' active' : '');
        btn.dataset.index = index;
        btn.style.cssText = [
            'flex: 1',
            'display: flex',
            'flex-direction: column',
            'align-items: center',
            'justify-content: center',
            'gap: 2px',
            'height: 100%',
            'background: none',
            'border: none',
            'cursor: pointer',
            'color: ' + (index === this._activeIndex ? 'var(--brand, #165DFF)' : 'var(--fg-tertiary, #C9CDD4)'),
            'transition: color 0.2s ease',
            'padding: 4px'
        ].join(';');

        var icon = document.createElement('div');
        icon.className = 'bottom-nav-icon';
        icon.innerHTML = '<iconify-icon icon="' + item.icon + '" class="text-xl"></iconify-icon>';

        var label = document.createElement('span');
        label.className = 'bottom-nav-label';
        label.textContent = item.label;
        label.style.fontSize = '10px';
        label.style.fontWeight = index === this._activeIndex ? '600' : '500';

        btn.appendChild(icon);
        btn.appendChild(label);

        btn.addEventListener('click', function () {
            self._setActive(index);
        });

        return btn;
    };

    BottomNavigation.prototype._setActive = function (index) {
        if (index === this._activeIndex) return;

        var items = this._nav.querySelectorAll('.bottom-nav-item');
        for (var i = 0; i < items.length; i++) {
            var isActive = i === index;
            items[i].classList.toggle('active', isActive);
            items[i].style.color = isActive ?
                'var(--brand, #165DFF)' : 'var(--fg-tertiary, #C9CDD4)';
            var label = items[i].querySelector('.bottom-nav-label');
            if (label) {
                label.style.fontWeight = isActive ? '600' : '500';
            }
        }

        this._activeIndex = index;

        if (this._onChange) {
            this._onChange(index, this.options.items[index]);
        }
    };

    BottomNavigation.prototype.onChange = function (callback) {
        this._onChange = callback;
        return this;
    };

    BottomNavigation.prototype.setActive = function (index) {
        this._setActive(index);
    };

    BottomNavigation.prototype.show = function () {
        this._nav.style.transform = 'translateY(0)';
    };

    BottomNavigation.prototype.hide = function () {
        this._nav.style.transform = 'translateY(100%)';
    };

    BottomNavigation.prototype.destroy = function () {
        if (this._nav && this._nav.parentNode) {
            this._nav.parentNode.removeChild(this._nav);
        }
        this._nav = null;
    };

    globalThis.BottomNavigation = BottomNavigation;

    // ========================================================================
    // SwipeBack - 左滑返回手势
    // ========================================================================

    function SwipeBack(options) {
        this.options = Object.assign({
            threshold: 100,
            edgeWidth: 30,
            duration: 300,
            resistance: 0.3
        }, options || {});

        this._startX = 0;
        this._startY = 0;
        this._currentX = 0;
        this._isSwiping = false;
        this._onBack = null;

        this._init();
    }

    SwipeBack.prototype._init = function () {
        var self = this;

        document.addEventListener('touchstart', function (e) {
            self._onTouchStart(e);
        }, { passive: true });

        document.addEventListener('touchmove', function (e) {
            self._onTouchMove(e);
        }, { passive: false });

        document.addEventListener('touchend', function (e) {
            self._onTouchEnd(e);
        }, { passive: true });
    };

    SwipeBack.prototype._onTouchStart = function (e) {
        var touch = e.touches[0];

        if (touch.clientX > this.options.edgeWidth) {
            return;
        }

        this._startX = touch.clientX;
        this._startY = touch.clientY;
        this._currentX = touch.clientX;
        this._isSwiping = false;
    };

    SwipeBack.prototype._onTouchMove = function (e) {
        var touch = e.touches[0];
        this._currentX = touch.clientX;

        var deltaX = this._currentX - this._startX;
        var deltaY = Math.abs(touch.clientY - this._startY);

        if (!this._isSwiping && deltaX > 10 && deltaX > deltaY) {
            this._isSwiping = true;
        }

        if (!this._isSwiping) return;

        e.preventDefault();
    };

    SwipeBack.prototype._onTouchEnd = function () {
        if (!this._isSwiping) return;

        this._isSwiping = false;

        var deltaX = this._currentX - this._startX;

        if (deltaX >= this.options.threshold) {
            if (this._onBack) {
                this._onBack();
            } else {
                if (window.history.length > 1) {
                    window.history.back();
                }
            }
        }
    };

    SwipeBack.prototype.onBack = function (callback) {
        this._onBack = callback;
        return this;
    };

    SwipeBack.prototype.destroy = function () {
        this._onBack = null;
    };

    globalThis.SwipeBack = SwipeBack;

    // ========================================================================
    // MobileTouch - 移动端触摸增强统一入口
    // ========================================================================

    var MobileTouch = {
        createPullToRefresh: function (container, options) {
            return new PullToRefresh(container, options);
        },
        createInfiniteScroll: function (container, options) {
            return new InfiniteScroll(container, options);
        },
        createSideMenu: function (menu, options) {
            return new SideMenu(menu, options);
        },
        createBottomNav: function (container, options) {
            return new BottomNavigation(container, options);
        },
        createSwipeBack: function (options) {
            return new SwipeBack(options);
        },
        createHandler: function (element) {
            return new TouchHandler(element);
        },
        isMobile: function () {
            return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        },
        isTouchDevice: function () {
            return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        }
    };

    globalThis.MobileTouch = MobileTouch;
})();
