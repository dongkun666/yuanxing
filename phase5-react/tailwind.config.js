/** @type {import('tailwindcss').Config} */
// Phase 5.1 复用 yuanxing 根 tailwind.config.js 设计 tokens (W17 phase5-prep §2.1)
// 颜色 / 字号 / 间距 / 业务色 跟根项目保持 100% 一致, 避免重构期双轨 UI 漂移
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // ===== 主品牌色 =====
        'brand': {
          DEFAULT: '#165DFF',
          hover: '#4080FF',
          active: '#0E4AD8',
          tint: '#E8F3FF',
          tint2: '#EEF3FF',
          tint3: '#F2F7FF',
          tint4: '#E5EBFF',
        },
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
        'success': { DEFAULT: '#00B42A', tint: '#E8FFEA' },
        'warning': { DEFAULT: '#FF7D00', tint: '#FFF7E6' },
        'danger':  { DEFAULT: '#F5222D', tint: '#FFF1F0' },
        'urgent':  { DEFAULT: '#FA8C16', tint: '#FFF3E0' },
        'wiki':    { DEFAULT: '#9333EA', tint: '#F5EBFF' },
        'ai':      { DEFAULT: '#6C5CE7', tint: '#EDEBFF' },
        'wechat':  '#07C160',
      },
      fontSize: {
        'xs': '12px',
        'sm': '14px',
        'base': '16px',
        'lg': '20px',
        'xl': '24px',
        '2xl': '32px',
      },
      spacing: {
        '18': '4.5rem',
      },
    },
  },
  plugins: [],
};