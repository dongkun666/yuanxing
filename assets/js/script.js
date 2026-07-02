/**
 * 主脚本 - helper 函数 + 案件/客户/模板配置
 * 拆分自原 script.js (2026-06-28 IIFE 拆分计划)
 * AppState/viewCache/viewFileMap/loadView/switchView/switchSidebarTab/bootstrapApp
 * 等已抽离到独立模块: app-state.js / router.js / bootstrap.js
 *
 * 加载顺序: api/auth/app-state/router → 业务模块 → script.js → bootstrap.js
 * 依赖: AppState (app-state.js), switchView (router.js), showToast (本文件)
 */

(function () {
    'use strict';

    // ===== 案件列表筛选 =====
    var caseCurrentPage = 1;

    // ===== 案件归档 =====

    // ===== 案件详情页操作 =====
    function shareCase() {
        var idx = typeof globalThis.currentCaseIndex !== 'undefined' ? globalThis.currentCaseIndex : -1;
        if (idx < 0) {
            showToast('请先打开一个案件', 'warning');
            return;
        }
        var caseMeta = [
            { caseName: '李明诉XX公司买卖合同纠纷', caseNumber: '(2026)京01民初128号' },
            { caseName: '赵六劳动争议仲裁案', caseNumber: '(2026)京02民初256号' },
            { caseName: '张三合同纠纷案', caseNumber: '(2026)京03民初789号' },
            { caseName: '某科技公司股权纠纷案', caseNumber: '(2026)京04民初345号' },
            { caseName: '王华借贷纠纷案', caseNumber: '(2026)京05民初567号' }
        ];
        var meta = caseMeta[idx] || { caseName: '案件', caseNumber: 'N/A' };
        var shareText =
            '【LexPrime 案件分享】\n案号: ' +
            meta.caseNumber +
            '\n案名: ' +
            meta.caseName +
            '\n查看详情: ' +
            location.origin +
            '/case/' +
            idx;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard
                .writeText(shareText)
                .then(function () {
                    showToast('案件信息已复制到剪贴板', 'success');
                })
                .catch(function () {
                    prompt('案件分享信息 (Ctrl+C 复制):', shareText);
                });
        } else {
            prompt('案件分享信息 (Ctrl+C 复制):', shareText);
        }
    }

    // ===== 归档管理操作 =====

    var currentEditSection = null;
    var sectionConfigs = {
        basic: {
            title: '编辑案件基本信息',
            fields: [
                { key: 'caseNumber', label: '案号', type: 'text', colSpan: 1 },
                { key: 'caseType', label: '案由', type: 'text', colSpan: 1 },
                {
                    key: 'status',
                    label: '案件状态',
                    type: 'select',
                    options: ['进行中', '已结案', '已归档', '中止审理'],
                    colSpan: 1
                },
                { key: 'claimAmount', label: '标的金额', type: 'text', colSpan: 1 },
                { key: 'contractAmount', label: '合同金额', type: 'text', colSpan: 1 },
                { key: 'signDate', label: '签约日期', type: 'date', colSpan: 1 },
                {
                    key: 'stage',
                    label: '代理阶段',
                    type: 'select',
                    options: ['一审', '二审', '再审', '执行', '仲裁'],
                    colSpan: 1
                },
                {
                    key: 'preservation',
                    label: '是否保全',
                    type: 'select',
                    options: ['已保全', '未保全', '保全中'],
                    colSpan: 1
                },
                {
                    key: 'paymentStatus',
                    label: '缴费情况',
                    type: 'select',
                    options: ['已缴费', '未缴费', '部分缴费'],
                    colSpan: 1
                },
                { key: 'specialTerms', label: '特殊约定', type: 'textarea', colSpan: 3 }
            ]
        },
        client: {
            title: '编辑客户信息',
            fields: [
                { key: 'name', label: '客户姓名', type: 'text', colSpan: 1 },
                { key: 'phone', label: '客户电话', type: 'text', colSpan: 1 },
                { key: 'idNumber', label: '客户证件号', type: 'text', colSpan: 1 },
                { key: 'legalRep', label: '法定代表人', type: 'text', colSpan: 1 },
                { key: 'address', label: '客户地址', type: 'textarea', colSpan: 2 }
            ]
        },
        opponent: {
            title: '编辑对方信息',
            fields: [
                { key: 'name', label: '对方姓名', type: 'text', colSpan: 1 },
                { key: 'phone', label: '对方电话', type: 'text', colSpan: 1 },
                { key: 'idNumber', label: '对方证件号', type: 'text', colSpan: 1 },
                { key: 'legalRep', label: '法定代表人', type: 'text', colSpan: 1 },
                { key: 'address', label: '对方地址', type: 'textarea', colSpan: 2 }
            ]
        },
        claims: {
            title: '编辑客户诉求',
            fields: [{ key: 'content', label: '客户诉求内容', type: 'textarea', rows: 6, colSpan: 2 }]
        },
        strategy: {
            title: '编辑办案思路',
            fields: [{ key: 'content', label: '办案思路', type: 'textarea', rows: 6, colSpan: 2 }]
        },
        summary: {
            title: '编辑案情简述',
            fields: [{ key: 'content', label: '案情简述', type: 'textarea', rows: 6, colSpan: 2 }]
        }
    };

    // AI 子标签页切换

    // 新建对话（合并版：同时清空侧边栏和主视图消息）

    // 选择历史对话

    // 历史对话搜索过滤

    // AI视图切换（左侧菜单点击 -> 右侧内容切换）

    // AI子视图切换辅助函数

    // 选择历史对话

    // 过滤历史记录

    // 更多菜单切换（每个标签各自独立菜单）

    // 跳转到会员订阅页面

    // 年月付切换
    // var isYearly = false; // → AppState.isYearly

    // 跳转到支付页面

    // 返回订阅页面

    // 支付方式选择
    // var selectedPayment = 'alipay'; // → AppState.selectedPayment

    // 支付成功

    // 从支付成功页跳转

    // 跳转到订单记录

    // 跳转到会员中心

    // 跳转到账号设置
    // 切换个人资料编辑模式
    // 切换个人资料编辑模式

    // 取消编辑，切回只读（不保存更改）

    // 保存个人资料

    // 保存成功提示

    // 添加专业领域标签

    // 头像预览
    // 头像上传处理

    // 删除专业领域标签

    // 添加专业领域标签（增强版）

    // 职业认证 - 证件文件上传
    function handleCertUpload(event) {
        var file = event.target.files[0];
        if (!file) return;

        if (file.size > 10 * 1024 * 1024) {
            alert('证件文件大小不能超过 10MB');
            return;
        }

        var preview = document.getElementById('cert-file-preview');
        var nameEl = document.getElementById('cert-file-name');
        var sizeEl = document.getElementById('cert-file-size');

        if (preview && nameEl && sizeEl) {
            nameEl.textContent = file.name;
            var sizeKB = (file.size / 1024).toFixed(1);
            sizeEl.textContent = sizeKB + ' KB';
            preview.classList.remove('hidden');
        }
    }

    // 职业认证 - 移除已上传文件

    // 职业认证 - 提交审核
    function submitCertification() {
        alert('您的律师执业认证申请已提交！\n我们将在 1-3 个工作日内完成审核。\n审核结果将以消息通知您。');
    }

    // 双因素认证切换

    // 设备管理

    // 账号注销确认

    // ========== 客户管理增强功能 ==========
    // 客户分类切换

    // 知识库管理 - 分类切换
    function switchKnowledgeTab(el, type) {
        document.querySelectorAll('#view-knowledge .flex.items-center.gap-1.flex-wrap button').forEach(function (btn) {
            btn.classList.remove('bg-[#165DFF]', 'text-white');
            btn.classList.add('text-[#4E5969]', 'hover:bg-[#F7F8FA]');
        });
        el.classList.remove('text-[#4E5969]', 'hover:bg-[#F7F8FA]');
        el.classList.add('bg-[#165DFF]', 'text-white');
        _knowledgeType = type;
        applyKnowledgeFilter();
    }

    var _knowledgeType = 'all';
    var _knowledgeSearch = '';
    var _knowledgeSort = null; // { field, dir }

    function triggerKnowledgeSearch(keyword) {
        var input = document.getElementById('kb-search-input');
        if (input) {
            input.value = keyword;
            _knowledgeSearch = keyword;
            applyKnowledgeFilter();
            // 滚动到搜索框位置
            try {
                input.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } catch (e) {}
        }
    }

    function sortKnowledgeTable(field, el) {
        var dir;
        if (_knowledgeSort && _knowledgeSort.field === field) {
            dir = _knowledgeSort.dir === 'asc' ? 'desc' : 'asc';
        } else {
            dir = field === 'cite' ? 'desc' : 'asc'; // 引用默认降序
        }
        _knowledgeSort = { field: field, dir: dir };

        // 重置所有 arrow
        document.querySelectorAll('#view-knowledge .sort-arrow').forEach(function (a) {
            a.textContent = '⇅';
            a.classList.remove('text-[#165DFF]');
            a.classList.add('text-[#C9CDD4]');
        });
        // 高亮当前
        var arrow = el.querySelector('.sort-arrow');
        if (arrow) {
            arrow.textContent = dir === 'asc' ? '↑' : '↓';
            arrow.classList.remove('text-[#C9CDD4]');
            arrow.classList.add('text-[#165DFF]');
        }

        // 排序
        var tbody = document.querySelector('#view-knowledge tbody');
        if (!tbody) return;
        var rows = Array.from(tbody.querySelectorAll('tr[data-knowledge-type]'));
        rows.sort(function (a, b) {
            var va, vb;
            if (field === 'date') {
                va = a.getAttribute('data-date') || '';
                vb = b.getAttribute('data-date') || '';
                return dir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
            } else if (field === 'cite') {
                va = parseInt(a.getAttribute('data-cite') || '0', 10);
                vb = parseInt(b.getAttribute('data-cite') || '0', 10);
                return dir === 'asc' ? va - vb : vb - va;
            } else if (field === 'title') {
                va = a.getAttribute('data-title') || '';
                vb = b.getAttribute('data-title') || '';
                return dir === 'asc' ? va.localeCompare(vb, 'zh-CN') : vb.localeCompare(va, 'zh-CN');
            }
            return 0;
        });
        rows.forEach(function (r) {
            tbody.appendChild(r);
        });
    }

    // 知识库搜索框 - 实时过滤
    (function () {
        var input = document.getElementById('kb-search-input');
        if (input) {
            input.addEventListener('input', function () {
                _knowledgeSearch = input.value;
                applyKnowledgeFilter();
            });
        }
    })();

    // ===== LLM Wiki 风格 3 Tab 切换 =====

    // ===== AI 编译 (Ingest) 交互 =====

    // 打开客户详情

    // 返回客户列表

    // 新建客户弹窗

    // 新建客户时利益冲突检索

    // 客户详情页利益冲突审查
    // 跳转到案件列表主页

    // 打开案件详情（跳转到案件详情页，默认显示案件概览 Tab）
    var currentCaseIndex = -1;

    // Tab 切换 - 案件详情

    // 证据材料标签页切换

    // 模板管理 - 标签页切换

    // 修复 template 视图 DOM 重组: 浏览器把 official tab 内的卡片视图和孤儿卡片飘到主体 div 直接子级

    // 模板管理 - 列表/卡片视图切换

    // 上传模板弹窗 (占位)

    // 删除个人模板 (客户端模拟)

    // 分类管理 - 弹窗控制

    // 分类管理 - 新增/删除 (客户端模拟, 不持久化)

    // 按时间排序个人模板 (desc/asc 切换)
    var _personalSortOrder = null; // null = 默认顺序, 'desc' = 最新的在前面, 'asc' = 最旧的在前

    // 同步更新"全部"标签的数字

    // 按分类筛选个人模板

    // 官方模板: 一级分类筛选 + 二级文书类型筛选 + 搜索
    var _officialCategory = 'all';
    var _officialType = 'all';
    var _officialSearch = '';

    // 清除搜索

    // 官方模板卡片预览 (占位)

    // 手动创建证据目录 - 打开模态框

    // 加载证据概览文件列表供选择
    var catalogSelectedFiles = [];

    // 切换文件选择状态

    // 更新已选文件数量显示

    // 关闭证据目录模态框

    // 提交证据目录

    // 编辑证据目录项
    var editingCatalogRow = null;

    // 覆盖提交函数以支持编辑模式
    var originalSubmitEvidenceCatalog = submitEvidenceCatalog;
    submitEvidenceCatalog = function () {
        if (editingCatalogRow) {
            // 编辑模式
            var number = document.getElementById('catalog-number').value.trim();
            var name = document.getElementById('catalog-name').value.trim();
            var pages = document.getElementById('catalog-pages').value.trim();
            var description = document.getElementById('catalog-description').value.trim();

            var typeRadios = document.getElementsByName('catalog-type');
            var type = '书证';
            for (var i = 0; i < typeRadios.length; i++) {
                if (typeRadios[i].checked) {
                    type = typeRadios[i].value;
                    break;
                }
            }

            if (!name) {
                showToast('请输入证据材料名称');
                return;
            }

            var typeClass = '';
            if (type === '书证') {
                typeClass = 'bg-blue-100 text-blue-700';
            } else if (type === '电子数据') {
                typeClass = 'bg-purple-100 text-purple-700';
            } else if (type === '视听资料') {
                typeClass = 'bg-orange-100 text-orange-700';
            } else {
                typeClass = 'bg-gray-100 text-gray-700';
            }

            // 更新 data-* 属性
            editingCatalogRow.dataset.number = number || '';
            editingCatalogRow.dataset.type = type;
            editingCatalogRow.dataset.name = name;
            editingCatalogRow.dataset.description = description || '';
            editingCatalogRow.dataset.pages = pages || '';

            // 更新可视内容
            var numDiv = editingCatalogRow.querySelector('[data-catalog-number]');
            if (numDiv) numDiv.textContent = number || '';

            var typeSpan = editingCatalogRow.querySelector('[data-catalog-type]');
            if (typeSpan) {
                typeSpan.className = 'text-[10px] ' + typeClass + ' px-1.5 py-0.5 rounded';
                typeSpan.textContent = type;
            }

            var nameSpan = editingCatalogRow.querySelector('[data-catalog-name]');
            if (nameSpan) {
                nameSpan.textContent = name;
                nameSpan.setAttribute('title', name);
            }

            var descEl = editingCatalogRow.querySelector('[data-catalog-description]');
            if (descEl) descEl.textContent = description || '-';

            var pagesEl = editingCatalogRow.querySelector('[data-catalog-pages]');
            if (pagesEl) pagesEl.textContent = pages || '-';

            // 保存关联文件到data属性
            if (catalogSelectedFiles.length > 0) {
                editingCatalogRow.setAttribute('data-linked-files', JSON.stringify(catalogSelectedFiles));
            } else {
                editingCatalogRow.removeAttribute('data-linked-files');
            }

            editingCatalogRow = null;
            closeAddEvidenceCatalogModal();
            showToast('证据目录已更新');
        } else {
            // 新增模式 - 调用原函数
            originalSubmitEvidenceCatalog();
        }
    };

    // 关闭模态框时重置编辑状态
    var originalCloseAddEvidenceCatalogModal = closeAddEvidenceCatalogModal;
    closeAddEvidenceCatalogModal = function () {
        editingCatalogRow = null;
        originalCloseAddEvidenceCatalogModal();
    };

    // 删除证据目录项

    // AI创建证据目录

    // 时间线相关函数

    // 证件管理相关函数

    // 委托合同相关函数

    // 证据材料相关函数

    // 文书管理相关函数（授权委托书、判决书/调解书、其他文书通用）
    var currentDocumentType = '';

    var documentTypeMap = {
        'power-attorney': {
            title: '上传授权委托书',
            listId: 'power-attorney-list',
            toast: '授权委托书已上传',
            deleteToast: '授权委托书已删除',
            subText: ''
        },
        judgment: {
            title: '上传判决书/调解书',
            listId: 'judgment-list',
            toast: '文书已上传',
            deleteToast: '文书已删除',
            subText: '判决文书'
        },
        other: {
            title: '上传其他文书',
            listId: 'other-doc-list',
            toast: '文书已上传',
            deleteToast: '文书已删除',
            subText: '其他'
        }
    };

    // AI 侧边面板子标签切换

    // 证据目录 AI 面板切换 (3 tab: 完整性/证明对象/法条)

    // 打开智能卷宗分析

    // 从卷宗分析/日程管理返回案件列表

    // 打开日程管理

    // 标记日历中的冲突日程

    // 字段校验（必填）

    // 邮箱格式校验

    // 自动保存（防抖）
    // var autoSaveTimer = null;

    // 保存通知设置

    // 绑定第三方账号

    // 解绑第三方账号

    // ===== 日程冲突检测（移到 AppState 让 schedule.js 可访问） =====
    AppState.scheduleData = (function () {
        // 优先读 localStorage (持久化用户日程); 损坏/空则回退到 mock 数据
        try {
            var saved = localStorage.getItem('lexprime_schedule_data');
            if (saved) {
                var data = JSON.parse(saved);
                if (Array.isArray(data)) return data;
            }
        } catch (e) {
            /* corrupted storage, fall through to mock */
        }
        return [
            {
                id: 1,
                title: '李明诉XX公司买卖合同纠纷开庭',
                date: getTodayDate(),
                time: '09:00',
                endTime: '11:00',
                type: '开庭',
                location: '朝阳区人民法院 第3法庭'
            },
            {
                id: 2,
                title: '王华借贷纠纷 - 策略讨论',
                date: getTodayDate(),
                time: '14:00',
                endTime: '15:30',
                type: '会议',
                location: '线上会议'
            },
            {
                id: 3,
                title: '提交张三合同纠纷补充证据',
                date: getTodayDate(),
                time: '16:00',
                endTime: '16:30',
                type: '待办',
                location: '',
                completed: true
            },
            {
                id: 4,
                title: '律所月度合伙人会议',
                date: getTodayDate(),
                time: '10:30',
                endTime: '11:30',
                type: '其他',
                location: '大会议室',
                completed: true
            },
            {
                id: 5,
                title: '某科技公司股权纠纷二审开庭',
                date: getTodayDate(),
                time: '15:00',
                endTime: '17:00',
                type: '开庭',
                location: '北京市高级人民法院 第8法庭'
            },
            {
                id: 6,
                title: '赵六劳动争议仲裁开庭',
                date: getFutureDate(1),
                time: '09:00',
                endTime: '12:00',
                type: '开庭',
                location: '朝阳区劳动仲裁委'
            },
            {
                id: 7,
                title: '张三合同纠纷证据交换',
                date: getFutureDate(2),
                time: '14:00',
                endTime: '16:00',
                type: '开庭',
                location: '海淀区人民法院'
            }
        ];
    })();

    // 通知数据 (AppState.notifications)
    // 优先读 localStorage (持久化用户已读状态); 损坏/空则回退到 mock
    // 字段: id, type (document/deadline/case/member/system), icon, color, title, desc, timeAgo, timestamp, unread, linkTo, linkParam
    AppState.notifications = (function () {
        try {
            var saved = localStorage.getItem('lexprime_notifications');
            if (saved) {
                var data = JSON.parse(saved);
                if (Array.isArray(data) && data.length > 0) return data;
            }
        } catch (e) {}
        return [
            {
                id: 'n1',
                type: 'document',
                icon: 'mdi:file-document-outline',
                color: 'brand',
                title: '起诉状已生成',
                desc: '李明诉XX公司买卖合同纠纷案的起诉状已完成 AI 草拟',
                timeAgo: '3 分钟前',
                timestamp: Date.now() - 3 * 60 * 1000,
                unread: true,
                linkTo: 'case',
                linkParam: '1'
            },
            {
                id: 'n2',
                type: 'deadline',
                icon: 'mdi:clock-alert-outline',
                color: 'danger',
                title: '证据提交即将截止',
                desc: '王华借贷纠纷案举证期还剩 2 天, 请尽快准备补充证据',
                timeAgo: '15 分钟前',
                timestamp: Date.now() - 15 * 60 * 1000,
                unread: true,
                linkTo: 'case',
                linkParam: '2'
            },
            {
                id: 'n3',
                type: 'case',
                icon: 'mdi:check-circle-outline',
                color: 'success',
                title: '案件已归档',
                desc: '张三合同纠纷案已完成结案归档, 可在归档列表查阅',
                timeAgo: '1 小时前',
                timestamp: Date.now() - 60 * 60 * 1000,
                unread: false,
                linkTo: 'archive',
                linkParam: ''
            },
            {
                id: 'n4',
                type: 'deadline',
                icon: 'mdi:calendar-clock-outline',
                color: 'warning',
                title: '明日开庭提醒',
                desc: '某科技公司股权纠纷案明日 09:00 开庭, 建议提前准备材料',
                timeAgo: '2 小时前',
                timestamp: Date.now() - 2 * 60 * 60 * 1000,
                unread: true,
                linkTo: 'schedule-calendar',
                linkParam: ''
            },
            {
                id: 'n5',
                type: 'case',
                icon: 'mdi:gavel',
                color: 'brand',
                title: '新案件已立案',
                desc: '赵六劳动争议仲裁案已立案, 进入准备阶段',
                timeAgo: '昨天 16:20',
                timestamp: Date.now() - 24 * 60 * 60 * 1000,
                unread: false,
                linkTo: 'case',
                linkParam: '6'
            },
            {
                id: 'n6',
                type: 'document',
                icon: 'mdi:file-pdf-box',
                color: 'brand',
                title: '合同审查完成',
                desc: '北京某科技公司股权回购协议审查报告已生成',
                timeAgo: '昨天 10:15',
                timestamp: Date.now() - 26 * 60 * 60 * 1000,
                unread: false,
                linkTo: 'case',
                linkParam: '7'
            },
            {
                id: 'n7',
                type: 'member',
                icon: 'mdi:account-star-outline',
                color: 'warning',
                title: '会员即将到期',
                desc: '专业版会员还剩 7 天到期, 续费可继续享 8 折优惠',
                timeAgo: '3 天前',
                timestamp: Date.now() - 3 * 24 * 60 * 60 * 1000,
                unread: false,
                linkTo: 'subscription',
                linkParam: ''
            },
            {
                id: 'n8',
                type: 'system',
                icon: 'mdi:update',
                color: 'brand',
                title: '系统升级通知',
                desc: 'LexPrime v2.1 已发布: 新增日程管理三态过滤, 工作台空态优化等',
                timeAgo: '5 天前',
                timestamp: Date.now() - 5 * 24 * 60 * 60 * 1000,
                unread: false,
                linkTo: 'workstation',
                linkParam: ''
            }
        ];
    })();

    // 工作台「今日日程」当前查看的日期 (AppState.todayScheduleDate)
    // 字符串 'YYYY-MM-DD', 默认今天, 用户可前后翻页查看历史/未来日程
    // 不持久化 (用户关掉浏览器重新打开默认回到今天, 避免「上次看的是几号」困惑)
    AppState.todayScheduleDate = (function () {
        var d = new Date();
        return (
            d.getFullYear() +
            '-' +
            String(d.getMonth() + 1).padStart(2, '0') +
            '-' +
            String(d.getDate()).padStart(2, '0')
        );
    })();

    // 个人模板 (AppState.personalTemplates) - 持久化用户上传的模板 (含初始 mock)
    // 字段: id, name, category, creator, updatedAt, size, fmt
    AppState.personalTemplates = (function () {
        try {
            var saved = localStorage.getItem('lexprime_personal_templates');
            if (saved) {
                var data = JSON.parse(saved);
                if (Array.isArray(data)) return data;
            }
        } catch (e) {}
        // 初始 mock 3 条 (来自原 hardcoded HTML)
        return [
            {
                id: 'p1',
                name: '起诉状-借款合同 v1',
                category: '诉状类',
                creator: '张律师',
                updatedAt: '2026-06-15 14:30',
                size: '',
                fmt: '.docx'
            },
            {
                id: 'p2',
                name: '答辩状-买卖合同 v2',
                category: '答辩类',
                creator: '李律师',
                updatedAt: '2026-06-18 10:15',
                size: '',
                fmt: '.docx'
            },
            {
                id: 'p3',
                name: '律师函-催款函 v1',
                category: '合同类',
                creator: '王律师',
                updatedAt: '2026-06-20 16:40',
                size: '',
                fmt: '.docx'
            }
        ];
    })();

    // ===== 新建日程弹窗 =====

    // ===== 更新今日日程角标 =====

    // ===== 今日日程筛选 =====

    // ===== 需要关注筛选 =====

    // ===== 案件动态筛选 =====

    // ===== 图表初始化（已移除） =====
    // 统计模块已删除，Chart.js 引用及 initCharts 函数已移除

    // ===== 日程详情弹窗 =====
    let currentDetailScheduleId = null;

    // ===== 冲突自动处理 =====
    let pendingSchedule = null;

    // ===== 庭审冲突预警 =====

    // ===== 动态详情弹窗 =====

    // ===== 动态搜索筛选 =====

    // ===== 发布动态 =====
    // var selectedDynamicType = '紧急'; // → AppState.selectedDynamicType

    // 动态发布 - 附件上传
    // var dynamicAttachments = []; // → AppState.dynamicAttachments

    // ===== 案件动态 - 视图切换 =====
    // var dynamicsViewData = [...] // → AppState.dynamicsViewData
    AppState.dynamicsViewData = [
        {
            type: '紧急',
            typeClass: 'bg-red-100 text-red-700',
            icon: 'mdi:alert-circle-outline',
            iconColor: 'text-red-500',
            title: '举证期限即将截止',
            caseName: '张三合同纠纷',
            time: '2026-06-10',
            desc: '举证期限将于2026年6月23日截止'
        },
        {
            type: '文书',
            typeClass: 'bg-blue-100 text-blue-700',
            icon: 'mdi:file-document-outline',
            iconColor: 'text-blue-500',
            title: '起诉状已完成',
            caseName: '李四借贷纠纷',
            time: '2026-06-09',
            desc: '民事起诉状已完成最终审核'
        },
        {
            type: '文书',
            typeClass: 'bg-blue-100 text-blue-700',
            icon: 'mdi:file-document-outline',
            iconColor: 'text-blue-500',
            title: '证据目录已更新',
            caseName: '王五股权转让纠纷',
            time: '2026-06-08',
            desc: '新增证据5-8号'
        },
        {
            type: '开庭',
            typeClass: 'bg-purple-100 text-purple-700',
            icon: 'mdi:gavel',
            iconColor: 'text-purple-500',
            title: '开庭日期已确定',
            caseName: '赵六劳动争议',
            time: '2026-06-07',
            desc: '2026年7月15日上午9:00开庭'
        },
        {
            type: '开庭',
            typeClass: 'bg-purple-100 text-purple-700',
            icon: 'mdi:gavel',
            iconColor: 'text-purple-500',
            title: '合议庭组成已确定',
            caseName: '孙七建设工程合同纠纷',
            time: '2026-06-06',
            desc: '审判长：张明法官'
        },
        {
            type: '归档',
            typeClass: 'bg-green-100 text-green-700',
            icon: 'mdi:archive-outline',
            iconColor: 'text-green-500',
            title: '案件已归档',
            caseName: '周八借款纠纷',
            time: '2026-06-05',
            desc: '已结案归档，档案第3柜12号'
        },
        {
            type: '归档',
            typeClass: 'bg-green-100 text-green-700',
            icon: 'mdi:archive-outline',
            iconColor: 'text-green-500',
            title: '判决书已上传',
            caseName: '吴九房屋租赁合同纠纷',
            time: '2026-06-04',
            desc: '一审判决书已收到并上传'
        },
        {
            type: '提醒',
            typeClass: 'bg-amber-100 text-amber-700',
            icon: 'mdi:bell-outline',
            iconColor: 'text-amber-500',
            title: '续约提醒',
            caseName: '某科技公司',
            time: '2026-06-03',
            desc: '顾问合同将于2026年7月1日到期'
        }
    ];

    // ===== AI一键提取要点 =====
    // var selectedExtractSource = 'case';
    function openAIExtractModal() {
        document.getElementById('extract-result-area').classList.add('hidden');
        document.getElementById('extract-loading').classList.add('hidden');
        document.getElementById('ai-extract-modal').classList.remove('hidden');
    }

    // ===== 批量上传 =====
    // var batchFiles = []; // → AppState.batchFiles
    function openBatchUploadModal() {
        document.getElementById('batch-upload-modal').classList.remove('hidden');
    }
    function closeBatchUploadModal() {
        document.getElementById('batch-upload-modal').classList.add('hidden');
    }
    function handleBatchSelect(input) {
        for (var i = 0; i < input.files.length; i++) {
            addBatchFile(input.files[i]);
        }
        input.value = '';
        renderBatchFiles();
    }
    function handleBatchDrop(event) {
        for (var i = 0; i < event.dataTransfer.files.length; i++) {
            addBatchFile(event.dataTransfer.files[i]);
        }
        renderBatchFiles();
    }
    function addBatchFile(file) {
        if (AppState.batchFiles.length >= 20) {
            alert('最多上传 20 个文件');
            return;
        }
        var icon = 'mdi:file-document-outline';
        var ext = file.name.split('.').pop().toLowerCase();
        if (['png', 'jpg', 'jpeg', 'gif', 'webp'].indexOf(ext) !== -1) icon = 'mdi:file-image-outline';
        else if (['pdf'].indexOf(ext) !== -1) icon = 'mdi:file-pdf-outline';
        else if (['doc', 'docx'].indexOf(ext) !== -1) icon = 'mdi:file-word-outline';
        else if (['xls', 'xlsx'].indexOf(ext) !== -1) icon = 'mdi:file-excel-outline';
        var size = file.size;
        var sizeStr =
            size < 1024
                ? size + 'B'
                : size < 1048576
                    ? (size / 1024).toFixed(1) + 'KB'
                    : (size / 1048576).toFixed(1) + 'MB';
        AppState.batchFiles.push({
            id: 'batch_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
            name: file.name,
            size: sizeStr,
            icon: icon,
            file: file
        });
    }
    function renderBatchFiles() {
        var area = document.getElementById('batch-progress-area');
        var list = document.getElementById('batch-file-list');
        var count = document.getElementById('batch-file-count');
        var uploadBtn = document.getElementById('batch-upload-count');
        if (AppState.batchFiles.length === 0) {
            area.classList.add('hidden');
            return;
        }
        area.classList.remove('hidden');
        count.textContent = AppState.batchFiles.length;
        uploadBtn.textContent = AppState.batchFiles.length;
        var html = '';
        AppState.batchFiles.forEach(function (f) {
            html +=
                '<div class="flex items-center gap-2 bg-white rounded-lg border border-[#E5E6EB] px-3 py-2">' +
                '<iconify-icon icon="' +
                f.icon +
                '" class="text-base text-[#165DFF] flex-shrink-0"></iconify-icon>' +
                '<div class="flex-1 min-w-0"><p class="text-xs text-gray-700 truncate">' +
                f.name +
                '</p><p class="text-[10px] text-gray-400">' +
                f.size +
                '</p></div>' +
                '<button onclick="removeBatchFile(\'' +
                f.id +
                '\')" class="text-gray-400 hover:text-red-500 flex-shrink-0"><iconify-icon icon="mdi:close-circle"></iconify-icon></button>' +
                '</div>';
        });
        list.innerHTML = html;
    }
    function removeBatchFile(id) {
        AppState.batchFiles = AppState.batchFiles.filter(function (f) {
            return f.id !== id;
        });
        renderBatchFiles();
    }
    function clearBatchFiles() {
        AppState.batchFiles = [];
        renderBatchFiles();
    }
    function confirmBatchUpload() {
        if (AppState.batchFiles.length === 0) {
            alert('请先选择文件');
            return;
        }
        var count = AppState.batchFiles.length;
        AppState.batchFiles.forEach(function (f) {
            addDynamicFile(f.file);
        });
        AppState.batchFiles = [];
        renderBatchFiles();
        closeBatchUploadModal();
        setTimeout(function () {
            alert('成功上传 ' + count + ' 个文件到附件列表');
        }, 100);
    }

    // 全局 Toast 提示
    function showToast(message) {
        var existing = document.querySelector('.custom-toast');
        if (existing) existing.remove();
        var toast = document.createElement('div');
        toast.className =
            'custom-toast fixed top-4 right-4 z-[9999] bg-green-50 border border-green-200 text-green-700 text-xs px-4 py-2.5 rounded-lg shadow-lg flex items-center gap-2 transform transition-all duration-300';
        toast.innerHTML =
            '<iconify-icon icon="mdi:check-circle-outline" class="text-green-500"></iconify-icon><span>' +
            (message || '操作成功') +
            '</span>';
        document.body.appendChild(toast);
        setTimeout(function () {
            toast.style.opacity = '0';
            setTimeout(function () {
                toast.remove();
            }, 300);
        }, 2500);
    }

    // ===== 移动端底部导航 =====
    function setMobileTabActive(btn) {
        var tabs = document.querySelectorAll('[data-mobile-tab]');
        tabs.forEach(function (t) {
            t.classList.remove('text-brand');
            t.classList.add('text-fg-tertiary');
            t.setAttribute('aria-selected', 'false');
        });
        if (btn) {
            btn.classList.remove('text-fg-tertiary');
            btn.classList.add('text-brand');
            btn.setAttribute('aria-selected', 'true');
        }
    }

    // ===== globalThis 桥接 (IIFE 内导出, 让其他模块可见) =====
    globalThis.showToast = showToast;
    globalThis.shareCase = shareCase;
    globalThis.setMobileTabActive = setMobileTabActive;

    // login view 加载后绑定事件
})();

// 页面加载时检查 template 视图是否需要修复 DOM 重组
(function () {
    function tryFix() {
        if (document.getElementById('view-template') && typeof fixTemplateViewDOM === 'function') {
            fixTemplateViewDOM();
        }
    }
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(tryFix, 50);
        setTimeout(tryFix, 300);
    } else {
        document.addEventListener('DOMContentLoaded', function () {
            setTimeout(tryFix, 50);
            setTimeout(tryFix, 300);
        });
    }
    // 兜底: 监听 main-content 变化, view-template 出现时立即修
    var main = document.getElementById('main-content');
    if (main) {
        var obs = new MutationObserver(function () {
            if (document.getElementById('view-template')) {
                setTimeout(tryFix, 30);
            }
        });
        obs.observe(main, { childList: true });
    }
})();
