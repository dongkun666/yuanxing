(function () {
    'use strict';

    var _attachments = [
        {
            id: 1,
            name: '起诉状_张三合同纠纷.pdf',
            type: '文书文件',
            fileType: 'pdf',
            caseName: '张三合同纠纷',
            size: '2.3MB',
            date: '2026-06-10',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-gradient-to-br from-red-50 to-red-100',
            tagClass: 'file-type-tag-pdf'
        },
        {
            id: 2,
            name: '证据目录_v3.xlsx',
            type: '证据材料',
            fileType: 'excel',
            caseName: '张三合同纠纷',
            size: '256KB',
            date: '2026-06-10',
            icon: 'mdi:file-excel-outline',
            iconColor: 'text-green-600',
            iconBg: 'bg-gradient-to-br from-green-50 to-green-100',
            tagClass: 'file-type-tag-excel'
        },
        {
            id: 3,
            name: '民事起诉状_终稿.docx',
            type: '文书文件',
            fileType: 'word',
            caseName: '李四借贷纠纷',
            size: '45KB',
            date: '2026-06-09',
            icon: 'mdi:file-word-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-gradient-to-br from-brand-tint3 to-brand-tint',
            tagClass: 'file-type-tag-word'
        },
        {
            id: 4,
            name: '举证期限告知书.pdf',
            type: '文书文件',
            fileType: 'pdf',
            caseName: '张三合同纠纷',
            size: '1.2MB',
            date: '2026-06-09',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-gradient-to-br from-red-50 to-red-100',
            tagClass: 'file-type-tag-pdf'
        },
        {
            id: 5,
            name: '证据照片_现场勘验.jpg',
            type: '图片',
            fileType: 'image',
            caseName: '王五股权转让纠纷',
            size: '3.5MB',
            date: '2026-06-08',
            icon: 'mdi:file-image-outline',
            iconColor: 'text-purple-500',
            iconBg: 'bg-gradient-to-br from-purple-50 to-purple-100',
            tagClass: 'file-type-tag-image'
        },
        {
            id: 6,
            name: '开庭传票.pdf',
            type: '文书文件',
            fileType: 'pdf',
            caseName: '赵六劳动争议',
            size: '0.5MB',
            date: '2026-06-07',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-gradient-to-br from-red-50 to-red-100',
            tagClass: 'file-type-tag-pdf'
        },
        {
            id: 7,
            name: '补充材料_银行流水.docx',
            type: '证据材料',
            fileType: 'word',
            caseName: '王五股权转让纠纷',
            size: '3.5MB',
            date: '2026-06-08',
            icon: 'mdi:file-word-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-gradient-to-br from-brand-tint3 to-brand-tint',
            tagClass: 'file-type-tag-word'
        },
        {
            id: 8,
            name: '合议庭组成通知书.pdf',
            type: '文书文件',
            fileType: 'pdf',
            caseName: '孙七建设工程合同纠纷',
            size: '0.3MB',
            date: '2026-06-06',
            icon: 'mdi:file-document-outline',
            iconColor: 'text-fg-tertiary',
            iconBg: 'bg-gradient-to-br from-gray-50 to-gray-100',
            tagClass: 'file-type-tag-other'
        },
        {
            id: 9,
            name: '结案报告.pdf',
            type: '文书文件',
            fileType: 'pdf',
            caseName: '周八借款纠纷',
            size: '32KB',
            date: '2026-06-05',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-gradient-to-br from-red-50 to-red-100',
            tagClass: 'file-type-tag-pdf'
        },
        {
            id: 10,
            name: '一审判决书.pdf',
            type: '文书文件',
            fileType: 'pdf',
            caseName: '吴九房屋租赁合同纠纷',
            size: '1.1MB',
            date: '2026-06-04',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-gradient-to-br from-red-50 to-red-100',
            tagClass: 'file-type-tag-pdf'
        },
        {
            id: 11,
            name: '证据目录_更新版.xlsx',
            type: '证据材料',
            fileType: 'excel',
            caseName: '王五股权转让纠纷',
            size: '128KB',
            date: '2026-06-08',
            icon: 'mdi:file-excel-outline',
            iconColor: 'text-green-600',
            iconBg: 'bg-gradient-to-br from-green-50 to-green-100',
            tagClass: 'file-type-tag-excel'
        },
        {
            id: 12,
            name: '代理词_张三案.docx',
            type: '文书文件',
            fileType: 'word',
            caseName: '张三合同纠纷',
            size: '38KB',
            date: '2026-06-03',
            icon: 'mdi:file-word-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-gradient-to-br from-brand-tint3 to-brand-tint',
            tagClass: 'file-type-tag-word'
        },
        {
            id: 13,
            name: '顾问合同_2025.pdf',
            type: '合同文件',
            fileType: 'pdf',
            caseName: '某科技公司',
            size: '0.6MB',
            date: '2026-06-03',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-gradient-to-br from-red-50 to-red-100',
            tagClass: 'file-type-tag-pdf'
        },
        {
            id: 14,
            name: '现场勘验照片2.jpg',
            type: '图片',
            fileType: 'image',
            caseName: '王五股权转让纠纷',
            size: '2.1MB',
            date: '2026-06-07',
            icon: 'mdi:file-image-outline',
            iconColor: 'text-purple-500',
            iconBg: 'bg-gradient-to-br from-purple-50 to-purple-100',
            tagClass: 'file-type-tag-image'
        },
        {
            id: 15,
            name: '答辩状_初稿.docx',
            type: '文书文件',
            fileType: 'word',
            caseName: '李四借贷纠纷',
            size: '52KB',
            date: '2026-06-02',
            icon: 'mdi:file-word-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-gradient-to-br from-brand-tint3 to-brand-tint',
            tagClass: 'file-type-tag-word'
        },
        {
            id: 16,
            name: '和解协议书_草案.pdf',
            type: '合同文件',
            fileType: 'pdf',
            caseName: '赵六劳动争议',
            size: '0.8MB',
            date: '2026-06-01',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-gradient-to-br from-red-50 to-red-100',
            tagClass: 'file-type-tag-pdf'
        },
        {
            id: 17,
            name: '费用结算表.xlsx',
            type: '其他',
            fileType: 'excel',
            caseName: '张三合同纠纷',
            size: '96KB',
            date: '2026-05-28',
            icon: 'mdi:file-excel-outline',
            iconColor: 'text-green-600',
            iconBg: 'bg-gradient-to-br from-green-50 to-green-100',
            tagClass: 'file-type-tag-excel'
        },
        {
            id: 18,
            name: '律师工作记录.txt',
            type: '其他',
            fileType: 'other',
            caseName: '周八借款纠纷',
            size: '15KB',
            date: '2026-05-25',
            icon: 'mdi:file-document-outline',
            iconColor: 'text-fg-tertiary',
            iconBg: 'bg-gradient-to-br from-gray-50 to-gray-100',
            tagClass: 'file-type-tag-other'
        },
        {
            id: 19,
            name: '调查笔录.pdf',
            type: '证据材料',
            fileType: 'pdf',
            caseName: '孙七建设工程合同纠纷',
            size: '0.4MB',
            date: '2026-05-20',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-gradient-to-br from-red-50 to-red-100',
            tagClass: 'file-type-tag-pdf'
        },
        {
            id: 20,
            name: '合同扫描件_盖章版.png',
            type: '图片',
            fileType: 'image',
            caseName: '吴九房屋租赁合同纠纷',
            size: '5.2MB',
            date: '2026-05-15',
            icon: 'mdi:file-image-outline',
            iconColor: 'text-purple-500',
            iconBg: 'bg-gradient-to-br from-purple-50 to-purple-100',
            tagClass: 'file-type-tag-image'
        },
        {
            id: 21,
            name: '上诉状_草稿.docx',
            type: '文书文件',
            fileType: 'word',
            caseName: '吴九房屋租赁合同纠纷',
            size: '41KB',
            date: '2026-05-10',
            icon: 'mdi:file-word-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-gradient-to-br from-brand-tint3 to-brand-tint',
            tagClass: 'file-type-tag-word'
        },
        {
            id: 22,
            name: '劳动合同_模板.docx',
            type: '合同文件',
            fileType: 'word',
            caseName: '模板库',
            size: '28KB',
            date: '2026-05-08',
            icon: 'mdi:file-word-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-gradient-to-br from-brand-tint3 to-brand-tint',
            tagClass: 'file-type-tag-word'
        },
        {
            id: 23,
            name: '借条_范本.pdf',
            type: '合同文件',
            fileType: 'pdf',
            caseName: '模板库',
            size: '120KB',
            date: '2026-05-05',
            icon: 'mdi:file-pdf-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-gradient-to-br from-red-50 to-red-100',
            tagClass: 'file-type-tag-pdf'
        },
        {
            id: 24,
            name: '授权委托书_模板.docx',
            type: '文书文件',
            fileType: 'word',
            caseName: '模板库',
            size: '35KB',
            date: '2026-05-01',
            icon: 'mdi:file-word-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-gradient-to-br from-brand-tint3 to-brand-tint',
            tagClass: 'file-type-tag-word'
        }
    ];

    var _currentTypeFilter = 'all';
    var _currentCaseFilter = 'all';
    var _currentFileTypeFilter = 'all';
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
            var matchFileType = _currentFileTypeFilter === 'all' || f.fileType === _currentFileTypeFilter;
            var keyword = _searchKeyword.toLowerCase();
            var matchSearch =
                !keyword ||
                f.name.toLowerCase().indexOf(keyword) > -1 ||
                f.caseName.toLowerCase().indexOf(keyword) > -1;
            return matchType && matchCase && matchFileType && matchSearch;
        });
    }

    function getFileTypeLabel(type) {
        var labels = {
            pdf: 'PDF',
            word: 'Word',
            excel: 'Excel',
            image: '图片',
            other: '其他'
        };
        return labels[type] || '其他';
    }

    function updateFileTypeTags() {
        var tagsContainer = document.getElementById('attachment-type-tags');
        if (!tagsContainer) return;

        var typeCounts = { all: _attachments.length, pdf: 0, word: 0, excel: 0, image: 0, other: 0 };
        _attachments.forEach(function (f) {
            if (typeCounts[f.fileType] !== undefined) {
                typeCounts[f.fileType]++;
            }
        });

        var tags = tagsContainer.querySelectorAll('.file-type-tag');
        tags.forEach(function (tag) {
            var type = tag.getAttribute('data-type');
            var countEl = tag.querySelector('.file-type-count');
            if (countEl && typeCounts[type] !== undefined) {
                countEl.textContent = typeCounts[type];
            }
        });
    }

    function renderGridCard(f, index) {
        var staggerIndex = index !== undefined ? index : 0;
        return (
            '<div class="attachment-card bg-white rounded-2xl border border-bg-border p-4 hover:shadow-xl hover:shadow-brand/5 transition-all duration-300 cursor-pointer group hover:-translate-y-1" data-animate="scale-in" data-stagger-group="attachment-cards" data-stagger-index="' +
            staggerIndex +
            '" data-delay="0.05">' +
            '<div class="flex items-start justify-between mb-3">' +
            '<div class="w-12 h-12 rounded-xl ' +
            f.iconBg +
            ' flex items-center justify-center group-hover:scale-110 transition-transform duration-300 shadow-sm">' +
            '<iconify-icon class="' +
            f.iconColor +
            ' text-2xl" icon="' +
            f.icon +
            '"></iconify-icon>' +
            '</div>' +
            '<div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-[-4px] group-hover:translate-y-0">' +
            '<button class="w-7 h-7 rounded-lg bg-bg-subtle hover:bg-brand-tint text-fg-tertiary hover:text-brand flex items-center justify-center transition-all" aria-label="下载文件" onclick="event.stopPropagation(); downloadAttachment(' +
            f.id +
            ')"><iconify-icon icon="mdi:download-outline" class="text-sm"></iconify-icon></button>' +
            '<button class="w-7 h-7 rounded-lg bg-bg-subtle hover:bg-red-50 text-fg-tertiary hover:text-red-500 flex items-center justify-center transition-all" aria-label="删除文件" onclick="event.stopPropagation(); deleteAttachment(' +
            f.id +
            ')"><iconify-icon icon="mdi:trash-outline" class="text-sm"></iconify-icon></button>' +
            '</div>' +
            '</div>' +
            '<p class="text-sm font-semibold text-fg-primary truncate mb-1.5 group-hover:text-brand transition-colors" title="' +
            escapeHtml(f.name) +
            '">' +
            escapeHtml(f.name) +
            '</p>' +
            '<div class="flex items-center gap-1.5 mb-3">' +
            '<span class="file-type-badge ' +
            f.tagClass +
            '">' +
            getFileTypeLabel(f.fileType) +
            '</span>' +
            '</div>' +
            '<p class="text-xs text-fg-tertiary mb-2 flex items-center gap-1">' +
            '<iconify-icon icon="mdi:briefcase-outline" class="text-[10px]"></iconify-icon>' +
            '<span class="truncate">' +
            escapeHtml(f.caseName) +
            '</span>' +
            '</p>' +
            '<div class="flex items-center justify-between pt-2 border-t border-bg-border/50">' +
            '<span class="text-[11px] text-fg-tertiary flex items-center gap-1">' +
            '<iconify-icon icon="mdi:file-outline" class="text-[10px]"></iconify-icon>' +
            f.size +
            '</span>' +
            '<span class="text-[11px] text-fg-tertiary flex items-center gap-1">' +
            '<iconify-icon icon="mdi:clock-outline" class="text-[10px]"></iconify-icon>' +
            f.date +
            '</span>' +
            '</div>' +
            '</div>'
        );
    }

    function renderListItem(f, index) {
        var staggerIndex = index !== undefined ? index : 0;
        return (
            '<div class="attachment-list-item bg-white rounded-xl border border-bg-border p-3 md:p-4 hover:shadow-lg hover:shadow-brand/5 transition-all duration-300 cursor-pointer flex items-center gap-3 md:gap-4 group hover:-translate-y-0.5" data-animate="fade-in-up" data-stagger-group="attachment-list-items" data-stagger-index="' +
            staggerIndex +
            '" data-delay="0.03">' +
            '<div class="w-11 h-11 md:w-12 md:h-12 rounded-xl ' +
            f.iconBg +
            ' flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform duration-300 shadow-sm">' +
            '<iconify-icon class="' +
            f.iconColor +
            ' text-xl md:text-2xl" icon="' +
            f.icon +
            '"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<p class="text-sm font-semibold text-fg-primary truncate group-hover:text-brand transition-colors" title="' +
            escapeHtml(f.name) +
            '">' +
            escapeHtml(f.name) +
            '</p>' +
            '<div class="flex items-center gap-2 md:gap-3 mt-1 flex-wrap">' +
            '<span class="file-type-badge ' +
            f.tagClass +
            '">' +
            getFileTypeLabel(f.fileType) +
            '</span>' +
            '<span class="text-[11px] text-fg-tertiary flex items-center gap-1">' +
            '<iconify-icon icon="mdi:briefcase-outline" class="text-[10px]"></iconify-icon>' +
            '<span class="truncate max-w-[120px]">' +
            escapeHtml(f.caseName) +
            '</span>' +
            '</span>' +
            '<span class="text-[11px] text-fg-tertiary hidden sm:inline">' +
            f.type +
            '</span>' +
            '</div>' +
            '</div>' +
            '<div class="flex items-center gap-3 md:gap-6 flex-shrink-0">' +
            '<div class="hidden md:flex flex-col items-end gap-1">' +
            '<span class="text-[11px] text-fg-tertiary flex items-center gap-1">' +
            '<iconify-icon icon="mdi:file-outline" class="text-[10px]"></iconify-icon>' +
            f.size +
            '</span>' +
            '<span class="text-[11px] text-fg-tertiary flex items-center gap-1">' +
            '<iconify-icon icon="mdi:calendar-outline" class="text-[10px]"></iconify-icon>' +
            f.date +
            '</span>' +
            '</div>' +
            '<div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-300">' +
            '<button class="table-action-btn table-action-btn-primary" aria-label="下载文件" onclick="event.stopPropagation(); downloadAttachment(' +
            f.id +
            ')"><iconify-icon icon="mdi:download-outline" class="text-xs"></iconify-icon>下载</button>' +
            '<button class="table-action-btn table-action-btn-danger" aria-label="删除文件" onclick="event.stopPropagation(); deleteAttachment(' +
            f.id +
            ')"><iconify-icon icon="mdi:trash-outline" class="text-xs"></iconify-icon>删除</button>' +
            '</div>' +
            '</div>' +
            '</div>'
        );
    }

    function renderAttachments() {
        var container = document.getElementById('attachment-grid');
        var emptyContainer = document.getElementById('attachmentEmptyState');
        if (!container) return;

        var filtered = getFilteredAttachments();
        var totalPages = Math.ceil(filtered.length / _pageSize);
        if (_currentPage > totalPages) _currentPage = 1;
        var start = (_currentPage - 1) * _pageSize;
        var pageData = filtered.slice(start, start + _pageSize);

        if (filtered.length === 0) {
            container.classList.add('hidden');
            if (emptyContainer) {
                emptyContainer.classList.remove('hidden');
                emptyContainer.classList.add('flex', 'items-center', 'justify-center');
                Utils.createEmptyState({
                    preset: _searchKeyword ? 'no-result' : 'empty-list',
                    title: _searchKeyword ? '没有找到匹配的文件' : '暂无附件文件',
                    description: _searchKeyword
                        ? '请尝试其他搜索关键词或调整筛选条件'
                        : '还没有上传任何文件，点击上传按钮开始管理您的文件',
                    actionText: '上传文件',
                    actionHandler: openBatchUploadModal,
                    secondaryActionText: _searchKeyword ? '重置筛选' : undefined,
                    secondaryActionHandler: _searchKeyword ? resetFilters : undefined,
                    container: emptyContainer
                });
            }
            updateCount(filtered.length);
            renderPagination(filtered.length, totalPages);
            return;
        }

        if (emptyContainer) {
            emptyContainer.classList.add('hidden');
            emptyContainer.classList.remove('flex', 'items-center', 'justify-center');
        }
        container.classList.remove('hidden');

        updateCount(filtered.length);

        if (_currentView === 'grid') {
            container.classList.remove('space-y-2', 'md:space-y-3');
            container.classList.add(
                'grid',
                'grid-cols-1',
                'sm:grid-cols-2',
                'lg:grid-cols-3',
                'xl:grid-cols-4',
                'gap-3',
                'md:gap-4'
            );
            container.innerHTML = pageData
                .map(function (f, idx) {
                    return renderGridCard(f, idx);
                })
                .join('');
        } else {
            container.classList.remove(
                'grid',
                'grid-cols-1',
                'sm:grid-cols-2',
                'lg:grid-cols-3',
                'xl:grid-cols-4',
                'gap-3',
                'md:gap-4'
            );
            container.classList.add('space-y-2', 'md:space-y-3');
            container.innerHTML = pageData
                .map(function (f, idx) {
                    return renderListItem(f, idx);
                })
                .join('');
        }

        renderPagination(filtered.length, totalPages);

        setTimeout(function () {
            if (typeof Animations !== 'undefined' && Animations.initPageAnimations) {
                Animations.initPageAnimations(container);
            }
        }, 50);
    }

    function updateCount(count) {
        var countEl = document.getElementById('attachment-count');
        if (countEl) countEl.textContent = '共 ' + count + ' 个文件';
    }

    function renderPagination(total, totalPages) {
        var existing = document.getElementById('attachment-pagination');
        if (existing) existing.remove();
        if (totalPages <= 1) return;

        var container = document.getElementById('attachment-grid');
        if (!container) return;

        var pagDiv = document.createElement('div');
        pagDiv.id = 'attachment-pagination';
        pagDiv.className =
            'col-span-full flex items-center justify-center gap-1.5 mt-6 pt-4 border-t border-bg-border/50';

        var html = '';
        if (_currentPage > 1) {
            html +=
                '<button class="w-8 h-8 md:w-9 md:h-9 rounded-xl hover:bg-bg-subtle flex items-center justify-center text-xs text-fg-tertiary hover:text-brand transition-all hover:-translate-y-0.5" onclick="changeAttachmentPage(' +
                (_currentPage - 1) +
                ')"><iconify-icon icon="mdi:chevron-left"></iconify-icon></button>';
        }
        for (var i = 1; i <= totalPages; i++) {
            if (i === _currentPage) {
                html +=
                    '<button class="w-8 h-8 md:w-9 md:h-9 rounded-xl bg-gradient-to-r from-brand to-brand-hover text-white flex items-center justify-center text-xs font-semibold shadow-md shadow-brand/20">' +
                    i +
                    '</button>';
            } else {
                html +=
                    '<button class="w-8 h-8 md:w-9 md:h-9 rounded-xl hover:bg-bg-subtle flex items-center justify-center text-xs text-fg-secondary hover:text-brand transition-all hover:-translate-y-0.5" onclick="changeAttachmentPage(' +
                    i +
                    ')">' +
                    i +
                    '</button>';
            }
        }
        if (_currentPage < totalPages) {
            html +=
                '<button class="w-8 h-8 md:w-9 md:h-9 rounded-xl hover:bg-bg-subtle flex items-center justify-center text-xs text-fg-tertiary hover:text-brand transition-all hover:-translate-y-0.5" onclick="changeAttachmentPage(' +
                (_currentPage + 1) +
                ')"><iconify-icon icon="mdi:chevron-right"></iconify-icon></button>';
        }
        pagDiv.innerHTML = html;
        container.appendChild(pagDiv);
    }

    function changeAttachmentPage(page) {
        _currentPage = page;
        renderAttachments();
        var contentArea = document.querySelector('#view-attachment-list .ws-card.overflow-hidden');
        if (contentArea) {
            contentArea.scrollTop = 0;
        }
    }

    function resetFilters() {
        _searchKeyword = '';
        _currentTypeFilter = 'all';
        _currentCaseFilter = 'all';
        _currentFileTypeFilter = 'all';
        _currentPage = 1;

        var searchInput = document.getElementById('attachment-search');
        if (searchInput) searchInput.value = '';

        var typeSelect = document.getElementById('attachment-type-filter');
        if (typeSelect) typeSelect.value = 'all';

        var caseSelect = document.getElementById('attachment-case-filter');
        if (caseSelect) caseSelect.value = 'all';

        updateActiveFileTypeTag('all');

        renderAttachments();
    }

    function filterByFileType(type) {
        _currentFileTypeFilter = type;
        _currentPage = 1;
        updateActiveFileTypeTag(type);
        renderAttachments();
    }

    function updateActiveFileTypeTag(type) {
        var tags = document.querySelectorAll('#attachment-type-tags .file-type-tag');
        tags.forEach(function (tag) {
            if (tag.getAttribute('data-type') === type) {
                tag.classList.add('active');
            } else {
                tag.classList.remove('active');
            }
        });
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
                activeBtn.classList.add('bg-gradient-to-r', 'from-brand', 'to-brand-hover', 'text-white', 'shadow-sm');
                activeBtn.classList.remove('bg-white', 'text-fg-secondary', 'hover:bg-bg-subtle');
            }
            if (inactiveBtn) {
                inactiveBtn.classList.add('bg-white', 'text-fg-secondary', 'hover:bg-bg-subtle');
                inactiveBtn.classList.remove(
                    'bg-gradient-to-r',
                    'from-brand',
                    'to-brand-hover',
                    'text-white',
                    'shadow-sm'
                );
            }
        }

        if (gridBtn) {
            gridBtn.addEventListener('click', function () {
                _currentView = 'grid';
                setActive(gridBtn, listBtn);
                _currentPage = 1;
                renderAttachments();
            });
        }

        if (listBtn) {
            listBtn.addEventListener('click', function () {
                _currentView = 'list';
                setActive(listBtn, gridBtn);
                _currentPage = 1;
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

    async function deleteAttachment(id) {
        var f = _attachments.find(function (x) {
            return x.id === id;
        });
        if (!f) return;
        var confirmed = await Utils.showConfirm('确定要删除文件 "' + f.name + '" 吗？');
        if (confirmed) {
            _attachments = _attachments.filter(function (x) {
                return x.id !== id;
            });
            renderAttachments();
            updateFileTypeTags();
            Utils.showToast('success', '文件已删除');
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
        updateFileTypeTags();
        renderAttachments();
    }

    globalThis.initAttachmentList = initAttachmentList;
    globalThis.downloadAttachment = downloadAttachment;
    globalThis.deleteAttachment = deleteAttachment;
    globalThis.changeAttachmentPage = changeAttachmentPage;
    globalThis.openBatchUploadModal = openBatchUploadModal;
    globalThis.filterByFileType = filterByFileType;
})();
