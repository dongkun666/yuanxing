/**
 * D3 W8 6 项 P1-P3 UI 修复 截图脚本
 *
 * 截 5 页面 × 2 视口 (桌面 1280×800 + 移动 375×667) = 10 张图
 * + 0/3/5 致命条款 3 种 case 各 1 张 (375×667) = 3 张图
 * = 共 13 张图, 落档到 docs/qa/d3-ui-fixes-w8/screenshots/
 *
 * 跑法: node scripts/d3-screenshots.js
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const REPO_ROOT = path.resolve(__dirname, '..');
const SCREENSHOT_DIR = path.join(REPO_ROOT, 'docs', 'qa', 'd3-ui-fixes-w8', 'screenshots');
// 用 http 127.0.0.1:8080 (python -m http.server 已在跑) 避免 file:// fetch 限制
const INDEX_URL = 'http://127.0.0.1:8080/index.html';

const PAGES = [
  { id: 'view-contract-review-upload',      name: '01-upload' },
  { id: 'view-contract-review-result',      name: '02-result' },
  { id: 'view-contract-review-suggestion',  name: '03-suggestion' },
  { id: 'view-contract-review-negotiation', name: '04-negotiation' },
  { id: 'view-contract-review-export',      name: '05-export' },
];

const VIEWPORTS = [
  { name: 'desktop', width: 1280, height: 800, isMobile: false },
  { name: 'mobile',  width: 375,  height: 667, isMobile: true },
];

const FATAL_TEST_CASES = [
  { name: '0-fatal', queryParam: '?test_fatals=0' },
  { name: '3-fatal', queryParam: '?test_fatals=3' },
  { name: '5-fatal', queryParam: '?test_fatals=5' },
];

async function main() {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }
  const browser = await chromium.launch({ headless: true });
  const summary = { pages: [], fatal_cases: [] };

  // ====== 1. 5 页面 × 2 视口 ======
  for (const vp of VIEWPORTS) {
    const ctx = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: 1,
      isMobile: vp.isMobile,
    });
    const page = await ctx.newPage();
    await page.goto(INDEX_URL, { waitUntil: 'networkidle', timeout: 30000 });
    // 等 contract-review.js 加载 (v=2 缓存破坏)
    await page.waitForFunction(() => window.CR && typeof window.CR.__updateStancePreview === 'function', { timeout: 10000 });

    for (const pg of PAGES) {
      // 切换到对应 view (用 switchView 触发 fetch + 显示)
      const viewId = pg.id.replace('view-', '');
      await page.evaluate((vid) => {
        if (typeof window.switchView === 'function') {
          window.switchView(vid, null);
        } else {
          // fallback: 直接 DOM 操作
          document.querySelectorAll('.view-content').forEach(el => el.classList.add('hidden'));
          const target = document.getElementById('view-' + vid);
          if (target) target.classList.remove('hidden');
        }
      }, viewId);
      // 等 view 加载 (可能需要 fetch)
      await page.waitForTimeout(800);
      const file = path.join(SCREENSHOT_DIR, `${pg.name}-${vp.name}.png`);
      await page.screenshot({ path: file, fullPage: false });
      summary.pages.push({ page: pg.name, viewport: vp.name, file });
      console.log(`  📸 ${pg.name} (${vp.name})`);
    }
    await ctx.close();
  }

  // ====== 2. 致命条款 0/3/5 三种 case (移动端) ======
  const mobileCtx = await browser.newContext({
    viewport: { width: 375, height: 667 },
    deviceScaleFactor: 1,
    isMobile: true,
  });
  for (const tc of FATAL_TEST_CASES) {
    const page = await mobileCtx.newPage();
    await page.goto(INDEX_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForFunction(() => window.CR && typeof window.CR.__applyFatalCollapse === 'function', { timeout: 10000 });
    // 切换到 result view
    await page.evaluate(() => {
      if (typeof window.switchView === 'function') {
        window.switchView('contract-review-result', null);
      }
    });
    // 等 view 加载 + 内联脚本运行完成
    await page.waitForSelector('#fatal-clauses-container', { timeout: 5000 });
    await page.waitForTimeout(800);
    // 现在清空 + 注入测试数据 + 应用折叠
    const n = parseInt(tc.queryParam.replace('?test_fatals=', ''), 10);
    const result = await page.evaluate((count) => {
      if (typeof window.CR.__testInjectFatalClauses === 'function') {
        window.CR.__testInjectFatalClauses(count);
      }
      if (typeof window.CR.__applyFatalCollapse === 'function') {
        return window.CR.__applyFatalCollapse(3);
      }
      return null;
    }, n);
    await page.waitForTimeout(300);
    const file = path.join(SCREENSHOT_DIR, `fatal-${tc.name}-mobile.png`);
    await page.screenshot({ path: file, fullPage: false });
    summary.fatal_cases.push({ case: tc.name, file, result });
    console.log(`  📸 fatal ${tc.name} (mobile) result:`, JSON.stringify(result));
    await page.close();
  }
  await mobileCtx.close();

  // ====== 3. 桌面端 5 致命 完整截图 (含 toggle 按钮) ======
  const desktopCtx = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
    isMobile: false,
  });
  const page = await desktopCtx.newPage();
  await page.goto(INDEX_URL, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForFunction(() => window.CR && typeof window.CR.__updateStancePreview === 'function', { timeout: 10000 });
  await page.evaluate(() => {
    if (typeof window.switchView === 'function') {
      window.switchView('contract-review-result', null);
    }
  });
  await page.waitForTimeout(1000);
  const file = path.join(SCREENSHOT_DIR, '02-result-5-fatal-desktop.png');
  await page.screenshot({ path: file, fullPage: false });
  console.log('  📸 02-result 5 fatal (desktop, default)');
  await desktopCtx.close();

  await browser.close();

  // 写 summary
  const summaryFile = path.join(SCREENSHOT_DIR, '..', 'screenshot-summary.json');
  fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2), 'utf-8');
  console.log(`\n✅ D3 W8 截图完成, 共 ${summary.pages.length} 页面 + ${summary.fatal_cases.length} 致命 case`);
  console.log(`   落档: ${SCREENSHOT_DIR}`);
  console.log(`   摘要: ${summaryFile}`);
}

main().catch(err => {
  console.error('❌ 截图失败:', err);
  process.exit(1);
});
