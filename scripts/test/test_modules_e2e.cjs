const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGE: ' + e.message));
  page.on('console', msg => { if (msg.type() === 'error') errors.push('CON: ' + msg.text()); });
  await page.goto('http://127.0.0.1:8080/?dev=1&v=' + Date.now());
  await page.waitForTimeout(800);

  const results = {};

  // 1. 知识库
  await page.click('text=知识库管理');
  await page.waitForTimeout(500);
  results.knowledge = {
    ingest: !!(await page.$('text=摄入 (Ingest)')),
    wiki: !!(await page.$('text=Wiki 页面')),
    lint: !!(await page.$('text=巡检 (Lint)')),
    compileBtn: !!(await page.$('text=AI 编译')),
  };

  // 2. AI 对话
  await page.click('[data-tab="ai"]');
  await page.waitForTimeout(500);
  results.ai = {
    newChat: !!(await page.$('text=新建对话')),
  };

  // 3. 模板
  await page.click('[data-tab="work"]');
  await page.waitForTimeout(300);
  await page.click('text=模板管理');
  await page.waitForTimeout(500);
  results.templates = {
    official: !!(await page.$('text=官方模板')),
    personal: !!(await page.$('text=个人模板')),
  };

  // 4. 账号 - 直接 evaluate
  results.account = {
    profile: !!(await page.evaluate(() => { switchToAccountSettings(); return !!document.getElementById('view-account-settings'); })),
    subscription: !!(await page.evaluate(() => { switchToSubscription(); return !!document.getElementById('view-subscription'); })),
  };

  // 5. 主文件
  await page.click('[data-tab="work"]');
  await page.waitForTimeout(300);
  await page.click('text=案件管理');
  await page.waitForTimeout(500);
  results.cases = { list: !!(await page.$('text=案件列表')) };
  await page.click('text=客户管理');
  await page.waitForTimeout(500);
  results.clients = { view: !!(await page.$('#view-client')) };
  await page.click('text=日程管理');
  await page.waitForTimeout(500);
  results.schedule = { view: !!(await page.$('#view-schedule-list')) };
  await page.click('text=归档管理');
  await page.waitForTimeout(500);
  results.archive = { list: !!(await page.$('text=归档列表').catch(() => null)) };

  await page.screenshot({ path: 'E:/falvxiangmu/screenshot_modules_e2e.png' });

  console.log('=== E2E 模块拆分测试 ===\n');
  Object.entries(results).forEach(([mod, items]) => {
    console.log(`  ${mod}:`);
    Object.entries(items).forEach(([k, v]) => console.log(`    ${v ? '✓' : '✗'} ${k}`));
  });
  console.log(`\n  Page errors: ${errors.length}`);
  errors.slice(0, 5).forEach(e => console.log('    !', e.slice(0, 120)));
  await browser.close();
})();
