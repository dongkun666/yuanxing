/**
 * AppState 模块 - 全局应用状态 (跨模块共享)
 * 拆分自 script.js (2026-06-28 IIFE 拆分计划)
 *
 * 加载顺序: 在 script.js / router.js 之前
 * 依赖: 无
 *
 * 任何模块都可以读 AppState.xxx (globalThis 双绑定)
 * 写入应通过模块的 setter 函数, 避免散落赋值
 */

(function() {
    'use strict';

    var AppState = {
        // ===== 业务状态 =====
        isYearly: false,
        selectedPayment: 'alipay',
        selectedDynamicType: '紧急',
        selectedExtractSource: 'case',
        batchFiles: [],
        dynamicsViewData: [],
        autoSaveTimer: null,
        dynamicAttachments: [],
        notificationsFilter: 'all',

        // ===== Auth 状态 (auth.js / AppState 双向同步) =====
        user: null,
        token: null,

        // ===== 全局错误日志 (上限 50, 防 localStorage 爆炸) =====
        errorLog: [],
    };

    globalThis.AppState = AppState;
})();