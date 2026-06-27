/**
 * 日程/工作台/案件动态模块
 * 包含: 日程 CRUD + 冲突检测 + 案件动态 + 工作台待办 + 庭审冲突预警
 * 加载: 在 script.js 之前同步加载
 */



        // loadView 已迁移到 router.js (2026-06-28 IIFE 拆分)
        function toggleTodo(el) {
            var cb = el.querySelector('input[type="checkbox"]');
            if (cb) {
                cb.checked = !cb.checked;
                el.querySelectorAll('.text-gray-800').forEach(function(t) {
                    t.classList.toggle('line-through');
                    t.classList.toggle('text-gray-300');
                });
                el.querySelectorAll('.text-gray-400').forEach(function(t) {
                    t.classList.toggle('line-through');
                    t.classList.toggle('text-gray-300');
                });
            }
        }

        function editSchedule(btn) {
            var item = btn.closest('[onclick*="toggleTodo"]') || btn.parentElement.parentElement;
            var timeEl = item.querySelector('.text-sm.font-bold');
            var titleEl = item.querySelector('.text-sm.font-medium');
            var descEl = item.querySelector('.text-xs.text-gray-400');
            
            if (titleEl) {
                var currentTitle = titleEl.textContent;
                var newTitle = prompt('修改日程事项：', currentTitle);
                if (newTitle && newTitle.trim() !== '') {
                    titleEl.textContent = newTitle.trim();
                }
            }
            if (descEl) {
                var currentDesc = descEl.textContent;
                var newDesc = prompt('修改案件/描述：', currentDesc);
                if (newDesc && newDesc.trim() !== '') {
                    descEl.textContent = newDesc.trim();
                }
            }
        }

        function deleteSchedule(btn) {
            if (confirm('确定删除此日程吗？')) {
                var item = btn.closest('[onclick*="toggleTodo"]');
                if (item) {
                    item.remove();
                }
            }
        }

    function switchToList(viewName, el) {
        // 更新侧边栏选中状态
        document.querySelectorAll('.sidebar-item').forEach(function(item) {
            item.classList.remove('active');
        });
        if (el) el.classList.add('active');

        var targetId = 'view-' + viewName;
        var target = document.getElementById(targetId);
        if (target && !isDevMode) {
            // 视图已存在，直接显示
            document.querySelectorAll('.view-content').forEach(function(v) {
                v.classList.add('hidden');
            });
            target.classList.remove('hidden');
            // 日程视图 hook: 渲染列表 + 应用筛选
            if (viewName === 'schedule-calendar' || viewName === 'schedule-list') {
                setTimeout(function() {
                    if (typeof renderScheduleList === 'function') renderScheduleList();
                    if (typeof initScheduleFilterToToday === 'function') initScheduleFilterToToday();
                }, 50);
            }
        } else {
            // 视图未加载 / dev 模式下强制刷新: 移除旧 target 后重新 fetch
            if (target) target.remove();
            // 视图未加载，动态加载
            loadView(viewName, function(html) {
                document.getElementById('main-content').insertAdjacentHTML('beforeend', html);
                var newTarget = document.getElementById(targetId);
                if (newTarget) {
                    document.querySelectorAll('.view-content').forEach(function(v) {
                        v.classList.add('hidden');
                    });
                    newTarget.classList.remove('hidden');
                    // 日程视图 hook: DOM 已插入, 渲染列表 + 应用筛选 + 默认筛今天
                    if (viewName === 'schedule-calendar' || viewName === 'schedule-list') {
                        setTimeout(function() {
                            if (typeof renderScheduleList === 'function') renderScheduleList();
                            if (typeof initScheduleFilterToToday === 'function') initScheduleFilterToToday();
                        }, 50);
                    }
                }
            });
        }
    }

    function openScheduleCalendar() {
        document.querySelectorAll('.view-content').forEach(function(v) {
            v.classList.add('hidden');
        });
        var calView = document.getElementById('view-schedule-calendar');
        if (calView) calView.classList.remove('hidden');
        // 标记日程冲突
        setTimeout(function() { markCalendarConflicts(); checkCourtConflicts(); }, 50);
    }

    function markCalendarConflicts() {
        var calDates = document.querySelectorAll('#view-schedule-calendar .grid.grid-cols-7 .py-3');
        calDates.forEach(function(cell) {
            // 清除旧的标记
            var oldConflict = cell.querySelector('.schedule-conflict-marker');
            if (oldConflict) oldConflict.remove();
            var oldRedDot = cell.querySelector('.schedule-conflict-red');
            if (oldRedDot) oldRedDot.remove();
            var oldCourt = cell.querySelector('.court-schedule-marker');
            if (oldCourt) oldCourt.remove();
        });

        // 按日期分组日程
        var dateGroups = {};
        AppState.scheduleData.forEach(function(item) {
            if (!dateGroups[item.date]) dateGroups[item.date] = [];
            dateGroups[item.date].push(item);
        });

        // 为开庭日程添加特殊标记（红色外边框）
        AppState.scheduleData.forEach(function(item) {
            if (item.type !== '开庭') return;
            var dayNum = parseInt(item.date.split('-')[2]);
            calDates.forEach(function(cell) {
                var cellText = cell.textContent.trim();
                var cellDay = parseInt(cellText);
                if (cellDay === dayNum) {
                    // 添加开庭标记：红色小徽章
                    if (!cell.querySelector('.court-schedule-marker')) {
                        var courtMarker = document.createElement('span');
                        courtMarker.className = 'court-schedule-marker text-[8px] text-red-600 font-medium block leading-none mt-0.5';
                        courtMarker.textContent = '开庭';
                        cell.appendChild(courtMarker);
                    }
                }
            });
        });

        // 对每组的日程检查时间重叠
        Object.keys(dateGroups).forEach(function(dateKey) {
            var items = dateGroups[dateKey];
            var hasConflict = false;
            for (var i = 0; i < items.length && !hasConflict; i++) {
                for (var j = i + 1; j < items.length && !hasConflict; j++) {
                    if (items[i].time < items[j].endTime && items[j].time < items[i].endTime) {
                        hasConflict = true;
                    }
                }
            }
            if (!hasConflict) return;

            // 对应到日历单元格：从日期字符串提取日数
            var dayNum = parseInt(dateKey.split('-')[2]);
            calDates.forEach(function(cell) {
                var cellText = cell.textContent.trim();
                var cellDay = parseInt(cellText);
                if (cellDay === dayNum) {
                    var conflictMarker = document.createElement('span');
                    conflictMarker.className = 'schedule-conflict-red w-1.5 h-1.5 rounded-full bg-red-500 inline-block mx-auto mt-0.5';
                    // 移除原有指示点（蓝色/红色），只标记冲突
                    var existingDots = cell.querySelectorAll('.rounded-full');
                    existingDots.forEach(function(d) {
                        if (!d.classList.contains('schedule-conflict-red')) {
                            d.style.display = 'none';
                        }
                    });
                    cell.appendChild(conflictMarker);
                }
            });
        });
    }


    function getTodayDate() {
        const d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
    }


    function getFutureDate(days) {
        const d = new Date();
        d.setDate(d.getDate() + days);
        return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
    }

    // ===== 工作台「今日日程」日期切换 =====
    // 把 'YYYY-MM-DD' 解析成 Date 对象 (本地时间)
    function parseDateStr(s) {
        if (!s) return new Date();
        var parts = s.split('-');
        return new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
    }
    // 把 Date 格式化成 'YYYY-MM-DD'
    function formatDate(d) {
        return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    }
    // 设置查看的日期 (任意合法日期字符串)
    function setTodayScheduleDate(dateStr) {
        if (typeof AppState === 'undefined') return;
        AppState.todayScheduleDate = dateStr;
        renderTodayScheduleDateControls();
        renderTodaySchedule();
    }
    // 前后翻页 (delta = -1 前一天 / +1 后一天)
    function shiftTodayScheduleDate(delta) {
        var cur = parseDateStr(AppState.todayScheduleDate);
        cur.setDate(cur.getDate() + delta);
        setTodayScheduleDate(formatDate(cur));
    }
    // 回到今天
    function resetTodayScheduleDate() {
        setTodayScheduleDate(getTodayDate());
    }
    // select onchange 回调
    function onTodayScheduleDateChange(field, val) {
        if (!AppState.todayScheduleDate) return;
        var parts = AppState.todayScheduleDate.split('-');
        var y = parseInt(parts[0]);
        var m = parseInt(parts[1]);
        var d = parseInt(parts[2]);
        if (field === 'year') y = parseInt(val);
        if (field === 'month') m = parseInt(val);
        if (field === 'day') d = parseInt(val);
        // 校验日期合法 (e.g. 2月30日自动回滚到月末)
        var newDate = new Date(y, m - 1, d);
        setTodayScheduleDate(formatDate(newDate));
    }
    // 渲染日期控件: 填充 3 个 select 的 options + 同步选中值
    function renderTodayScheduleDateControls() {
        var container = document.getElementById('today-schedule-date-controls');
        if (!container) return;
        var dateStr = AppState.todayScheduleDate || getTodayDate();
        var parts = dateStr.split('-');
        var y = parseInt(parts[0]);
        var m = parseInt(parts[1]);
        var d = parseInt(parts[2]);
        var todayStr = getTodayDate();
        // 年: 当前年 -2 ~ 当前年 +5 (8 年范围, 覆盖历史 + 未来计划)
        var yearSel = container.querySelector('select[data-field="year"]');
        if (yearSel) {
            var currentYear = parseInt(todayStr.split('-')[0]);
            yearSel.innerHTML = '';
            for (var i = currentYear - 2; i <= currentYear + 5; i++) {
                var opt = document.createElement('option');
                opt.value = String(i);
                opt.textContent = String(i);
                if (i === y) opt.selected = true;
                yearSel.appendChild(opt);
            }
        }
        // 月: 1-12
        var monthSel = container.querySelector('select[data-field="month"]');
        if (monthSel) {
            monthSel.innerHTML = '';
            for (var i = 1; i <= 12; i++) {
                var opt = document.createElement('option');
                opt.value = String(i);
                opt.textContent = String(i);
                if (i === m) opt.selected = true;
                monthSel.appendChild(opt);
            }
        }
        // 日: 根据年/月动态生成 (28/29/30/31)
        var daySel = container.querySelector('select[data-field="day"]');
        if (daySel) {
            daySel.innerHTML = '';
            var daysInMonth = new Date(y, m, 0).getDate();
            for (var i = 1; i <= daysInMonth; i++) {
                var opt = document.createElement('option');
                opt.value = String(i);
                opt.textContent = String(i);
                if (i === d) opt.selected = true;
                daySel.appendChild(opt);
            }
        }
        // 「回到今天」按钮: 仅在非今天时显示, 今天时隐藏
        var todayBtn = container.querySelector('[title="回到今天"]');
        if (todayBtn) {
            if (dateStr === todayStr) todayBtn.classList.add('hidden');
            else todayBtn.classList.remove('hidden');
        }
        // 标题文案: 今天时显示「今日」, 非今天时显示「YYYY年M月D日」
        var titleEl = document.querySelector('#view-workstation h4');
        if (titleEl) {
            // 找含「今日日程」的 h4
            var allH4 = document.querySelectorAll('#view-workstation h4');
            for (var i = 0; i < allH4.length; i++) {
                if (allH4[i].textContent.indexOf('日程') >= 0) {
                    var iconHtml = allH4[i].innerHTML.match(/<iconify-icon[^>]*><\/iconify-icon>/);
                    var iconStr = iconHtml ? iconHtml[0] : '';
                    var newLabel = dateStr === todayStr ? '今日日程' : formatDateLabel(dateStr) + ' 日程';
                    // 保留 icon + badge
                    var badgeHtml = '';
                    var badge = allH4[i].querySelector('#today-schedule-badge');
                    if (badge) badgeHtml = badge.outerHTML;
                    allH4[i].innerHTML = iconStr + ' ' + newLabel + ' ' + badgeHtml;
                    break;
                }
            }
        }
    }
    // 中文日期标签: 2026-06-28 → 2026年6月28日
    function formatDateLabel(dateStr) {
        var parts = dateStr.split('-');
        return parts[0] + '年' + parseInt(parts[1]) + '月' + parseInt(parts[2]) + '日';
    }


    function checkScheduleConflict(date, time) {
        if (!date || !time) return null;
        const conflicts = AppState.scheduleData.filter(item => {
            if (item.date !== date) return false;
            if (time >= item.time && time < item.endTime) return true;
            return false;
        });
        return conflicts.length > 0 ? conflicts : null;
    }


    function checkAndShowConflict() {
        const date = document.getElementById('sched-date').value;
        const time = document.getElementById('sched-time').value;
        const warningEl = document.getElementById('schedule-conflict-warning');
        const detailEl = document.getElementById('schedule-conflict-detail');
        if (!warningEl || !detailEl) return;
        const conflicts = checkScheduleConflict(date, time);
        if (conflicts && conflicts.length > 0) {
            detailEl.innerHTML = conflicts.map(c =>
                '• <span class="font-medium">' + c.title + '</span><br><span class="text-amber-600">' + c.time + ' - ' + c.endTime + '</span>'
            ).join('<br>');
            warningEl.classList.remove('hidden');
        } else {
            warningEl.classList.add('hidden');
        }
    }


    function bindScheduleConflictCheck() {
        const dateInput = document.getElementById('sched-date');
        const timeInput = document.getElementById('sched-time');
        if (dateInput) dateInput.addEventListener('change', checkAndShowConflict);
        if (timeInput) timeInput.addEventListener('change', checkAndShowConflict);
    }

    function openScheduleModal(scheduleId) {
        _editingScheduleId = scheduleId || null;
        const today = new Date().toISOString().split('T')[0];
        const titleEl = document.getElementById('schedule-modal-title');
        // 标题动态切换
        if (titleEl) titleEl.textContent = _editingScheduleId ? '修改日程' : '新建日程';

        if (_editingScheduleId) {
            // 编辑模式: 预填表单
            var item = AppState.scheduleData.find(function(s) { return s.id === _editingScheduleId; });
            if (item) {
                document.getElementById('sched-title').value = item.title || '';
                document.getElementById('sched-date').value = item.date || today;
                document.getElementById('sched-time').value = item.time || '09:00';
                document.getElementById('sched-note').value = item.location || '';
                var caseSel = document.getElementById('sched-case');
                if (caseSel) caseSel.value = item.caseId || '';
                // 单选 type
                var typeRadios = document.querySelectorAll('input[name="sched-type"]');
                typeRadios.forEach(function(r) { r.checked = (r.value === (item.type || '其他')); });
                // 单选 remind
                var remindRadios = document.querySelectorAll('input[name="sched-remind"]');
                remindRadios.forEach(function(r) { r.checked = (r.value === String(item.remind || '60')); });
            }
        } else {
            // 新建模式: 默认今天 + 09:00 + 清空
            document.getElementById('sched-date').value = today;
            document.getElementById('sched-time').value = '09:00';
            document.getElementById('sched-title').value = '';
            document.getElementById('sched-note').value = '';
            // 默认单选
            var defaultType = document.querySelector('input[name="sched-type"][value="开庭"]');
            if (defaultType) defaultType.checked = true;
            var defaultRemind = document.querySelector('input[name="sched-remind"][value="60"]');
            if (defaultRemind) defaultRemind.checked = true;
        }

        document.getElementById('schedule-modal').classList.remove('hidden');
        // 检查当天冲突并绑定监听
        setTimeout(function() {
            checkAndShowConflict();
            bindScheduleConflictCheck();
        }, 100);
    }

    // 当前正在编辑的日程 id (null = 新建模式)
    var _editingScheduleId = null;

    function closeScheduleModal() {
        document.getElementById('schedule-modal').classList.add('hidden');
        _editingScheduleId = null;
    }


    function saveSchedule() {
        const title = document.getElementById('sched-title').value.trim();
        const date = document.getElementById('sched-date').value;
        const time = document.getElementById('sched-time').value;
        if (!title) {
            showToast('请输入日程标题');
            return;
        }
        if (!date) {
            showToast('请选择日期');
            return;
        }
        if (!time) {
            showToast('请选择时间');
            return;
        }
        const type = document.querySelector('input[name="sched-type"]:checked')?.value || '其他';
        const caseSelect = document.getElementById('sched-case');
        const caseVal = caseSelect ? caseSelect.value : '';
        const caseName = caseSelect && caseSelect.selectedIndex >= 0 ? (caseSelect.options[caseSelect.selectedIndex].text || '') : '';
        const note = document.getElementById('sched-note').value.trim();
        const remind = document.querySelector('input[name="sched-remind"]:checked')?.value || '60';

        // 计算结束时间 (默认 +1 小时)
        const endHour = parseInt(time.split(':')[0]) + 1;
        const endTime = String(endHour).padStart(2,'0') + ':' + time.split(':')[1];

        if (_editingScheduleId) {
            // 修改模式: 直接更新现有项 (跳过冲突检测 - 用户已在编辑自己)
            var idx = AppState.scheduleData.findIndex(function(s) { return s.id === _editingScheduleId; });
            if (idx > -1) {
                AppState.scheduleData[idx] = Object.assign({}, AppState.scheduleData[idx], {
                    title: title,
                    date: date,
                    time: time,
                    endTime: endTime,
                    type: type,
                    caseId: caseVal,
                    caseName: caseName,
                    location: note || '',
                    note: note,
                    remind: remind
                });
                persistSchedule();
                closeScheduleModal();
                showToast('日程已更新');
                renderScheduleList();
                if (typeof filterScheduleByDate === 'function') filterScheduleByDate();
                if (typeof updateTodayScheduleBadge === 'function') updateTodayScheduleBadge();
                if (typeof renderTodaySchedule === 'function') renderTodaySchedule();
            }
            return;
        }

        // 新建模式: 冲突检测
        const conflicts = checkScheduleConflict(date, time);
        if (conflicts && conflicts.length > 0) {
            // 暂存待保存日程
            pendingSchedule = {
                id: Date.now(),
                title: title,
                date: date,
                time: time,
                endTime: endTime,
                type: type,
                caseId: caseVal,
                caseName: caseName,
                location: note || '',
                note: note,
                remind: remind
            };
            showConflictResolve(conflicts);
            return; // 等待用户选择
        }

        // 新建模式: push 到日程数据
        const newItem = {
            id: Date.now(),
            title: title,
            date: date,
            time: time,
            endTime: endTime,
            type: type,
            caseId: caseVal,
            caseName: caseName,
            location: note || '',
            note: note,
            remind: remind
        };
        AppState.scheduleData.push(newItem);
        persistSchedule();
        closeScheduleModal();
        showToast('日程已创建');
        renderScheduleList();
        if (typeof filterScheduleByDate === 'function') filterScheduleByDate();
        if (typeof updateTodayScheduleBadge === 'function') updateTodayScheduleBadge();
        if (typeof renderTodaySchedule === 'function') renderTodaySchedule();
    }

    // 删除日程 (从卡片按钮触发)
    function deleteScheduleItem(id) {
        var item = AppState.scheduleData.find(function(s) { return s.id === id; });
        if (!item) return;
        if (!confirm('确定删除「' + item.title + '」吗？')) return;
        var idx = AppState.scheduleData.findIndex(function(s) { return s.id === id; });
        if (idx > -1) AppState.scheduleData.splice(idx, 1);
        persistSchedule();
        showToast('日程已删除');
        renderScheduleList();
        if (typeof filterScheduleByDate === 'function') filterScheduleByDate();
        if (typeof updateTodayScheduleBadge === 'function') updateTodayScheduleBadge();
        if (typeof renderTodaySchedule === 'function') renderTodaySchedule();
    }

    // 切换日程完成状态 (复选框): 完成 → 未完成 反之亦然
    // 状态: completed = true / false
    // 联动: persistSchedule + renderScheduleList + renderTodaySchedule + badge
    function toggleScheduleComplete(id) {
        var item = AppState.scheduleData.find(function(s) { return s.id === id; });
        if (!item) return;
        item.completed = !item.completed;
        persistSchedule();
        renderScheduleList();
        if (typeof renderTodaySchedule === 'function') renderTodaySchedule();
        if (typeof updateTodayScheduleBadge === 'function') updateTodayScheduleBadge();
        // 详情页如果开着也刷新 (避免状态不一致)
        if (typeof currentDetailScheduleId !== 'undefined' && currentDetailScheduleId === id && typeof openScheduleDetail === 'function') {
            openScheduleDetail(id);
        }
        showToast(item.completed ? '已标记为完成' : '已取消完成');
    }

    // 渲染日程"完成"复选框 (公共片段, renderScheduleList + renderTodaySchedule 共用)
    // 参数: s = schedule item
    // 返回: HTML 字符串 (button 模拟 checkbox, 避免 input click 与 row click 冲突)
    function renderScheduleCheckbox(s) {
        var done = !!s.completed;
        var btnCls = done
            ? 'bg-brand border-brand text-white'
            : 'border-bg-border hover:border-brand bg-white';
        var icon = done
            ? '<iconify-icon icon="mdi:check-bold" class="text-xs"></iconify-icon>'
            : '';
        return '<button type="button" onclick="event.stopPropagation(); toggleScheduleComplete(' + s.id + ')" ' +
               'class="w-4 h-4 rounded border-2 ' + btnCls + ' flex items-center justify-center transition-colors flex-none" ' +
               'title="' + (done ? '已完成 (点击取消)' : '标记为完成') + '">' + icon + '</button>';
    }

    // 三态过滤器 predicate
    // scope: 'today' = 工作台「今日日程」, 'list' = 日程管理
    // filter 值: 'all' (全部) | 'pending' (待办/未完成) | 'completed' (已完成)
    // 默认: today='pending' (聚焦今日待办), list='all'
    function getScheduleFilterPredicate(scope) {
        var f = scope === 'today' ? (AppState.scheduleFilterToday || 'pending') : (AppState.scheduleFilterList || 'all');
        if (f === 'pending') return function(s) { return !s.completed; };
        if (f === 'completed') return function(s) { return !!s.completed; };
        return function() { return true; }; // 'all'
    }

    // 切换三态过滤 (供工作台/日程管理的三态按钮调用)
    // scope: 'today' | 'list'
    // value: 'all' | 'pending' | 'completed'
    function setScheduleFilter(scope, value) {
        if (scope === 'today') AppState.scheduleFilterToday = value;
        else AppState.scheduleFilterList = value;
        // 刷新两个视图 (联动)
        if (typeof renderScheduleList === 'function') renderScheduleList();
        if (typeof renderTodaySchedule === 'function') renderTodaySchedule();
        if (typeof renderScheduleFilterTabs === 'function') renderScheduleFilterTabs();
    }

    // 渲染三态按钮组 (工作台头部 + 日程管理头部公用)
    // containerId: 'today-schedule-filter' | 'schedule-filter-tabs'
    // scope: 'today' | 'list'
    function renderScheduleFilterTabs(containerId, scope) {
        var c = document.getElementById(containerId);
        if (!c) return;
        var cur = scope === 'today' ? (AppState.scheduleFilterToday || 'pending') : (AppState.scheduleFilterList || 'all');
        var opts = [
            { value: 'all', label: '全部' },
            { value: 'pending', label: '待办' },
            { value: 'completed', label: '已完成' }
        ];
        var htmlStr = '';
        opts.forEach(function(o) {
            var active = cur === o.value;
            var cls = active
                ? 'bg-brand text-white'
                : 'bg-bg-subtle text-fg-secondary hover:bg-bg';
            htmlStr += '<button type="button" onclick="setScheduleFilter(\'' + scope + '\', \'' + o.value + '\')" class="text-[10px] px-2 py-0.5 rounded-full ' + cls + ' transition-colors font-medium">' + o.label + '</button>';
        });
        c.innerHTML = htmlStr;
    }

    // localStorage 持久化
    function persistSchedule() {
        try { localStorage.setItem('lexprime_schedule_data', JSON.stringify(AppState.scheduleData)); } catch (e) { console.warn('持久化日程失败:', e); }
    }

    // 渲染庭审日程列表 (calendar 视图的"本月庭审安排")
    // 按日期升序, 同日按时间升序, 当前日期打"今天"标
    function renderScheduleList() {
        var container = document.getElementById('schedule-list');
        if (!container) return;
        var empty = document.getElementById('schedule-empty');
        var countEl = document.getElementById('schedule-count');

        // 排序: 未完成优先 (completed 沉底), 同状态按 date+time 升序
        var sorted = AppState.scheduleData
            .filter(getScheduleFilterPredicate('list'))
            .sort(function(a, b) {
                if (!!a.completed !== !!b.completed) return a.completed ? 1 : -1;
                var ka = (a.date || '') + ' ' + (a.time || '');
                var kb = (b.date || '') + ' ' + (b.time || '');
                return ka < kb ? -1 : ka > kb ? 1 : 0;
            });

        if (countEl) countEl.textContent = '共 ' + sorted.length + ' 项';

        if (sorted.length === 0) {
            container.innerHTML = '';
            if (empty) empty.classList.remove('hidden');
            return;
        }
        if (empty) empty.classList.add('hidden');

        var today = getTodayDate();
        var colorMap = {
            '开庭': { border: 'border-l-purple-500', tagBg: 'bg-purple-100', tagText: 'text-purple-700' },
            '会议': { border: 'border-l-blue-500', tagBg: 'bg-blue-100', tagText: 'text-blue-700' },
            '待办': { border: 'border-l-green-500', tagBg: 'bg-green-100', tagText: 'text-green-700' },
            '其他': { border: 'border-l-amber-500', tagBg: 'bg-amber-100', tagText: 'text-amber-700' }
        };

        var htmlStr = '';
        sorted.forEach(function(s) {
            var c = colorMap[s.type] || colorMap['其他'];
            var dateObj = s.date ? new Date(s.date + 'T00:00:00') : null;
            var day = dateObj ? dateObj.getDate() : '?';
            var weekdays = ['周日','周一','周二','周三','周四','周五','周六'];
            var weekday = dateObj ? weekdays[dateObj.getDay()] : '';
            var isToday = s.date === today;
            var done = !!s.completed;
            var titleCls = done ? 'text-sm font-medium text-fg-tertiary line-through' : 'text-sm font-medium text-fg-primary';

            htmlStr += '<div class="group ' + (done ? 'bg-bg-subtle ' : 'bg-white ') + 'rounded-xl border border-bg-border p-4 hover:shadow-sm transition-shadow border-l-4 cursor-pointer ' + c.border + '" data-date="' + (s.date || '') + '" data-year="' + (dateObj ? dateObj.getFullYear() : '') + '" data-month="' + (dateObj ? String(dateObj.getMonth()+1).padStart(2,'0') : '') + '" data-day="' + (dateObj ? String(dateObj.getDate()).padStart(2,'0') : '') + '" data-schedule-id="' + s.id + '" onclick="openScheduleDetail(' + s.id + ')">' +
                '<div class="flex items-start gap-4">' +
                    '<div class="flex-shrink-0 flex items-center justify-center pt-1">' +
                        renderScheduleCheckbox(s) +
                    '</div>' +
                    '<div class="flex-shrink-0 text-center w-12">' +
                        '<div class="text-lg font-bold ' + c.tagText + '">' + day + '</div>' +
                        '<div class="text-[10px] text-fg-tertiary">' + weekday + '</div>' +
                    '</div>' +
                    '<div class="flex-1 min-w-0">' +
                        '<div class="flex items-center gap-2 mb-1 flex-wrap">' +
                            '<span class="text-[10px] px-1.5 py-0.5 rounded-full ' + c.tagBg + ' ' + c.tagText + ' font-medium">' + (s.type || '其他') + '</span>' +
                            '<span class="' + titleCls + '">' + escapeHtml(s.title || '') + '</span>' +
                            (isToday ? '<span class="text-[10px] px-1.5 py-0.5 rounded-full bg-urgent text-white font-medium">今天</span>' : '') +
                        '</div>' +
                        '<div class="text-xs text-fg-tertiary flex items-center gap-3 flex-wrap">' +
                            '<span><iconify-icon class="text-xs" icon="mdi:clock-time-four-outline"></iconify-icon> ' + (s.time || '') + (s.endTime ? ' - ' + s.endTime : '') + '</span>' +
                            (s.location ? '<span><iconify-icon class="text-xs" icon="mdi:map-marker-outline"></iconify-icon> ' + escapeHtml(s.location) + '</span>' : '') +
                        '</div>' +
                    '</div>' +
                    '<div class="flex-shrink-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">' +
                        '<button class="text-sm text-fg-secondary hover:bg-bg-subtle px-2.5 py-1 rounded flex items-center gap-1" onclick="event.stopPropagation(); openScheduleDetail(' + s.id + ')" title="详情">' +
                            '<iconify-icon icon="mdi:eye-outline"></iconify-icon>' +
                            '<span>详情</span>' +
                        '</button>' +
                        '<button class="text-sm text-brand hover:bg-brand-tint3 px-2.5 py-1 rounded flex items-center gap-1" onclick="event.stopPropagation(); openScheduleModal(' + s.id + ')" title="修改">' +
                            '<iconify-icon icon="mdi:pencil-outline"></iconify-icon>' +
                            '<span>修改</span>' +
                        '</button>' +
                        '<button class="text-sm text-red-500 hover:bg-red-50 px-2.5 py-1 rounded flex items-center gap-1" onclick="event.stopPropagation(); deleteScheduleItem(' + s.id + ')" title="删除">' +
                            '<iconify-icon icon="mdi:trash-can-outline"></iconify-icon>' +
                            '<span>删除</span>' +
                        '</button>' +
                    '</div>' +
                '</div>' +
            '</div>';
        });
        container.innerHTML = htmlStr;

        // 刷新三态按钮
        if (typeof renderScheduleFilterTabs === 'function') renderScheduleFilterTabs('schedule-filter-tabs', 'list');
    }

    function escapeHtml(str) {
        return String(str).replace(/[&<>"']/g, function(m) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
        });
    }

    // 日期格式化为中文: "2026-06-27" → "2026年6月27日 周六"
    function formatDateCN(dateStr) {
        if (!dateStr) return '';
        var d = new Date(dateStr + 'T00:00:00');
        if (isNaN(d.getTime())) return dateStr;
        var weekdays = ['周日','周一','周二','周三','周四','周五','周六'];
        return d.getFullYear() + '年' + (d.getMonth() + 1) + '月' + d.getDate() + '日 ' + weekdays[d.getDay()];
    }

    // ===== 详情页 CTA 按钮 =====

    // 跳到关联案件详情
    function goToCaseFromDetail() {
        if (!currentDetailScheduleId) return;
        var item = AppState.scheduleData.find(function(s) { return s.id === currentDetailScheduleId; });
        if (!item || !item.caseId) {
            showToast('该日程未关联案件');
            return;
        }
        closeScheduleDetail();
        switchView('case');
        // 触发案件详情
        setTimeout(function() {
            if (typeof openCaseDetail === 'function') {
                openCaseDetail(item.caseId);
            }
        }, 100);
    }

    // 打开案件分析 (从详情页)
    function openCaseAnalysisFromDetail() {
        if (!currentDetailScheduleId) return;
        var item = AppState.scheduleData.find(function(s) { return s.id === currentDetailScheduleId; });
        if (!item || !item.caseId) {
            showToast('该日程未关联案件, 无案件分析');
            return;
        }
        closeScheduleDetail();
        if (typeof openCaseAnalysis === 'function') openCaseAnalysis(item.caseId);
        else switchView('case-analysis');
    }

    // 生成准备清单 (mock 演示)
    function generatePrepChecklistFromDetail() {
        if (!currentDetailScheduleId) return;
        var item = AppState.scheduleData.find(function(s) { return s.id === currentDetailScheduleId; });
        if (!item) return;
        var checklist = [
            '✓ 携带律师执业证、身份证',
            '✓ 准备起诉状/答辩状副本',
            '✓ 整理证据材料原件及复印件',
            '✓ 提前 30 分钟到达 ' + (item.location || '庭审地点'),
            '✓ 确认着装 (律师袍或正装)',
            '✓ 庭审前再次核实案号 ' + (item.caseName || '')
        ];
        if (typeof showToast === 'function') showToast('准备清单已生成 (' + checklist.length + ' 项)');
        console.log('[庭审准备清单]', checklist.join('\n'));
    }

    // 打开 AI 庭审助手 (mock)
    function openAITrialCoach() {
        if (typeof showToast === 'function') showToast('AI 庭审助手功能开发中...');
    }

    // 复制日程
    function duplicateSchedule() {
        if (!currentDetailScheduleId) return;
        var item = AppState.scheduleData.find(function(s) { return s.id === currentDetailScheduleId; });
        if (!item) return;
        var copy = Object.assign({}, item, {
            id: Date.now(),
            title: item.title + ' (副本)'
        });
        AppState.scheduleData.push(copy);
        persistSchedule();
        showToast('日程已复制');
        renderScheduleList();
        if (typeof filterScheduleByDate === 'function') filterScheduleByDate();
        if (typeof renderTodaySchedule === 'function') renderTodaySchedule();
    }

    function updateTodayScheduleBadge() {
        const badge = document.getElementById('today-schedule-badge');
        if (!badge) return;
        const today = getTodayDate();
        const todayItems = AppState.scheduleData.filter(s => s.date === today);
        const total = todayItems.length;
        const pending = todayItems.filter(s => !s.completed).length;
        // 优先显示未完成数; 都完成了显示总条数 (badge 用 success 色调)
        if (pending > 0 && pending < total) {
            badge.textContent = pending;
            badge.classList.remove('bg-brand');
            badge.classList.add('bg-urgent');
        } else if (pending === 0 && total > 0) {
            badge.textContent = total;
            badge.classList.remove('bg-brand', 'bg-urgent');
            badge.classList.add('bg-success');
            badge.title = '今日日程已全部完成';
        } else {
            badge.textContent = total;
            badge.classList.remove('bg-urgent', 'bg-success');
            badge.classList.add('bg-brand');
        }
    }

    // 渲染工作台「今日日程」列表 (联动日程管理: 同一份 AppState.scheduleData)
    // 排序: 按 time 升序
    // 行为: 点击行 → 打开详情; [修改] → 编辑; [删除] → 删除
    // 限制: 工作台最多展示 5 条; 超出显示「还有 N 条 → 查看全部」
    function renderTodaySchedule() {
        var container = document.getElementById('today-schedule-list');
        var emptyEl = document.getElementById('today-schedule-empty');
        if (!container) return;
        var today = AppState.todayScheduleDate || getTodayDate();
        // 同步日期控件状态 (options + 选中值) — 防止 controls 在初始时未渲染
        renderTodayScheduleDateControls();
        var items = AppState.scheduleData
            .filter(function(s) { return s.date === today; })
            .filter(getScheduleFilterPredicate('today'))
            .sort(function(a, b) {
                // 未完成优先 (completed 沉底), 同状态按 time 升序
                if (!!a.completed !== !!b.completed) return a.completed ? 1 : -1;
                var ka = (a.time || '99:99');
                var kb = (b.time || '99:99');
                return ka < kb ? -1 : ka > kb ? 1 : 0;
            });
        updateTodayScheduleBadge();
        if (items.length === 0) {
            container.innerHTML = '';
            if (emptyEl) {
                // 空态文案: 根据 filter 智能提示 (避免「日程不见了」的误判)
                var f = AppState.scheduleFilterToday || 'pending';
                var todayAll = AppState.scheduleData.filter(function(s) { return s.date === today; });
                var todayDone = todayAll.filter(function(s) { return s.completed; }).length;
                if (f === 'pending' && todayDone > 0) {
                    // 用户在「待办」视图, 但今天所有日程都已完成 → 引导切到「已完成」看历史
                    emptyEl.innerHTML =
                        '<iconify-icon icon="mdi:check-circle" class="text-3xl mb-2 text-success"></iconify-icon>' +
                        '<p class="text-xs">今日待办已全部完成 🎉</p>' +
                        '<p class="text-[10px] text-fg-tertiary mt-0.5 mb-2">' + todayDone + ' 项已完成</p>' +
                        '<div class="flex items-center gap-1.5">' +
                            '<button onclick="setScheduleFilter(\'today\', \'completed\')" class="px-2.5 py-1 text-[10px] text-brand bg-brand-tint3 hover:bg-brand-tint rounded transition-colors">查看已完成</button>' +
                            '<button onclick="setScheduleFilter(\'today\', \'all\')" class="px-2.5 py-1 text-[10px] text-fg-secondary bg-bg-subtle hover:bg-bg rounded transition-colors">查看全部</button>' +
                        '</div>';
                } else if (f === 'completed' && todayDone === 0) {
                    emptyEl.innerHTML =
                        '<iconify-icon icon="mdi:calendar-check-outline" class="text-3xl mb-2 text-fg-tertiary"></iconify-icon>' +
                        '<p class="text-xs">今日还没有已完成日程</p>' +
                        '<button onclick="setScheduleFilter(\'today\', \'pending\')" class="mt-2 px-2.5 py-1 text-[10px] text-brand bg-brand-tint3 hover:bg-brand-tint rounded transition-colors">查看待办</button>';
                } else {
                    // 默认空态 (没有任何日程) — 恢复新建日程按钮
                    emptyEl.innerHTML =
                        '<iconify-icon icon="mdi:calendar-check-outline" class="text-3xl mb-2 text-fg-tertiary"></iconify-icon>' +
                        '<p class="text-xs">今日没有日程</p>' +
                        '<button onclick="openScheduleModal()" class="mt-3 px-3 py-1 text-xs text-brand bg-brand-tint3 hover:bg-brand-tint rounded transition-colors flex items-center gap-1">' +
                            '<iconify-icon icon="mdi:plus"></iconify-icon>' +
                            '<span>新建日程</span>' +
                        '</button>';
                }
                emptyEl.classList.remove('hidden');
            }
            return;
        }
        if (emptyEl) emptyEl.classList.add('hidden');

        var colorMap = {
            '开庭': { text: 'text-purple-600', bg: 'bg-purple-50', icon: 'mdi:gavel', iconColor: 'text-purple-500' },
            '会议': { text: 'text-blue-600', bg: 'bg-blue-50', icon: 'mdi:account-group-outline', iconColor: 'text-blue-500' },
            '待办': { text: 'text-green-600', bg: 'bg-green-50', icon: 'mdi:check-circle-outline', iconColor: 'text-green-500' },
            '其他': { text: 'text-amber-600', bg: 'bg-amber-50', icon: 'mdi:calendar-blank-outline', iconColor: 'text-amber-500' }
        };

        // 截断: 工作台最多 5 条
        var MAX_DISPLAY = 5;
        var displayItems = items.slice(0, MAX_DISPLAY);
        var overflowCount = items.length - displayItems.length;

        var htmlStr = '';
        displayItems.forEach(function(s) {
            var c = colorMap[s.type] || colorMap['其他'];
            var isPast = false;
            if (s.time) {
                var endTime = s.endTime || (parseInt(s.time.split(':')[0]) + 1) + ':' + s.time.split(':')[1];
                var now = new Date();
                var end = new Date(today + 'T' + endTime + ':00');
                isPast = now > end;
            }
            var done = !!s.completed;
            var titleCls = done ? 'text-sm font-medium text-fg-tertiary line-through truncate' : 'text-sm font-medium text-fg-primary truncate';
            htmlStr += '<div class="group flex items-start gap-2 p-2 rounded-lg ' + (done ? 'bg-bg-subtle ' : '') + 'hover:bg-brand-tint3 transition-colors cursor-pointer" data-schedule-id="' + s.id + '">' +
                '<div class="flex-none pt-0.5">' +
                    renderScheduleCheckbox(s) +
                '</div>' +
                '<div class="w-12 flex-none text-right">' +
                    '<span class="text-sm font-bold ' + (isPast ? 'text-fg-tertiary line-through' : c.text) + '">' + (s.time || '--:--') + '</span>' +
                '</div>' +
                '<div class="flex-1 min-w-0">' +
                    '<p class="' + titleCls + '">' + escapeHtml(s.title || '') + '</p>' +
                    '<p class="text-xs text-fg-tertiary truncate">' + escapeHtml(s.location || s.caseName || s.type || '') + '</p>' +
                '</div>' +
                '<div class="flex-none ' + c.iconColor + '">' +
                    '<iconify-icon icon="' + c.icon + '"></iconify-icon>' +
                '</div>' +
                '<div class="flex-none flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity ml-1">' +
                    '<button class="w-6 h-6 rounded hover:bg-brand-tint flex items-center justify-center text-fg-tertiary hover:text-brand transition-colors" onclick="event.stopPropagation(); openScheduleDetail(' + s.id + ')" title="详情">' +
                        '<iconify-icon class="text-sm" icon="mdi:eye-outline"></iconify-icon>' +
                    '</button>' +
                    '<button class="w-6 h-6 rounded hover:bg-brand-tint flex items-center justify-center text-fg-tertiary hover:text-brand transition-colors" onclick="event.stopPropagation(); openScheduleModal(' + s.id + ')" title="修改">' +
                        '<iconify-icon class="text-sm" icon="mdi:pencil"></iconify-icon>' +
                    '</button>' +
                    '<button class="w-6 h-6 rounded hover:bg-red-100 flex items-center justify-center text-fg-tertiary hover:text-red-500 transition-colors" onclick="event.stopPropagation(); deleteScheduleItem(' + s.id + ')" title="删除">' +
                        '<iconify-icon class="text-sm" icon="mdi:close"></iconify-icon>' +
                    '</button>' +
                '</div>' +
            '</div>';
        });

        // 「还有 N 条 → 查看全部」
        if (overflowCount > 0) {
            htmlStr += '<div class="text-center pt-2 border-t border-bg-border mt-1">' +
                '<button class="text-xs text-brand hover:text-brand-hover font-medium inline-flex items-center gap-1" onclick="switchView(\'schedule-calendar\')">' +
                    '还有 ' + overflowCount + ' 条 · 查看全部' +
                    '<iconify-icon icon="mdi:chevron-right" class="text-sm"></iconify-icon>' +
                '</button>' +
            '</div>';
        }

        container.innerHTML = htmlStr;

        // 绑定行点击 → 打开详情
        container.querySelectorAll('[data-schedule-id]').forEach(function(row) {
            row.addEventListener('click', function() {
                var id = Number(row.getAttribute('data-schedule-id'));
                if (typeof openScheduleDetail === 'function') openScheduleDetail(id);
            });
        });

        // 刷新三态按钮
        if (typeof renderScheduleFilterTabs === 'function') renderScheduleFilterTabs('today-schedule-filter', 'today');
    }

    function filterSchedule(type, btn) {
        document.querySelectorAll('#view-schedule-list .filter-btn').forEach(b => {
            b.className = 'filter-btn text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200';
        });
        btn.className = 'filter-btn text-xs px-3 py-1.5 rounded-full bg-[#165DFF] text-white';
        document.querySelectorAll('#view-schedule-list .arco-card').forEach(card => {
            try {
                var tagEl = card.querySelector('.rounded-full:first-child');
                var tag = tagEl ? tagEl.textContent.trim() : '';
                if (type === 'all' || tag === type) {
                    card.classList.remove('hidden');
                } else {
                    card.classList.add('hidden');
                }
            } catch(e) {
                // 防御性：如果提取失败，跳过该卡片
                card.classList.remove('hidden');
            }
        });
    }

    function filterAttention(type, btn) {
        document.querySelectorAll('#view-attention-list .att-filter-btn').forEach(b => {
            b.className = 'att-filter-btn text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200';
        });
        btn.className = 'att-filter-btn text-xs px-3 py-1.5 rounded-full bg-[#165DFF] text-white';
        document.querySelectorAll('#view-attention-list .bg-white.rounded-xl').forEach(card => {
            var tagEl = card.querySelector('.rounded-full:first-child');
            var tag = tagEl ? tagEl.textContent.trim() : '';
            if (type === 'all' || tag === type) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
    }

    function filterDynamics(type, btn) {
        document.querySelectorAll('#view-case-dynamics .dyn-filter-btn').forEach(b => {
            b.className = 'dyn-filter-btn text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200';
        });
        btn.className = 'dyn-filter-btn text-xs px-3 py-1.5 rounded-full bg-[#165DFF] text-white';
        document.querySelectorAll('#view-case-dynamics .bg-white.rounded-xl').forEach(card => {
            const tag = card.querySelector('.rounded-full:first-child')?.textContent.trim();
            if (type === 'all' || tag === type) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
        searchDynamics(); // 结合搜索关键词
    }


    function filterScheduleByDate() {
    var yearEl = document.getElementById('schedule-filter-year');
    var monthEl = document.getElementById('schedule-filter-month');
    var dayEl = document.getElementById('schedule-filter-day');
    if (!yearEl || !monthEl || !dayEl) return;
    var year = yearEl.value;
    var month = monthEl.value;
    var day = dayEl.value;

    var cards = document.querySelectorAll('#view-schedule-calendar [data-date]');
    var visible = 0;

    cards.forEach(function(card) {
        var dateStr = card.getAttribute('data-date') || '';
        var parts = dateStr.split('-');
        var cy = parts[0] || '';
        var cm = parts[1] || '';
        var cd = parts[2] || '';

        var show = true;
        if (year && cy !== year) show = false;
        if (show && month && cm !== month) show = false;
        if (show && day && cd !== day) show = false;

        if (show) {
            card.classList.remove('hidden');
            visible++;
        } else {
            card.classList.add('hidden');
        }
    });

    var countEl = document.getElementById('schedule-filter-count');
    if (countEl) {
        if (year || month || day) {
            countEl.textContent = '已筛选 ' + visible + ' / ' + cards.length + ' 项';
        } else {
            countEl.textContent = '';
        }
    }

    var noResult = document.getElementById('schedule-no-result');
    if (noResult) {
        if (visible === 0 && (year || month || day)) {
            noResult.classList.remove('hidden');
        } else {
            noResult.classList.add('hidden');
        }
    }
}

function clearScheduleFilter() {
    var yearEl = document.getElementById('schedule-filter-year');
    var monthEl = document.getElementById('schedule-filter-month');
    var dayEl = document.getElementById('schedule-filter-day');
    if (yearEl) yearEl.value = '';
    if (monthEl) monthEl.value = '';
    if (dayEl) dayEl.value = '';
    filterScheduleByDate();
}

// 进入日程管理时, 默认筛选 = 今天 (年/月/日 全部锁今天)
// 让用户进来直接看到今天的庭审, 而不是「全部日期」无目的浏览
function initScheduleFilterToToday() {
    var today = new Date();
    var y = today.getFullYear().toString();
    var m = String(today.getMonth() + 1).padStart(2, '0');
    var d = String(today.getDate()).padStart(2, '0');

    var yearEl = document.getElementById('schedule-filter-year');
    var monthEl = document.getElementById('schedule-filter-month');
    var dayEl = document.getElementById('schedule-filter-day');

    // 动态补年份到选项 (避免 hardcoded 缺年份)
    if (yearEl && !Array.from(yearEl.options).some(function(o) { return o.value === y; })) {
        var opt = document.createElement('option');
        opt.value = y;
        opt.textContent = y + ' 年';
        yearEl.appendChild(opt);
    }
    // 动态补日期到选项
    if (dayEl && !Array.from(dayEl.options).some(function(o) { return o.value === d; })) {
        var dopt = document.createElement('option');
        dopt.value = d;
        dopt.textContent = d.replace(/^0/, '') + ' 日';
        dayEl.appendChild(dopt);
    }

    if (yearEl) yearEl.value = y;
    if (monthEl) monthEl.value = m;
    if (dayEl) dayEl.value = d;

    filterScheduleByDate();
}

function jumpToToday() {
    var today = new Date();
    var y = today.getFullYear().toString();
    var m = String(today.getMonth() + 1).padStart(2, '0');
    var d = String(today.getDate()).padStart(2, '0');

    var yearEl = document.getElementById('schedule-filter-year');
    var monthEl = document.getElementById('schedule-filter-month');
    var dayEl = document.getElementById('schedule-filter-day');

    // 动态补今天的年份到选项 (避免 hardcoded 年份缺失)
    if (yearEl && !Array.from(yearEl.options).some(function(o) { return o.value === y; })) {
        var opt = document.createElement('option');
        opt.value = y;
        opt.textContent = y + ' 年';
        yearEl.appendChild(opt);
    }

    if (yearEl) yearEl.value = y;
    if (monthEl) monthEl.value = m;
    if (dayEl) dayEl.value = d;

    filterScheduleByDate();
}

function openScheduleDetail(id) {
        const item = AppState.scheduleData.find(s => s.id === id);
        if (!item) return;
        currentDetailScheduleId = id;

        document.getElementById('sdetail-title').textContent = item.title;
        document.getElementById('sdetail-date').textContent = formatDateCN(item.date);
        document.getElementById('sdetail-time').textContent = item.time + ' - ' + (item.endTime || '');
        document.getElementById('sdetail-location').textContent = item.location || '未设置';
        document.getElementById('sdetail-case').textContent = item.caseName || '未关联案件';
        document.getElementById('sdetail-note').textContent = item.note || '';

        // 类型徽章
        const badge = document.getElementById('sdetail-type-badge');
        const typeColors = { '开庭': ['bg-purple-100', 'text-purple-700'], '会议': ['bg-blue-100', 'text-blue-700'], '待办': ['bg-green-100', 'text-green-700'], '其他': ['bg-amber-100', 'text-amber-700'] };
        const colors = typeColors[item.type] || ['bg-gray-100', 'text-gray-700'];
        badge.className = 'text-xs px-2.5 py-1 rounded-full font-medium ' + colors.join(' ');
        badge.textContent = item.type;

        // 头部左边框颜色
        const header = document.getElementById('sdetail-header');
        const borderColors = { '开庭': '#7c3aed', '会议': '#3b82f6', '待办': '#22c55e', '其他': '#f59e0b' };
        header.style.borderLeftColor = borderColors[item.type] || '#165DFF';

        // 倒计时: 距今多少天/小时/已开始/已过
        var countdownEl = document.getElementById('sdetail-countdown');
        var countdownIcon = document.getElementById('sdetail-countdown-icon');
        if (countdownEl && item.date && item.time) {
            var target = new Date(item.date + 'T' + item.time + ':00');
            var now = new Date();
            var diffMs = target.getTime() - now.getTime();
            var absMin = Math.abs(Math.floor(diffMs / 60000));
            var days = Math.floor(absMin / (60 * 24));
            var hours = Math.floor((absMin % (60 * 24)) / 60);
            var mins = absMin % 60;
            var timeText;
            var iconName = 'mdi:calendar-clock-outline';
            if (diffMs > 0) {
                // 未来
                timeText = days > 0 ? '还有 ' + days + ' 天' + (hours > 0 ? ' ' + hours + ' 小时' : '')
                    : hours > 0 ? '还有 ' + hours + ' 小时' + (mins > 0 ? ' ' + mins + ' 分' : '')
                    : '还有 ' + mins + ' 分钟';
                iconName = days === 0 ? 'mdi:alarm-light-outline' : (days <= 3 ? 'mdi:alarm' : 'mdi:calendar-clock-outline');
            } else if (Math.abs(diffMs) < 60 * 60 * 1000) {
                // 1 小时内已过
                timeText = '刚刚开始 / 进行中';
                iconName = 'mdi:progress-clock';
            } else {
                // 已过
                timeText = '已过 ' + days + ' 天' + (hours > 0 ? ' ' + hours + ' 小时' : '');
                iconName = 'mdi:calendar-check-outline';
            }
            countdownEl.textContent = timeText;
            if (countdownIcon) countdownIcon.setAttribute('icon', iconName);
        }

        // 提醒文本 (头部 + 主体)
        var remindMap = { '0': '不提醒', '15': '提前 15 分钟', '60': '提前 1 小时', '1440': '提前 1 天' };
        var remindText = remindMap[item.remind] || '不提醒';
        var remindTopEl = document.getElementById('sdetail-remind-text');
        if (remindTopEl) remindTopEl.textContent = '🔔 ' + remindText;
        document.getElementById('sdetail-remind').textContent = remindText;

        // 关联案件: 显示「查看」按钮
        var caseLink = document.getElementById('sdetail-case-link');
        if (caseLink) {
            if (item.caseId) {
                caseLink.classList.remove('hidden');
            } else {
                caseLink.classList.add('hidden');
            }
        }

        // 检查冲突
        checkDetailConflict(item);

        document.getElementById('sdetail-note-row').classList.toggle('hidden', !item.note);
        document.getElementById('schedule-detail-modal').classList.remove('hidden');
    }


    function closeScheduleDetail() {
        document.getElementById('schedule-detail-modal').classList.add('hidden');
        currentDetailScheduleId = null;
    }


    function checkDetailConflict(item) {
        const warningEl = document.getElementById('sdetail-conflict');
        const detailEl = document.getElementById('sdetail-conflict-detail');
        
        const conflicts = AppState.scheduleData.filter(s => 
            s.id !== item.id && s.date === item.date &&
            item.time < s.endTime && item.endTime > s.time
        );
        
        if (conflicts.length > 0) {
            detailEl.innerHTML = conflicts.map(c => 
                '• <span class="font-medium">' + c.title + '</span> (' + c.time + '-' + (c.endTime||'') + ')'
            ).join('<br>');
            warningEl.classList.remove('hidden');
        } else {
            warningEl.classList.add('hidden');
        }
    }


    function editScheduleFromDetail() {
        closeScheduleDetail();
        openScheduleModal();
    }


    function deleteScheduleFromDetail() {
        if (!currentDetailScheduleId) return;
        if (confirm('确定要删除该日程吗？')) {
            const idx = AppState.scheduleData.findIndex(s => s.id === currentDetailScheduleId);
            if (idx > -1) AppState.scheduleData.splice(idx, 1);
            closeScheduleDetail();
            alert('日程已删除');
            if (typeof openScheduleCalendar === 'function') openScheduleCalendar();
        }
    }


    function showConflictResolve(conflicts) {
        const listEl = document.getElementById('conflict-list');
        listEl.innerHTML = conflicts.map(c => 
            '<div class="flex items-center gap-3 bg-red-50 rounded-lg p-3">' +
                '<iconify-icon icon="mdi:calendar-remove-outline" class="text-red-400 text-lg"></iconify-icon>' +
                '<div class="flex-1">' +
                    '<div class="text-sm font-medium text-red-700">' + c.title + '</div>' +
                    '<div class="text-xs text-red-500">' + c.time + ' - ' + (c.endTime||'') + '</div>' +
                '</div>' +
            '</div>'
        ).join('');
        
        // 推荐空闲时段
        const slotsEl = document.getElementById('suggested-slots');
        const date = pendingSchedule.date;
        const busyPeriods = conflicts.map(c => ({ start: c.time, end: c.endTime }));
        const suggestions = suggestFreeSlots(date, busyPeriods);
        slotsEl.innerHTML = suggestions.map(s => 
            '<button onclick="selectSuggestedSlot(\'' + s.start + '\',\'' + s.end + '\')" class="text-xs px-3 py-1.5 rounded-full border border-[#165DFF] text-[#165DFF] hover:bg-blue-50 transition-colors">' + s.start + ' - ' + s.end + '</button>'
        ).join('');
        
        document.getElementById('conflict-resolve-modal').classList.remove('hidden');
    }


    function closeConflictResolve() {
        document.getElementById('conflict-resolve-modal').classList.add('hidden');
        pendingSchedule = null;
    }


    function conflictResolveAction(action) {
        if (action === 'cancel') {
            closeConflictResolve();
            return;
        }
        if (action === 'ignore') {
            closeConflictResolve();
            if (pendingSchedule) {
                AppState.scheduleData.push(pendingSchedule);
                pendingSchedule = null;
                alert('日程已创建（含冲突）');
            }
            return;
        }
        if (action === 'reschedule') {
            closeConflictResolve();
            if (pendingSchedule) {
                AppState.scheduleData.push(pendingSchedule);
                pendingSchedule = null;
                alert('日程已调整至推荐时段');
            }
            return;
        }
    }


    function selectSuggestedSlot(start, end) {
        if (pendingSchedule) {
            pendingSchedule.time = start;
            pendingSchedule.endTime = end;
        }
        document.getElementById('sched-time').value = start;
    }


    function suggestFreeSlots(date, busyPeriods) {
        const allSlots = [];
        for (let h = 8; h < 20; h++) {
            allSlots.push({ start: String(h).padStart(2,'0') + ':00', end: String(h+1).padStart(2,'0') + ':00' });
        }
        return allSlots.filter(slot => 
            !busyPeriods.some(busy => slot.start < busy.end && slot.end > busy.start)
        ).slice(0, 4);
    }

    function checkCourtConflicts() {
        const courtSchedules = AppState.scheduleData.filter(s => s.type === '开庭');
        const conflicts = [];
        
        for (let i = 0; i < courtSchedules.length; i++) {
            for (let j = i + 1; j < courtSchedules.length; j++) {
                const a = courtSchedules[i], b = courtSchedules[j];
                if (a.date === b.date && a.time < b.endTime && a.endTime > b.time) {
                    conflicts.push({ a, b });
                }
            }
        }
        
        const bar = document.getElementById('court-conflict-bar');
        const detail = document.getElementById('court-conflict-detail');
        
        if (conflicts.length > 0) {
            detail.innerHTML = conflicts.map(c => 
                '• <span class="font-medium">' + c.a.title + '</span> 与 <span class="font-medium">' + c.b.title + '</span> 时间重叠（' + c.a.date + ' ' + c.a.time + '-' + c.b.endTime + '）'
            ).join('<br>');
            bar.classList.remove('hidden');
        } else {
            bar.classList.add('hidden');
        }
        
        return conflicts;
    }


    function dismissCourtConflict() {
        document.getElementById('court-conflict-bar').classList.add('hidden');
    }

    function openCaseDynamicDetail(index) {
        var dynamics = [
            { type: '紧急', typeClass: 'bg-red-100 text-red-700', title: '举证期限即将截止', caseName: '张三合同纠纷', time: '2026-06-10 14:30', handler: '李明', description: '张三合同纠纷一案的举证期限将于2026年6月23日截止，请尽快整理并提交相关证据材料，避免因逾期导致证据失权。', files: ['证据目录_v3.xlsx (256KB)', '举证期限告知书.pdf (1.2MB)'], note: '请务必在截止日前完成证据交换，已通知对方代理人。', action: '去处理' },
            { type: '文书', typeClass: 'bg-blue-100 text-blue-700', title: '起诉状已完成', caseName: '李四借贷纠纷', time: '2026-06-09 16:20', handler: '王芳', description: '李四借贷纠纷案的民事起诉状已完成最终审核，经合伙人确认无误，可安排打印盖章后提交法院立案。', files: ['民事起诉状_终稿.docx (45KB)'], note: '已安排下周一早提交立案庭。', action: '查看文书' },
            { type: '文书', typeClass: 'bg-blue-100 text-blue-700', title: '证据目录已更新', caseName: '王五股权转让纠纷', time: '2026-06-08 11:00', handler: '赵磊', description: '根据最新补充的银行流水和股权变更登记材料，已更新证据目录，新增证据5-8号，请确认是否完整。', files: ['证据目录_更新版.xlsx (128KB)', '补充材料_银行流水.pdf (3.5MB)'], note: '', action: '查看详情' },
            { type: '开庭', typeClass: 'bg-purple-100 text-purple-700', title: '开庭日期已确定', caseName: '赵六劳动争议', time: '2026-06-07 09:00', handler: '陈静', description: '赵六诉某科技公司劳动争议案，经与法院沟通，开庭时间定于2026年7月15日上午9:00，在市劳动争议仲裁委员会第一仲裁庭。', files: ['开庭传票.pdf (0.5MB)'], note: '请提前30分钟到达，带齐证据原件。', action: '查看详情' },
            { type: '开庭', typeClass: 'bg-purple-100 text-purple-700', title: '合议庭组成已确定', caseName: '孙七建设工程合同纠纷', time: '2026-06-06 15:00', handler: '刘强', description: '孙七建设工程合同纠纷案合议庭成员已确定，审判长：张明法官，审判员：李华、王丽。当事人对合议庭成员如申请回避，需在5日内提出。', files: ['合议庭组成通知书.pdf (0.3MB)'], note: '已与当事人确认无回避申请。', action: '查看详情' },
            { type: '归档', typeClass: 'bg-green-100 text-green-700', title: '案件已归档', caseName: '周八借款纠纷', time: '2026-06-05 17:00', handler: '李明', description: '周八借款纠纷案已结案归档。判决已生效，案卷材料已按档案管理规定整理完毕，存放于档案室第3柜第12号。', files: ['结案报告.docx (32KB)', '判决书.pdf (0.8MB)'], note: '归档编号：2026-0312', action: '查看归档' },
            { type: '归档', typeClass: 'bg-green-100 text-green-700', title: '判决书已上传', caseName: '吴九房屋租赁合同纠纷', time: '2026-06-04 14:00', handler: '王芳', description: '吴九房屋租赁合同纠纷案一审判决书已收到并上传系统。判决结果：被告支付租金及违约金合计￥45,600。双方是否上诉待确认。', files: ['一审判决书.pdf (1.1MB)'], note: '已通知当事人查收判决书，上诉期限15天。', action: '查看判决书' },
            { type: '提醒', typeClass: 'bg-amber-100 text-amber-700', title: '续约提醒', caseName: '常年法律顾问 - 某科技公司', time: '2026-06-03 10:00', handler: '系统自动', description: '某科技公司常年法律顾问服务合同将于2026年7月1日到期，如需续约请提前30天联系客户沟通续约事宜。', files: ['顾问合同_2025.pdf (0.6MB)'], note: '客户满意度较高，建议主动联系续约。', action: '查看详情' }
        ];
        var d = dynamics[index] || dynamics[0];
        document.getElementById('detail-type-badge').textContent = d.type;
        document.getElementById('detail-type-badge').className = 'text-[10px] font-medium px-1.5 py-0.5 rounded-full ' + d.typeClass;
        document.getElementById('detail-title').textContent = d.title;
        document.getElementById('detail-case-name').textContent = d.caseName;
        document.getElementById('detail-time').textContent = d.time;
        document.getElementById('detail-handler').textContent = d.handler;
        document.getElementById('detail-description').textContent = d.description;
        document.getElementById('detail-note').textContent = d.note || '暂无备注';
        document.getElementById('detail-action-btn').textContent = d.action;
        
        // 动态渲染关联文件
        var filesContainer = document.getElementById('detail-files-list');
        if (filesContainer) {
            var filesHtml = '';
            var fileIcons = {
                'xlsx': 'mdi:file-excel-outline',
                'xls': 'mdi:file-excel-outline',
                'pdf': 'mdi:file-pdf-outline',
                'doc': 'mdi:file-word-outline',
                'docx': 'mdi:file-word-outline',
                'jpg': 'mdi:file-image-outline',
                'png': 'mdi:file-image-outline',
                'gif': 'mdi:file-image-outline'
            };
            var fileColors = {
                'xlsx': 'bg-green-100 text-green-500',
                'xls': 'bg-green-100 text-green-500',
                'pdf': 'bg-red-100 text-red-500',
                'doc': 'bg-blue-100 text-blue-500',
                'docx': 'bg-blue-100 text-blue-500',
                'jpg': 'bg-purple-100 text-purple-500',
                'png': 'bg-purple-100 text-purple-500',
                'gif': 'bg-purple-100 text-purple-500'
            };
            
            (d.files || []).forEach(function(f) {
                var ext = f.split('(')[0].split('.').pop().trim().toLowerCase();
                var icon = fileIcons[ext] || 'mdi:file-document-outline';
                var color = fileColors[ext] || 'bg-gray-100 text-gray-500';
                var name = f.split('(')[0].trim();
                var sizeMatch = f.match(/\(([^)]+)\)/);
                var sizeStr = sizeMatch ? sizeMatch[1] : '';
                filesHtml += '<div class="flex items-center gap-3 bg-gray-50 rounded-lg px-3 py-2.5 hover:bg-gray-100 transition-colors cursor-pointer">' +
                    '<div class="w-8 h-8 rounded-lg ' + color.split(' ')[0] + ' flex items-center justify-center flex-shrink-0">' +
                        '<iconify-icon icon="' + icon + '" class="' + color.split(' ')[1] + ' text-base"></iconify-icon>' +
                    '</div>' +
                    '<div class="flex-1 min-w-0">' +
                        '<p class="text-xs font-medium text-gray-700 truncate">' + name + '</p>' +
                        '<p class="text-[10px] text-gray-400">' + sizeStr + '</p>' +
                    '</div>' +
                    '<button class="text-[11px] text-[#165DFF] hover:underline flex-shrink-0">预览</button>' +
                '</div>';
            });
            filesContainer.innerHTML = filesHtml;
        }
        
        document.getElementById('case-dynamic-detail-modal').classList.remove('hidden');
    }

    function closeCaseDynamicDetail() {
        document.getElementById('case-dynamic-detail-modal').classList.add('hidden');
    }

    function searchDynamics() {
        var keyword = document.getElementById('dynamics-search-input').value.trim().toLowerCase();
        document.querySelectorAll('#view-case-dynamics .bg-white.rounded-xl').forEach(function(card) {
            var text = card.textContent.toLowerCase();
            if (keyword === '' || text.indexOf(keyword) !== -1) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
        var visibleCount = document.querySelectorAll('#view-case-dynamics .bg-white.rounded-xl:not(.hidden)').length;
        var totalCount = document.querySelectorAll('#view-case-dynamics .bg-white.rounded-xl').length;
        var countEl = document.querySelector('#view-case-dynamics h2 + span');
        if (countEl) countEl.textContent = '共 ' + visibleCount + ' / ' + totalCount + ' 条';
        
        // 显示/隐藏空状态
        var emptyState = document.getElementById('dynamics-empty-state');
        if (emptyState) {
            if (visibleCount === 0) {
                emptyState.classList.remove('hidden');
            } else {
                emptyState.classList.add('hidden');
            }
        }
    }

    function selectDynamicType(btn, type) {
        document.querySelectorAll('.dyn-type-option').forEach(function(b) {
            b.className = 'dyn-type-option text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200';
        });
        btn.className = 'dyn-type-option text-xs px-3 py-1.5 rounded-full bg-[#165DFF] text-white';
        AppState.selectedDynamicType = type;
    }

    function openNewDynamicModal() {
        document.getElementById('new-dynamic-modal').classList.remove('hidden');
    }

    function closeNewDynamicModal() {
        document.getElementById('new-dynamic-modal').classList.add('hidden');
    }


    function handleDynamicFileSelect(input) {
        var files = input.files;
        for (var i = 0; i < files.length; i++) {
            addDynamicFile(files[i]);
        }
        input.value = '';
    }


    function handleDynamicFileDrop(event) {
        var files = event.dataTransfer.files;
        for (var i = 0; i < files.length; i++) {
            addDynamicFile(files[i]);
        }
    }


    function addDynamicFile(file) {
        var size = file.size;
        var sizeStr = '';
        if (size < 1024) sizeStr = size + 'B';
        else if (size < 1024 * 1024) sizeStr = (size / 1024).toFixed(1) + 'KB';
        else sizeStr = (size / 1024 / 1024).toFixed(1) + 'MB';
        
        var icon = 'mdi:file-document-outline';
        var ext = file.name.split('.').pop().toLowerCase();
        if (['png','jpg','jpeg','gif','webp'].indexOf(ext) !== -1) icon = 'mdi:file-image-outline';
        else if (['pdf'].indexOf(ext) !== -1) icon = 'mdi:file-pdf-outline';
        else if (['doc','docx'].indexOf(ext) !== -1) icon = 'mdi:file-word-outline';
        else if (['xls','xlsx'].indexOf(ext) !== -1) icon = 'mdi:file-excel-outline';
        
        var fileId = 'dyn_file_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
        
        AppState.dynamicAttachments.push({
            id: fileId,
            name: file.name,
            size: sizeStr,
            icon: icon,
            file: file
        });
        
        renderDynamicFilePreview();
    }


    function removeDynamicFile(fileId) {
        AppState.dynamicAttachments = AppState.dynamicAttachments.filter(function(f) { return f.id !== fileId; });
        renderDynamicFilePreview();
    }


    function renderDynamicFilePreview() {
        var container = document.getElementById('dynamic-file-preview-list');
        if (!container) return;
        
        if (AppState.dynamicAttachments.length === 0) {
            container.classList.add('hidden');
            return;
        }
        container.classList.remove('hidden');
        
        var html = '';
        AppState.dynamicAttachments.forEach(function(f) {
            html += '<div class="flex items-center gap-2 bg-white rounded-lg border border-[#E5E6EB] px-3 py-2">' +
                '<iconify-icon icon="' + f.icon + '" class="text-base text-[#165DFF] flex-shrink-0"></iconify-icon>' +
                '<div class="flex-1 min-w-0">' +
                    '<p class="text-xs text-gray-700 truncate">' + f.name + '</p>' +
                    '<p class="text-[10px] text-gray-400">' + f.size + '</p>' +
                '</div>' +
                '<button onclick="removeDynamicFile(\'' + f.id + '\')" class="text-gray-400 hover:text-red-500 flex-shrink-0">' +
                    '<iconify-icon icon="mdi:close-circle"></iconify-icon>' +
                '</button>' +
            '</div>';
        });
        container.innerHTML = html;
    }

    
    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');
    }

    
    function submitNewDynamic() {
        var title = document.getElementById('new-dynamic-title').value.trim();
        if (!title) { alert('请填写动态标题'); return; }
        var desc = document.getElementById('new-dynamic-desc').value.trim();
        var caseName = document.getElementById('new-dynamic-case').value || '未关联案件';
        var isUrgent = document.getElementById('new-dynamic-urgent').checked;
        var now = new Date();
        var timeStr = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0') + '-' + String(now.getDate()).padStart(2,'0') + ' ' + String(now.getHours()).padStart(2,'0') + ':' + String(now.getMinutes()).padStart(2,'0');
        var typeColorMap = {
            '紧急': { border: 'border-l-red-500', bg: 'bg-red-50', icon: 'mdi:alert-circle-outline', iconColor: 'text-red-500', tagBg: 'bg-red-100', tagText: 'text-red-700' },
            '文书': { border: 'border-l-blue-500', bg: 'bg-blue-50', icon: 'mdi:file-document-outline', iconColor: 'text-blue-500', tagBg: 'bg-blue-100', tagText: 'text-blue-700' },
            '开庭': { border: 'border-l-purple-500', bg: 'bg-purple-50', icon: 'mdi:gavel', iconColor: 'text-purple-500', tagBg: 'bg-purple-100', tagText: 'text-purple-700' },
            '归档': { border: 'border-l-green-500', bg: 'bg-green-50', icon: 'mdi:archive-outline', iconColor: 'text-green-500', tagBg: 'bg-green-100', tagText: 'text-green-700' },
            '提醒': { border: 'border-l-amber-500', bg: 'bg-amber-50', icon: 'mdi:bell-outline', iconColor: 'text-amber-500', tagBg: 'bg-amber-100', tagText: 'text-amber-700' }
        };
        var colors = typeColorMap[AppState.selectedDynamicType] || typeColorMap['提醒'];
        // 构建附件标签行
        var attachHtml = '';
        if (AppState.dynamicAttachments.length > 0) {
            attachHtml = '<div class="flex items-center gap-2 mt-1.5">' +
                AppState.dynamicAttachments.map(function(a) {
                    return '<span class="inline-flex items-center gap-1 text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full"><iconify-icon icon="' + a.icon + '" class="text-xs"></iconify-icon>' + escapeHtml(a.name) + '</span>';
                }).join('') +
            '</div>';
        }
        var cardHtml = '<div class="bg-white rounded-xl border border-[#E5E6EB] p-4 hover:shadow-sm transition-shadow ' + colors.border + '">' +
            '<div class="flex items-start gap-3">' +
                '<div class="w-9 h-9 rounded-lg ' + colors.bg + ' flex items-center justify-center flex-shrink-0">' +
                    '<iconify-icon icon="' + colors.icon + '" class="' + colors.iconColor + ' text-lg"></iconify-icon>' +
                '</div>' +
                '<div class="flex-1 min-w-0">' +
                    '<div class="flex items-center gap-2 mb-1">' +
                        '<span class="text-[10px] ' + colors.tagBg + ' ' + colors.tagText + ' font-medium px-1.5 py-0.5 rounded-full">' + (isUrgent ? '紧急' : AppState.selectedDynamicType) + '</span>' +
                        '<span class="font-medium text-sm text-gray-800">' + escapeHtml(title) + '</span>' +
                    '</div>' +
                    '<p class="text-xs text-gray-500">案件：' + escapeHtml(caseName) + ' · ' + (escapeHtml(desc.substring(0,30)) || '暂无详细描述') + '</p>' +
                    attachHtml +
                    '<div class="flex items-center gap-3 mt-2">' +
                        '<span class="text-[10px] text-gray-400"><iconify-icon icon="mdi:clock-outline" class="mr-0.5"></iconify-icon>' + timeStr + '</span>' +
                        '<span class="text-[10px] text-gray-400"><iconify-icon icon="mdi:account-outline" class="mr-0.5"></iconify-icon>我</span>' +
                    '</div>' +
                '</div>' +
                '<button class="text-[11px] text-[#165DFF] hover:underline flex-shrink-0 mt-1" onclick="alert(\'' + escapeHtml(title) + '\\n\\n案件：' + escapeHtml(caseName) + '\\n' + (escapeHtml(desc.substring(0,50)) || '') + '\\n\\n附件：' + (AppState.dynamicAttachments.length > 0 ? AppState.dynamicAttachments.map(function(a){return escapeHtml(a.name)}).join(', ') : '无') + '\')">查看</button>' +
            '</div>' +
        '</div>';
        var listContainer = document.querySelector('#dynamics-list-view');
        if (listContainer) {
            var tempDiv = document.createElement('div');
            tempDiv.innerHTML = cardHtml;
            listContainer.insertBefore(tempDiv.firstElementChild, listContainer.firstElementChild);
        }
        var totalCards = document.querySelectorAll('#view-case-dynamics .bg-white.rounded-xl').length;
        var countEl = document.querySelector('#view-case-dynamics h2 + span');
        if (countEl) countEl.textContent = '共 ' + totalCards + ' 条';
        closeNewDynamicModal();
        document.getElementById('new-dynamic-title').value = '';
        document.getElementById('new-dynamic-desc').value = '';
        document.getElementById('new-dynamic-case').value = '';
        document.getElementById('new-dynamic-urgent').checked = false;
        AppState.selectedDynamicType = '紧急';
        document.querySelectorAll('.dyn-type-option').forEach(function(b, i) {
            b.className = 'dyn-type-option text-xs px-3 py-1.5 rounded-full ' + (i === 0 ? 'bg-[#165DFF] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200');
        });
        // 重置附件
        AppState.dynamicAttachments = [];
        renderDynamicFilePreview();
    }


    function switchDynamicsView(view) {
        var listBtn = document.getElementById('dyn-view-list');
        var tlBtn = document.getElementById('dyn-view-timeline');
        var listView = document.getElementById('dynamics-list-view');
        var tlView = document.getElementById('dynamics-timeline-view');
        
        if (view === 'timeline') {
            listBtn.className = 'flex items-center gap-1 h-8 px-2.5 text-xs bg-white text-gray-600 hover:bg-gray-50 transition-colors';
            tlBtn.className = 'flex items-center gap-1 h-8 px-2.5 text-xs bg-[#165DFF] text-white transition-colors';
            listView.classList.add('hidden');
            tlView.classList.remove('hidden');
            renderDynamicsTimeline();
        } else {
            tlBtn.className = 'flex items-center gap-1 h-8 px-2.5 text-xs bg-white text-gray-600 hover:bg-gray-50 transition-colors';
            listBtn.className = 'flex items-center gap-1 h-8 px-2.5 text-xs bg-[#165DFF] text-white transition-colors';
            tlView.classList.add('hidden');
            listView.classList.remove('hidden');
        }
    }


    function renderDynamicsTimeline() {
        var container = document.querySelector('#dynamics-timeline-view .relative.pl-8');
        if (!container) return;
        if (container.querySelectorAll('.dyn-tl-item').length > 0) return;
        
        var htmlStr = '';
        AppState.dynamicsViewData.forEach(function(d, i) {
            var dotColor = d.iconColor.replace('text-', 'border-');
            htmlStr += '<div class="dyn-tl-item relative pb-6">' +
                '<div class="absolute left-[-22px] top-1 w-3 h-3 rounded-full border-2 bg-white ' + (dotColor || 'border-blue-500') + '"></div>' +
                '<div class="bg-white rounded-xl border border-[#E5E6EB] p-4 hover:shadow-sm transition-shadow cursor-pointer" onclick="openCaseDynamicDetail(' + i + ')">' +
                    '<div class="flex items-start gap-3">' +
                        '<div class="w-8 h-8 rounded-lg ' + d.typeClass.split(' ')[0].replace('text-', 'bg-').replace('-700', '-50') + ' flex items-center justify-center flex-shrink-0">' +
                            '<iconify-icon icon="' + d.icon + '" class="' + d.iconColor + ' text-base"></iconify-icon>' +
                        '</div>' +
                        '<div class="flex-1 min-w-0">' +
                            '<div class="flex items-center gap-2 mb-0.5">' +
                                '<span class="text-[10px] ' + d.typeClass + ' font-medium px-1.5 py-0.5 rounded-full">' + d.type + '</span>' +
                                '<span class="font-medium text-sm text-gray-800">' + d.title + '</span>' +
                            '</div>' +
                            '<p class="text-xs text-gray-500">' + d.caseName + ' · ' + d.desc + '</p>' +
                            '<span class="text-[10px] text-gray-400 mt-1 inline-block">' + d.time + '</span>' +
                        '</div>' +
                    '</div>' +
                '</div>' +
            '</div>';
        });
        container.insertAdjacentHTML('beforeend', htmlStr);
    }
