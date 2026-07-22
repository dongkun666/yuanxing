const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const zlib = require('zlib');
const CleanCSS = require('clean-css');
const { minify: terserMinify } = require('terser');

const ROOT_DIR = path.join(__dirname, '..');
const ASSETS_CSS_DIR = path.join(ROOT_DIR, 'assets', 'css');
const ASSETS_JS_DIR = path.join(ROOT_DIR, 'assets', 'js');
const JS_DIST_DIR = path.join(ASSETS_JS_DIR, 'dist');
const CSS_DIST_DIR = path.join(ASSETS_CSS_DIR, 'dist');

const ENABLE_GZIP = true;
const ENABLE_BROTLI = true;
const ENABLE_CRITICAL_INLINE = true;

function formatBytes(bytes) {
  return (bytes / 1024).toFixed(2) + ' KB';
}

async function buildTailwind() {
  const { execSync } = require('child_process');

  const inputFile = path.join(ASSETS_CSS_DIR, 'tailwind-input.css');
  const outputFile = path.join(CSS_DIST_DIR, 'tailwind.min.css');

  if (!fs.existsSync(CSS_DIST_DIR)) {
    fs.mkdirSync(CSS_DIST_DIR, { recursive: true });
  }

  const inputSize = fs.existsSync(path.join(ASSETS_CSS_DIR, 'tailwind.css'))
    ? Buffer.byteLength(fs.readFileSync(path.join(ASSETS_CSS_DIR, 'tailwind.css'), 'utf8'), 'utf8')
    : 0;

  execSync(
    `npx tailwindcss -i "${inputFile}" -o "${outputFile}" --minify`,
    { cwd: ROOT_DIR, stdio: 'pipe' }
  );

  const output = fs.readFileSync(outputFile, 'utf8');
  const minifiedSize = Buffer.byteLength(output, 'utf8');

  const reduction = inputSize > 0
    ? ((1 - minifiedSize / inputSize) * 100).toFixed(1)
    : 'N/A';

  console.log('=== Tailwind CSS ===');
  console.log(`  tailwind-input.css -> dist/tailwind.min.css (JIT + purge + minify)`);
  console.log(`  原 tailwind.css:  ${formatBytes(inputSize)}`);
  console.log(`  编译压缩后:       ${formatBytes(minifiedSize)}`);
  console.log(`  减少:             ${reduction}%`);
  console.log();
}

async function buildCustomCSS() {
  const files = ['styles.css', 'marketplace.css'];
  const results = [];

  if (!fs.existsSync(CSS_DIST_DIR)) {
    fs.mkdirSync(CSS_DIST_DIR, { recursive: true });
  }

  for (const file of files) {
    const inputPath = path.join(ASSETS_CSS_DIR, file);
    if (!fs.existsSync(inputPath)) continue;

    const outputPath = path.join(CSS_DIST_DIR, file.replace('.css', '.min.css'));
    const input = fs.readFileSync(inputPath, 'utf8');
    const originalSize = Buffer.byteLength(input, 'utf8');

    const result = new CleanCSS().minify(input);
    const output = result.styles;
    const minifiedSize = Buffer.byteLength(output, 'utf8');

    fs.writeFileSync(outputPath, output);

    const reduction = ((1 - minifiedSize / originalSize) * 100).toFixed(1);
    results.push({ file, originalSize, minifiedSize, reduction });
  }

  console.log('=== 自定义 CSS ===');
  for (const r of results) {
    const outName = r.file.replace('.css', '.min.css');
    console.log(`  ${r.file} -> dist/${outName}`);
    console.log(`    原始大小: ${formatBytes(r.originalSize)}`);
    console.log(`    压缩后:   ${formatBytes(r.minifiedSize)}`);
    console.log(`    减少:     ${r.reduction}%`);
  }
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

function getFileHash(filePath) {
  const content = fs.readFileSync(filePath);
  return crypto.createHash('md5').update(content).digest('hex').slice(0, 8);
}

function compressFile(inputPath) {
  if (!fs.existsSync(inputPath)) return;

  const content = fs.readFileSync(inputPath);
  const originalSize = content.length;

  if (ENABLE_GZIP) {
    const gzipContent = zlib.gzipSync(content, { level: zlib.constants.Z_BEST_COMPRESSION });
    fs.writeFileSync(inputPath + '.gz', gzipContent);
    console.log(`    gzip:    ${formatBytes(gzipContent.length)} (${((1 - gzipContent.length / originalSize) * 100).toFixed(1)}%)`);
  }

  if (ENABLE_BROTLI) {
    const brotliContent = zlib.brotliCompressSync(content, {
      params: { [zlib.constants.BROTLI_PARAM_QUALITY]: 11 }
    });
    fs.writeFileSync(inputPath + '.br', brotliContent);
    console.log(`    brotli:  ${formatBytes(brotliContent.length)} (${((1 - brotliContent.length / originalSize) * 100).toFixed(1)}%)`);
  }
}

function inlineCriticalResources(html) {
  if (!ENABLE_CRITICAL_INLINE) return html;

  const criticalJsFiles = ['api.js', 'auth.js', 'app-state.js', 'router.js', 'utils.js'];
  const criticalCssFiles = ['tailwind.min.css'];

  let result = html;

  criticalJsFiles.forEach(function (file) {
    const filePath = path.join(JS_DIST_DIR, file);
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8');
      const scriptTag = '<script src="./assets/js/dist/' + file + '[^"]*"></script>';
      const regex = new RegExp(scriptTag, 'g');
      result = result.replace(regex, '<script>' + content + '</script>');
    }
  });

  criticalCssFiles.forEach(function (file) {
    const filePath = path.join(CSS_DIST_DIR, file);
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8');
      const linkTag = '<link rel="stylesheet" href="./assets/css/dist/' + file + '[^"]*">';
      const regex = new RegExp(linkTag, 'g');
      result = result.replace(regex, '<style>' + content + '</style>');
    }
  });

  return result;
}

function addPreloadLinks(html) {
  const preloadResources = [
    { type: 'script', href: './assets/js/dist/script.js' },
    { type: 'script', href: './assets/js/dist/cases-list.js' },
    { type: 'script', href: './assets/js/dist/cases-detail.js' },
    { type: 'style', href: './assets/css/dist/styles.min.css' },
    { type: 'style', href: './assets/css/dist/marketplace.min.css' },
    { type: 'font', href: './assets/fonts/Inter-Regular.woff2', as: 'font' }
  ];

  let preloadHtml = '';
  preloadResources.forEach(function (res) {
    const asAttr = res.as ? 'as="' + res.as + '"' : '';
    preloadHtml += '<link rel="preload" ' + asAttr + ' href="' + res.href + '">\n';
  });

  const prefetchResources = [
    { type: 'script', href: './assets/js/dist/schedule.js' },
    { type: 'script', href: './assets/js/dist/knowledge.js' },
    { type: 'script', href: './assets/js/dist/marketplace.js' }
  ];

  prefetchResources.forEach(function (res) {
    preloadHtml += '<link rel="prefetch" href="' + res.href + '">\n';
  });

  return html.replace('<!-- Tailwind CSS -->', preloadHtml + '<!-- Tailwind CSS -->');
}

function compressDistFiles() {
  console.log('=== 资源压缩 ===');

  const jsFiles = fs.readdirSync(JS_DIST_DIR).filter(function (file) {
    return file.endsWith('.js');
  });

  jsFiles.forEach(function (file) {
    const filePath = path.join(JS_DIST_DIR, file);
    console.log(`  ${file}:`);
    compressFile(filePath);
  });

  const cssFiles = fs.readdirSync(CSS_DIST_DIR).filter(function (file) {
    return file.endsWith('.css');
  });

  cssFiles.forEach(function (file) {
    const filePath = path.join(CSS_DIST_DIR, file);
    console.log(`  ${file}:`);
    compressFile(filePath);
  });

  console.log();
}

// 生成生产版 index.html: 把 JS/CSS 引用切换到 dist 压缩产物 + 内容哈希
// 保留 index.html 作为开发版, 输出 index.prod.html 供部署使用
function buildProdHtml() {
  const srcFile = path.join(ROOT_DIR, 'index.html');
  const outFile = path.join(ROOT_DIR, 'index.prod.html');

  let html = fs.readFileSync(srcFile, 'utf8');

  // 替换 JS 引用: ./assets/js/XXX.js?v=N -> ./assets/js/dist/XXX.js?v=<hash>
  // 不动 iconify-icon.min.js (第三方已压缩, 不在 dist 内)
  html = html.replace(/\.\/assets\/js\/([a-z0-9-]+\.js)(\?v=\d+)?/g, function (match, fileName) {
    if (fileName === 'iconify-icon.min.js') return match;
    const distPath = path.join(JS_DIST_DIR, fileName);
    if (!fs.existsSync(distPath)) return match;
    const hash = getFileHash(distPath);
    return './assets/js/dist/' + fileName + '?v=' + hash;
  });

  // 替换 Tailwind CSS: tailwind.css -> dist/tailwind.min.css
  html = html.replace(/\.\/assets\/css\/tailwind\.css(\?v=\d+)?/g, function () {
    const cssPath = path.join(CSS_DIST_DIR, 'tailwind.min.css');
    if (!fs.existsSync(cssPath)) return match;
    const hash = getFileHash(cssPath);
    return './assets/css/dist/tailwind.min.css?v=' + hash;
  });

  // 替换自定义 CSS: styles.css / marketplace.css -> dist/*.min.css
  const customCssFiles = ['styles.css', 'marketplace.css'];
  customCssFiles.forEach(function (file) {
    const minName = file.replace('.css', '.min.css');
    const distPath = path.join(CSS_DIST_DIR, minName);
    if (!fs.existsSync(distPath)) return;
    const hash = getFileHash(distPath);
    const regex = new RegExp(
      '\\.\\/assets\\/css\\/' + file.replace('.', '\\.') + '(\\?v=\\d+)?',
      'g'
    );
    html = html.replace(regex, './assets/css/dist/' + minName + '?v=' + hash);
  });

  // 添加资源预加载和预获取
  html = addPreloadLinks(html);

  // 内联关键资源
  html = inlineCriticalResources(html);

  fs.writeFileSync(outFile, html);
  console.log('=== 生产 HTML ===');
  console.log('  index.html -> index.prod.html');
  console.log('  切换: JS/CSS 全部指向 dist/ 压缩产物 + 内容哈希');
  console.log('  优化: 添加 preload/prefetch 资源预加载');
  console.log('  优化: 关键 CSS/JS 内联到 HTML');
  console.log('  部署时: 用 index.prod.html 替换 index.html');
  console.log();
}

async function main() {
  console.log('开始构建...\n');

  try {
    await buildTailwind();
    await buildCustomCSS();
    await buildJS();
    compressDistFiles();
    buildProdHtml();
    console.log('构建完成！');
  } catch (err) {
    console.error('构建失败:', err);
    process.exit(1);
  }
}

main();
