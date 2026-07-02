/**
 * 账号 - 个人资料/认证/设备/账号模块
 * 拆分自 account.js (2026-06-28 IIFE 拆分计划)
 *
 * 包含: 个人资料编辑/保存 + 头像上传 + 专业领域标签 + 证件认证 + 2FA + 设备管理 + 账号注销 + 第三方账号绑定
 * 依赖: AppState (app-state.js), showSaveSuccess (本文件内)
 *
 * 加载顺序: 在 account-notifications.js / account-subscription.js 之后 (无外部依赖)
 */

(function () {
    'use strict';

    // ===== 个人资料编辑 =====
    function toggleProfileEdit() {
        var display = document.getElementById('profile-display');
        var edit = document.getElementById('profile-edit');
        var btn = document.getElementById('edit-profile-btn');

        if (display && edit && btn) {
            var isEditing = !edit.classList.contains('hidden');
            if (isEditing) {
                cancelProfileEdit();
            } else {
                display.classList.add('hidden');
                edit.classList.remove('hidden');
                btn.classList.add('hidden');
            }
        }
    }

    function cancelProfileEdit() {
        var display = document.getElementById('profile-display');
        var edit = document.getElementById('profile-edit');
        var btn = document.getElementById('edit-profile-btn');
        if (display && edit && btn) {
            edit.classList.add('hidden');
            display.classList.remove('hidden');
            btn.classList.remove('hidden');
            btn.innerHTML = '<iconify-icon icon="mdi:pencil-outline" class="text-sm"></iconify-icon><span>修改</span>';
            btn.className =
                'px-4 py-2 text-xs font-semibold rounded-xl border border-brand text-brand hover:bg-brand-tint transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md hover:shadow-brand/10 flex items-center gap-1.5';
        }
    }

    async function saveProfile() {
        var name = document.getElementById('profile-name');
        var phone = document.getElementById('profile-phone');
        var email = document.getElementById('profile-email');
        var firm = document.getElementById('profile-firm');
        var license = document.getElementById('profile-license');
        var bio = document.getElementById('profile-bio');

        if (!name || !name.value.trim()) {
            Utils.showToast('warning', '请输入姓名');
            if (name) name.focus();
            return;
        }
        if (!phone || !phone.value.trim()) {
            Utils.showToast('warning', '请输入手机号');
            if (phone) phone.focus();
            return;
        }

        var phoneVal = phone.value.trim();
        if (!/^1\d{10}$/.test(phoneVal) && !/^\d{3,4}\*{4}\d{4}$/.test(phoneVal)) {
            var phoneConfirm = await Utils.showConfirm('手机号格式异常，是否仍要保存？');
            if (!phoneConfirm) return;
        }

        var emailVal = email ? email.value.trim() : '';
        if (emailVal && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailVal)) {
            var emailConfirm = await Utils.showConfirm('邮箱格式不正确，是否仍要保存？');
            if (!emailConfirm) return;
        }

        var displayGrid = document.querySelector('#profile-display .grid.grid-cols-2');
        if (displayGrid) {
            var displayItems = displayGrid.querySelectorAll('div');
            if (displayItems.length >= 6) {
                var nameP = displayItems[0].querySelector('p.text-sm');
                if (nameP) nameP.textContent = name.value.trim();

                var phoneP = displayItems[1].querySelector('p.text-sm');
                if (phoneP) phoneP.textContent = phone.value.trim();

                var emailP = displayItems[2].querySelector('p.text-sm');
                if (emailP) emailP.textContent = email.value.trim() || '未设置';

                var firmP = displayItems[3].querySelector('p.text-sm');
                if (firmP) firmP.textContent = firm.value.trim() || '未设置';

                var licenseP = displayItems[4].querySelector('p.text-sm');
                if (licenseP) licenseP.textContent = license.value.trim() || '未设置';

                var editTags = document.querySelectorAll('#edit-skill-tags .inline-flex');
                var displayTagsContainer = displayItems[5].querySelector('.flex.flex-wrap');
                if (displayTagsContainer && editTags.length > 0) {
                    displayTagsContainer.innerHTML = '';
                    editTags.forEach(function (tag) {
                        var tagText = tag.textContent.replace('×', '').replace('+ 添加', '').trim();
                        if (tagText) {
                            var span = document.createElement('span');
                            span.className =
                                'inline-flex px-2 py-0.5 rounded-full bg-gradient-to-r from-brand-tint to-brand-tint2 text-brand text-[10px] font-medium';
                            span.textContent = tagText;
                            displayTagsContainer.appendChild(span);
                        }
                    });
                }
            }
        }

        var displayBio = document.querySelector('#profile-display .border-t p.text-sm');
        if (displayBio && bio) {
            displayBio.textContent = bio.value.trim() || '未填写';
        }

        var profileContainer = document.querySelector('#profile-display')?.closest('.flex');
        if (profileContainer) {
            var nameUnderAvatar = profileContainer.querySelector('.flex-shrink-0 p.text-xs');
            if (nameUnderAvatar) nameUnderAvatar.textContent = name.value.trim();
        }

        showSaveSuccess('个人资料已保存成功');
        cancelProfileEdit();
    }

    function showSaveSuccess(msg) {
        var existing = document.getElementById('save-toast');
        if (existing) existing.remove();

        var toast = document.createElement('div');
        toast.id = 'save-toast';
        toast.className =
            'fixed top-4 right-4 z-[999] bg-green-50 border border-green-200 text-green-700 text-sm px-5 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-slide-in';
        toast.innerHTML =
            '<iconify-icon icon="mdi:check-circle" class="text-green-600 text-lg"></iconify-icon><span>' +
            msg +
            '</span><button onclick="this.parentElement.remove()" class="ml-2 text-green-400 hover:text-green-600" aria-label="关闭提示"><iconify-icon icon="mdi:close" class="text-sm"></iconify-icon></button>';
        document.body.appendChild(toast);

        setTimeout(function () {
            if (toast.parentElement) {
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.3s';
                setTimeout(function () {
                    if (toast.parentElement) toast.remove();
                }, 300);
            }
        }, 3000);
    }

    // ===== 头像/标签/认证 =====
    async function addTagInput(el) {
        var tag = await Utils.showPrompt('请输入专业领域名称：', '');
        if (tag && tag.trim()) {
            var span = document.createElement('span');
            span.className =
                'inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-gradient-to-r from-brand-tint to-brand-tint2 text-brand text-[10px] font-medium';
            span.innerHTML =
                tag.trim() +
                ' <button onclick="removeTag(this); autoSaveProfile()" class="hover:text-danger transition-colors" aria-label="移除标签"><iconify-icon icon="mdi:close" class="text-xs"></iconify-icon></button>';
            el.parentNode.insertBefore(span, el);
        }
    }

    function handleAvatarUpload(event) {
        var file = event.target.files[0];
        if (!file) return;

        if (file.size > 5 * 1024 * 1024) {
            showSaveSuccess('头像文件大小不能超过 5MB');
            return;
        }

        var allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            showSaveSuccess('仅支持 JPG、PNG、WebP 格式的图片');
            return;
        }

        var progress = document.getElementById('avatar-progress-display');
        var success = document.getElementById('avatar-success-display');
        if (progress) progress.classList.remove('hidden');
        if (success) success.classList.add('hidden');

        setTimeout(function () {
            var reader = new FileReader();
            reader.onload = function (e) {
                var img = document.getElementById('avatar-image-display');
                var icon = document.getElementById('avatar-icon-display');
                var preview = document.getElementById('avatar-preview-display');

                if (img && icon && preview) {
                    img.src = e.target.result;
                    img.classList.remove('hidden');
                    icon.style.display = 'none';
                    preview.style.backgroundImage = 'none';
                }

                if (progress) progress.classList.add('hidden');
                if (success) success.classList.remove('hidden');

                showSaveSuccess('头像上传成功');

                setTimeout(function () {
                    if (success) success.classList.add('hidden');
                }, 3000);
            };
            reader.readAsDataURL(file);
        }, 800);
    }

    function removeTag(btn) {
        var tag = btn.closest('span');
        if (tag) {
            tag.remove();
        }
    }

    async function showAddTagDialog(el) {
        var tag = await Utils.showPrompt('请输入专业领域名称：\n（如：知识产权、刑事辩护、婚姻家事等）', '');
        if (tag && tag.trim()) {
            var span = document.createElement('span');
            span.className =
                'inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-[#E8F3FF] text-[#165DFF] text-xs font-medium';
            span.innerHTML =
                tag.trim() +
                ' <button onclick="removeTag(this); autoSaveProfile()" class="hover:text-red-500 transition-colors"><iconify-icon icon="mdi:close" class="text-xs"></iconify-icon></button>';
            el.parentNode.insertBefore(span, el);
        }
    }

    function removeCertFile() {
        var preview = document.getElementById('cert-file-preview');
        var upload = document.getElementById('cert-upload');
        if (preview) preview.classList.add('hidden');
        if (upload) upload.value = '';
    }

    async function toggle2FA(checkbox) {
        var status = document.getElementById('2fa-status');
        if (checkbox.checked) {
            var enableConfirm = await Utils.showConfirm(
                '开启双因素认证将提高账号安全性。\n\n建议使用 Authenticator App（如 Google Authenticator、Microsoft Authenticator）或短信验证码。\n\n是否继续开启？'
            );
            if (enableConfirm) {
                status.textContent = '已开启';
                status.className = 'text-[10px] text-green-600 font-medium';
            } else {
                checkbox.checked = false;
            }
        } else {
            var disableConfirm = await Utils.showConfirm('关闭双因素认证将降低账号安全等级，确定要关闭吗？');
            if (disableConfirm) {
                status.textContent = '未开启';
                status.className = 'text-[10px] text-[#C9CDD4]';
            } else {
                checkbox.checked = true;
            }
        }
    }

    function showDeviceManager() {
        var deviceInfo =
            '📱 当前登录设备\n' +
            '━━━━━━━━━━━━━━━━━━\n' +
            '1️⃣ Windows PC\n' +
            '   浏览器：Chrome 120.0\n' +
            '   IP：192.168.1.100\n' +
            '   最近活动：现在\n' +
            '   [当前设备]\n\n' +
            '2️⃣ iPhone 15\n' +
            '   系统：iOS 18.0\n' +
            '   IP：192.168.1.101\n' +
            '   最近活动：2 小时前\n' +
            '   [点击移除此设备]';
        Utils.showModal({
            id: 'device-manager-modal',
            title: '设备管理',
            content: '<pre class="text-xs text-fg-secondary whitespace-pre-wrap font-mono bg-bg-subtle p-3 rounded-lg">' + Utils.escapeHtml(deviceInfo) + '</pre>',
            size: 'md',
            icon: 'mdi:devices'
        });
    }

    async function confirmAccountDeletion() {
        var step1 = await Utils.showConfirm(
            '⚠️ 确认要注销账号吗？\n\n注销后：\n· 所有案件数据将被永久清除\n· 所有文书和材料将无法恢复\n· 您的会员权益将立即终止\n\n此操作不可撤销！'
        );
        if (step1) {
            var step2 = await Utils.showPrompt('请输入「确认注销」以继续操作：', '');
            if (step2 === '确认注销') {
                Utils.showToast('success', '您的账号注销申请已提交。系统将在 7 天冷静期后执行注销。在此期间重新登录可取消注销。');
            } else {
                Utils.showToast('error', '输入不正确，注销操作已取消。');
            }
        }
    }

    // ===== 校验 =====
    function validateField(el, msg) {
        if (!el.value.trim()) {
            el.classList.add('border-red-400', 'bg-[#FFF0F0]');
            el.classList.remove('border-[#E5E6EB]');
            var errorEl = el.parentNode.querySelector('.field-error');
            if (!errorEl) {
                errorEl = document.createElement('p');
                errorEl.className = 'field-error text-[10px] text-red-400 mt-1';
                errorEl.textContent = msg;
                el.parentNode.appendChild(errorEl);
            }
        } else {
            el.classList.remove('border-red-400', 'bg-[#FFF0F0]');
            el.classList.add('border-[#E5E6EB]');
            var phoneErrorEl = el.parentNode.querySelector('.field-error');
            if (phoneErrorEl) phoneErrorEl.remove();
        }
    }

    function validateEmail(el) {
        var val = el.value.trim();
        var emailErrorEl;
        if (val && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
            el.classList.add('border-[#FAAD14]', 'bg-[#FFF7E6]');
            el.classList.remove('border-[#E5E6EB]');
            emailErrorEl = el.parentNode.querySelector('.field-error');
            if (!emailErrorEl) {
                emailErrorEl = document.createElement('p');
                emailErrorEl.className = 'field-error text-[10px] text-[#FAAD14] mt-1';
                emailErrorEl.textContent = '邮箱格式不正确';
                el.parentNode.appendChild(emailErrorEl);
            }
        } else {
            el.classList.remove('border-[#FAAD14]', 'bg-[#FFF7E6]');
            el.classList.add('border-[#E5E6EB]');
            emailErrorEl = el.parentNode.querySelector('.field-error');
            if (emailErrorEl) emailErrorEl.remove();
        }
    }

    // ===== 自动保存 =====
    function autoSaveProfile() {
        if (AppState.autoSaveTimer) clearTimeout(AppState.autoSaveTimer);

        var saveBtn = document.getElementById('profile-save-btn');
        var saveText = document.getElementById('save-btn-text');
        var saveSpinner = document.getElementById('save-btn-spinner');
        if (saveBtn) {
            saveBtn.style.opacity = '0.8';
            saveBtn.style.cursor = 'default';
        }
        if (saveText) saveText.textContent = '保存中...';
        if (saveSpinner) saveSpinner.classList.remove('hidden');

        AppState.autoSaveTimer = setTimeout(function () {
            if (saveBtn) {
                saveBtn.style.opacity = '1';
                saveBtn.style.cursor = 'pointer';
            }
            if (saveText) saveText.textContent = '已保存';
            if (saveSpinner) saveSpinner.classList.add('hidden');

            setTimeout(function () {
                if (saveText && saveText.textContent === '已保存') {
                    saveText.textContent = '保存';
                }
            }, 2000);
        }, 1500);
    }

    function saveNotificationSettings() {
        var toggles = document.querySelectorAll('.notif-toggle');
        var enabled = [];
        var disabled = [];
        toggles.forEach(function (t, i) {
            if (t.checked) enabled.push(i);
            else disabled.push(i);
        });
        showSaveSuccess('通知设置已保存');
    }

    // ===== 第三方账号 =====
    function bindAccount(name) {
        showSaveSuccess('正在跳转至' + name + '授权页面...');
    }

    async function unbindAccount(name) {
        var confirmed = await Utils.showConfirm('确定要解绑' + name + '吗？解绑后可能影响相关功能使用。');
        if (confirmed) {
            showSaveSuccess(name + '已解绑');
        }
    }

    // ===== 设置页面导航切换 =====
    function switchSettingsSection(sectionName, navBtn) {
        var sections = document.querySelectorAll('.settings-section');
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

        var navItems = document.querySelectorAll('.settings-nav-item');
        navItems.forEach(function (item) {
            item.classList.remove('bg-gradient-to-r', 'from-brand', 'to-brand-hover', 'text-white', 'shadow-md', 'shadow-brand/20');
            item.classList.add('text-fg-secondary', 'hover:bg-bg-subtle', 'hover:text-fg-primary', 'group');
            var icon = item.querySelector('iconify-icon');
            if (icon) {
                icon.classList.remove('text-white');
                icon.classList.add('group-hover:text-brand', 'transition-colors');
            }
        });

        if (navBtn) {
            navBtn.classList.remove('text-fg-secondary', 'hover:bg-bg-subtle', 'hover:text-fg-primary', 'group');
            navBtn.classList.add('bg-gradient-to-r', 'from-brand', 'to-brand-hover', 'text-white', 'shadow-md', 'shadow-brand/20');
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

    // ===== 账户设置页面初始化 =====
    function initAccountSettings() {
        var view = document.getElementById('view-account-settings');
        if (!view || view.classList.contains('initialized')) return;

        view.classList.add('initialized');

        if (typeof Animations !== 'undefined' && typeof Animations.initPageAnimations === 'function') {
            Animations.initPageAnimations(view);
        }
    }

    // ===== 双绑定 =====
    globalThis.toggleProfileEdit = toggleProfileEdit;
    globalThis.cancelProfileEdit = cancelProfileEdit;
    globalThis.saveProfile = saveProfile;
    globalThis.showSaveSuccess = showSaveSuccess;
    globalThis.addTagInput = addTagInput;
    globalThis.handleAvatarUpload = handleAvatarUpload;
    globalThis.removeTag = removeTag;
    globalThis.showAddTagDialog = showAddTagDialog;
    globalThis.removeCertFile = removeCertFile;
    globalThis.toggle2FA = toggle2FA;
    globalThis.showDeviceManager = showDeviceManager;
    globalThis.confirmAccountDeletion = confirmAccountDeletion;
    globalThis.validateField = validateField;
    globalThis.validateEmail = validateEmail;
    globalThis.autoSaveProfile = autoSaveProfile;
    globalThis.saveNotificationSettings = saveNotificationSettings;
    globalThis.bindAccount = bindAccount;
    globalThis.unbindAccount = unbindAccount;
    globalThis.switchSettingsSection = switchSettingsSection;
    globalThis.initAccountSettings = initAccountSettings;
})();
