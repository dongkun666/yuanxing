const globals = require('globals');

module.exports = [
    {
        ignores: ['assets/js/iconify-icon.min.js']
    },
    {
        languageOptions: {
            ecmaVersion: 2020,
            sourceType: 'script',
            globals: {
                ...globals.browser,
                ...globals.node,
                Utils: 'readonly',
                showToast: 'readonly',
                switchView: 'readonly',
                switchToList: 'readonly',
                switchToMemberCenter: 'readonly',
                setMobileTabActive: 'readonly',
                AppState: 'readonly',
                API: 'readonly',
                escapeHtml: 'readonly',
                Iconify: 'readonly',
                hljs: 'readonly',
                Chart: 'readonly',
                echarts: 'readonly',
                Vue: 'readonly',
                Auth: 'readonly',
                loadView: 'readonly',
                switchSidebarTab: 'readonly',
                setupOutsideClickClose: 'readonly',
                fixTemplateViewDOM: 'readonly',
                renderPersonalTemplates: 'readonly',
                renderScheduleList: 'readonly',
                filterScheduleByDate: 'readonly',
                setNotificationsFilter: 'readonly',
                initAttachmentList: 'readonly',
                initAttentionList: 'readonly',
                initArchive: 'readonly',
                initFirm: 'readonly',
                initOrders: 'readonly',
                switchDynamicsView: 'readonly',
                initCaseDynamics: 'readonly',
                initCompaniesDb: 'readonly',
                initCasesDb: 'readonly',
                initZhixing: 'readonly',
                initLawsDb: 'readonly',
                initDeadlineView: 'readonly',
                initAIDocView: 'readonly',
                initCaseProgress: 'readonly',
                updateTodayScheduleBadge: 'readonly',
                renderTodayScheduleDateControls: 'readonly',
                renderTodaySchedule: 'readonly'
            }
        },
        rules: {
            'strict': ['error', 'function'],
            'no-unused-vars': ['warn', { 'varsIgnorePattern': '^_' }],
            'no-undef': 'error',
            'no-console': ['warn', { 'allow': ['warn', 'error'] }],
            'no-alert': 'warn',
            'eqeqeq': ['error', 'always'],
            'no-empty': ['error', { 'allowEmptyCatch': true }],
            'no-extra-semi': 'error',
            'semi': ['error', 'always'],
            'no-trailing-spaces': 'error',
            'quotes': ['error', 'single', { 'allowTemplateLiterals': true }],
            'comma-spacing': ['error', { 'before': false, 'after': true }],
            'indent': ['error', 4],
            'max-len': ['warn', { 'code': 150 }],
            'no-redeclare': ['error', { 'builtinGlobals': true }],
            'no-self-assign': 'error',
            'no-self-compare': 'error',
            'no-unreachable': 'error',
            'no-unsafe-negation': 'error',
            'valid-typeof': 'error'
        }
    }
];
