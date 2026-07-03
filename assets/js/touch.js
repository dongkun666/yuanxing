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
        this.element.addEventListener('touchstart', function (e) { self._onTouchStart(e); }, { passive: true });
        this.element.addEventListener('touchmove', function (e) { self._onTouchMove(e); }, { passive: false });
        this.element.addEventListener('touchend', function (e) { self._onTouchEnd(e); }, { passive: true });
        this.element.addEventListener('touchcancel', function (e) { self._onTouchEnd(e); }, { passive: true });
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

            this._longPressTimer = setTimeout(function () {
                if (!self._isScrolling && !self._isLongPressTriggered) {
                    self._isLongPressTriggered = true;
                    self._trigger('longpress', {
                        x: self._startX,
                        y: self._startY,
                        target: e.target
                    });
                }
            }.bind(this), this._longPressThreshold);
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
                velocityX: (this._currentX - prevX),
                velocityY: (this._currentY - prevY),
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
        var self = this;

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
})();