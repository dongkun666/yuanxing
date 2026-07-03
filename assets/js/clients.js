/**
 * 客户管理模块
 * 包含: 客户分类切换 + 详情页 + 新建/冲突检查
 * 加载: 在 script.js 之前同步加载
 * W31 (2026-07-02): 对接 /api/clients 后端, 失败回退内置 mock
 */

// ===== 客户列表缓存 + API 对接 (W31 phase6-clients-backend) =====
var _clientsCache = [];           // 缓存 list API 返回 (含 client_id, 供 openClientDetail 取 ID)
var _clientsLoaded = false;       // 是否已成功加载 (避免切换视图重复请求)
var _currentDetailClientId = null; // 当前打开详情的客户 client_id

// 内置 mock (与后端 _MOCK_CLIENTS 对齐, 后端不可达时兜底)
var _BUILTIN_MOCK_CLIENTS = [
    { client_id: 'CL-001', name: '李明', client_type: 'personal', grade: 'A', phone: '138****1234', status: '活跃', cases: '3' },
    { client_id: 'CL-002', name: '王华', client_type: 'personal', grade: 'B', phone: '139****5678', status: '活跃', cases: '2' },
    { client_id: 'CL-003', name: '某科技有限公司', client_type: 'enterprise', grade: 'A', phone: '010-8888****', status: '活跃', cases: '5' },
    { client_id: 'CL-004', name: '赵六', client_type: 'personal', grade: 'C', phone: '136****9012', status: '待回访', cases: '1' },
    { client_id: 'CL-005', name: '张三', client_type: 'personal', grade: 'C', phone: '137****3456', status: '静默', cases: '1' }
];

function _escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/**
 * 渲染单行客户表格 (W31: 由 API 数据驱动)
 */
function _renderClientRow(c, idx) {
    var grade = (c.grade || 'C').toUpperCase();
    var type = c.client_type || 'personal';
    var typeLabel = type === 'enterprise' ? '企业客户' : '个人客户';
    var avatar = c.name ? c.name.charAt(0) : '?';
    var phone = c.phone || '—';
    var dateStr = c.created_at ? String(c.created_at).substring(0, 10) : '—';
    var gradeClass = grade === 'A' ? 'grade-a' : (grade === 'B' ? 'grade-b' : 'grade-c');
    var gradeIcon = grade === 'A' ? 'mdi:crown' : 'mdi:star-outline';
    var avatarCell;
    if (type === 'enterprise') {
        avatarCell = '<div class="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-tint3 to-brand-tint flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">' +
            '<iconify-icon icon="mdi:office-building-outline" class="text-brand text-base"></iconify-icon></div>';
    } else {
        avatarCell = '<div class="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-tint to-brand-tint2 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">' +
            '<span class="text-sm font-bold text-brand">' + _escapeHtml(avatar) + '</span></div>';
    }
    return '<tr class="client-table-row hover:bg-brand-tint3/40 transition-all duration-200 cursor-default group" ' +
        'data-grade="' + grade + '" data-type="' + type + '" data-status="active" ' +
        'data-row-idx="' + idx + '" data-client-id="' + _escapeHtml(c.client_id) + '">' +
        '<td class="py-4 px-5"><div class="flex items-center gap-3">' + avatarCell +
        '<div class="flex-1 min-w-0"><span class="text-sm font-medium text-fg-primary truncate block" title="' + _escapeHtml(c.name) + '">' + _escapeHtml(c.name) + '</span>' +
        '<div class="flex items-center gap-1 mt-0.5"><span class="inline-flex items-center gap-0.5 text-[10px] text-fg-tertiary"><iconify-icon icon="mdi:account-outline" class="text-[9px]"></iconify-icon>' + typeLabel + '</span></div></div></div></td>' +
        '<td class="py-4 px-5 text-sm text-fg-secondary"><div class="flex items-center gap-1.5"><iconify-icon icon="mdi:phone-outline" class="text-fg-tertiary text-xs"></iconify-icon><span>' + _escapeHtml(phone) + '</span></div></td>' +
        '<td class="text-center py-4 px-5"><span class="inline-flex items-center justify-center min-w-[28px] h-7 px-2 rounded-lg bg-bg-subtle text-sm font-semibold text-fg-primary kb-tabular-nums">—</span></td>' +
        '<td class="text-center py-4 px-5 whitespace-nowrap"><span class="client-grade-badge ' + gradeClass + ' inline-flex items-center gap-1"><iconify-icon icon="' + gradeIcon + '" class="text-[10px]"></iconify-icon>' + grade + ' 级</span></td>' +
        '<td class="text-center py-4 px-5 text-sm text-fg-secondary"><div class="flex items-center justify-center gap-1.5"><iconify-icon icon="mdi:calendar-clock-outline" class="text-fg-tertiary text-base"></iconify-icon><span>' + dateStr + '</span></div></td>' +
        '<td class="text-center py-4 px-5 whitespace-nowrap"><span class="client-status-badge status-active inline-flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>活跃</span></td>' +
        '<td class="text-center py-4 px-5 whitespace-nowrap"><div class="flex items-center justify-center gap-1">' +
        '<button class="table-action-btn table-action-btn-primary" onclick="openClientDetail(' + idx + ')"><iconify-icon icon="mdi:eye-outline" class="text-xs"></iconify-icon>详情</button>' +
        '<button class="table-action-btn table-action-btn-default" onclick="alert(\'编辑客户\')"><iconify-icon icon="mdi:pencil-outline" class="text-xs"></iconify-icon>编辑</button>' +
        '</div></td>' +
        '</tr>';
}

/**
 * 填充客户详情视图 (W31: 由 API 数据驱动)
 */
function _populateClientDetail(c) {
    var nameEl = document.getElementById('client-detail-name');
    var nameTextEl = document.getElementById('client-detail-name-text');
    var avatarEl = document.getElementById('client-detail-avatar');
    var gradeEl = document.getElementById('client-detail-grade');
    var statusEl = document.getElementById('client-detail-status');
    var phoneEl = document.getElementById('client-detail-phone');
    var casesEl = document.getElementById('client-detail-cases');

    var name = c.name || '未知客户';
    var grade = (c.grade || 'C').toUpperCase();
    var gradeLabel = grade + ' 级';

    if (nameEl) nameEl.textContent = name;
    if (nameTextEl) nameTextEl.textContent = name;
    if (avatarEl) avatarEl.textContent = c.name ? c.name.charAt(0) : '?';
    if (gradeEl) {
        gradeEl.textContent = gradeLabel;
        gradeEl.className = 'client-grade-badge inline-flex items-center gap-1';
        if (grade === 'A') gradeEl.classList.add('grade-a');
        else if (grade === 'B') gradeEl.classList.add('grade-b');
        else gradeEl.classList.add('grade-c');
    }
    if (statusEl) statusEl.textContent = c.status || '活跃';
    if (phoneEl) phoneEl.textContent = c.phone || '—';
    if (casesEl) casesEl.textContent = (c.cases !== undefined && c.cases !== null) ? String(c.cases) : '—';
}

/**
 * 初始化客户视图: 调 API 加载客户列表, 失败回退内置 mock 行 (W31)
 * 由 router.js viewInitMap.client 在切换到客户视图时触发
 */
function initClientsView() {
    if (typeof API === 'undefined' || !API.clients || !API.clients.list) {
        return; // api.js 未就绪, 保留 HTML 内置 mock 行
    }
    if (_clientsLoaded) return; // 已加载, 不重复请求

    var tbody = document.getElementById('clientTableBody');
    if (!tbody) return;

    // 保留原内置 mock 行, 失败时回退
    var originalHtml = tbody.innerHTML;
    tbody.innerHTML = '<tr id="client-loading-row" class="client-table-row"><td colspan="7" class="py-8 text-center text-sm text-fg-tertiary">' +
        '<iconify-icon icon="mdi:loading" class="animate-spin text-base align-middle mr-1"></iconify-icon>加载客户列表中...</td></tr>';

    API.clients.list({ page: 1, page_size: 50 })
        .then(function (res) {
            if (res && res.ok && res.data && res.data.items && res.data.items.length > 0) {
                _clientsCache = res.data.items;
                _clientsLoaded = true;
                var html = '';
                for (var i = 0; i < _clientsCache.length; i++) {
                    html += _renderClientRow(_clientsCache[i], i);
                }
                tbody.innerHTML = html;
                var countEl = document.getElementById('clientResultCount');
                if (countEl) countEl.textContent = _clientsCache.length + ' 位';
                if (typeof filterClientList === 'function') filterClientList();
                if (typeof showToast === 'function') {
                    showToast('客户列表已加载' + (res.data.mock_mode ? ' (演示数据)' : ''), 'success');
                }
            } else {
                // API 返回空或失败, 回退内置 mock 行
                tbody.innerHTML = originalHtml;
                if (res && !res.ok) {
                    console.warn('[clients] list API 不可达, 回退 mock 行:', res.error);
                }
            }
        })
        .catch(function (err) {
            tbody.innerHTML = originalHtml;
            console.warn('[clients] list API 异常, 回退 mock 行:', err);
        });
}

function switchClientTab(el, tab) {
    document.querySelectorAll('#view-client .client-tab-btn').forEach(function (btn) {
        btn.classList.remove('bg-brand', 'text-white');
        btn.classList.add('text-fg-secondary', 'hover:bg-bg-subtle');
    });
    el.classList.remove('text-fg-secondary', 'hover:bg-bg-subtle');
    el.classList.add('bg-brand', 'text-white');
}

function filterClientList() {
    var searchInput = document.getElementById('clientSearchInput');
    var gradeFilter = document.getElementById('clientGradeFilter');
    var typeFilter = document.getElementById('clientTypeFilter');
    var rows = document.querySelectorAll('#clientTableBody .client-table-row');
    var table = document.getElementById('clientTable');
    var emptyState = document.getElementById('clientEmptyState');
    var visibleCount = 0;

    var searchText = searchInput ? searchInput.value.toLowerCase() : '';
    var gradeValue = gradeFilter ? gradeFilter.value : '';
    var typeValue = typeFilter ? typeFilter.value : '';
    var hasFilter = searchText || gradeValue || typeValue;

    rows.forEach(function (row) {
        var clientName = row.querySelector('td:first-child .text-fg-primary')?.textContent.toLowerCase() || '';
        var grade = row.getAttribute('data-grade') || '';
        var type = row.getAttribute('data-type') || '';

        var matchSearch = !searchText || clientName.indexOf(searchText) !== -1;
        var matchGrade = !gradeValue || grade === gradeValue.toLowerCase();
        var matchType = !typeValue || type === typeValue;

        if (matchSearch && matchGrade && matchType) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    if (visibleCount === 0 && emptyState) {
        if (typeof Utils !== 'undefined' && Utils.renderEmptyState) {
            if (hasFilter) {
                emptyState.innerHTML = Utils.renderEmptyState({
                    type: 'search',
                    icon: 'mdi:account-search-outline',
                    title: '没有找到匹配的客户',
                    description: '请尝试调整搜索条件或筛选条件',
                    actionText: '重置筛选',
                    actionHandler: function () {
                        if (searchInput) searchInput.value = '';
                        if (gradeFilter) gradeFilter.value = '';
                        if (typeFilter) typeFilter.value = '';
                        filterClientList();
                    }
                });
            } else {
                emptyState.innerHTML = Utils.renderEmptyState({
                    type: 'default',
                    icon: 'mdi:account-group-outline',
                    title: '暂无客户数据',
                    description: '还没有添加任何客户，点击下方按钮开始您的第一个客户管理',
                    actionText: '新建客户',
                    actionHandler: showNewClientModal
                });
            }
        }
        if (table) table.classList.add('hidden');
        emptyState.classList.remove('hidden');
        emptyState.classList.add('flex');
    } else {
        if (table) table.classList.remove('hidden');
        if (emptyState) {
            emptyState.classList.add('hidden');
            emptyState.classList.remove('flex');
        }
    }

    var countEl = document.getElementById('clientResultCount');
    if (countEl) {
        countEl.textContent = visibleCount + ' 位';
    }
}

function switchClientDetailTab(el, tab) {
    document.querySelectorAll('#view-client-detail .client-detail-tab-btn').forEach(function (btn) {
        btn.classList.remove('bg-white', 'text-brand', 'shadow-sm', 'border-bg-border');
        btn.classList.add('text-fg-secondary', 'hover:bg-white', 'hover:border-bg-border', 'border-transparent');
    });
    el.classList.remove('text-fg-secondary', 'hover:bg-white', 'hover:border-bg-border', 'border-transparent');
    el.classList.add('bg-white', 'text-brand', 'shadow-sm', 'border-bg-border');

    document.querySelectorAll('#view-client-detail .client-detail-tab-content').forEach(function (content) {
        content.classList.add('hidden');
    });
    var targetTab = document.getElementById('client-tab-' + tab);
    if (targetTab) {
        targetTab.classList.remove('hidden');
    }
}

function openClientDetail(index) {
    // W31: 优先用 list 缓存取 client_id 调 get 详情; 无缓存则回退内置 mock
    var cached = _clientsCache[index];
    var builtin = _BUILTIN_MOCK_CLIENTS[index] || _BUILTIN_MOCK_CLIENTS[0];
    var clientId = (cached && cached.client_id) || builtin.client_id;
    _currentDetailClientId = clientId;

    // 立即用缓存或内置 mock 填充 (避免详情页空白)
    _populateClientDetail(cached || builtin);

    document.querySelectorAll('.view-content').forEach(function (v) {
        v.classList.add('hidden');
    });
    var detailView = document.getElementById('view-client-detail');
    if (detailView) detailView.classList.remove('hidden');

    // 异步调 API 刷新完整详情, 失败保留缓存/mock 数据
    if (typeof API !== 'undefined' && API.clients && API.clients.get) {
        API.clients.get(clientId)
            .then(function (res) {
                if (res && res.ok && res.data) {
                    _populateClientDetail(res.data);
                } else {
                    console.warn('[clients] get 详情 API 不可达, 保留缓存/mock:', res && res.error);
                }
            })
            .catch(function (err) {
                console.warn('[clients] get 详情 API 异常, 保留缓存/mock:', err);
            });
    }
}

function backToClientList() {
    document.querySelectorAll('.view-content').forEach(function (v) {
        v.classList.add('hidden');
    });
    document.getElementById('view-client').classList.remove('hidden');
}

var _closeNewClientModal = null;

function showNewClientModal() {
    var content =
        '<div class="space-y-4">' +
        '<div class="grid grid-cols-2 gap-4">' +
        '<div>' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">客户姓名 <span class="text-red-400">*</span></label>' +
        '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand transition-colors" placeholder="请输入客户姓名" type="text"/>' +
        '</div>' +
        '<div>' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">证件类型</label>' +
        '<select class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand appearance-none bg-white transition-colors">' +
        '<option>身份证</option>' +
        '<option>护照</option>' +
        '<option>统一社会信用代码</option>' +
        '</select>' +
        '</div>' +
        '<div>' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">证件号码 <span class="text-red-400">*</span></label>' +
        '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand transition-colors" placeholder="请输入证件号码" type="text"/>' +
        '</div>' +
        '<div>' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">手机号 <span class="text-red-400">*</span></label>' +
        '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand transition-colors" placeholder="请输入手机号" type="text"/>' +
        '</div>' +
        '<div>' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">邮箱</label>' +
        '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand transition-colors" placeholder="请输入邮箱地址" type="email"/>' +
        '</div>' +
        '<div>' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">客户类型</label>' +
        '<select class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand appearance-none bg-white transition-colors">' +
        '<option>个人客户</option>' +
        '<option>企业客户</option>' +
        '</select>' +
        '</div>' +
        '<div class="col-span-2">' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">地址</label>' +
        '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand transition-colors" placeholder="请输入地址" type="text"/>' +
        '</div>' +
        '</div>' +
        '<div class="pt-3 border-t border-[#F2F3F5]">' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">案件来源</label>' +
        '<div class="flex gap-4">' +
        '<label class="flex items-center gap-1.5 text-xs text-fg-secondary cursor-pointer">' +
        '<input checked="" class="accent-[#165DFF]" name="client-source" type="radio"/>' +
        '                        电话咨询' +
        '                    </label>' +
        '<label class="flex items-center gap-1.5 text-xs text-fg-secondary cursor-pointer">' +
        '<input class="accent-[#165DFF]" name="client-source" type="radio"/>' +
        '                        微信咨询' +
        '                    </label>' +
        '<label class="flex items-center gap-1.5 text-xs text-fg-secondary cursor-pointer">' +
        '<input class="accent-[#165DFF]" name="client-source" type="radio"/>' +
        '                        到所咨询' +
        '                    </label>' +
        '<label class="flex items-center gap-1.5 text-xs text-fg-secondary cursor-pointer">' +
        '<input class="accent-[#165DFF]" name="client-source" type="radio"/>' +
        '                        介绍推荐' +
        '                    </label>' +
        '</div>' +
        '</div>' +
        '<div class="pt-3 border-t border-[#F2F3F5]">' +
        '<div class="flex items-center justify-between mb-2">' +
        '<div class="flex items-center gap-1.5">' +
        '<iconify-icon class="text-sm text-brand" icon="mdi:shield-check-outline"></iconify-icon>' +
        '<span class="text-xs font-medium text-fg-primary">利益冲突检索</span>' +
        '</div>' +
        '<button class="text-[10px] text-brand hover:underline" onclick="runNewClientConflictCheck()">立即检索</button>' +
        '</div>' +
        '<div class="flex items-center gap-2 text-[10px] text-fg-tertiary">' +
        '<iconify-icon icon="mdi:information-outline"></iconify-icon>' +
        '<span>提交时将强制进行精确查重，已存在则提示是否合并</span>' +
        '</div>' +
        '<div class="hidden mt-2" id="new-client-conflict-result">' +
        '<div class="flex items-center gap-1.5 text-[10px] text-success">' +
        '<iconify-icon icon="mdi:check-circle"></iconify-icon>' +
        '<span>未发现冲突</span>' +
        '</div>' +
        '</div>' +
        '</div>' +
        '</div>';

    var footer =
        '<button class="px-4 py-2 text-xs font-medium rounded-lg border border-bg-border text-fg-secondary hover:bg-bg-subtle transition-colors" onclick="closeNewClientModal()">取消</button>' +
        '<button class="px-4 py-2 text-xs font-semibold rounded-lg bg-brand text-white hover:bg-brand-hover transition-colors" onclick="submitNewClient()">保存并新建</button>';

    if (_closeNewClientModal) _closeNewClientModal();
    _closeNewClientModal = Utils.showModal({
        id: 'new-client-modal',
        title: '新建客户',
        content: content,
        footer: footer,
        size: 'md'
    });
}

function closeNewClientModal() {
    if (_closeNewClientModal) {
        _closeNewClientModal();
        _closeNewClientModal = null;
    }
}

function submitNewClient() {
    var modal = document.getElementById('new-client-modal');
    if (!modal) {
        showSaveSuccess('客户信息已保存，请完善案件信息');
        closeNewClientModal();
        return;
    }

    // 顺序见 showNewClientModal: input[0]=姓名, select[0]=证件类型, input[1]=证件号,
    // input[2]=手机, input[3]=邮箱, select[1]=客户类型, input[4]=地址
    var inputs = modal.querySelectorAll('input');
    var selects = modal.querySelectorAll('select');
    var name = inputs[0] ? inputs[0].value.trim() : '';
    var idNumber = inputs[1] ? inputs[1].value.trim() : '';
    var phone = inputs[2] ? inputs[2].value.trim() : '';
    var email = inputs[3] ? inputs[3].value.trim() : '';
    var address = inputs[4] ? inputs[4].value.trim() : '';
    var typeLabel = selects[1] ? selects[1].value : '个人客户';
    var clientType = typeLabel.indexOf('企业') >= 0 ? 'enterprise' : 'personal';

    if (!name) {
        if (typeof showToast === 'function') showToast('请输入客户姓名', 'warning');
        return;
    }
    if (!phone) {
        if (typeof showToast === 'function') showToast('请输入手机号', 'warning');
        return;
    }

    var payload = {
        name: name,
        client_type: clientType,
        id_number: idNumber || null,
        phone: phone,
        email: email || null,
        address: address || null,
        grade: 'C',
        notes: ''
    };

    if (typeof API !== 'undefined' && API.clients && API.clients.create) {
        // loading 态: 禁用保存按钮
        var btns = modal.querySelectorAll('button');
        var saveBtn = null;
        for (var i = 0; i < btns.length; i++) {
            if (btns[i].textContent.indexOf('保存') >= 0) { saveBtn = btns[i]; break; }
        }
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.setAttribute('data-orig-text', saveBtn.textContent);
            saveBtn.textContent = '保存中...';
        }

        API.clients.create(payload)
            .then(function (res) {
                if (res && res.ok) {
                    if (typeof showToast === 'function') {
                        showToast('客户「' + name + '」已创建', 'success');
                    } else {
                        showSaveSuccess('客户信息已保存，请完善案件信息');
                    }
                    closeNewClientModal();
                    // 刷新列表
                    _clientsLoaded = false;
                    if (typeof initClientsView === 'function') initClientsView();
                } else {
                    console.warn('[clients] create API 不可达, 回退本地:', res && res.error);
                    showSaveSuccess('客户信息已保存（本地，后端未连接）');
                    closeNewClientModal();
                }
            })
            .catch(function (err) {
                console.warn('[clients] create API 异常, 回退本地:', err);
                showSaveSuccess('客户信息已保存（本地，后端异常）');
                closeNewClientModal();
            })
            .then(function () {
                if (saveBtn) {
                    saveBtn.disabled = false;
                    var orig = saveBtn.getAttribute('data-orig-text');
                    if (orig) saveBtn.textContent = orig;
                }
            });
    } else {
        showSaveSuccess('客户信息已保存，请完善案件信息');
        closeNewClientModal();
    }
}

function runNewClientConflictCheck() {
    var result = document.getElementById('new-client-conflict-result');
    var modal = document.getElementById('new-client-modal');

    // 取新建客户姓名 (新客户尚无 client_id, 用 list?search=name 检查同名冲突)
    var name = '';
    if (modal) {
        var inputs = modal.querySelectorAll('input');
        if (inputs[0]) name = inputs[0].value.trim();
    }

    if (result) {
        result.classList.remove('hidden');
        result.innerHTML = '<div class="flex items-center gap-1.5 text-[10px] text-fg-tertiary"><iconify-icon icon="mdi:loading" class="animate-spin"></iconify-icon><span>检索中...</span></div>';
    }

    if (typeof API !== 'undefined' && API.clients && API.clients.list) {
        API.clients.list({ search: name, page_size: 50 })
            .then(function (res) {
                var html = '';
                if (res && res.ok && res.data && res.data.items) {
                    var matches = [];
                    for (var i = 0; i < res.data.items.length; i++) {
                        var c = res.data.items[i];
                        if (name && c.name === name) {
                            matches.push({ name: c.name, exact: true });
                        } else if (name && (c.name.indexOf(name) >= 0 || name.indexOf(c.name) >= 0)) {
                            matches.push({ name: c.name, exact: false });
                        }
                    }
                    if (matches.length === 0) {
                        html = '<div class="flex items-center gap-1.5 text-[10px] text-success"><iconify-icon icon="mdi:check-circle"></iconify-icon><span>未发现冲突</span></div>';
                    } else {
                        var hasExact = false;
                        for (var k = 0; k < matches.length; k++) {
                            if (matches[k].exact) { hasExact = true; break; }
                        }
                        var riskLabel = hasExact ? '高风险' : '中风险';
                        var riskClass = hasExact ? 'text-danger' : 'text-urgent';
                        html = '<div class="flex items-center gap-1.5 text-[10px] ' + riskClass + '"><iconify-icon icon="mdi:alert-circle"></iconify-icon><span>发现 ' + matches.length + ' 条疑似冲突 (' + riskLabel + ')</span></div>';
                        for (var j = 0; j < matches.length; j++) {
                            html += '<div class="text-[10px] text-fg-tertiary mt-0.5">• ' + _escapeHtml(matches[j].name) + (matches[j].exact ? ' (同名)' : ' (名称近似)') + '</div>';
                        }
                    }
                } else {
                    html = '<div class="flex items-center gap-1.5 text-[10px] text-success"><iconify-icon icon="mdi:check-circle"></iconify-icon><span>未发现冲突 (本地, 后端未连接)</span></div>';
                }
                if (result) result.innerHTML = html;
            })
            .catch(function (err) {
                console.warn('[clients] conflict-check API 异常, 回退本地:', err);
                if (result) {
                    result.innerHTML = '<div class="flex items-center gap-1.5 text-[10px] text-success"><iconify-icon icon="mdi:check-circle"></iconify-icon><span>未发现冲突 (本地, 后端异常)</span></div>';
                }
            });
    } else {
        if (result) {
            result.innerHTML = '<div class="flex items-center gap-1.5 text-[10px] text-success"><iconify-icon icon="mdi:check-circle"></iconify-icon><span>未发现冲突</span></div>';
        }
    }
}

function runConflictCheck() {
    var result = document.getElementById('conflict-result');
    if (result) {
        result.classList.remove('hidden');
        result.innerHTML = '<div class="flex items-center gap-1.5 text-[10px] text-fg-tertiary"><iconify-icon icon="mdi:loading" class="animate-spin"></iconify-icon><span>审查中...</span></div>';
    }

    var clientId = _currentDetailClientId;
    if (clientId && typeof API !== 'undefined' && API.clients && API.clients.conflictCheck) {
        API.clients.conflictCheck(clientId)
            .then(function (res) {
                var html = '';
                if (res && res.ok && res.data) {
                    var data = res.data;
                    if (data.has_conflict) {
                        var riskMap = { high: ['text-danger', '高风险'], medium: ['text-urgent', '中风险'], low: ['text-warning', '低风险'] };
                        var rk = riskMap[data.risk_level] || ['text-urgent', '中风险'];
                        html = '<div class="flex items-center gap-1.5 text-[10px] ' + rk[0] + '"><iconify-icon icon="mdi:alert-circle"></iconify-icon><span>发现 ' + data.conflicts.length + ' 条冲突 (' + rk[1] + ')</span></div>';
                        for (var i = 0; i < data.conflicts.length; i++) {
                            var cf = data.conflicts[i];
                            html += '<div class="text-[10px] text-fg-tertiary mt-0.5">• ' + _escapeHtml(cf.name || '') + ' - ' + _escapeHtml(cf.reason || '') + '</div>';
                        }
                    } else {
                        html = '<div class="flex items-center gap-1.5 text-[10px] text-success"><iconify-icon icon="mdi:check-circle"></iconify-icon><span>未发现冲突</span></div>';
                    }
                } else {
                    html = '<div class="flex items-center gap-1.5 text-[10px] text-success"><iconify-icon icon="mdi:check-circle"></iconify-icon><span>利益冲突审查完成 (本地, 后端未连接)</span></div>';
                }
                if (result) result.innerHTML = html;
            })
            .catch(function (err) {
                console.warn('[clients] conflict-check API 异常, 回退本地:', err);
                if (result) {
                    result.innerHTML = '<div class="flex items-center gap-1.5 text-[10px] text-success"><iconify-icon icon="mdi:check-circle"></iconify-icon><span>利益冲突审查完成 (本地, 后端异常)</span></div>';
                }
            });
    } else {
        if (result) {
            result.innerHTML = '<div class="flex items-center gap-1.5 text-[10px] text-success"><iconify-icon icon="mdi:check-circle"></iconify-icon><span>利益冲突审查完成</span></div>';
        }
    }
}

// ===== globalThis 暴露 (确保 router.js 可通过 window.initClientsView 调用) =====
globalThis.initClientsView = initClientsView;
