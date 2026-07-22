/**
 * 案件 - 详情入口/字段编辑/tab 切换模块
 * 拆分自 cases.js (2026-06-28 IIFE 拆分计划)
 *
 * 包含: 案件详情入口 (openCaseDetail) + 字段编辑 (getFieldValue/setFieldValue/
 *       renderEditForm/renderFieldInput/editSection/saveEditSection) +
 *       案件 tab 切换 (switchCaseTab) + 材料 tab 切换 (switchMaterialsTab)
 * 依赖: sectionConfigs (script.js), caseCurrentPage (script.js),
 *       currentEditSection/currentCaseIndex (script.js),
 *       loadView/switchView (router.js), showToast (script.js)
 *
 * 加载顺序: 在 cases-list.js 之后, cases-tabs.js 之前
 */

(function () {
    'use strict';

    // ===== 跨模块共享状态 (script.js 在 IIFE 内 var, 不挂 globalThis, 需显式桥接) =====
    if (typeof globalThis.currentCaseIndex === 'undefined') globalThis.currentCaseIndex = -1;

    // ===== 字段编辑 =====
    var _closeEditSectionModal = null;

    function getFieldValue(section, key) {
        var el = document.getElementById('field-' + section + '-' + key);
        if (!el) return '';
        if (section === 'claims' || section === 'strategy' || section === 'summary') {
            return el.innerText.trim();
        }
        return el.innerText.trim();
    }

    function setFieldValue(section, key, value) {
        var el = document.getElementById('field-' + section + '-' + key);
        if (!el) return;
        if (section === 'claims') {
            var lines = value.split('\n').filter(function (l) {
                return l.trim();
            });
            el.innerHTML = lines
                .map(function (line, i) {
                    return '<p>' + (i + 1) + '. ' + line.replace(/^\d+\.\s*/, '') + '</p>';
                })
                .join('');
        } else if (section === 'strategy' || section === 'summary') {
            el.innerText = value;
        } else if (key === 'status') {
            el.innerText = value;
            el.className =
                'text-[11px] font-medium px-2 py-0.5 rounded-full ' +
                (value === '进行中'
                    ? 'bg-blue-100 text-blue-700'
                    : value === '已结案'
                        ? 'bg-green-100 text-green-700'
                        : value === '已归档'
                            ? 'bg-gray-100 text-gray-700'
                            : 'bg-orange-100 text-orange-700');
        } else if (key === 'preservation') {
            el.innerText = value;
            el.className =
                'text-[11px] font-medium px-2 py-0.5 rounded-full ' +
                (value === '已保全'
                    ? 'bg-green-100 text-green-700'
                    : value === '未保全'
                        ? 'bg-gray-100 text-gray-700'
                        : 'bg-orange-100 text-orange-700');
        } else if (section === 'opponent' && key === 'legalRep') {
            el.innerText = value;
            if (!value || value === '未提供 · 请补充') {
                el.className = 'text-sm text-red-500';
            } else {
                el.className = 'text-sm text-gray-800';
            }
        } else {
            el.innerText = value;
        }
    }

    function renderEditForm(section) {
        var config = sectionConfigs[section];
        if (!config) return '';
        var html = '';
        var fields = config.fields;
        for (var i = 0; i < fields.length; i += 2) {
            var field1 = fields[i];
            var field2 = fields[i + 1];
            if (field1.colSpan === 2 || (field1.colSpan === 3 && !field2)) {
                html += '<div class="space-y-1">';
                html += '<label class="block text-xs font-medium text-gray-700">' + field1.label + '</label>';
                html += renderFieldInput(section, field1);
                html += '</div>';
            } else {
                html += '<div class="grid grid-cols-2 gap-4">';
                html += '<div class="space-y-1">';
                html += '<label class="block text-xs font-medium text-gray-700">' + field1.label + '</label>';
                html += renderFieldInput(section, field1);
                html += '</div>';
                if (field2) {
                    html += '<div class="space-y-1">';
                    html += '<label class="block text-xs font-medium text-gray-700">' + field2.label + '</label>';
                    html += renderFieldInput(section, field2);
                    html += '</div>';
                }
                html += '</div>';
            }
        }
        return html;
    }

    function renderFieldInput(section, field) {
        var value = getFieldValue(section, field.key);
        var inputClass =
            'w-full border border-[#E5E6EB] rounded-lg px-3 py-2 text-sm text-[#1D2129] focus:outline-none focus:border-[#165DFF] transition-colors';
        if (field.type === 'textarea') {
            var rows = field.rows || 4;
            return (
                '<textarea class="' +
                inputClass +
                ' resize-none" data-field="' +
                field.key +
                '" rows="' +
                rows +
                '">' +
                value +
                '</textarea>'
            );
        } else if (field.type === 'select') {
            var options = field.options || [];
            var optionsHtml = options
                .map(function (opt) {
                    return '<option value="' + opt + '"' + (opt === value ? ' selected' : '') + '>' + opt + '</option>';
                })
                .join('');
            return (
                '<select class="' +
                inputClass +
                ' appearance-none bg-white" data-field="' +
                field.key +
                '">' +
                optionsHtml +
                '</select>'
            );
        } else if (field.type === 'date') {
            return (
                '<input type="date" class="' + inputClass + '" data-field="' + field.key + '" value="' + value + '"/>'
            );
        } else {
            return (
                '<input type="text" class="' + inputClass + '" data-field="' + field.key + '" value="' + value + '"/>'
            );
        }
    }

    function editSection(section) {
        currentEditSection = section;
        var config = sectionConfigs[section];
        if (!config) return;
        var content = renderEditForm(section);
        var footer =
            '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeEditSectionModal()">取消</button>' +
            '<button class="h-9 px-4 text-xs text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="saveEditSection()">保存</button>';
        if (_closeEditSectionModal) _closeEditSectionModal();
        _closeEditSectionModal = Utils.showModal({
            id: 'edit-section-modal',
            title: config.title,
            content: content,
            footer: footer,
            size: 'lg',
            onClose: function () {
                currentEditSection = null;
                _closeEditSectionModal = null;
            }
        });
    }

    function closeEditSectionModal() {
        if (_closeEditSectionModal) {
            _closeEditSectionModal();
            _closeEditSectionModal = null;
        }
    }

    function saveEditSection() {
        if (!currentEditSection) return;
        var config = sectionConfigs[currentEditSection];
        if (!config) return;
        var modalElement = document.getElementById('edit-section-modal');
        if (!modalElement) return;
        var inputs = modalElement.querySelectorAll('[data-field]');
        for (var i = 0; i < inputs.length; i++) {
            var input = inputs[i];
            var fieldKey = input.getAttribute('data-field');
            var value = input.value;
            setFieldValue(currentEditSection, fieldKey, value);
        }
        closeEditSectionModal();
        showToast('保存成功');
    }

    // ===== 案件详情入口 =====
    function openCaseDetail(index) {
        var caseMeta = [
            {
                caseName: '李明诉XX公司买卖合同纠纷',
                caseNumber: '(2026)京01民初128号',
                type: '民间借贷纠纷',
                status: '进行中'
            },
            {
                caseName: '赵六劳动争议仲裁案',
                caseNumber: '(2026)京02民初256号',
                type: '劳动争议仲裁',
                status: '进行中'
            },
            { caseName: '张三合同纠纷案', caseNumber: '(2026)京03民初789号', type: '合同纠纷', status: '待开庭' },
            {
                caseName: '某科技公司股权纠纷案',
                caseNumber: '(2026)京04民初345号',
                type: '知识产权侵权',
                status: '已立案'
            },
            { caseName: '王华借贷纠纷案', caseNumber: '(2026)京05民初567号', type: '离婚纠纷', status: '进行中' }
        ];

        globalThis.currentCaseIndex = index;

        document.querySelectorAll('.view-content').forEach(function (v) {
            v.classList.add('hidden');
        });

        var caseView = document.getElementById('view-case');
        if (caseView) {
            caseView.classList.remove('hidden');
            if (caseMeta[index]) {
                var meta = caseMeta[index];
                var titleEl = document.getElementById('case-detail-title');
                if (titleEl) titleEl.textContent = meta.caseName;
            }
            var tab = document.querySelector('.case-tab[data-tab="overview"]');
            if (tab) switchCaseTab('overview', tab);
        } else {
            loadView('case', function (html) {
                document.getElementById('main-content').insertAdjacentHTML('beforeend', html);
                var newCaseView = document.getElementById('view-case');
                if (newCaseView) {
                    newCaseView.classList.remove('hidden');
                    if (caseMeta[index]) {
                        var meta = caseMeta[index];
                        var titleEl = document.getElementById('case-detail-title');
                        if (titleEl) titleEl.textContent = meta.caseName;
                    }
                    var tab = document.querySelector('.case-tab[data-tab="overview"]');
                    if (tab) switchCaseTab('overview', tab);
                }
            });
        }
    }

    function switchCaseTab(tabName, btn) {
        document.querySelectorAll('[id^="case-tab-"]').forEach(function (el) {
            el.classList.add('hidden');
            el.classList.remove('flex', 'flex-row', 'flex-col');
        });
        var target = document.getElementById('case-tab-' + tabName);
        if (target) {
            target.classList.remove('hidden');
            target.classList.add('flex');
            if (tabName === 'documents') {
                target.classList.add('flex-row');
            } else {
                target.classList.add('flex-col');
            }
        }
        document.querySelectorAll('.case-tab').forEach(function (b) {
            b.classList.remove('border-[#165DFF]', 'text-[#165DFF]');
            b.classList.add('border-transparent', 'text-gray-500');
        });
        if (btn) {
            btn.classList.remove('border-transparent', 'text-gray-500');
            btn.classList.add('border-[#165DFF]', 'text-[#165DFF]');
        }
    }

    function switchMaterialsTab(tabName, btn) {
        document.getElementById('materials-tab-overview').classList.add('hidden');
        document.getElementById('materials-tab-catalog').classList.add('hidden');
        document.getElementById('materials-tab-' + tabName).classList.remove('hidden');
        document.querySelectorAll('.materials-tab').forEach(function (tab) {
            tab.classList.remove('text-[#165DFF]', 'border-[#165DFF]');
            tab.classList.add('text-gray-500', 'border-transparent');
        });
        if (btn) {
            btn.classList.remove('text-gray-500', 'border-transparent');
            btn.classList.add('text-[#165DFF]', 'border-[#165DFF]');
        }
    }

    // ===== 双绑定 =====
    globalThis.getFieldValue = getFieldValue;
    globalThis.setFieldValue = setFieldValue;
    globalThis.renderEditForm = renderEditForm;
    globalThis.renderFieldInput = renderFieldInput;
    globalThis.editSection = editSection;
    globalThis.closeEditSectionModal = closeEditSectionModal;
    globalThis.saveEditSection = saveEditSection;
    globalThis.openCaseDetail = openCaseDetail;
    globalThis.switchCaseTab = switchCaseTab;
    globalThis.switchMaterialsTab = switchMaterialsTab;
})();
