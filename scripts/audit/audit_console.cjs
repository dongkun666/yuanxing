const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });
  const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await ctx.newPage();

  const errors = [];
  const warnings = [];
  const pageErrors = [];
  const networkErrors = [];
  const consoleByType = {};

  page.on('console', msg => {
    const t = msg.type();
    const text = msg.text();
    if (!consoleByType[t]) consoleByType[t] = [];
    consoleByType[t].push(text);
    if (t === 'error') errors.push(text);
    if (t === 'warning') warnings.push(text);
  });
  page.on('pageerror', err => pageErrors.push(err.message));
  page.on('response', resp => {
    if (resp.status() >= 400 && !resp.url().includes('favicon')) {
      networkErrors.push(`${resp.status()} ${resp.url()}`);
    }
  });

  await page.goto('http://127.0.0.1:8080/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  // 走遍所有 view
  const views = [
    'workstation', 'schedule-list', 'attention-list', 'case-list', 'case',
    'client', 'archive', 'template', 'knowledge', 'ai',
    'subscription', 'member-center', 'orders', 'account-settings',
    'payment', 'attachment-list', 'case-analysis', 'case-dynamics',
    'schedule-calendar', 'client-detail', 'payment-success'
  ];
  for (const v of views) {
    try {
      await page.evaluate((vid) => {
        if (typeof switchView === 'function') {
          try { switchView(vid); } catch (e) { console.error('switchView ' + vid + ': ' + e.message); }
        }
      }, v);
      await page.waitForTimeout(400);
    } catch (e) {}
  }
  // 切到 case-detail + tab 全部切一遍
  await page.evaluate(() => switchView('case-list'));
  await page.waitForTimeout(1500);
  await page.evaluate(() => openCaseDetail(0));
  await page.waitForTimeout(2500);
  for (const tab of ['overview', 'timeline', 'documents', 'materials', 'evidence', 'contract', 'authorization', 'judgment', 'other']) {
    await page.evaluate((t) => {
      const btn = document.querySelector('.case-tab[data-tab="' + t + '"]');
      if (btn) switchCaseTab(t, btn);
    }, tab);
    await page.waitForTimeout(300);
  }

  console.log('=== Network errors (status >= 400) ===');
  networkErrors.forEach(e => console.log('  ' + e));
  console.log('');
  console.log('=== Page errors (JS exceptions) ===');
  pageErrors.forEach(e => console.log('  ' + e));
  console.log('');
  console.log('=== Console errors ===');
  errors.forEach(e => console.log('  ' + e));
  console.log('');
  console.log('=== Console warnings ===');
  warnings.forEach(e => console.log('  ' + e));
  console.log('');
  console.log('=== Summary ===');
  console.log('Total console messages by type:');
  for (const k of Object.keys(consoleByType)) {
    console.log('  ' + k + ': ' + consoleByType[k].length);
  }

  await browser.close();
})();
