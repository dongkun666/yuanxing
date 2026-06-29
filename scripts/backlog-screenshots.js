/**
 * W9 A1 PRD backlog 总览 截图脚本 (修 A2 router.js bug)
 *
 * 截 backlog 视图 (5 视图: 总览/按状态/按优先级/按 owner/按来源律师)
 * 桌面 + 移动 = 10 张图, 落档到 docs/qa/backlog-board-w9/screenshots/
 *
 * 跑法: node scripts/backlog-screenshots.js
 *
 * 依赖: index.html + http://127.0.0.1:8080 + http://127.0.0.1:8000/api/backlog/board
 *
 * A2 commit 5cdaabe 的 router.js 用 insertAdjacentHTML 注入 view html, 但浏览器
 * 不执行 innerHTML 里的 <script> 标签 → backlog IIFE 没跑 → __loadBacklogBoard undefined.
 * 本脚本绕过 router, 直接 fetch view html + eval script + 调 __loadBacklogBoard.
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const REPO_ROOT = path.resolve(__dirname, '..');
const SCREENSHOT_DIR = path.join(REPO_ROOT, 'docs', 'qa', 'backlog-board-w9', 'screenshots');
const INDEX_URL = 'http://127.0.0.1:8080/index.html';

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

async function injectBacklogView(page) {
  // 1. fetch view html
  const html = await page.evaluate(async () => {
    const r = await fetch('/templates/views/backlog/index.html');
    return await r.text();
  });

  // 2. split html into markup + script blocks
  const scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
  const scripts = [];
  let match;
  while ((match = scriptRegex.exec(html)) !== null) {
    scripts.push(match[1]);
  }
  const markup = html.replace(scriptRegex, '');

  // 3. inject markup (insertAdjacentHTML)
  await page.evaluate((mk) => {
    document.getElementById('main-content').insertAdjacentHTML('beforeend', mk);
    // 4. eval each script block manually (innerHTML script doesn't auto-execute)
  }, markup);

  // 5. run each script via Function constructor (proper scope)
  for (const s of scripts) {
    await page.evaluate((src) => {
      // eslint-disable-next-line no-new-func
      const fn = new Function(src);
      fn();
    }, s);
  }

  // 6. show view-backlog, hide others
  await page.evaluate(() => {
    document.querySelectorAll('.view-content').forEach(el => el.classList.add('hidden'));
    const target = document.getElementById('view-backlog');
    if (target) target.classList.remove('hidden');
    // dev: monkey-patch fetch so /api/* goes to backend 8000 (避免 dev server 8080 404)
    if (!window.__fetchPatched) {
      const orig = window.fetch.bind(window);
      window.fetch = (url, opts) => {
        if (typeof url === 'string' && url.startsWith('/api/')) {
          return orig('http://127.0.0.1:8000' + url, opts);
        }
        return orig(url, opts);
      };
      window.__fetchPatched = true;
    }
  });

  // 7. trigger load
  const hasFn = await page.evaluate(() => typeof window.__loadBacklogBoard);
  if (hasFn === 'function') {
    await page.evaluate(() => window.__loadBacklogBoard());
  } else {
    process.stdout.write('  ⚠️  __loadBacklogBoard still undefined after eval\n');
  }

  // 8. wait for fetch + render
  await page.waitForTimeout(2000);
}

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

    page.on('response', resp => {
      if (resp.url().includes('/api/backlog/')) {
        process.stdout.write(`  🔗 ${resp.status()} ${resp.url().substring(resp.url().indexOf('/api/'))}\n`);
      }
    });

    await page.goto(INDEX_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await injectBacklogView(page);

    const subtitle = await page.evaluate(() => document.getElementById('backlog-subtitle')?.textContent || 'N/A');
    process.stdout.write(`  📋 subtitle: ${subtitle}\n`);

    // 截 5 个视图 (每个 view 切换)
    for (const v of VIEWS) {
      await page.evaluate((viewId) => {
        const btn = document.querySelector(`#view-backlog .view-tab[data-view="${viewId}"]`);
        if (btn) btn.click();
      }, v.id);
      await page.waitForTimeout(800);
      const file = path.join(SCREENSHOT_DIR, `${v.name}-${vp.name}.png`);
      await page.screenshot({ path: file, fullPage: false });
      summary.captured.push({ view: v.name, viewport: vp.name, file, label: v.label });
      process.stdout.write(`  📸 ${v.label} (${vp.name})\n`);
    }

    await ctx.close();
  }

  await browser.close();

  const summaryFile = path.join(SCREENSHOT_DIR, '..', 'screenshot-summary.json');
  fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2), 'utf-8');
  process.stdout.write(`\n✅ W9 A1 backlog 截图完成, 共 ${summary.captured.length} 张图\n`);
  process.stdout.write(`   落档: ${SCREENSHOT_DIR}\n`);
  process.stdout.write(`   摘要: ${summaryFile}\n`);
}

main().catch(err => {
  process.stderr.write('❌ 截图失败: ' + err.message + '\n' + err.stack + '\n');
  process.exit(1);
});