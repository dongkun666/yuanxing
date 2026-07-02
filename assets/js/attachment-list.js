(function () {
    'use strict';

    var _attachments = [
        {
            id: 1,
            name: '起诉状_张三合同纠纷.pdf',
            type: '文书文件',
            caseName: '张三合同纠纷',
            size: '2.3MB',
            date: '2026-06-10',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-red-50'
        },
        {
            id: 2,
            name: '证据目录_v3.xlsx',
            type: '证据材料',
            caseName: '张三合同纠纷',
            size: '256KB',
            date: '2026-06-10',
            icon: 'mdi:file-excel-outline',
            iconColor: 'text-green-500',
            iconBg: 'bg-green-50'
        },
        {
            id: 3,
            name: '民事起诉状_终稿.docx',
            type: '文书文件',
            caseName: '李四借贷纠纷',
            size: '45KB',
            date: '2026-06-09',
            icon: 'mdi:file-word-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-brand-tint3'
        },
        {
            id: 4,
            name: '举证期限告知书.pdf',
            type: '文书文件',
            caseName: '张三合同纠纷',
            size: '1.2MB',
            date: '2026-06-09',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-red-50'
        },
        {
            id: 5,
            name: '证据照片_现场勘验.jpg',
            type: '图片',
            caseName: '王五股权转让纠纷',
            size: '3.5MB',
            date: '2026-06-08',
            icon: 'mdi:file-image-outline',
            iconColor: 'text-purple-500',
            iconBg: 'bg-purple-50'
        },
        {
            id: 6,
            name: '开庭传票.pdf',
            type: '文书文件',
            caseName: '赵六劳动争议',
            size: '0.5MB',
            date: '2026-06-07',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-red-50'
        },
        {
            id: 7,
            name: '补充材料_银行流水.docx',
            type: '证据材料',
            caseName: '王五股权转让纠纷',
            size: '3.5MB',
            date: '2026-06-08',
            icon: 'mdi:file-word-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-brand-tint3'
        },
        {
            id: 8,
            name: '合议庭组成通知书.pdf',
            type: '文书文件',
            caseName: '孙七建设工程合同纠纷',
            size: '0.3MB',
            date: '2026-06-06',
            icon: 'mdi:file-document-outline',
            iconColor: 'text-fg-tertiary',
            iconBg: 'bg-gray-50'
        },
        {
            id: 9,
            name: '结案报告.pdf',
            type: '文书文件',
            caseName: '周八借款纠纷',
            size: '32KB',
            date: '2026-06-05',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-red-50'
        },
        {
            id: 10,
            name: '一审判决书.pdf',
            type: '文书文件',
            caseName: '吴九房屋租赁合同纠纷',
            size: '1.1MB',
            date: '2026-06-04',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-red-50'
        },
        {
            id: 11,
            name: '证据目录_更新版.xlsx',
            type: '证据材料',
            caseName: '王五股权转让纠纷',
            size: '128KB',
            date: '2026-06-08',
            icon: 'mdi:file-excel-outline',
            iconColor: 'text-green-500',
            iconBg: 'bg-green-50'
        },
        {
            id: 12,
            name: '代理词_张三案.docx',
            type: '文书文件',
            caseName: '张三合同纠纷',
            size: '38KB',
            date: '2026-06-03',
            icon: 'mdi:file-word-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-brand-tint3'
        },
        {
            id: 13,
            name: '顾问合同_2025.pdf',
            type: '合同文件',
            caseName: '某科技公司',
            size: '0.6MB',
            date: '2026-06-03',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-red-50'
        },
        {
            id: 14,
            name: '现场勘验照片2.jpg',
            type: '图片',
            caseName: '王五股权转让纠纷',
            size: '2.1MB',
            date: '2026-06-07',
            icon: 'mdi:file-image-outline',
            iconColor: 'text-purple-500',
            iconBg: 'bg-purple-50'
        },
        {
            id: 15,
            name: '答辩状_初稿.docx',
            type: '文书文件',
            caseName: '李四借贷纠纷',
            size: '52KB',
            date: '2026-06-02',
            icon: 'mdi:file-word-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-brand-tint3'
        },
        {
            id: 16,
            name: '和解协议书_草案.pdf',
            type: '合同文件',
            caseName: '赵六劳动争议',
            size: '0.8MB',
            date: '2026-06-01',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-red-50'
        },
        {
            id: 17,
            name: '费用结算表.xlsx',
            type: '其他',
            caseName: '张三合同纠纷',
            size: '96KB',
            date: '2026-05-28',
            icon: 'mdi:file-excel-outline',
            iconColor: 'text-green-500',
            iconBg: 'bg-green-50'
        },
        {
            id: 18,
            name: '律师工作记录.txt',
            type: '其他',
            caseName: '周八借款纠纷',
            size: '15KB',
            date: '2026-05-25',
            icon: 'mdi:file-document-outline',
            iconColor: 'text-fg-tertiary',
            iconBg: 'bg-gray-50'
        },
        {
            id: 19,
            name: '调查笔录.pdf',
            type: '证据材料',
            caseName: '孙七建设工程合同纠纷',
            size: '0.4MB',
            date: '2026-05-20',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-red-50'
        },
        {
            id: 20,
            name: '合同扫描件_盖章版.png',
            type: '图片',
            caseName: '吴九房屋租赁合同纠纷',
            size: '5.2MB',
            date: '2026-05-15',
            icon: 'mdi:file-image-outline',
            iconColor: 'text-purple-500',
            iconBg: 'bg-purple-50'
        },
        {
            id: 21,
            name: '上诉状_草稿.docx',
            type: '文书文件',
            caseName: '吴九房屋租赁合同纠纷',
            size: '41KB',
            date: '2026-05-10',
            icon: 'mdi:file-word-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-brand-tint3'
        },
        {
            id: 22,
            name: '劳动合同_模板.docx',
            type: '合同文件',
            caseName: '模板库',
            size: '28KB',
            date: '2026-05-08',
            icon: 'mdi:file-word-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-brand-tint3'
        },
        {
            id: 23,
            name: '借条_范本.pdf',
            type: '合同文件',
            caseName: '模板库',
            size: '120KB',
            date: '2026-05-05',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-red-50'
        },
        {
            id: 24,
            name: '授权委托书_模板.docx',
            type: '文书文件',
            caseName: '模板库',
            size: '35KB',
            date: '2026-05-01',
            icon: 'mdi:file-word-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-brand-tint3'
        }
    ];

    var _currentTypeFilter = 'all';
    var _currentCaseFilter = 'all';
    var _searchKeyword = '';
    var _currentView = 'grid';
    var _currentPage = 1;
    var _pageSize = 12;
    var _searchTimer = null;

    var _typeOptions = ['全部分类', '文书文件', '证据材料', '合同文件', '图片', '其他'];
    var _caseOptions = [
        '全部案件',
        '张三合同纠纷',
        '李四借贷纠纷',
        '王五股权转让纠纷',
        '赵六劳动争议',
        '孙七建设工程合同纠纷',
        '周八借款纠纷',
        '吴九房屋租赁合同纠纷',
        '某科技公司',
        '模板库'
    ];

    function getFilteredAttachments() {
        return _attachments.filter(function (f) {
            var matchType = _currentTypeFilter === 'all' || f.type === _currentTypeFilter;
            var matchCase = _currentCaseFilter === 'all' || f.caseName === _currentCaseFilter;
            var keyword = _searchKeyword.toLowerCase();
            var matchSearch =
                !keyword ||
                f.name.toLowerCase().indexOf(keyword) > -1 ||
                f.caseName.toLowerCase().indexOf(keyword) > -1;
            return matchType && matchCase && matchSearch;
        });
    }

    function renderGridCard(f) {
        return (
            '<div class="bg-white rounded-xl border border-bg-border p-4 hover:shadow-sm transition-shadow cursor-pointer group">' +
            '<div class="flex items-start justify-between mb-3">' +
            '<div class="w-10 h-10 rounded-xl ' +
            f.iconBg +
            ' flex items-center justify-center">' +
            '<iconify-icon class="' +
            f.iconColor +
            ' text-xl" icon="' +
            f.icon +
            '"></iconify-icon>' +
            '</div>' +
            '<span class="text-[10px] text-fg-tertiary opacity-0 group-hover:opacity-100 transition-opacity">' +
            '<button class="text-fg-tertiary hover:text-brand mr-1" aria-label="下载文件" onclick="event.stopPropagation(); downloadAttachment(' +
            f.id +
            ')"><iconify-icon icon="mdi:download"></iconify-icon></button>' +
            '<button class="text-fg-tertiary hover:text-red-500" aria-label="删除文件" onclick="event.stopPropagation(); deleteAttachment(' +
            f.id +
            ')"><iconify-icon icon="mdi:delete-outline"></iconify-icon></button>' +
            '</span>' +
            '</div>' +
            '<p class="text-xs font-medium text-fg-primary truncate">' +
            escapeHtml(f.name) +
            '</p>' +
            '<p class="text-[10px] text-fg-tertiary mt-1">案件：' +
            escapeHtml(f.caseName) +
            '</p>' +
            '<div class="flex items-center justify-between mt-2">' +
            '<span class="text-[10px] text-fg-tertiary">' +
            f.size +
            '</span>' +
            '<span class="text-[10px] text-fg-tertiary">' +
            f.date +
            '</span>' +
            '</div>' +
            '</div>'
        );
    }

    function renderListItem(f) {
        return (
            '<div class="bg-white rounded-lg border border-bg-border p-3 hover:shadow-sm transition-shadow cursor-pointer flex items-center gap-3">' +
            '<div class="w-10 h-10 rounded-lg ' +
            f.iconBg +
            ' flex items-center justify-center flex-shrink-0">' +
            '<iconify-icon class="' +
            f.iconColor +
            ' text-xl" icon="' +
            f.icon +
            '"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<p class="text-sm font-medium text-fg-primary truncate">' +
            escapeHtml(f.name) +
            '</p>' +
            '<div class="flex items-center gap-3 mt-0.5">' +
            '<span class="text-[10px] text-fg-tertiary">' +
            escapeHtml(f.caseName) +
            '</span>' +
            '<span class="text-[10px] text-fg-tertiary">' +
            f.type +
            '</span>' +
            '</div>' +
            '</div>' +
            '<div class="flex items-center gap-4 flex-shrink-0">' +
            '<span class="text-[10px] text-fg-tertiary">' +
            f.size +
            '</span>' +
            '<span class="text-[10px] text-fg-tertiary">' +
            f.date +
            '</span>' +
            '<div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">' +
            '<button class="p-1 text-fg-tertiary hover:text-brand rounded" aria-label="下载文件" onclick="event.stopPropagation(); downloadAttachment(' +
            f.id +
            ')"><iconify-icon icon="mdi:download"></iconify-icon></button>' +
            '<button class="p-1 text-fg-tertiary hover:text-red-500 rounded" aria-label="删除文件" onclick="event.stopPropagation(); deleteAttachment(' +
            f.id +
            ')"><iconify-icon icon="mdi:delete-outline"></iconify-icon></button>' +
            '</div>' +
            '</div>' +
            '</div>'
        );
    }

    function renderAttachments() {
        var container = document.getElementById('attachment-grid');
        if (!container) return;

        var filtered = getFilteredAttachments();
        var totalPages = Math.ceil(filtered.length / _pageSize);
        if (_currentPage > totalPages) _currentPage = 1;
        var start = (_currentPage - 1) * _pageSize;
        var pageData = filtered.slice(start, start + _pageSize);

        if (filtered.length === 0) {
            container.classList.remove(
                'grid',
                'grid-cols-1',
                'sm:grid-cols-2',
                'lg:grid-cols-3',
                'xl:grid-cols-4',
                'gap-3',
                'space-y-2'
            );
            container.classList.add('flex-1', 'flex', 'items-center', 'justify-center');
            container.innerHTML =
                '<div class="text-center">' +
                '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:folder-open-outline"></iconify-icon>' +
                '<p class="text-sm text-fg-tertiary mt-3">没有找到匹配的文件</p>' +
                '</div>';
            return;
        }

        container.classList.remove('flex-1', 'flex', 'items-center', 'justify-center');
        if (_currentView === 'grid') {
            container.classList.remove('space-y-2');
            container.classList.add(
                'grid',
                'grid-cols-1',
                'sm:grid-cols-2',
                'lg:grid-cols-3',
                'xl:grid-cols-4',
                'gap-3'
            );
            container.innerHTML = pageData
                .map(function (f) {
                    return renderGridCard(f);
                })
                .join('');
        } else {
            container.classList.remove(
                'grid',
                'grid-cols-1',
                'sm:grid-cols-2',
                'lg:grid-cols-3',
                'xl:grid-cols-4',
                'gap-3'
            );
            container.classList.add('space-y-2');
            container.innerHTML = pageData
                .map(function (f) {
                    return renderListItem(f);
                })
                .join('');
        }

        var countEl = document.getElementById('attachment-count');
        if (countEl) countEl.textContent = '共 ' + filtered.length + ' 个文件';

        renderPagination(filtered.length, totalPages);
    }

    function renderPagination(total, totalPages) {
        var existing = document.getElementById('attachment-pagination');
        if (existing) existing.remove();
        if (totalPages <= 1) return;

        var container = document.getElementById('attachment-grid');
        if (!container) return;

        var pagDiv = document.createElement('div');
        pagDiv.id = 'attachment-pagination';
        pagDiv.className = 'col-span-full flex items-center justify-center gap-1 mt-4';

        var html = '';
        if (_currentPage > 1) {
            html +=
                '<button class="w-8 h-8 rounded-lg hover:bg-bg-subtle flex items-center justify-center text-xs text-fg-tertiary" onclick="changeAttachmentPage(' +
                (_currentPage - 1) +
                ')"><iconify-icon icon="mdi:chevron-left"></iconify-icon></button>';
        }
        for (var i = 1; i <= totalPages; i++) {
            if (i === _currentPage) {
                html +=
                    '<button class="w-8 h-8 rounded-lg bg-brand text-white flex items-center justify-center text-xs font-medium">' +
                    i +
                    '</button>';
            } else {
                html +=
                    '<button class="w-8 h-8 rounded-lg hover:bg-bg-subtle flex items-center justify-center text-xs text-fg-secondary" onclick="changeAttachmentPage(' +
                    i +
                    ')">' +
                    i +
                    '</button>';
            }
        }
        if (_currentPage < totalPages) {
            html +=
                '<button class="w-8 h-8 rounded-lg hover:bg-bg-subtle flex items-center justify-center text-xs text-fg-tertiary" onclick="changeAttachmentPage(' +
                (_currentPage + 1) +
                ')"><iconify-icon icon="mdi:chevron-right"></iconify-icon></button>';
        }
        pagDiv.innerHTML = html;
        container.appendChild(pagDiv);
    }

    function changeAttachmentPage(page) {
        _currentPage = page;
        renderAttachments();
    }

    function initFilters() {
        var typeSelect = document.getElementById('attachment-type-filter');
        var caseSelect = document.getElementById('attachment-case-filter');
        var searchInput = document.getElementById('attachment-search');

        if (typeSelect) {
            typeSelect.innerHTML = _typeOptions
                .map(function (t, i) {
                    return '<option value="' + (i === 0 ? 'all' : t) + '">' + t + '</option>';
                })
                .join('');
            typeSelect.addEventListener('change', function () {
                _currentTypeFilter = this.value;
                _currentPage = 1;
                renderAttachments();
            });
        }

        if (caseSelect) {
            caseSelect.innerHTML = _caseOptions
                .map(function (c, i) {
                    return '<option value="' + (i === 0 ? 'all' : c) + '">' + c + '</option>';
                })
                .join('');
            caseSelect.addEventListener('change', function () {
                _currentCaseFilter = this.value;
                _currentPage = 1;
                renderAttachments();
            });
        }

        if (searchInput) {
            searchInput.addEventListener('input', function () {
                clearTimeout(_searchTimer);
                var val = this.value;
                _searchTimer = setTimeout(function () {
                    _searchKeyword = val;
                    _currentPage = 1;
                    renderAttachments();
                }, 300);
            });
        }
    }

    function initViewToggle() {
        var gridBtn = document.getElementById('attachment-grid-view');
        var listBtn = document.getElementById('attachment-list-view');

        function setActive(activeBtn, inactiveBtn) {
            if (activeBtn) {
                activeBtn.classList.add('bg-brand', 'text-white');
                activeBtn.classList.remove('bg-white', 'text-fg-secondary', 'hover:bg-gray-50');
            }
            if (inactiveBtn) {
                inactiveBtn.classList.add('bg-white', 'text-fg-secondary', 'hover:bg-gray-50');
                inactiveBtn.classList.remove('bg-brand', 'text-white');
            }
        }

        if (gridBtn) {
            gridBtn.addEventListener('click', function () {
                _currentView = 'grid';
                setActive(gridBtn, listBtn);
                renderAttachments();
            });
        }

        if (listBtn) {
            listBtn.addEventListener('click', function () {
                _currentView = 'list';
                setActive(listBtn, gridBtn);
                renderAttachments();
            });
        }
    }

    function downloadAttachment(id) {
        var f = _attachments.find(function (x) {
            return x.id === id;
        });
        if (f && typeof showToast === 'function') {
            showToast('开始下载: ' + f.name);
        }
    }

    function deleteAttachment(id) {
        var f = _attachments.find(function (x) {
            return x.id === id;
        });
        if (!f) return;
        if (confirm('确定要删除文件 "' + f.name + '" 吗？')) {
            _attachments = _attachments.filter(function (x) {
                return x.id !== id;
            });
            renderAttachments();
            if (typeof showToast === 'function') showToast('文件已删除');
        }
    }

    function openBatchUploadModal() {
        if (typeof showToast === 'function') {
            showToast('上传功能开发中...');
        }
    }

    function initAttachmentList() {
        initFilters();
        initViewToggle();
        renderAttachments();
    }

    globalThis.initAttachmentList = initAttachmentList;
    globalThis.downloadAttachment = downloadAttachment;
    globalThis.deleteAttachment = deleteAttachment;
    globalThis.changeAttachmentPage = changeAttachmentPage;
    globalThis.openBatchUploadModal = openBatchUploadModal;
})();
