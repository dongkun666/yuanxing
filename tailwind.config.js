/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './templates/modals.html',
    './templates/views/**/*.html',
    './templates/marketplace/**/*.html',
    './assets/js/*.js',
    './assets/js/**/*.js'
  ],
  theme: {
    extend: {
      colors: {
        // ===== 主品牌色 =====
        'brand': {
          DEFAULT: '#165DFF',  // 主蓝 (primary)
          hover: '#4080FF',    // 主蓝 hover
          active: '#0E4AD8',   // 主蓝 active/focus
          tint: '#E8F3FF',     // 主蓝极浅背景
          tint2: '#EEF3FF',    // 主蓝浅背景
          tint3: '#F2F7FF',    // 主蓝更浅背景
          tint4: '#E5EBFF',    // 主蓝 hover 浅背景
        },

        // ===== 灰阶 (从浅到深) =====
        'bg': {
          DEFAULT: '#F2F3F5',
          subtle: '#F7F8FA',
          border: '#E5E6EB',
        },
        'fg': {
          primary: '#1D2129',
          secondary: '#4E5969',
          tertiary: '#86909C',
          disabled: '#C9CDD4',
        },

        // ===== 状态色 =====
        'success': {
          DEFAULT: '#00B42A',
          tint: '#E8FFEA',
        },
        'warning': {
          DEFAULT: '#FF7D00',
          tint: '#FFF7E6',
        },
        'danger': {
          DEFAULT: '#F5222D',
          tint: '#FFF1F0',
        },
        'urgent': {
          DEFAULT: '#FA8C16',
          tint: '#FFF3E0',
        },

        // ===== 业务色 (知识库领域) =====
        'wiki': {
          DEFAULT: '#9333EA',  // Wiki 页面主色 (紫)
          tint: '#F5EBFF',
        },
        'ai': {
          DEFAULT: '#6C5CE7',  // AI 主题色
          tint: '#EDEBFF',
        },
        'wechat': '#07C160',   // 微信绿 (社交登录)

        // ===== 兼容旧名 (过渡期) =====
        'arco-blue-6': '#165DFF',
        'arco-blue-5': '#4080FF',
        'arco-blue-1': '#E8F3FF',
        'arco-gray-1': '#F2F3F5',
        'arco-gray-2': '#F7F8FA',
        'arco-gray-3': '#E5E6EB',
        'arco-gray-10': '#1D2129',
        'arco-gray-8': '#4E5969',
        'arco-gray-6': '#86909C',
        'arco-gray-4': '#C9CDD4',
      },

      // ===== 字号体系 (5 档) =====
      fontSize: {
        'xs': '12px',     // 12 - 辅助文字 (原 11/12/13 收敛到 12)
        'sm': '14px',     // 14 - 正文 (原 13/14 收敛到 14)
        'base': '16px',   // 16 - 强调
        'lg': '20px',     // 20 - 标题
        'xl': '24px',     // 24 - 大标题
        '2xl': '32px',    // 32 - 数字
      },

      // ===== 间距体系 =====
      spacing: {
        '18': '4.5rem',   // 72px
      },
    },
  },
  plugins: [],
}
