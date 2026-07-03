(function () {
    'use strict';

    // ===== 会员中心页面导航切换 =====
    function switchMemberSection(sectionName, navBtn) {
        var sections = document.querySelectorAll('.member-section');
        sections.forEach(function (section) {
            section.classList.add('hidden');
        });

        var targetSection = document.getElementById('section-' + sectionName);
        if (targetSection) {
            targetSection.classList.remove('hidden');
            targetSection.style.animation = 'none';
            targetSection.offsetHeight;
            targetSection.style.animation = '';
        }

        var navItems = document.querySelectorAll('.member-nav-item');
        navItems.forEach(function (item) {
            item.classList.remove(
                'bg-gradient-to-r',
                'from-brand',
                'to-brand-hover',
                'text-white',
                'shadow-md',
                'shadow-brand/20'
            );
            item.classList.add('text-fg-secondary', 'hover:bg-bg-subtle', 'hover:text-fg-primary', 'group');
            var icon = item.querySelector('iconify-icon');
            if (icon) {
                icon.classList.remove('text-white');
                icon.classList.add('group-hover:text-brand', 'transition-colors');
            }
        });

        if (navBtn) {
            navBtn.classList.remove('text-fg-secondary', 'hover:bg-bg-subtle', 'hover:text-fg-primary', 'group');
            navBtn.classList.add(
                'bg-gradient-to-r',
                'from-brand',
                'to-brand-hover',
                'text-white',
                'shadow-md',
                'shadow-brand/20'
            );
            var activeIcon = navBtn.querySelector('iconify-icon');
            if (activeIcon) {
                activeIcon.classList.remove('group-hover:text-brand', 'transition-colors');
                activeIcon.classList.add('text-white');
            }
        }

        if (typeof Animations !== 'undefined' && typeof Animations.initPageAnimations === 'function') {
            if (targetSection) {
                Animations.initPageAnimations(targetSection);
            }
        }
    }

    // ===== 自动续费切换 =====
    function toggleAutoRenewal(toggle) {
        if (toggle.checked) {
            if (typeof showToast === 'function') {
                showToast('自动续费已开启');
            }
        } else {
            if (typeof showToast === 'function') {
                showToast('自动续费已关闭');
            }
        }
    }

    // ===== 会员中心页面初始化 =====
    function initMemberCenter() {
        var view = document.getElementById('view-member-center');
        if (!view || view.classList.contains('initialized')) return;

        view.classList.add('initialized');

        if (typeof Animations !== 'undefined' && typeof Animations.initPageAnimations === 'function') {
            Animations.initPageAnimations(view);
        }
    }

    globalThis.switchMemberSection = switchMemberSection;
    globalThis.toggleAutoRenewal = toggleAutoRenewal;
    globalThis.initMemberCenter = initMemberCenter;
})();
