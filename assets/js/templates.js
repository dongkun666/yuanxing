/**
 * 模板管理模块 - 官方模板 + 个人模板
 * 包含: Tab 切换 + 视图切换 + 上传/分类/筛选/排序/预览
 * 加载: 在 script.js 之前同步加载
 */

function switchTemplateTab(tabName, btn) {
    document.getElementById('template-tab-personal').classList.add('hidden');
    document.getElementById('template-tab-official').classList.add('hidden');
    document.getElementById('template-tab-' + tabName).classList.remove('hidden');
    document.querySelectorAll('.template-tab').forEach(function (tab) {
        tab.classList.remove('text-[#165DFF]', 'border-[#165DFF]');
        tab.classList.add('text-gray-500', 'border-transparent');
        tab.removeAttribute('data-active');
    });
    if (btn) {
        btn.classList.remove('text-gray-500', 'border-transparent');
        btn.classList.add('text-[#165DFF]', 'border-[#165DFF]');
        btn.setAttribute('data-active', 'true');
    }
    // 官方 tab 仅列表视图: 切到 official 时强制把视图切换按钮对齐到 list
    if (tabName === 'official') {
        var listBtn = document.querySelector('.template-view-btn[data-view="list"]');
        if (listBtn) switchTemplateView('list', listBtn);
    }
    // 切到个人 tab: 渲染个人模板 (从 AppState.personalTemplates 数据驱动, 含持久化)
    if (tabName === 'personal') {
        if (typeof renderPersonalTemplates === 'function') renderPersonalTemplates();
    }
}

function fixTemplateViewDOM() {
    var main = document.querySelector('.max-w-7xl.mx-auto.space-y-4');
    if (!main) return;
    var personal = document.getElementById('template-tab-personal');
    var official = document.getElementById('template-tab-official');
    if (!personal || !official) return;
    var personalCardView = personal.querySelector('.template-view-card');
    var officialCardView = official.querySelector('.template-view-card');
    // 备用: official tab 内 template-view-card 飘出时, 找 main 中第一个非 personal 的 template-view-card
    if (!officialCardView) {
        var allCards = document.querySelectorAll('.template-view-card');
        for (var j = 0; j < allCards.length; j++) {
            if (allCards[j] !== personalCardView) {
                officialCardView = allCards[j];
                break;
            }
        }
    }
    var orphans = [];
    for (var i = 0; i < main.children.length; i++) {
        var c = main.children[i];
        if (c === personal || c === official) continue;
        if (c.classList && c.classList.contains('fixed')) continue;
        if (
            c.className &&
            (c.className.indexOf('rounded-xl') !== -1 || c.className.indexOf('template-view-card') !== -1)
        ) {
            orphans.push(c);
        }
    }
    if (!orphans.length) return;
    orphans.forEach(function (el) {
        if (el.classList.contains('template-view-card')) {
            var cards = el.querySelectorAll('[data-template-category]');
            var firstCat = cards[0] ? cards[0].getAttribute('data-template-category') : '';
            if (firstCat === '诉状类' || firstCat === '答辩类' || firstCat === '合同类') {
                if (personalCardView && el !== personalCardView) {
                    while (el.firstChild) personalCardView.appendChild(el.firstChild);
                    el.parentNode.removeChild(el);
                }
            } else {
                if (officialCardView && el !== officialCardView) {
                    while (el.firstChild) officialCardView.appendChild(el.firstChild);
                    el.parentNode.removeChild(el);
                }
            }
            return;
        }
        var cat = el.getAttribute('data-template-category');
        if (!cat) return;
        if (cat === '诉状类' || cat === '答辩类' || cat === '合同类') {
            if (personalCardView) personalCardView.appendChild(el);
        } else {
            if (officialCardView) officialCardView.appendChild(el);
        }
    });
}

function switchTemplateView(viewName, btn) {
    // 官方模板仅保留列表视图 (产品决定: 官方模板统一用列表展示更高效)
    // 检查当前激活的 tab: 官方 tab 时强制 list + 把按钮高亮对齐到 list 按钮
    // 通过 data-active 属性追踪当前 tab (由 switchTemplateTab 设置)
    var activeTabBtn = document.querySelector('.template-tab[data-active="true"]');
    var activeTab = activeTabBtn
        ? activeTabBtn.textContent.indexOf('个人') >= 0
            ? 'personal'
            : 'official'
        : 'personal';
    if (activeTab === 'official') {
        viewName = 'list';
        btn = document.querySelector('.template-view-btn[data-view="list"]');
    }
    document.querySelectorAll('.template-view-btn').forEach(function (b) {
        b.classList.remove('bg-blue-50', 'text-[#165DFF]');
        b.classList.add('text-gray-500', 'hover:text-gray-700');
    });
    if (btn) {
        btn.classList.add('bg-blue-50', 'text-[#165DFF]');
        btn.classList.remove('text-gray-500', 'hover:text-gray-700');
    }
    // 切换 personal + official 两个 tab 内的视图
    // 官方模板仅保留列表视图 (产品决定: 官方模板统一用列表展示更高效), 强制 list
    ['personal', 'official'].forEach(function (tab) {
        var effectiveView = tab === 'official' ? 'list' : viewName;
        var listView = document.querySelector('#template-tab-' + tab + ' .template-view-list');
        var cardView = document.querySelector('#template-tab-' + tab + ' .template-view-card');
        if (effectiveView === 'list') {
            if (listView) listView.classList.remove('hidden');
            if (cardView) cardView.classList.add('hidden');
        } else {
            if (listView) listView.classList.add('hidden');
            if (cardView) cardView.classList.remove('hidden');
        }
    });
    // 切到卡片视图时同步调用官方模板 filter, 让 grid 列数按可见卡片数适配
    if (viewName === 'card' && typeof applyOfficialFilter === 'function') {
        applyOfficialFilter();
    }
}

function persistPersonalTemplates() {
    if (typeof AppState === 'undefined') return;
    try {
        localStorage.setItem('lexprime_personal_templates', JSON.stringify(AppState.personalTemplates));
    } catch (e) {
        console.warn('持久化个人模板失败:', e);
    }
}

// 简单 HTML 转义 (防止 name 含 <> 时 XSS)
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// 分类标签颜色映射 (复用 submitUploadTemplate 已有 colorCls)
function personalCategoryColor(c) {
    var colorCls = {
        诉状类: 'bg-brand-tint text-brand',
        答辩类: 'bg-wiki-tint text-wiki',
        合同类: 'bg-warning-tint text-warning',
        申请类: 'bg-success-tint text-success'
    };
    return colorCls[c] || 'bg-bg-subtle text-fg-secondary';
}

// 渲染个人模板列表 (列表视图 + 卡片视图) - 数据驱动
function renderPersonalTemplates() {
    if (typeof AppState === 'undefined' || !AppState.personalTemplates) return;
    var tbody = document.querySelector('#template-tab-personal tbody');
    var cardContainer = document.querySelector('#template-tab-personal .template-view-card');
    if (!tbody) return;
    var htmlStr = '';
    AppState.personalTemplates.forEach(function (t, idx) {
        var cls = personalCategoryColor(t.category);
        var sizeHtml = t.size
            ? '<span class="text-[10px] text-fg-tertiary ml-1">(' + escapeHtml(t.size) + ')</span>'
            : '';
        htmlStr +=
            '<tr class="hover:bg-bg-subtle/50 group transition-colors" data-template-id="' +
            escapeHtml(t.id) +
            '" data-template-category="' +
            escapeHtml(t.category) +
            '">' +
            '<td class="py-4 px-5">' +
            '<div class="flex items-center gap-3">' +
            '<div class="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-tint to-brand-tint2 flex items-center justify-center group-hover:from-brand-tint2 group-hover:to-brand-tint3 transition-all">' +
            '<iconify-icon class="text-xl text-brand" icon="mdi:file-document-outline"></iconify-icon>' +
            '</div>' +
            '<span class="text-sm text-fg-primary font-semibold">' +
            escapeHtml(t.name) +
            '</span>' +
            sizeHtml +
            '</div>' +
            '</td>' +
            '<td class="py-4 px-5"><span class="text-[11px] ' +
            cls +
            ' px-2 py-0.5 rounded-lg font-medium">' +
            escapeHtml(t.category) +
            '</span></td>' +
            '<td class="py-4 px-5 text-xs text-fg-secondary">' +
            escapeHtml(t.creator || '') +
            '</td>' +
            '<td class="py-4 px-5 text-xs text-fg-tertiary">' +
            escapeHtml(t.updatedAt || '') +
            '</td>' +
            '<td class="py-4 px-5 text-center">' +
            '<div class="flex items-center justify-center gap-1">' +
            '<button class="text-xs text-brand hover:bg-brand-tint3 px-2.5 py-1.5 rounded-lg font-medium transition-colors">使用</button>' +
            '<button class="text-xs text-brand hover:bg-brand-tint3 px-2.5 py-1.5 rounded-lg font-medium transition-colors">编辑</button>' +
            '<button class="text-xs text-danger hover:bg-danger-tint px-2.5 py-1.5 rounded-lg font-medium transition-colors" onclick="deletePersonalTemplate(this)">删除</button>' +
            '</div>' +
            '</td>' +
            '</tr>';
    });
    tbody.innerHTML = htmlStr;
    // 卡片视图 (同步)
    if (cardContainer) {
        var cardHtml = '';
        AppState.personalTemplates.forEach(function (t, idx) {
            var cls = personalCategoryColor(t.category);
            var catColorMap = {
                诉状类: 'from-brand-tint via-brand-tint2 to-white',
                答辩类: 'from-wiki-tint via-purple-100 to-white',
                合同类: 'from-warning-tint via-orange-100 to-white',
                申请类: 'from-success-tint via-green-100 to-white'
            };
            var gradientCls = catColorMap[t.category] || 'from-brand-tint via-brand-tint2 to-white';
            var textColorMap = {
                诉状类: 'text-brand',
                答辩类: 'text-wiki',
                合同类: 'text-warning',
                申请类: 'text-success'
            };
            var textCls = textColorMap[t.category] || 'text-brand';
            var borderHoverMap = {
                诉状类: 'hover:border-brand/30',
                答辩类: 'hover:border-wiki/30',
                合同类: 'hover:border-warning/30',
                申请类: 'hover:border-success/30'
            };
            var borderHoverCls = borderHoverMap[t.category] || 'hover:border-brand/30';
            cardHtml +=
                '<div class="tpl-card bg-white border border-bg-border rounded-2xl overflow-hidden shadow-sm hover:shadow-xl ' +
                borderHoverCls +
                ' transition-all duration-300 hover:-translate-y-1 cursor-pointer group" data-template-id="' +
                escapeHtml(t.id) +
                '" data-template-category="' +
                escapeHtml(t.category) +
                '" data-animate="scale-in" data-stagger-group="personal-cards" data-stagger-index="' +
                idx +
                '" data-delay="0.1">' +
                '<div class="relative h-32 bg-gradient-to-br ' +
                gradientCls +
                ' overflow-hidden">' +
                '<div class="absolute top-3 right-3">' +
                '<span class="text-[10px] bg-white/90 backdrop-blur-sm ' +
                textCls +
                ' px-2 py-0.5 rounded-full font-semibold shadow-sm">' +
                escapeHtml(t.category) +
                '</span>' +
                '</div>' +
                '<div class="absolute inset-0 flex items-center justify-center">' +
                '<div class="w-14 h-14 rounded-2xl bg-white/80 backdrop-blur-sm flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">' +
                '<iconify-icon class="text-3xl ' +
                textCls +
                '" icon="mdi:file-document-outline"></iconify-icon>' +
                '</div>' +
                '</div>' +
                '<div class="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-white/60 to-transparent"></div>' +
                '</div>' +
                '<div class="p-4">' +
                '<h4 class="text-sm font-bold text-fg-primary mb-2 group-hover:' +
                textCls +
                ' transition-colors line-clamp-1">' +
                escapeHtml(t.name) +
                '</h4>' +
                '<div class="flex items-center justify-between text-[11px] text-fg-tertiary mb-3">' +
                '<span class="flex items-center gap-1">' +
                '<iconify-icon icon="mdi:account-outline" class="text-xs"></iconify-icon>' +
                escapeHtml(t.creator || '') +
                '</span>' +
                '<span>' +
                (t.updatedAt ? t.updatedAt.split(' ')[0] : '') +
                '</span>' +
                '</div>' +
                '<div class="flex items-center justify-between pt-3 border-t border-bg-border/50">' +
                '<div class="flex items-center gap-1 text-[10px] text-fg-tertiary">' +
                '<iconify-icon icon="mdi:star" class="text-warning"></iconify-icon>' +
                '<span class="font-medium text-fg-secondary">4.8</span>' +
                '<span class="text-fg-disabled">·</span>' +
                '<span>' +
                (t.size || '使用') +
                '</span>' +
                '</div>' +
                '<div class="flex items-center gap-1">' +
                '<button class="w-7 h-7 rounded-lg bg-brand-tint3 text-brand hover:bg-gradient-to-r hover:from-brand hover:to-brand-hover hover:text-white transition-all duration-200 flex items-center justify-center" onclick="event.stopPropagation(); showToast(\'已使用该模板\')" title="使用">' +
                '<iconify-icon icon="mdi:check" class="text-xs"></iconify-icon>' +
                '</button>' +
                '<button class="w-7 h-7 rounded-lg bg-bg-subtle text-fg-tertiary hover:bg-danger-tint hover:text-danger transition-all duration-200 flex items-center justify-center" onclick="event.stopPropagation(); deletePersonalTemplate(this)" title="删除">' +
                '<iconify-icon icon="mdi:trash-can-outline" class="text-xs"></iconify-icon>' +
                '</button>' +
                '</div>' +
                '</div>' +
                '</div>' +
                '</div>';
        });
        cardContainer.innerHTML = cardHtml;
    }
    // 头部计数
    var headerCount = document.querySelector('.template-view-header-count');
    if (headerCount) headerCount.textContent = '共 ' + AppState.personalTemplates.length + ' 个';
}

var _closeUploadTemplateModal = null;

function openUploadTemplateModal() {
    var content =
        '<div class="space-y-4">' +
        '<div>' +
        '<label class="text-xs text-fg-tertiary mb-1.5 block">模板名称 <span class="text-red-500">*</span></label>' +
        '<input class="w-full bg-bg-subtle border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand focus:bg-white" id="upload-template-name" placeholder="如：起诉状-借款合同 v3" maxlength="50" type="text"/>' +
        '</div>' +
        '<div>' +
        '<label class="text-xs text-fg-tertiary mb-1.5 block">所属分类 <span class="text-red-500">*</span></label>' +
        '<select class="w-full bg-bg-subtle border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand focus:bg-white" id="upload-template-category">' +
        '<option value="">请选择分类</option>' +
        buildUploadCategoryOptions() +
        '</select>' +
        '</div>' +
        '<div>' +
        '<label class="text-xs text-fg-tertiary mb-1.5 block">文件格式</label>' +
        '<div class="flex items-center gap-4 text-sm">' +
        '<label class="flex items-center gap-1.5 cursor-pointer">' +
        '<input checked class="text-brand focus:ring-brand" name="upload-template-format" type="radio" value="docx"/><span>.docx</span>' +
        '</label>' +
        '<label class="flex items-center gap-1.5 cursor-pointer">' +
        '<input class="text-brand focus:ring-brand" name="upload-template-format" type="radio" value="pdf"/><span>.pdf</span>' +
        '</label>' +
        '<label class="flex items-center gap-1.5 cursor-pointer">' +
        '<input class="text-brand focus:ring-brand" name="upload-template-format" type="radio" value="txt"/><span>.txt</span>' +
        '</label>' +
        '</div>' +
        '</div>' +
        '<div>' +
        '<label class="text-xs text-fg-tertiary mb-1.5 block">模板文件 <span class="text-red-500">*</span></label>' +
        '<div class="border-2 border-dashed border-bg-border rounded-lg p-6 text-center hover:border-brand transition-colors cursor-pointer" id="upload-template-dropzone" onclick="document.getElementById(\'upload-template-file\').click()">' +
        '<iconify-icon class="text-3xl text-gray-300" icon="mdi:cloud-upload-outline"></iconify-icon>' +
        '<p class="text-sm text-fg-tertiary mt-2" id="upload-template-filename">点击或拖拽文件到此处</p>' +
        '<p class="text-[10px] text-fg-tertiary mt-1">支持 .docx / .pdf / .txt, 单文件最大 10MB</p>' +
        '<input accept=".docx,.pdf,.txt" class="hidden" id="upload-template-file" type="file" onchange="document.getElementById(\'upload-template-filename\').textContent = this.files[0] ? this.files[0].name : \'点击或拖拽文件到此处\'"/>' +
        '</div>' +
        '</div>' +
        '</div>';

    var footer =
        '<button class="text-sm bg-white border border-bg-border hover:bg-gray-50 px-4 py-1.5 rounded-lg" onclick="closeUploadTemplateModal()">取消</button>' +
        '<button class="text-sm text-white bg-brand hover:bg-blue-600 px-4 py-1.5 rounded-lg flex items-center gap-1.5" onclick="submitUploadTemplate()">' +
        '<iconify-icon icon="mdi:cloud-upload-outline"></iconify-icon>上传' +
        '</button>';

    if (_closeUploadTemplateModal) _closeUploadTemplateModal();
    _closeUploadTemplateModal = Utils.showModal({
        id: 'upload-template-modal',
        title: '上传模板',
        icon: 'mdi:cloud-upload-outline',
        content: content,
        footer: footer,
        size: 'md'
    });
}

function buildUploadCategoryOptions() {
    // 从主页面个人模板标签栏同步分类 (排除"全部")
    var tabs = document.querySelectorAll('.personal-category-tab[data-category]:not([data-category="all"])');
    var html = '';
    tabs.forEach(function (tab) {
        var name = tab.getAttribute('data-category');
        if (name) html += '<option value="' + escapeHtml(name) + '">' + escapeHtml(name) + '</option>';
    });
    return html;
}

function closeUploadTemplateModal() {
    if (_closeUploadTemplateModal) {
        _closeUploadTemplateModal();
        _closeUploadTemplateModal = null;
    }
}

function submitUploadTemplate() {
    var name = (document.getElementById('upload-template-name').value || '').trim();
    var category = document.getElementById('upload-template-category').value;
    var fileInput = document.getElementById('upload-template-file');
    var file = fileInput.files[0];
    if (!name) {
        showToast('请输入模板名称');
        return;
    }
    if (!category) {
        showToast('请选择分类');
        return;
    }
    if (!file) {
        showToast('请选择文件');
        return;
    }
    // 格式校验
    var ext = file.name.split('.').pop().toLowerCase();
    if (['docx', 'pdf', 'txt'].indexOf(ext) < 0) {
        showToast('仅支持 .docx / .pdf / .txt 格式');
        return;
    }
    if (file.size > 10 * 1024 * 1024) {
        showToast('文件大小不能超过 10MB');
        return;
    }
    // 取文件大小
    var sizeKb = Math.round(file.size / 1024);
    var sizeText = sizeKb < 1024 ? sizeKb + ' KB' : (sizeKb / 1024).toFixed(1) + ' MB';
    // 选中的格式 radio
    var fmtRadio = document.querySelector('input[name="upload-template-format"]:checked');
    var fmt = fmtRadio ? fmtRadio.value : ext;
    // 当前用户 (mock 张律师)
    var creator = '张律师';
    var now = new Date();
    var pad = function (n) {
        return n < 10 ? '0' + n : '' + n;
    };
    var timeStr =
        now.getFullYear() +
        '-' +
        pad(now.getMonth() + 1) +
        '-' +
        pad(now.getDate()) +
        ' ' +
        pad(now.getHours()) +
        ':' +
        pad(now.getMinutes());
    // 数据驱动: push 到 AppState.personalTemplates + 持久化
    if (typeof AppState === 'undefined' || !AppState.personalTemplates) return;
    var newId = 'p_' + Date.now();
    AppState.personalTemplates.unshift({
        id: newId,
        name: name,
        category: category,
        creator: creator,
        updatedAt: timeStr,
        size: sizeText,
        fmt: '.' + fmt
    });
    persistPersonalTemplates();
    // 重渲染整个个人模板列表 (列表 + 卡片视图同步)
    renderPersonalTemplates();
    closeUploadTemplateModal();
    showToast('模板「' + name + '」已上传');
}

async function deletePersonalTemplate(btn) {
    var confirmed = await Utils.showConfirm('确定删除该模板?');
    if (!confirmed) return;
    // 数据驱动: 从 AppState.personalTemplates 按 id 删 + 持久化 + 重渲染
    if (typeof AppState === 'undefined' || !AppState.personalTemplates) return;
    var tr = btn.closest('tr');
    var card = btn.closest('.bg-white.border.rounded-xl');
    var templateId = (tr && tr.getAttribute('data-template-id')) || (card && card.getAttribute('data-template-id'));
    if (!templateId) {
        // fallback: 按名字找
        var rowName = tr
            ? tr.querySelector('td:first-child span')
                ? tr.querySelector('td:first-child span').textContent.trim()
                : ''
            : '';
        var idx = AppState.personalTemplates.findIndex(function (t) {
            return t.name === rowName;
        });
        if (idx >= 0) templateId = AppState.personalTemplates[idx].id;
    }
    if (templateId) {
        var idx2 = AppState.personalTemplates.findIndex(function (t) {
            return t.id === templateId;
        });
        if (idx2 >= 0) AppState.personalTemplates.splice(idx2, 1);
        persistPersonalTemplates();
        renderPersonalTemplates();
        showToast('已删除');
    } else {
        showToast('找不到模板');
    }
}

var _closeCategoryManageModal = null;

function openCategoryManageModal() {
    var content =
        '<!-- 新建分类输入区 -->' +
        '<div class="pb-4 mb-4 border-b border-gray-100">' +
        '<label class="text-xs text-fg-tertiary mb-2 block">新建分类</label>' +
        '<div class="flex items-center gap-2">' +
        '<input class="flex-1 bg-bg-subtle border border-bg-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand focus:bg-white" id="new-category-input" placeholder="如：劳动仲裁类、知识产权类..." type="text" maxlength="20" onkeydown="if(event.key===\'Enter\') addCategory()"/>' +
        '<button class="text-sm text-white bg-brand hover:bg-blue-600 px-4 py-2 rounded-lg flex items-center gap-1" onclick="addCategory()">' +
        '<iconify-icon icon="mdi:plus"></iconify-icon>添加' +
        '</button>' +
        '</div>' +
        '</div>' +
        '<!-- 分类列表 -->' +
        '<div class="text-xs text-fg-tertiary mb-3" id="category-list-count">共 0 个分类</div>' +
        '<div class="space-y-2" id="category-list"></div>';

    var footer =
        '<button class="text-sm bg-white border border-bg-border hover:bg-gray-50 px-4 py-1.5 rounded-lg" onclick="closeCategoryManageModal()">关闭</button>';

    if (_closeCategoryManageModal) _closeCategoryManageModal();
    _closeCategoryManageModal = Utils.showModal({
        id: 'category-manage-modal',
        title: '个人模板分类管理',
        icon: 'mdi:folder-cog-outline',
        content: content,
        footer: footer,
        size: 'md'
    });

    // 同步现有分类到弹窗列表 (从主页面标签栏读取)
    syncCategoryListToModal();
}

// 从主页面个人模板标签栏同步分类到弹窗内的列表
function syncCategoryListToModal() {
    var list = document.getElementById('category-list');
    var countEl = document.getElementById('category-list-count');
    if (!list) return;
    list.innerHTML = '';
    var tabs = document.querySelectorAll('.personal-category-tab[data-category]:not([data-category="all"])');
    tabs.forEach(function (tab) {
        var name = tab.getAttribute('data-category');
        if (!name) return;
        // 计算该分类下的模板数
        var count = 0;
        var rows = document.querySelectorAll('#template-tab-personal tbody tr[data-template-category]');
        rows.forEach(function (tr) {
            if (tr.getAttribute('data-template-category') === name) count++;
        });
        var div = document.createElement('div');
        div.className =
            'category-item flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100';
        div.setAttribute('data-category', name);
        div.innerHTML =
            '<div class="flex items-center gap-3">' +
            '<iconify-icon class="text-base text-brand" icon="mdi:folder-outline"></iconify-icon>' +
            '<span class="text-sm text-fg-primary font-medium">' +
            escapeHtml(name) +
            '</span>' +
            '<span class="text-[10px] text-fg-tertiary">(' +
            count +
            ' 个模板)</span>' +
            '</div>' +
            '<button class="text-xs text-red-500 hover:bg-red-50 px-2 py-1 rounded delete-category-btn" onclick="deleteCategory(\'' +
            name.replace(/'/g, '\\\'') +
            '\')">' +
            '<iconify-icon icon="mdi:trash-can-outline"></iconify-icon>删除</button>';
        list.appendChild(div);
    });
    if (countEl) countEl.textContent = '共 ' + tabs.length + ' 个分类';
}

function closeCategoryManageModal() {
    if (_closeCategoryManageModal) {
        _closeCategoryManageModal();
        _closeCategoryManageModal = null;
    }
}

function addCategory() {
    var input = document.getElementById('new-category-input');
    var name = (input.value || '').trim();
    if (!name) {
        showToast('请输入分类名称');
        return;
    }
    if (name.length > 20) {
        showToast('分类名称不能超过 20 个字符');
        return;
    }
    // 检查重名
    var exists = Array.from(document.querySelectorAll('.category-item')).some(function (el) {
        return el.getAttribute('data-category') === name;
    });
    if (exists) {
        showToast('该分类已存在');
        return;
    }
    // 创建新分类项 (弹窗内)
    var list = document.getElementById('category-list');
    var countEl = document.getElementById('category-list-count');
    var div = document.createElement('div');
    div.className = 'category-item flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100';
    div.setAttribute('data-category', name);
    div.innerHTML =
        '<div class="flex items-center gap-3">' +
        '<iconify-icon class="text-base text-[#165DFF]" icon="mdi:folder-outline"></iconify-icon>' +
        '<span class="text-sm text-gray-800 font-medium">' +
        name +
        '</span>' +
        '<span class="text-[10px] text-gray-400">(0 个模板)</span>' +
        '</div>' +
        '<button class="text-xs text-red-500 hover:bg-red-50 px-2 py-1 rounded delete-category-btn" onclick="deleteCategory(\'' +
        name.replace(/'/g, '\\\'') +
        '\')">' +
        '<iconify-icon icon="mdi:trash-can-outline"></iconify-icon>删除</button>';
    list.appendChild(div);
    // 同步添加到个人模板标签栏
    var tabs = document.getElementById('personal-category-tabs');
    if (tabs) {
        var tabBtn = document.createElement('button');
        tabBtn.className =
            'personal-category-tab text-xs px-3 py-1 rounded-full bg-white border border-gray-200 text-gray-600 hover:border-[#165DFF] hover:text-[#165DFF]';
        tabBtn.setAttribute('data-category', name);
        tabBtn.setAttribute('onclick', 'filterPersonalByCategory(\'' + name.replace(/'/g, '\\\'') + '\', this)');
        tabBtn.textContent = name + ' (0)';
        tabs.appendChild(tabBtn);
    }
    // 同步更新"全部"标签的数字
    updateAllCategoryCount();
    input.value = '';
    // 更新计数
    var total = list.querySelectorAll('.category-item').length;
    if (countEl) countEl.textContent = '共 ' + total + ' 个分类';
    showToast('分类「' + name + '」已添加');
}

function sortPersonalTemplates(btn) {
    // 切换顺序
    if (_personalSortOrder === 'desc') {
        _personalSortOrder = 'asc';
    } else {
        _personalSortOrder = 'desc';
    }
    var order = _personalSortOrder;
    // 解析行的时间字符串 (第 4 列 td)
    function parseTime(tr) {
        var tds = tr.querySelectorAll('td');
        var timeStr = tds.length >= 4 ? (tds[3].textContent || '').trim() : '';
        var d = new Date(timeStr.replace(/-/g, '/'));
        return isNaN(d.getTime()) ? 0 : d.getTime();
    }
    // 排序 tbody
    var tbody = document.querySelector('#template-tab-personal tbody');
    if (tbody) {
        var rows = Array.from(tbody.querySelectorAll('tr[data-template-category]'));
        rows.sort(function (a, b) {
            var ta = parseTime(a),
                tb = parseTime(b);
            return order === 'desc' ? tb - ta : ta - tb;
        });
        rows.forEach(function (r) {
            tbody.appendChild(r);
        });
    }
    // 同步排序卡片视图 (按卡片底部时间排序)
    var cardContainer = document.querySelector('#template-tab-personal .template-view-card');
    if (cardContainer) {
        var cards = Array.from(cardContainer.querySelectorAll('div[data-template-category]'));
        cards.sort(function (a, b) {
            var ta = 0,
                tb = 0;
            var timeSpans = a.querySelectorAll('span');
            var taStr = timeSpans.length ? timeSpans[timeSpans.length - 1].textContent.trim() : '';
            var dA = new Date(taStr.replace(/-/g, '/'));
            ta = isNaN(dA.getTime()) ? 0 : dA.getTime();
            timeSpans = b.querySelectorAll('span');
            var tbStr = timeSpans.length ? timeSpans[timeSpans.length - 1].textContent.trim() : '';
            var dB = new Date(tbStr.replace(/-/g, '/'));
            tb = isNaN(dB.getTime()) ? 0 : dB.getTime();
            return order === 'desc' ? tb - ta : ta - tb;
        });
        cards.forEach(function (c) {
            cardContainer.appendChild(c);
        });
    }
    // 按钮视觉反馈
    if (btn) {
        document.querySelectorAll('.sort-btn').forEach(function (b) {
            b.classList.remove('bg-[#165DFF]', 'text-white');
            b.classList.add('text-[#165DFF]', 'bg-[#EEF3FF]');
        });
        btn.classList.add('bg-[#165DFF]', 'text-white');
        btn.classList.remove('text-[#165DFF]', 'bg-[#EEF3FF]');
        // 更新图标方向
        var icon = btn.querySelector('iconify-icon');
        if (icon) {
            icon.setAttribute('icon', order === 'desc' ? 'mdi:sort-variant' : 'mdi:sort-reverse-variant');
        }
    }
    // 重新应用当前分类筛选 (排序后保持筛选)
    var activeTab = document.querySelector('.personal-category-tab.bg-\\[\\#165DFF\\]');
    if (activeTab) {
        var cat = activeTab.getAttribute('data-category');
        filterPersonalByCategory(cat, activeTab);
    }
    showToast(order === 'desc' ? '已按时间降序排列' : '已按时间升序排列');
}

function parseTime(tr) {
    var tds = tr.querySelectorAll('td');
    var timeStr = tds.length >= 4 ? (tds[3].textContent || '').trim() : '';
    var d = new Date(timeStr.replace(/-/g, '/'));
    return isNaN(d.getTime()) ? 0 : d.getTime();
}

function updateAllCategoryCount() {
    var allTab = document.querySelector('.personal-category-tab[data-category="all"]');
    if (allTab) {
        var total = document.querySelectorAll('#template-tab-personal tbody tr[data-template-category]').length;
        allTab.textContent = '全部 (' + total + ')';
    }
}

function filterPersonalByCategory(category, btn) {
    // 更新 active 样式
    document.querySelectorAll('.personal-category-tab').forEach(function (b) {
        b.classList.remove(
            'bg-gradient-to-r',
            'from-brand',
            'to-brand-hover',
            'text-white',
            'font-medium',
            'shadow-sm',
            'shadow-brand/20'
        );
        b.classList.add('bg-white', 'border', 'border-bg-border', 'text-fg-secondary');
    });
    if (btn) {
        btn.classList.add(
            'bg-gradient-to-r',
            'from-brand',
            'to-brand-hover',
            'text-white',
            'font-medium',
            'shadow-sm',
            'shadow-brand/20'
        );
        btn.classList.remove('bg-white', 'border', 'border-bg-border', 'text-fg-secondary');
    }
    applyPersonalFilters();
}

function filterOfficialByCategory(category, btn) {
    _officialCategory = category;
    // 更新一级 active 样式
    var officialTabs = document.querySelectorAll('.official-category-tab');
    officialTabs.forEach(function (b) {
        b.classList.remove('bg-[#165DFF]', 'text-white', 'border-[#165DFF]', 'hover:bg-[#0E4AD8]');
        b.classList.add('bg-white', 'border-gray-200', 'text-gray-600', 'hover:bg-gray-50');
    });
    if (btn) {
        btn.classList.add('bg-[#165DFF]', 'text-white', 'border-[#165DFF]', 'hover:bg-[#0E4AD8]');
        btn.classList.remove('bg-white', 'border-gray-200', 'text-gray-600', 'hover:bg-gray-50');
    }
    // 二级筛选: 执行/其他 不显示起诉/答辩类型
    var typeFilter = document.getElementById('official-type-filter');
    if (typeFilter) {
        if (category === '执行' || category === '其他') {
            typeFilter.classList.add('hidden');
        } else {
            typeFilter.classList.remove('hidden');
        }
    }
    // 切到「执行/其他」时强制 type 回到 all
    if (category === '执行' || category === '其他') {
        _officialType = 'all';
        filterOfficialByType('all', document.querySelector('.official-type-tab[data-type="all"]'));
        return;
    }
    applyOfficialFilter();
}

function filterOfficialByType(type, btn) {
    _officialType = type;
    // 更新二级 active 样式
    document.querySelectorAll('.official-type-tab').forEach(function (b) {
        b.classList.remove('bg-[#165DFF]', 'text-white', 'border-[#165DFF]', 'hover:bg-[#0E4AD8]');
        b.classList.add('bg-white', 'border-gray-200', 'text-gray-600', 'hover:bg-gray-50');
    });
    if (btn) {
        btn.classList.add('bg-[#165DFF]', 'text-white', 'border-[#165DFF]', 'hover:bg-[#0E4AD8]');
        btn.classList.remove('bg-white', 'border-gray-200', 'text-gray-600', 'hover:bg-gray-50');
    }
    applyOfficialFilter();
}

function applyOfficialFilter() {
    var rows = document.querySelectorAll('#template-tab-official tbody tr[data-template-category]');
    var visibleRowCount = 0;
    rows.forEach(function (tr) {
        var cat = tr.getAttribute('data-template-category');
        var typ = tr.getAttribute('data-template-type');
        var catMatch = _officialCategory === 'all' || cat === _officialCategory;
        var typeMatch = _officialType === 'all' || typ === _officialType;
        var searchMatch = true;
        if (_searchKeyword) {
            var text = tr.textContent.toLowerCase();
            searchMatch = text.indexOf(_searchKeyword) >= 0;
        }
        var visible = catMatch && typeMatch && searchMatch;
        tr.style.display = visible ? '' : 'none';
        if (visible) visibleRowCount++;
    });

    var listEmpty = document.getElementById('official-list-empty');
    if (listEmpty) {
        listEmpty.classList.toggle('hidden', visibleRowCount > 0);
    }

    var cards = document.querySelectorAll('#template-tab-official .template-view-card > div[data-template-category]');
    var visibleCount = 0;
    cards.forEach(function (card) {
        var cat = card.getAttribute('data-template-category');
        var typ = card.getAttribute('data-template-type');
        var catMatch = _officialCategory === 'all' || cat === _officialCategory;
        var typeMatch = _officialType === 'all' || typ === _officialType;
        var searchMatch = true;
        if (_searchKeyword) {
            var text = card.textContent.toLowerCase();
            searchMatch = text.indexOf(_searchKeyword) >= 0;
        }
        var visible = catMatch && typeMatch && searchMatch;
        card.style.display = visible ? '' : 'none';
        if (visible) visibleCount++;
    });

    var grid = document.getElementById('official-card-grid');
    if (grid) {
        var cols = visibleCount === 0 ? 4 : visibleCount <= 2 ? 2 : visibleCount <= 4 ? 3 : 4;
        grid.style.gridTemplateColumns = 'repeat(' + cols + ', minmax(0, 1fr))';
    }

    var emptyEl = document.getElementById('official-card-empty');
    if (emptyEl) {
        emptyEl.classList.toggle('hidden', visibleCount > 0);
    }

    var countEl = document.getElementById('official-card-count');
    if (countEl) countEl.textContent = visibleCount;
    var totalEl = document.getElementById('official-card-total');
    if (totalEl) totalEl.textContent = cards.length;
}

var _closeOfficialTemplatePreview = null;

function previewOfficialTemplate(cardEl) {
    var titleEl = cardEl.querySelector('h4');
    var title = titleEl ? titleEl.textContent.trim() : '未命名模板';
    var cat = cardEl.dataset.templateCategory || '';
    var typ = cardEl.dataset.templateType || '';
    var descEl = cardEl.querySelector('p');
    var desc = descEl ? descEl.textContent.trim() : '';

    var content =
        '<div class="space-y-4">' +
        '<div class="p-4 bg-bg-subtle rounded-xl">' +
        '<div class="flex items-start gap-3">' +
        '<div class="w-12 h-12 rounded-lg bg-brand-tint text-brand flex items-center justify-center flex-shrink-0">' +
        '<iconify-icon icon="mdi:file-document-outline" class="text-xl"></iconify-icon>' +
        '</div>' +
        '<div class="flex-1 min-w-0">' +
        '<h4 class="text-sm font-semibold text-fg-primary mb-1">' +
        escapeHtml(title) +
        '</h4>' +
        '<div class="flex items-center gap-2 flex-wrap">' +
        '<span class="text-[10px] bg-brand-tint text-brand font-medium px-1.5 py-0.5 rounded-full">' +
        escapeHtml(cat) +
        '</span>' +
        '<span class="text-[10px] bg-bg text-fg-tertiary font-medium px-1.5 py-0.5 rounded-full">' +
        escapeHtml(typ) +
        '</span>' +
        '</div>' +
        '</div>' +
        '</div>' +
        '</div>' +
        '<div class="p-4 bg-white border border-bg-border rounded-xl">' +
        '<p class="text-[11px] text-fg-tertiary mb-2">模板说明</p>' +
        '<p class="text-xs text-fg-secondary leading-relaxed">' +
        escapeHtml(
            desc ||
                '官方标准模板，由 LexPrime 法务团队审核发布，符合最新法律法规要求。可直接下载使用，或保存为个人模板后编辑。'
        ) +
        '</p>' +
        '</div>' +
        '<div class="grid grid-cols-2 gap-3 text-sm">' +
        '<div class="p-3 bg-bg-subtle rounded-lg">' +
        '<p class="text-[11px] text-fg-tertiary mb-1">模板格式</p>' +
        '<p class="text-sm text-fg-primary">.docx</p>' +
        '</div>' +
        '<div class="p-3 bg-bg-subtle rounded-lg">' +
        '<p class="text-[11px] text-fg-tertiary mb-1">文件大小</p>' +
        '<p class="text-sm text-fg-primary">约 45 KB</p>' +
        '</div>' +
        '</div>' +
        '<div class="p-4 bg-brand-tint/50 rounded-xl">' +
        '<p class="text-[11px] text-brand mb-2">使用提示</p>' +
        '<p class="text-xs text-fg-secondary leading-relaxed">点击「使用模板」可直接创建新文档并自动填充案件信息；点击「保存到个人」可将模板加入个人模板库以便后续编辑。</p>' +
        '</div>' +
        '</div>';

    var footer =
        '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeOfficialTemplatePreview()">关闭</button>' +
        '<button class="h-9 px-4 text-xs text-brand bg-brand-tint border border-brand/20 rounded-lg hover:bg-brand-tint/70" onclick="closeOfficialTemplatePreview(); saveTemplateToPersonal(\'' +
        escapeHtml(title).replace(/'/g, '\\\'') +
        '\')">保存到个人</button>' +
        '<button class="h-9 px-4 text-xs text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="closeOfficialTemplatePreview(); if(typeof showToast===\'function\')showToast(\'正在下载模板...\', \'info\')">下载模板</button>';

    if (_closeOfficialTemplatePreview) _closeOfficialTemplatePreview();
    _closeOfficialTemplatePreview = Utils.showModal({
        id: 'official-template-preview-modal',
        title: '模板预览',
        icon: 'mdi:file-document-outline',
        content: content,
        footer: footer,
        size: 'md'
    });
}

function closeOfficialTemplatePreview() {
    if (_closeOfficialTemplatePreview) {
        _closeOfficialTemplatePreview();
        _closeOfficialTemplatePreview = null;
    }
}

function saveTemplateToPersonal(name) {
    if (typeof showToast === 'function') showToast('模板「' + name + '」已保存到个人模板库', 'success');
}

async function deleteCategory(name) {
    // 检查该分类下是否还有模板 (在个人模板表格中)
    var rows = document.querySelectorAll('#template-tab-personal tbody tr');
    var hasTemplate = Array.from(rows).some(function (tr) {
        var badge = tr.querySelector('td:nth-child(2) span');
        return badge && badge.textContent.trim() === name;
    });
    if (hasTemplate) {
        showToast('该分类下还有模板, 请先删除模板');
        return;
    }
    var confirmed = await Utils.showConfirm('确定删除分类「' + name + '」?');
    if (!confirmed) return;
    var item = document.querySelector('.category-item[data-category="' + name + '"]');
    if (item) item.remove();
    // 同步移除个人模板标签栏按钮
    var tabBtn = document.querySelector('.personal-category-tab[data-category="' + name + '"]');
    if (tabBtn) tabBtn.remove();
    var countEl = document.getElementById('category-list-count');
    var list = document.getElementById('category-list');
    if (countEl && list) {
        var total = list.querySelectorAll('.category-item').length;
        countEl.textContent = '共 ' + total + ' 个分类';
    }
    showToast('分类「' + name + '」已删除');
}

var _personalSortOrder = 'desc';
var _officialCategory = 'all';
var _officialType = 'all';
var _searchKeyword = '';

function initTemplatePage() {
    initTemplateEmptyStates();
    initTemplateLawyerRecommend();
    if (typeof Animations !== 'undefined' && typeof Animations.initPageAnimations === 'function') {
        var viewEl = document.getElementById('view-template');
        if (viewEl) {
            Animations.initPageAnimations(viewEl);
        }
    }
}

function initTemplateLawyerRecommend() {
    var container = document.getElementById('template-lawyer-list');
    if (!container) return;

    var criteria = {
        required_specialties: ['contract_dispute'],
        sort_by: 'match_score',
        page: 1,
        page_size: 3,
        filters: {}
    };

    if (typeof window.MarketplaceFn !== 'undefined' && typeof window.MarketplaceFn.matchLawyersV2 === 'function') {
        window.MarketplaceFn.matchLawyersV2(criteria).then(function (result) {
            if (result.ok && result.data && result.data.lawyers && result.data.lawyers.length > 0) {
                renderTemplateLawyerList(container, result.data.lawyers);
            } else {
                renderTemplateLawyerEmpty(container);
            }
        });
    } else {
        renderTemplateLawyerEmpty(container);
    }
}

function renderTemplateLawyerList(container, lawyers) {
    var html = lawyers
        .slice(0, 3)
        .map(function (l) {
            var score = l.match_score || {};
            var totalScore = score.total_score !== undefined ? score.total_score : 0;
            var scorePct = Math.round(totalScore * 100);
            var specialtyLabels = (l.specialties || [])
                .slice(0, 2)
                .map(function (s) {
                    if (typeof window.MarketplaceData !== 'undefined' && window.MarketplaceData.CASE_TYPES) {
                        var t = window.MarketplaceData.CASE_TYPES.find(function (c) {
                            return c.value === s;
                        });
                        return t ? t.label : s;
                    }
                    return s;
                })
                .join(' · ');

            return (
                '<div class="bg-bg-subtle/30 rounded-lg p-4 hover:bg-brand-tint/20 transition-colors cursor-pointer border border-transparent hover:border-brand/30" onclick="MarketplaceFn.openMatchDetail(\'' +
                escapeHtml(l.lawyer_id) +
                '\')">' +
                '<div class="flex items-center gap-3 mb-3">' +
                '<div class="w-10 h-10 rounded-full bg-gradient-to-br from-brand to-wiki flex items-center justify-center text-white font-semibold flex-shrink-0">' +
                escapeHtml(l.name ? l.name.substring(0, 1) : '?') +
                '</div>' +
                '<div class="flex-1 min-w-0">' +
                '<div class="text-sm font-semibold text-fg-primary truncate">' +
                escapeHtml(l.name) +
                '</div>' +
                '<div class="text-[10px] text-fg-tertiary truncate">' +
                escapeHtml(l.firm_id || '独立律师') +
                '</div>' +
                '</div>' +
                '<div class="text-right flex-shrink-0">' +
                '<div class="text-lg font-bold text-brand">' +
                scorePct +
                '</div>' +
                '<div class="text-[9px] text-fg-tertiary">匹配度</div>' +
                '</div>' +
                '</div>' +
                '<div class="text-[11px] text-fg-secondary mb-2">' +
                escapeHtml(specialtyLabels || '多领域') +
                '</div>' +
                '<div class="flex items-center gap-2 text-[10px] text-fg-tertiary flex-wrap">' +
                '<span><iconify-icon icon="mdi:map-marker-outline" class="text-xs"></iconify-icon> ' +
                escapeHtml(l.region || '未填') +
                '</span>' +
                '<span><iconify-icon icon="mdi:briefcase-outline" class="text-xs"></iconify-icon> ' +
                (l.experience_years || 0) +
                '年</span>' +
                '<span><iconify-icon icon="mdi:star" class="text-xs text-urgent"></iconify-icon> ' +
                (l.rating || 0).toFixed(1) +
                '</span>' +
                '</div>' +
                '<button class="mt-3 w-full text-xs py-1.5 rounded-lg bg-brand/10 text-brand hover:bg-brand hover:text-white transition-colors font-medium" onclick="event.stopPropagation();MarketplaceFn.openMatchDetail(\'' +
                escapeHtml(l.lawyer_id) +
                '\')">' +
                '查看匹配详情' +
                '</button>' +
                '</div>'
            );
        })
        .join('');

    container.innerHTML = html;
}

function renderTemplateLawyerEmpty(container) {
    container.innerHTML =
        '<div class="col-span-full text-center py-6 text-fg-tertiary text-xs">' +
        '<iconify-icon icon="mdi:account-search-outline" class="text-2xl mb-2 block mx-auto"></iconify-icon>' +
        '暂无推荐律师' +
        '</div>';
}

function initTemplateEmptyStates() {
    var personalListEmpty = document.getElementById('personal-list-empty');
    if (personalListEmpty && Utils && typeof Utils.createEmptyState === 'function') {
        Utils.createEmptyState({
            preset: 'templates',
            icon: 'mdi:file-document-outline',
            title: '暂无个人模板',
            description: '上传您的第一个模板，开始高效管理文档',
            actionText: '上传模板',
            actionHandler: function () {
                openUploadTemplateModal();
            },
            container: personalListEmpty
        });
    }

    var personalCardEmpty = document.getElementById('personal-card-empty');
    if (personalCardEmpty && Utils && typeof Utils.createEmptyState === 'function') {
        Utils.createEmptyState({
            preset: 'templates',
            icon: 'mdi:file-document-outline',
            title: '暂无个人模板',
            description: '上传您的第一个模板，开始高效管理文档',
            actionText: '上传模板',
            actionHandler: function () {
                openUploadTemplateModal();
            },
            container: personalCardEmpty
        });
    }

    var officialListEmpty = document.getElementById('official-list-empty');
    if (officialListEmpty && Utils && typeof Utils.createEmptyState === 'function') {
        Utils.createEmptyState({
            preset: 'search',
            icon: 'mdi:file-search-outline',
            title: '未找到匹配的模板',
            description: '试试调整筛选条件或搜索关键词',
            container: officialListEmpty
        });
    }

    var officialCardEmpty = document.getElementById('official-card-empty');
    if (officialCardEmpty && Utils && typeof Utils.createEmptyState === 'function') {
        Utils.createEmptyState({
            preset: 'search',
            icon: 'mdi:file-search-outline',
            title: '未找到匹配的模板',
            description: '试试调整筛选条件或搜索关键词',
            container: officialCardEmpty
        });
    }
}

function filterTemplatesBySearch(keyword) {
    _searchKeyword = (keyword || '').trim().toLowerCase();
    applyAllFilters();
}

function applyAllFilters() {
    var activeTabBtn = document.querySelector('.template-tab[data-active="true"]');
    var activeTab = activeTabBtn
        ? activeTabBtn.textContent.indexOf('个人') >= 0
            ? 'personal'
            : 'official'
        : 'personal';

    if (activeTab === 'personal') {
        applyPersonalFilters();
    } else {
        applyOfficialFilter();
    }
}

function applyPersonalFilters() {
    var activeCatTab = document.querySelector('.personal-category-tab.bg-\\[\\#165DFF\\]');
    var category = activeCatTab ? activeCatTab.getAttribute('data-category') : 'all';

    var rows = document.querySelectorAll('#template-tab-personal tbody tr[data-template-category]');
    var visibleRowCount = 0;
    rows.forEach(function (tr) {
        var catMatch = category === 'all' || tr.getAttribute('data-template-category') === category;
        var searchMatch = true;
        if (_searchKeyword) {
            var text = tr.textContent.toLowerCase();
            searchMatch = text.indexOf(_searchKeyword) >= 0;
        }
        var visible = catMatch && searchMatch;
        tr.style.display = visible ? '' : 'none';
        if (visible) visibleRowCount++;
    });

    var listEmpty = document.getElementById('personal-list-empty');
    if (listEmpty) {
        listEmpty.classList.toggle('hidden', visibleRowCount > 0);
    }

    var cards = document.querySelectorAll('#template-tab-personal .template-view-card > div[data-template-category]');
    var visibleCardCount = 0;
    cards.forEach(function (card) {
        var catMatch = category === 'all' || card.getAttribute('data-template-category') === category;
        var searchMatch = true;
        if (_searchKeyword) {
            var text = card.textContent.toLowerCase();
            searchMatch = text.indexOf(_searchKeyword) >= 0;
        }
        var visible = catMatch && searchMatch;
        card.style.display = visible ? '' : 'none';
        if (visible) visibleCardCount++;
    });

    var cardEmpty = document.getElementById('personal-card-empty');
    if (cardEmpty) {
        cardEmpty.classList.toggle('hidden', visibleCardCount > 0);
    }
}

function refreshTemplateAnimations(scope) {
    if (typeof Animations === 'undefined' || typeof Animations.initPageAnimations !== 'function') return;
    var root = scope || document.getElementById('view-template');
    if (!root) return;

    var animatedEls = root.querySelectorAll('[data-animate]');
    animatedEls.forEach(function (el) {
        el.style.opacity = '';
        el.style.transform = '';
    });

    setTimeout(function () {
        Animations.initPageAnimations(root);
    }, 50);
}

var _originalSwitchTemplateTab = switchTemplateTab;
switchTemplateTab = function (tabName, btn) {
    _originalSwitchTemplateTab(tabName, btn);
    setTimeout(function () {
        var tabEl = document.getElementById('template-tab-' + tabName);
        if (tabEl) {
            refreshTemplateAnimations(tabEl);
        }
    }, 100);
};

var _originalRenderPersonalTemplates = renderPersonalTemplates;
renderPersonalTemplates = function () {
    _originalRenderPersonalTemplates();
    var cardContainer = document.querySelector('#template-tab-personal .template-view-card');
    if (cardContainer) {
        var cards = cardContainer.querySelectorAll('div[data-template-category]');
        cards.forEach(function (card, idx) {
            if (!card.hasAttribute('data-animate')) {
                card.setAttribute('data-animate', 'scale-in');
                card.setAttribute('data-stagger-group', 'personal-cards');
                card.setAttribute('data-stagger-index', String(idx));
                card.setAttribute('data-delay', '0.1');
            }
        });
    }
    applyPersonalFilters();
};

document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('view-template')) {
        initTemplatePage();
    }
});
