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

async function main() {
  console.log('开始构建...\n');

  try {
    await buildCSS();
    await buildJS();
    console.log('构建完成！');
  } catch (err) {
    console.error('构建失败:', err);
    process.exit(1);
  }
}

main();
