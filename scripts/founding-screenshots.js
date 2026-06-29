/**
 * W13 C1 follow-up: 创始体验官招募页 视觉验证截图 (lex-bd · 2026-06-30)
 *
 * 截 2 张图:
 * - PC:  1440x900 (桌面标准)  → tests/screenshots/founding-pc-{ts}.png
 * - 移动: 375x812 (iPhone 13 mini) → tests/screenshots/founding-mobile-{ts}.png
 *
 * 6 模块完整性检查 (Playwright assertions):
 * 1. 创史价值主张 (¥449/年 5 折 + 终身优先客服) — section.hero-gradient h1
 * 2. 名额倒计时 (剩 80 席 / 总 100 席) — section#countdown + #days-left 已被填充
 * 3. 已加入律师头像 (L1-L6 + WX + BA 8 个卡) — section#founders .rounded-2xl
 * 4. 7/26 启动预告 — section#launch-pre 含 60 分钟启动仪式文案
 * 5. 立即加入按钮 (founding_joined track) — section#apply form#founding-apply-form + #founding-apply-btn
 * 6. 创始群二维码 (placeholder 占位) — section#founding-qr 3 个 mdi:qrcode iconify-icon
 *
 * 跑法:
 *   1. 启 frontend: py -m http.server 8080 (yuanxing 根目录)
 *   2. node scripts/founding-screenshots.js
 *
 * 落档:
 * - tests/screenshots/founding-pc-{timestamp}.png
 * - tests/screenshots/founding-mobile-{timestamp}.png
 * - docs/qa/c1-followup-screenshots/screenshot-summary.json (QA 摘要)
 *
 * 路由: http://127.0.0.1:8080/templates/views/founding/index.html?dev=1
 * (founding/index.html 是 standalone 完整页面, 不需要 router 集成, 不调后端)
 */
const fs = require('fs');
const path = require('path');
const http = require('http');
const { chromium } = require('playwright');

const REPO_ROOT = path.resolve(__dirname, '..');
const SCREENSHOT_DIR = path.join(REPO_ROOT, 'tests', 'screenshots');
const QA_DIR = path.join(REPO_ROOT, 'docs', 'qa', 'c1-followup-screenshots');
const QA_SCREENSHOT_DIR = path.join(QA_DIR, 'screenshots');
const SUMMARY_FILE = path.join(QA_DIR, 'screenshot-summary.json');
const FOUNDING_URL = 'http://127.0.0.1:8080/templates/views/founding/index.html?dev=1';

const VIEWPORTS = [
  { name: 'pc',     width: 1440, height: 900, isMobile: false },
  { name: 'mobile', width: 375,  height: 812, isMobile: true  },
];

// 6 模块选择器 + 内容断言
const MODULES = [
  {
    id: 'founding-value-prop',
    label: '创史价值主张',
    selector: 'section.hero-gradient h1',
    expectText: '5 折',
    extra: '1 年个人版 5 折 · 终身优先客服 · 投票权',
  },
  {
    id: 'countdown',
    label: '名额倒计时',
    selector: 'section#countdown',
    expectText: '名额倒计时',
    extra: '#days-left 已被倒计时填充',
  },
  {
    id: 'advocates',
    label: '已加入律师头像',
    selector: 'section#founders',
    expectText: '创史律师首批名单',
    extra: 'L1-L6 + WX + BA 共 8 个律师卡',
  },
  {
    id: 'launch-teaser',
    label: '7/26 启动预告',
    selector: 'section#launch-pre',
    expectText: '60 分钟启动仪式',
    extra: '7/26 周日 14:00-15:00 公测启动仪式',
  },
  {
    id: 'join-btn',
    label: '立即加入按钮 (申请表单)',
    selector: 'section#apply form#founding-apply-form',
    expectText: '立即申请创始体验官',
    extra: 'button#founding-apply-btn + founding_joined track',
  },
  {
    id: 'qrcode',
    label: '创始群二维码 (placeholder)',
    selector: 'section#founding-qr',
    expectText: '创史律师专属微信群',
    extra: '3 个 mdi:qrcode iconify-icon 占位',
  },
];

// 前置检查: 8080 dev server 是否在跑 + founding URL 可访问
function precheckServer() {
  return new Promise((resolve, reject) => {
    const req = http.get(FOUNDING_URL, { timeout: 5000 }, (res) => {
      if (res.statusCode === 200) {
        resolve({ status: res.statusCode, length: res.headers['content-length'] || 'unknown' });
      } else {
        reject(new Error(`founding URL 返回 ${res.statusCode}, 期望 200`));
      }
    });
    req.on('timeout', () => { req.destroy(new Error('请求超时 (5s)')); });
    req.on('error', (err) => reject(err));
  });
}

function ts() {
  // 20260630-033500 格式
  const d = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

async function runForViewport(browser, vp, timestamp, summary) {
  const ctx = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    deviceScaleFactor: 1,
    isMobile: vp.isMobile,
  });
  const page = await ctx.newPage();

  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', err => consoleErrors.push('PAGE: ' + err.message));

  process.stdout.write(`\n  🚀 视口 ${vp.name} (${vp.width}x${vp.height}, mobile=${vp.isMobile}) 启动\n`);
  await page.goto(FOUNDING_URL, { waitUntil: 'networkidle', timeout: 30000 });

  // ===== 6 模块完整性断言 =====
  const moduleResults = [];
  for (const m of MODULES) {
    try {
      const loc = page.locator(m.selector).first();
      await loc.waitFor({ state: 'visible', timeout: 5000 });
      const text = (await loc.innerText()).trim();
      const containsExpect = text.includes(m.expectText);
      // 额外 deep check
      let extraOk = true;
      let extraDetail = '';
      if (m.id === 'countdown') {
        const daysLeft = await page.locator('#days-left').innerText();
        extraOk = daysLeft !== '--' && /^\d+$/.test(daysLeft);
        extraDetail = `#days-left = "${daysLeft}"`;
      } else if (m.id === 'advocates') {
        const cards = await page.locator('section#founders .grid > div').count();
        extraOk = cards >= 8;
        extraDetail = `律师卡数 = ${cards} (期望 ≥ 8)`;
      } else if (m.id === 'join-btn') {
        const btnVisible = await page.locator('#founding-apply-btn').isVisible();
        extraOk = btnVisible;
        extraDetail = `#founding-apply-btn visible = ${btnVisible}`;
      } else if (m.id === 'qrcode') {
        const qrIcons = await page.locator('section#founding-qr iconify-icon[icon="mdi:qrcode"]').count();
        extraOk = qrIcons >= 3;
        extraDetail = `mdi:qrcode 图标数 = ${qrIcons} (期望 ≥ 3)`;
      }
      const pass = containsExpect && extraOk;
      moduleResults.push({ id: m.id, label: m.label, pass, expectText: m.expectText, extra: m.extra, extraDetail });
      process.stdout.write(`    ${pass ? '✅' : '❌'} ${m.label.padEnd(20, ' ')} expect="${m.expectText}" | ${extraDetail}\n`);
      if (!pass) {
        throw new Error(`模块 ${m.id} (${m.label}) 断言失败: 文本包含=${containsExpect}, extra=${extraOk} (${extraDetail})`);
      }
    } catch (err) {
      moduleResults.push({ id: m.id, label: m.label, pass: false, error: err.message });
      process.stdout.write(`    ❌ ${m.label} 异常: ${err.message}\n`);
      throw err; // 任何一个模块失败就中止, 不留半残截图
    }
  }

  // ===== 截图保存 =====
  const file = path.join(SCREENSHOT_DIR, `founding-${vp.name}-${timestamp}.png`);
  await page.screenshot({ path: file, fullPage: false });
  // 同时复制到 docs/qa/ 归档 (W7-W11 一致落档)
  const qaFile = path.join(QA_SCREENSHOT_DIR, `founding-${vp.name}-${timestamp}.png`);
  fs.copyFileSync(file, qaFile);
  process.stdout.write(`  📸 已保存: ${path.relative(REPO_ROOT, file)}\n`);
  process.stdout.write(`  📸 已归档: ${path.relative(REPO_ROOT, qaFile)}\n`);

  // 验证 localStorage 中有 founding_viewed track event
  const events = await page.evaluate(() => {
    try { return JSON.parse(localStorage.getItem('__founding_events') || '[]'); }
    catch { return []; }
  });
  const viewed = events.find(e => e.event === 'founding_viewed');
  process.stdout.write(`  📊 track events: ${events.length} 个, founding_viewed=${viewed ? '✅' : '❌'}\n`);

  summary.captured.push({
    viewport: vp.name,
    width: vp.width,
    height: vp.height,
    file: path.relative(REPO_ROOT, file),
    qa_file: path.relative(REPO_ROOT, qaFile),
    modules: moduleResults,
    track_viewed: !!viewed,
    track_event_count: events.length,
    console_errors: consoleErrors,
  });

  await ctx.close();
}

async function main() {
  process.stdout.write('🔍 W13 C1 follow-up 截图脚本 (lex-bd · 创始体验官招募页)\n');
  process.stdout.write(`   URL: ${FOUNDING_URL}\n`);
  process.stdout.write(`   视口: PC 1440x900 + 移动 375x812\n`);

  // 前置: dev server 健康检查
  process.stdout.write('\n🩺 前置检查: 8080 dev server + founding URL 可访问性\n');
  try {
    const info = await precheckServer();
    process.stdout.write(`   ✅ founding URL 200 OK (length=${info.length})\n`);
  } catch (err) {
    process.stderr.write(`   ❌ dev server 不可达: ${err.message}\n`);
    process.stderr.write('   请先启: cd E:\\元枢法智前端\\yuanxing && py -m http.server 8080\n');
    process.exit(1);
  }

  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }
  if (!fs.existsSync(QA_SCREENSHOT_DIR)) {
    fs.mkdirSync(QA_SCREENSHOT_DIR, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const summary = {
    task: 'W13 C1-followup-screenshots',
    agent: 'lex-bd',
    timestamp: ts(),
    url: FOUNDING_URL,
    viewports: VIEWPORTS.map(v => ({ name: v.name, w: v.width, h: v.height })),
    modules: MODULES.map(m => ({ id: m.id, label: m.label })),
    captured: [],
  };

  const startTs = ts();
  for (const vp of VIEWPORTS) {
    await runForViewport(browser, vp, startTs, summary);
  }

  await browser.close();

  fs.writeFileSync(SUMMARY_FILE, JSON.stringify(summary, null, 2), 'utf-8');
  process.stdout.write(`\n✅ W13 C1-followup 截图完成\n`);
  process.stdout.write(`   共 ${summary.captured.length} 张图\n`);
  process.stdout.write(`   主落档: ${SCREENSHOT_DIR}\n`);
  process.stdout.write(`   QA 摘要: ${path.relative(REPO_ROOT, SUMMARY_FILE)}\n`);

  const allPass = summary.captured.every(c => c.modules.every(m => m.pass));
  if (!allPass) {
    process.stderr.write('❌ 有模块断言失败, 见 summary\n');
    process.exit(2);
  }
}

main().catch(err => {
  process.stderr.write('❌ 截图失败: ' + err.message + '\n' + err.stack + '\n');
  process.exit(1);
});