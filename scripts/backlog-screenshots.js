/**
 * A2 W8 PRD backlog 总览 截图脚本
 *
 * 截 backlog 视图 (5 视图: 总览/按状态/按优先级/按 owner/按来源律师)
 * 桌面 + 移动 = 10 张图, 落档到 docs/qa/backlog-board-w8/screenshots/
 *
 * 跑法: node scripts/backlog-screenshots.js
 *
 * 依赖: index.html + http://127.0.0.1:8080 + http://127.0.0.1:8000/api/backlog/board
 *       (需要先跑 backend uvicorn + dev server)
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const REPO_ROOT = path.resolve(__dirname, '..');
const SCREENSHOT_DIR = path.join(REPO_ROOT, 'docs', 'qa', 'backlog-board-w8', 'screenshots');
const INDEX_URL = 'http://127.0.0.1:8080/index.html';

// 5 视图
const VIEWS = [
  { id: 'summary', name: '01-summary', label: '总览' },
  { id: 'status', name: '02-status', label: '按状态' },
  { id: 'priority', name: '03-priority', label: '按优先级' },
  { id: 'owner', name: '04-owner', label: '按 Owner' },
  { id: 'source', name: '05-source', label: '按来源律师' }
];

const VIEWPORTS = [
  { name: 'desktop', width: 1280, height: 800, isMobile: false },
  { name: 'mobile',  width: 375,  height: 667, isMobile: true }
];

async function main() {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }
  const browser = await chromium.launch({ headless: true });
  const summary = { captured: [] };

  for (const vp of VIEWPORTS) {
    const ctx = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: 1,
      isMobile: vp.isMobile
    });
    const page = await ctx.newPage();

    // 网络监听 (检测 API 调用)
    page.on('response', resp => {
      if (resp.url().includes('/api/backlog/')) {
        console.log(`  🔗 ${resp.status()} ${resp.url().substring(resp.url().indexOf('/api/'))}`);
      }
    });

    await page.goto(INDEX_URL, { waitUntil: 'networkidle', timeout: 30000 });

    // 切到 backlog view
    await page.evaluate(() => {
      if (typeof window.switchView === 'function') {
        window.switchView('backlog', null);
      } else {
        document.querySelectorAll('.view-content').forEach(el => el.classList.add('hidden'));
        const target = document.getElementById('view-backlog');
        if (target) target.classList.remove('hidden');
      }
    });

    // 等 view 渲染
    await page.waitForTimeout(1500);

    // 截 5 个视图
    for (const v of VIEWS) {
      await page.evaluate((viewId) => {
        const btn = document.querySelector(`#view-backlog .view-tab[data-view="${viewId}"]`);
        if (btn) btn.click();
      }, v.id);
      await page.waitForTimeout(600);
      const file = path.join(SCREENSHOT_DIR, `${v.name}-${vp.name}.png`);
      await page.screenshot({ path: file, fullPage: false });
      summary.captured.push({ view: v.name, viewport: vp.name, file, label: v.label });
      console.log(`  📸 ${v.label} (${vp.name})`);
    }

    await ctx.close();
  }

  await browser.close();

  // 写 summary
  const summaryFile = path.join(SCREENSHOT_DIR, '..', 'screenshot-summary.json');
  fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2), 'utf-8');
  console.log(`\n✅ A2 backlog 截图完成, 共 ${summary.captured.length} 张图`);
  console.log(`   落档: ${SCREENSHOT_DIR}`);
  console.log(`   摘要: ${summaryFile}`);
}

main().catch(err => {
  console.error('❌ 截图失败:', err);
  process.exit(1);
});
