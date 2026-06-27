/**
 * 模板管理模块 - 官方模板 + 个人模板
 * 包含: Tab 切换 + 视图切换 + 上传/分类/筛选/排序/预览
 * 加载: 在 script.js 之前同步加载
 */


    function switchTemplateTab(tabName, btn) {
        document.getElementById('template-tab-personal').classList.add('hidden');
        document.getElementById('template-tab-official').classList.add('hidden');
        document.getElementById('template-tab-' + tabName).classList.remove('hidden');
        document.querySelectorAll('.template-tab').forEach(function(tab) {
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
            if (c.className && (c.className.indexOf('rounded-xl') !== -1 || c.className.indexOf('template-view-card') !== -1)) {
                orphans.push(c);
            }
        }
        if (!orphans.length) return;
        orphans.forEach(function(el) {
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
        var activeTab = activeTabBtn ? (activeTabBtn.textContent.indexOf('个人') >= 0 ? 'personal' : 'official') : 'personal';
        if (activeTab === 'official') {
            viewName = 'list';
            btn = document.querySelector('.template-view-btn[data-view="list"]');
        }
        document.querySelectorAll('.template-view-btn').forEach(function(b) {
            b.classList.remove('bg-blue-50', 'text-[#165DFF]');
            b.classList.add('text-gray-500', 'hover:text-gray-700');
        });
        if (btn) {
            btn.classList.add('bg-blue-50', 'text-[#165DFF]');
            btn.classList.remove('text-gray-500', 'hover:text-gray-700');
        }
        // 切换 personal + official 两个 tab 内的视图
        // 官方模板仅保留列表视图 (产品决定: 官方模板统一用列表展示更高效), 强制 list
        ['personal', 'official'].forEach(function(tab) {
            var effectiveView = (tab === 'official') ? 'list' : viewName;
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

    function openUploadTemplateModal() {
        var modal = document.getElementById('upload-template-modal');
        if (!modal) return;
        // 同步分类下拉
        var sel = document.getElementById('upload-template-category');
        if (sel) {
            sel.innerHTML = '<option value="">请选择分类</option>';
            var cats = document.querySelectorAll('.category-item');
            cats.forEach(function(item) {
                var name = item.getAttribute('data-category');
                var opt = document.createElement('option');
                opt.value = name;
                opt.textContent = name;
                sel.appendChild(opt);
            });
        }
        // 重置表单
        var nameInput = document.getElementById('upload-template-name');
        if (nameInput) nameInput.value = '';
        var fileInput = document.getElementById('upload-template-file');
        if (fileInput) fileInput.value = '';
        var filename = document.getElementById('upload-template-filename');
        if (filename) filename.textContent = '点击或拖拽文件到此处';
        modal.classList.remove('hidden');
    }


    function closeUploadTemplateModal() {
        var modal = document.getElementById('upload-template-modal');
        if (modal) modal.classList.add('hidden');
    }


    function submitUploadTemplate() {
        var name = (document.getElementById('upload-template-name').value || '').trim();
        var category = document.getElementById('upload-template-category').value;
        var fileInput = document.getElementById('upload-template-file');
        var file = fileInput.files[0];
        if (!name) { showToast('请输入模板名称'); return; }
        if (!category) { showToast('请选择分类'); return; }
        if (!file) { showToast('请选择文件'); return; }
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
        // 类型徽章颜色 (按分类)
        var colorCls = {
            '诉状类': 'bg-blue-100 text-blue-700',
            '答辩类': 'bg-purple-100 text-purple-700',
            '合同类': 'bg-orange-100 text-orange-700',
            '申请类': 'bg-green-100 text-green-700'
        };
        var cls = colorCls[category] || 'bg-gray-100 text-gray-600';
        // 当前用户 (mock 张律师)
        var creator = '张律师';
        var now = new Date();
        var pad = function(n) { return n < 10 ? '0' + n : '' + n; };
        var timeStr = now.getFullYear() + '-' + pad(now.getMonth()+1) + '-' + pad(now.getDate()) + ' ' + pad(now.getHours()) + ':' + pad(now.getMinutes());
        // 创建新行, 插到 tbody 顶部
        var tbody = document.querySelector('#template-tab-personal tbody');
        if (!tbody) { showToast('模板列表不存在'); return; }
        var tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-50 group';
        tr.setAttribute('data-template-category', category);
        tr.innerHTML = '<td class="py-3 px-5">' +
            '<div class="flex items-center gap-2">' +
            '<iconify-icon class="text-base text-[#165DFF]" icon="mdi:file-document-outline"></iconify-icon>' +
            '<span class="text-sm text-gray-800 font-medium">' + name.replace(/</g, '&lt;') + '</span>' +
            '<span class="text-[10px] text-gray-400">(' + sizeText + ')</span>' +
            '</div>' +
            '</td>' +
            '<td class="py-3 px-5"><span class="text-[10px] ' + cls + ' px-1.5 py-0.5 rounded font-medium">' + category + '</span></td>' +
            '<td class="py-3 px-5 text-xs text-gray-600">' + creator + '</td>' +
            '<td class="py-3 px-5 text-xs text-gray-500">' + timeStr + '</td>' +
            '<td class="py-3 px-5 text-center">' +
            '<div class="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">' +
            '<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded">使用</button>' +
            '<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded">编辑</button>' +
            '<button class="text-xs text-red-500 hover:bg-red-50 px-2 py-1 rounded" onclick="deletePersonalTemplate(this)">删除</button>' +
            '</div>' +
            '</td>';
        tbody.insertBefore(tr, tbody.firstChild);
        // 同时添加到卡片视图
        var cardContainer = document.querySelector('#template-tab-personal .template-view-card');
        if (cardContainer) {
            var card = document.createElement('div');
            card.className = 'bg-white border border-[#E5E6EB] rounded-xl p-4 hover:shadow-md hover:border-[#165DFF] transition-all cursor-pointer group';
            card.setAttribute('data-template-category', category);
            card.innerHTML = '<div class="flex items-start justify-between mb-3">' +
                '<iconify-icon class="text-2xl text-[#165DFF]" icon="mdi:file-document-outline"></iconify-icon>' +
                '<span class="text-[10px] ' + cls + ' px-1.5 py-0.5 rounded font-medium">' + category + '</span>' +
                '</div>' +
                '<h4 class="text-sm font-bold text-gray-800 mb-2 group-hover:text-[#165DFF]">' + name.replace(/</g, '&lt;') + '</h4>' +
                '<div class="flex items-center justify-between text-[10px] text-gray-400 pt-3 border-t border-gray-100">' +
                '<span class="flex items-center gap-1"><iconify-icon icon="mdi:account-outline"></iconify-icon>' + creator + '</span>' +
                '<span>' + timeStr + '</span>' +
                '</div>';
            cardContainer.insertBefore(card, cardContainer.firstChild);
        }
        // 更新"全部"标签数字
        if (typeof updateAllCategoryCount === 'function') updateAllCategoryCount();
        // 更新对应分类标签数字
        var tabBtn = document.querySelector('.personal-category-tab[data-category="' + category + '"]');
        if (tabBtn) {
            var m = tabBtn.textContent.match(/\((\d+)\)/);
            if (m) tabBtn.textContent = category + ' (' + (parseInt(m[1]) + 1) + ')';
        }
        // 更新弹窗内分类数
        var item = document.querySelector('.category-item[data-category="' + category + '"]');
        if (item) {
            var countSpan = item.querySelector('span.text-\\[10px\\]');
            if (countSpan) {
                var cm = countSpan.textContent.match(/\d+/);
                if (cm) countSpan.textContent = '(' + (parseInt(cm[0]) + 1) + ' 个模板)';
            }
        }
        // 更新标题栏"共 N 个"数字
        var headerCount = document.querySelector('.template-view-header-count');
        if (headerCount) {
            var hm = headerCount.textContent.match(/\d+/);
            if (hm) headerCount.textContent = '共 ' + (parseInt(hm[0]) + 1) + ' 个';
        }
        closeUploadTemplateModal();
        showToast('模板「' + name + '」已上传');
    }

    function deletePersonalTemplate(btn) {
        if (!confirm('确定删除该模板?')) return;
        var tr = btn.closest('tr');
        if (!tr) return;
        var category = tr.getAttribute('data-template-category');
        var rowName = tr.querySelector('td:first-child span') ? tr.querySelector('td:first-child span').textContent.trim() : '';
        tr.remove();
        // 同步删除卡片视图中的对应卡片
        document.querySelectorAll('#template-tab-personal .template-view-card > div[data-template-category]').forEach(function(card) {
            var cardName = card.querySelector('h4') ? card.querySelector('h4').textContent.trim() : '';
            if (card.getAttribute('data-template-category') === category && (rowName === '' || cardName === rowName || cardName.indexOf(rowName.split(' (')[0]) === 0)) {
                card.remove();
            }
        });
        if (typeof updateAllCategoryCount === 'function') updateAllCategoryCount();
        if (category) {
            var tabBtn = document.querySelector('.personal-category-tab[data-category="' + category + '"]');
            if (tabBtn) {
                var m = tabBtn.textContent.match(/\((\d+)\)/);
                if (m) {
                    var n = Math.max(0, parseInt(m[1]) - 1);
                    tabBtn.textContent = category + ' (' + n + ')';
                }
            }
        }
        showToast('已删除');
    }

    function openCategoryManageModal() {
        var modal = document.getElementById('category-manage-modal');
        if (modal) modal.classList.remove('hidden');
    }

    function closeCategoryManageModal() {
        var modal = document.getElementById('category-manage-modal');
        if (modal) modal.classList.add('hidden');
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
        var exists = Array.from(document.querySelectorAll('.category-item')).some(function(el) {
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
        div.innerHTML = '<div class="flex items-center gap-3">' +
            '<iconify-icon class="text-base text-[#165DFF]" icon="mdi:folder-outline"></iconify-icon>' +
            '<span class="text-sm text-gray-800 font-medium">' + name + '</span>' +
            '<span class="text-[10px] text-gray-400">(0 个模板)</span>' +
            '</div>' +
            '<button class="text-xs text-red-500 hover:bg-red-50 px-2 py-1 rounded delete-category-btn" onclick="deleteCategory(\'' + name.replace(/'/g, "\\'") + '\')">' +
            '<iconify-icon icon="mdi:trash-can-outline"></iconify-icon>删除</button>';
        list.appendChild(div);
        // 同步添加到个人模板标签栏
        var tabs = document.getElementById('personal-category-tabs');
        if (tabs) {
            var tabBtn = document.createElement('button');
            tabBtn.className = 'personal-category-tab text-xs px-3 py-1 rounded-full bg-white border border-gray-200 text-gray-600 hover:border-[#165DFF] hover:text-[#165DFF]';
            tabBtn.setAttribute('data-category', name);
            tabBtn.setAttribute('onclick', "filterPersonalByCategory('" + name.replace(/'/g, "\\'") + "', this)");
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
            rows.sort(function(a, b) {
                var ta = parseTime(a), tb = parseTime(b);
                return order === 'desc' ? (tb - ta) : (ta - tb);
            });
            rows.forEach(function(r) { tbody.appendChild(r); });
        }
        // 同步排序卡片视图 (按卡片底部时间排序)
        var cardContainer = document.querySelector('#template-tab-personal .template-view-card');
        if (cardContainer) {
            var cards = Array.from(cardContainer.querySelectorAll('div[data-template-category]'));
            cards.sort(function(a, b) {
                var ta = 0, tb = 0;
                var timeSpans = a.querySelectorAll('span');
                var taStr = timeSpans.length ? timeSpans[timeSpans.length - 1].textContent.trim() : '';
                var dA = new Date(taStr.replace(/-/g, '/'));
                ta = isNaN(dA.getTime()) ? 0 : dA.getTime();
                timeSpans = b.querySelectorAll('span');
                var tbStr = timeSpans.length ? timeSpans[timeSpans.length - 1].textContent.trim() : '';
                var dB = new Date(tbStr.replace(/-/g, '/'));
                tb = isNaN(dB.getTime()) ? 0 : dB.getTime();
                return order === 'desc' ? (tb - ta) : (ta - tb);
            });
            cards.forEach(function(c) { cardContainer.appendChild(c); });
        }
        // 按钮视觉反馈
        if (btn) {
            document.querySelectorAll('.sort-btn').forEach(function(b) {
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
        document.querySelectorAll('.personal-category-tab').forEach(function(b) {
            b.classList.remove('bg-[#165DFF]', 'text-white', 'font-medium');
            b.classList.add('bg-white', 'border', 'border-gray-200', 'text-gray-600');
        });
        if (btn) {
            btn.classList.add('bg-[#165DFF]', 'text-white', 'font-medium');
            btn.classList.remove('bg-white', 'border', 'border-gray-200', 'text-gray-600');
        }
        // 筛选列表行
        document.querySelectorAll('#template-tab-personal tbody tr[data-template-category]').forEach(function(tr) {
            if (category === 'all' || tr.getAttribute('data-template-category') === category) {
                tr.style.display = '';
            } else {
                tr.style.display = 'none';
            }
        });
        // 筛选卡片
        document.querySelectorAll('#template-tab-personal .template-view-card > div[data-template-category]').forEach(function(card) {
            if (category === 'all' || card.getAttribute('data-template-category') === category) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    }


    function filterOfficialByCategory(category, btn) {
        _officialCategory = category;
        // 更新一级 active 样式
        var officialTabs = document.querySelectorAll('.official-category-tab');
        officialTabs.forEach(function(b) {
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
        document.querySelectorAll('.official-type-tab').forEach(function(b) {
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
        // 双重过滤: cat + type
        var rows = document.querySelectorAll('#template-tab-official tbody tr[data-template-category]');
        rows.forEach(function(tr) {
            var cat = tr.getAttribute('data-template-category');
            var typ = tr.getAttribute('data-template-type');
            var catMatch = _officialCategory === 'all' || cat === _officialCategory;
            var typeMatch = _officialType === 'all' || typ === _officialType;
            tr.style.display = (catMatch && typeMatch) ? '' : 'none';
        });
        var cards = document.querySelectorAll('#template-tab-official .template-view-card > div[data-template-category]');
        var visibleCount = 0;
        cards.forEach(function(card) {
            var cat = card.getAttribute('data-template-category');
            var typ = card.getAttribute('data-template-type');
            var catMatch = _officialCategory === 'all' || cat === _officialCategory;
            var typeMatch = _officialType === 'all' || typ === _officialType;
            var visible = catMatch && typeMatch;
            card.style.display = visible ? '' : 'none';
            if (visible) visibleCount++;
        });
        // 动态调整 grid 列数: 1-2 张用 2 列, 3-4 张用 3 列, 5+ 张用 4 列
        var grid = document.getElementById('official-card-grid');
        if (grid) {
            var cols = visibleCount === 0 ? 4 : visibleCount <= 2 ? 2 : visibleCount <= 4 ? 3 : 4;
            grid.style.gridTemplateColumns = 'repeat(' + cols + ', minmax(0, 1fr))';
        }
        // 0 张时显示空状态
        var emptyEl = document.getElementById('official-card-empty');
        if (emptyEl) {
            if (visibleCount === 0) {
                emptyEl.classList.remove('hidden');
                emptyEl.style.display = 'block';
            } else {
                emptyEl.classList.add('hidden');
                emptyEl.style.display = 'none';
            }
        }
        // 底部统计: 当前命中数
        var countEl = document.getElementById('official-card-count');
        if (countEl) countEl.textContent = visibleCount;
        var totalEl = document.getElementById('official-card-total');
        if (totalEl) totalEl.textContent = cards.length;
    }

    function previewOfficialTemplate(cardEl) {
        var titleEl = cardEl.querySelector('h4');
        var title = titleEl ? titleEl.textContent.trim() : '未命名模板';
        var cat = cardEl.dataset.templateCategory || '';
        var typ = cardEl.dataset.templateType || '';
        if (typeof showToast === 'function') {
            showToast('预览「' + title + '」(分类: ' + cat + ' · 类型: ' + typ + ')');
        } else {
            alert('预览「' + title + '」(分类: ' + cat + ' · 类型: ' + typ + ')');
        }
    }


    function deleteCategory(name) {
        // 检查该分类下是否还有模板 (在个人模板表格中)
        var rows = document.querySelectorAll('#template-tab-personal tbody tr');
        var hasTemplate = Array.from(rows).some(function(tr) {
            var badge = tr.querySelector('td:nth-child(2) span');
            return badge && badge.textContent.trim() === name;
        });
        if (hasTemplate) {
            showToast('该分类下还有模板, 请先删除模板');
            return;
        }
        if (!confirm('确定删除分类「' + name + '」?')) return;
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
