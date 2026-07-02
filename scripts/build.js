const fs = require('fs');
const path = require('path');
const CleanCSS = require('clean-css');
const { minify: terserMinify } = require('terser');

const ASSETS_CSS_DIR = path.join(__dirname, '..', 'assets', 'css');
const ASSETS_JS_DIR = path.join(__dirname, '..', 'assets', 'js');
const JS_DIST_DIR = path.join(ASSETS_JS_DIR, 'dist');

function formatBytes(bytes) {
  return (bytes / 1024).toFixed(2) + ' KB';
}

async function buildCSS() {
  const inputFile = path.join(ASSETS_CSS_DIR, 'tailwind.css');
  const outputFile = path.join(ASSETS_CSS_DIR, 'tailwind.min.css');

  const input = fs.readFileSync(inputFile, 'utf8');
  const originalSize = Buffer.byteLength(input, 'utf8');

  const result = new CleanCSS().minify(input);
  const output = result.styles;
  const minifiedSize = Buffer.byteLength(output, 'utf8');

  fs.writeFileSync(outputFile, output);

  const reduction = ((1 - minifiedSize / originalSize) * 100).toFixed(1);

  console.log('=== CSS ===');
  console.log(`  tailwind.css -> tailwind.min.css`);
  console.log(`  原始大小: ${formatBytes(originalSize)}`);
  console.log(`  压缩后:   ${formatBytes(minifiedSize)}`);
  console.log(`  减少:     ${reduction}%`);
  console.log();
}

async function buildJS() {
  if (!fs.existsSync(JS_DIST_DIR)) {
    fs.mkdirSync(JS_DIST_DIR, { recursive: true });
  }

  const files = fs.readdirSync(ASSETS_JS_DIR).filter((file) => {
    return file.endsWith('.js') && !file.endsWith('.min.js') && file !== 'iconify-icon.min.js';
  });

  console.log('=== JS ===');

  for (const file of files) {
    const inputPath = path.join(ASSETS_JS_DIR, file);
    const outputPath = path.join(JS_DIST_DIR, file);

    const input = fs.readFileSync(inputPath, 'utf8');
    const originalSize = Buffer.byteLength(input, 'utf8');

    const result = await terserMinify(input);
    const output = result.code;
    const minifiedSize = Buffer.byteLength(output, 'utf8');

    fs.writeFileSync(outputPath, output);

    const reduction = ((1 - minifiedSize / originalSize) * 100).toFixed(1);

    console.log(`  ${file} -> dist/${file}`);
    console.log(`    原始大小: ${formatBytes(originalSize)}`);
    console.log(`    压缩后:   ${formatBytes(minifiedSize)}`);
    console.log(`    减少:     ${reduction}%`);
  }
}

// 生成生产版 index.html: 把 ./assets/js/XXX.js?v=N 替换为 ./assets/js/dist/XXX.js?v=<hash>
// 保留 index.html 作为开发版, 输出 index.prod.html 供部署使用
function buildProdHtml() {
  const crypto = require('crypto');
  const rootDir = path.join(__dirname, '..');
  const srcFile = path.join(rootDir, 'index.html');
  const outFile = path.join(rootDir, 'index.prod.html');

  let html = fs.readFileSync(srcFile, 'utf8');

  // 替换 ./assets/js/XXX.js?v=N -> ./assets/js/dist/XXX.js?v=<hash>
  // 不动 iconify-icon.min.js (第三方已压缩, 不在 dist 内)
  html = html.replace(/\.\/assets\/js\/([a-z0-9-]+\.js)\?v=\d+/g, function (match, fileName) {
    if (fileName === 'iconify-icon.min.js') return match;
    const distPath = path.join(JS_DIST_DIR, fileName);
    if (!fs.existsSync(distPath)) return match;
    const content = fs.readFileSync(distPath);
    const hash = crypto.createHash('md5').update(content).digest('hex').slice(0, 8);
    return './assets/js/dist/' + fileName + '?v=' + hash;
  });

  // 替换 CSS 引用 (tailwind.css -> tailwind.min.css), 兼容有无 ?v=
  html = html.replace(/\.\/assets\/css\/tailwind\.css(\?v=\d+)?/g, function () {
    const cssPath = path.join(ASSETS_CSS_DIR, 'tailwind.min.css');
    const content = fs.readFileSync(cssPath);
    const hash = crypto.createHash('md5').update(content).digest('hex').slice(0, 8);
    return './assets/css/tailwind.min.css?v=' + hash;
  });

  fs.writeFileSync(outFile, html);
  console.log('=== 生产 HTML ===');
  console.log('  index.html -> index.prod.html (引用 dist 压缩产物 + 内容哈希)');
  console.log('  部署时: 用 index.prod.html 替换 index.html');
  console.log();
}

async function main() {
  console.log('开始构建...\n');

  try {
    await buildCSS();
    await buildJS();
    buildProdHtml();
    console.log('构建完成！');
  } catch (err) {
    console.error('构建失败:', err);
    process.exit(1);
  }
}

main();
