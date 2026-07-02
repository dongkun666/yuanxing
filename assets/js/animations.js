/**
 * Animations 模块 - GSAP 动画工具函数
 * 提供页面入场动画、滚动触发动画等通用动画能力
 *
 * 加载顺序: 在 utils.js 之后, 业务模块之前
 * 依赖: gsap (GSAP 核心库), ScrollTrigger (GSAP 插件)
 *
 * 暴露: Animations.fadeInUp, Animations.staggerFadeIn, Animations.scaleIn,
 *       Animations.slideInLeft, Animations.slideInRight, Animations.initPageAnimations
 */

(function () {
    'use strict';

    var gsapAvailable = typeof gsap !== 'undefined';

    if (gsapAvailable && typeof ScrollTrigger !== 'undefined') {
        gsap.registerPlugin(ScrollTrigger);
    }

    var defaultEase = 'power2.out';
    var defaultDuration = 0.6;
    var defaultStagger = 0.08;

    function getOptions(options) {
        options = options || {};
        return {
            duration: options.duration || defaultDuration,
            delay: options.delay || 0,
            ease: options.ease || defaultEase,
            stagger: options.stagger !== undefined ? options.stagger : defaultStagger,
            y: options.y !== undefined ? options.y : 20,
            x: options.x !== undefined ? options.x : 30,
            scale: options.scale !== undefined ? options.scale : 0.95,
            onComplete: options.onComplete || null
        };
    }

    function fadeInUp(selector, options) {
        if (!gsapAvailable) return;
        var opts = getOptions(options);
        var elements = document.querySelectorAll(selector);
        if (!elements.length) return;

        gsap.fromTo(elements,
            {
                opacity: 0,
                y: opts.y
            },
            {
                opacity: 1,
                y: 0,
                duration: opts.duration,
                delay: opts.delay,
                ease: opts.ease,
                onComplete: opts.onComplete
            }
        );
    }

    function staggerFadeIn(selector, options) {
        if (!gsapAvailable) return;
        var opts = getOptions(options);
        var elements = document.querySelectorAll(selector);
        if (!elements.length) return;

        gsap.fromTo(elements,
            {
                opacity: 0,
                y: opts.y
            },
            {
                opacity: 1,
                y: 0,
                duration: opts.duration,
                delay: opts.delay,
                ease: opts.ease,
                stagger: opts.stagger,
                onComplete: opts.onComplete
            }
        );
    }

    function scaleIn(selector, options) {
        if (!gsapAvailable) return;
        var opts = getOptions(options);
        var elements = document.querySelectorAll(selector);
        if (!elements.length) return;

        gsap.fromTo(elements,
            {
                opacity: 0,
                scale: opts.scale
            },
            {
                opacity: 1,
                scale: 1,
                duration: opts.duration,
                delay: opts.delay,
                ease: 'power3.out',
                onComplete: opts.onComplete
            }
        );
    }

    function slideInLeft(selector, options) {
        if (!gsapAvailable) return;
        var opts = getOptions(options);
        var elements = document.querySelectorAll(selector);
        if (!elements.length) return;

        gsap.fromTo(elements,
            {
                opacity: 0,
                x: -opts.x
            },
            {
                opacity: 1,
                x: 0,
                duration: opts.duration,
                delay: opts.delay,
                ease: opts.ease,
                onComplete: opts.onComplete
            }
        );
    }

    function slideInRight(selector, options) {
        if (!gsapAvailable) return;
        var opts = getOptions(options);
        var elements = document.querySelectorAll(selector);
        if (!elements.length) return;

        gsap.fromTo(elements,
            {
                opacity: 0,
                x: opts.x
            },
            {
                opacity: 1,
                x: 0,
                duration: opts.duration,
                delay: opts.delay,
                ease: opts.ease,
                onComplete: opts.onComplete
            }
        );
    }

    function initPageAnimations(scope) {
        if (!gsapAvailable) return;

        var root = scope || document;
        var animatedElements = root.querySelectorAll('[data-animate]');

        if (!animatedElements.length) return;

        var animationMap = {
            'fade-in-up': function (el, opts) {
                gsap.fromTo(el,
                    { opacity: 0, y: opts.y },
                    {
                        opacity: 1,
                        y: 0,
                        duration: opts.duration,
                        delay: opts.delay,
                        ease: opts.ease
                    }
                );
            },
            'scale-in': function (el, opts) {
                gsap.fromTo(el,
                    { opacity: 0, scale: opts.scale },
                    {
                        opacity: 1,
                        scale: 1,
                        duration: opts.duration,
                        delay: opts.delay,
                        ease: 'power3.out'
                    }
                );
            },
            'slide-in-left': function (el, opts) {
                gsap.fromTo(el,
                    { opacity: 0, x: -opts.x },
                    {
                        opacity: 1,
                        x: 0,
                        duration: opts.duration,
                        delay: opts.delay,
                        ease: opts.ease
                    }
                );
            },
            'slide-in-right': function (el, opts) {
                gsap.fromTo(el,
                    { opacity: 0, x: opts.x },
                    {
                        opacity: 1,
                        x: 0,
                        duration: opts.duration,
                        delay: opts.delay,
                        ease: opts.ease
                    }
                );
            }
        };

        var staggerGroups = {};

        animatedElements.forEach(function (el) {
            var type = el.getAttribute('data-animate');
            var delay = parseFloat(el.getAttribute('data-delay')) || 0;
            var duration = parseFloat(el.getAttribute('data-duration')) || defaultDuration;
            var staggerGroup = el.getAttribute('data-stagger-group');
            var staggerIndex = parseInt(el.getAttribute('data-stagger-index'));
            var staggerAmount = parseFloat(el.getAttribute('data-stagger-amount')) || defaultStagger;

            var opts = {
                delay: delay,
                duration: duration,
                y: 20,
                x: 30,
                scale: 0.95,
                ease: defaultEase
            };

            if (staggerGroup && !isNaN(staggerIndex)) {
                if (!staggerGroups[staggerGroup]) {
                    staggerGroups[staggerGroup] = [];
                }
                staggerGroups[staggerGroup].push({
                    el: el,
                    type: type,
                    index: staggerIndex,
                    opts: opts,
                    staggerAmount: staggerAmount
                });
            } else {
                var animFn = animationMap[type];
                if (animFn) {
                    animFn(el, opts);
                }
            }
        });

        Object.keys(staggerGroups).forEach(function (groupName) {
            var group = staggerGroups[groupName];
            group.sort(function (a, b) {
                return a.index - b.index;
            });

            group.forEach(function (item, idx) {
                var animFn = animationMap[item.type];
                if (animFn) {
                    var opts = Object.assign({}, item.opts, {
                        delay: item.opts.delay + idx * item.staggerAmount
                    });
                    animFn(item.el, opts);
                }
            });
        });
    }

    globalThis.Animations = {
        fadeInUp: fadeInUp,
        staggerFadeIn: staggerFadeIn,
        scaleIn: scaleIn,
        slideInLeft: slideInLeft,
        slideInRight: slideInRight,
        initPageAnimations: initPageAnimations,
        isAvailable: function () {
            return gsapAvailable;
        }
    };
})();
