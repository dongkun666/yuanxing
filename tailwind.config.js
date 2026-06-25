/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './templates/modals.html',
    './templates/views/**/*.html',
    './assets/js/script.js'
  ],
  // 由于代码里大量使用 arbitrary value（如 bg-[#165DFF]），Tailwind 3 已支持扫描这些
  theme: {
    extend: {
      colors: {
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
        'arco-success': '#00B42A',
        'arco-warning': '#FF7D00',
        'arco-danger': '#F53F3F'
      }
    }
  },
  plugins: []
}
