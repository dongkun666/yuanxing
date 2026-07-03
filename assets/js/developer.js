/**
 * LexPrime 开发者中心前端模块
 *
 * 功能: 开放平台 API 管理页面交互
 * 依赖: api.js, script.js (showToast)
 */

(function () {
    'use strict';

    var DeveloperState = {
        registered: false,
        apiKeys: [],
        usage: null
    };

    var DeveloperAPI = {
        BASE: '/api/developer',

        register: function (data) {
            return API.post(DeveloperAPI.BASE + '/register', data);
        },

        getApiKeys: function () {
            return API.get(DeveloperAPI.BASE + '/api-keys');
        },

        createApiKey: function (data) {
            return API.post(DeveloperAPI.BASE + '/api-keys', data);
        },

        deleteApiKey: function (id) {
            return API.delete(DeveloperAPI.BASE + '/api-keys/' + encodeURIComponent(id));
        },

        getUsage: function () {
            return API.get(DeveloperAPI.BASE + '/usage');
        }
    };

    function switchDevTab(tabName) {
        var tabBtns = document.querySelectorAll('.dev-tab-btn');
        for (var i = 0; i < tabBtns.length; i++) {
            var btn = tabBtns[i];
            if (btn.getAttribute('data-tab') === tabName) {
                btn.classList.add('active', 'text-brand', 'border-brand');
                btn.classList.remove('text-fg-tertiary', 'border-transparent');
            } else {
                btn.classList.remove('active', 'text-brand', 'border-brand');
                btn.classList.add('text-fg-tertiary', 'border-transparent');
            }
        }

        var tabContents = document.querySelectorAll('.dev-tab-content');
        for (var j = 0; j < tabContents.length; j++) {
            var content = tabContents[j];
            if (content.id === 'dev-tab-' + tabName) {
                content.classList.remove('hidden');
            } else {
                content.classList.add('hidden');
            }
        }
    }

    function openDevRegisterModal() {
        var modal = document.getElementById('dev-register-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    function closeDevRegisterModal() {
        var modal = document.getElementById('dev-register-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    function submitDevRegister() {
        var nameEl = document.getElementById('dev-reg-name');
        var emailEl = document.getElementById('dev-reg-email');
        var typeEl = document.getElementById('dev-reg-type');
        var purposeEl = document.getElementById('dev-reg-purpose');

        var name = nameEl ? nameEl.value.trim() : '';
        var email = emailEl ? emailEl.value.trim() : '';
        var developerType = typeEl ? typeEl.value : 'individual';
        var purpose = purposeEl ? purposeEl.value.trim() : '';

        if (!name) {
            if (typeof showToast === 'function') {
                showToast('请输入开发者名称', 'error');
            }
            return;
        }
        if (!email) {
            if (typeof showToast === 'function') {
                showToast('请输入联系邮箱', 'error');
            }
            return;
        }

        DeveloperAPI.register({
            name: name,
            email: email,
            developer_type: developerType,
            purpose: purpose
        }).then(function () {
            DeveloperState.registered = true;
            closeDevRegisterModal();
            if (typeof showToast === 'function') {
                showToast('开发者注册成功', 'success');
            }
            loadDevApiKeys();
        }).catch(function (err) {
            if (typeof showToast === 'function') {
                showToast('注册失败: ' + (err.message || '未知错误'), 'error');
            }
        });
    }

    function openCreateApiKeyModal() {
        var modal = document.getElementById('create-api-key-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    function closeCreateApiKeyModal() {
        var modal = document.getElementById('create-api-key-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    function submitCreateApiKey() {
        var nameEl = document.getElementById('new-api-key-name');
        var name = nameEl ? nameEl.value.trim() : '';

        if (!name) {
            if (typeof showToast === 'function') {
                showToast('请输入 API Key 名称', 'error');
            }
            return;
        }

        var scopes = ['cases', 'contract', 'doc_gen', 'companies'];

        DeveloperAPI.createApiKey({
            name: name,
            scopes: scopes
        }).then(function () {
            closeCreateApiKeyModal();
            if (typeof showToast === 'function') {
                showToast('API Key 创建成功', 'success');
            }
            loadDevApiKeys();
        }).catch(function (err) {
            if (typeof showToast === 'function') {
                showToast('创建失败: ' + (err.message || '未知错误'), 'error');
            }
        });
    }

    function deleteDevApiKey(id) {
        if (typeof window.confirm === 'function' && !window.confirm('确定要删除这个 API Key 吗？')) {
            return;
        }
        DeveloperAPI.deleteApiKey(id).then(function () {
            if (typeof showToast === 'function') {
                showToast('API Key 已删除', 'success');
            }
            loadDevApiKeys();
        }).catch(function (err) {
            if (typeof showToast === 'function') {
                showToast('删除失败: ' + (err.message || '未知错误'), 'error');
            }
        });
    }

    function loadDevApiKeys() {
        DeveloperAPI.getApiKeys().then(function (data) {
            DeveloperState.apiKeys = data.items || data || [];
            renderDevApiKeys();
            updateDevStats();
        }).catch(function () {
            renderDevApiKeys();
        });
    }

    function renderDevApiKeys() {
        var tbody = document.getElementById('dev-api-keys-tbody');
        if (!tbody) {
            return;
        }

        var keys = DeveloperState.apiKeys;
        if (!keys || keys.length === 0) {
            tbody.innerHTML =
                '<tr>' +
                '<td colspan="6" class="py-12 text-center text-fg-tertiary text-sm">' +
                '暂无 API Key，点击上方按钮创建' +
                '</td>' +
                '</tr>';
            return;
        }

        var html = '';
        for (var i = 0; i < keys.length; i++) {
            var key = keys[i];
            var maskedKey = key.api_key ? key.api_key.substring(0, 8) + '...' + key.api_key.substring(key.api_key.length - 4) : '********';
            html +=
                '<tr class="border-b border-bg-border/50 hover:bg-bg-subtle/30 transition-colors">' +
                '<td class="py-3 px-4 text-sm text-fg-primary font-medium">' + escapeHtml(key.name || '未命名') + '</td>' +
                '<td class="py-3 px-4 text-xs text-fg-secondary font-mono">' + maskedKey + '</td>' +
                '<td class="py-3 px-4">' +
                '<span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">活跃</span>' +
                '</td>' +
                '<td class="py-3 px-4 text-sm text-fg-secondary">' + (key.call_count || 0) + '</td>' +
                '<td class="py-3 px-4 text-xs text-fg-tertiary">' + (key.created_at || '-') + '</td>' +
                '<td class="py-3 px-4 text-center">' +
                '<button class="text-xs text-danger hover:text-danger-hover" onclick="deleteDevApiKey(\'' + (key.id || '') + '\')">删除</button>' +
                '</td>' +
                '</tr>';
        }
        tbody.innerHTML = html;
    }

    function loadDevUsage() {
        DeveloperAPI.getUsage().then(function (data) {
            DeveloperState.usage = data;
            updateDevStats();
        }).catch(function () {
        });
    }

    function updateDevStats() {
        var keyCountEl = document.getElementById('dev-api-key-count');
        var monthlyCallsEl = document.getElementById('dev-monthly-calls');
        var todayCallsEl = document.getElementById('dev-today-calls');
        var usageMonthlyEl = document.getElementById('dev-usage-monthly');
        var totalCallsEl = document.getElementById('dev-total-calls');

        var keyCount = DeveloperState.apiKeys ? DeveloperState.apiKeys.length : 0;
        if (keyCountEl) {
            keyCountEl.textContent = keyCount;
        }

        var usage = DeveloperState.usage || {};
        var monthly = usage.monthly_calls || 0;
        var today = usage.today_calls || 0;
        var total = usage.total_calls || 0;

        if (monthlyCallsEl) {
            monthlyCallsEl.textContent = formatNumber(monthly);
        }
        if (todayCallsEl) {
            todayCallsEl.textContent = formatNumber(today);
        }
        if (usageMonthlyEl) {
            usageMonthlyEl.textContent = formatNumber(monthly);
        }
        if (totalCallsEl) {
            totalCallsEl.textContent = formatNumber(total);
        }
    }

    function formatNumber(num) {
        if (num >= 10000) {
            return (num / 10000).toFixed(1) + '万';
        }
        return num.toString();
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }

    function initDeveloperPage() {
        loadDevApiKeys();
        loadDevUsage();
    }

    window.switchDevTab = switchDevTab;
    window.openDevRegisterModal = openDevRegisterModal;
    window.closeDevRegisterModal = closeDevRegisterModal;
    window.submitDevRegister = submitDevRegister;
    window.openCreateApiKeyModal = openCreateApiKeyModal;
    window.closeCreateApiKeyModal = closeCreateApiKeyModal;
    window.submitCreateApiKey = submitCreateApiKey;
    window.deleteDevApiKey = deleteDevApiKey;

    window.DeveloperAPI = DeveloperAPI;
    window.DeveloperState = DeveloperState;
    window.initDeveloperPage = initDeveloperPage;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            if (document.getElementById('view-developer')) {
                initDeveloperPage();
            }
        });
    } else {
        if (document.getElementById('view-developer')) {
            initDeveloperPage();
        }
    }
})();
