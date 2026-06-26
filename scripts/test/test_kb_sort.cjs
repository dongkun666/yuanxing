// 测试知识库排序 + AI 洞察点击
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-cache']
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    bypassCSP: true
  });
  await context.route('**/*', route => {
    const headers = { ...route.request().headers() };
    delete headers['if-none-match'];
    delete headers['if-modified-since'];
    headers['cache-control'] = 'no-cache';
    route.continue({ headers });
  });
  const page = await context.newPage();
  page.on('console', m => console.log(`[${m.type()}] ${m.text()}`));
  page.on('pageerror', e => console.log(`[err] ${e.message}`));

  await page.goto('http://127.0.0.1:8080/?dev=1&_t=' + Date.now(), { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
  // 点击侧边栏「知识库管理」
  await page.evaluate(() => {
    var links = document.querySelectorAll('.sidebar-item');
    for (var l of links) {
      if (l.textContent && l.textContent.includes('知识库')) { l.click(); break; }
    }
  });
  await page.waitForTimeout(2500);

  // 0. sanity check
  var sanityCount = await page.evaluate(() => {
    var rows = document.querySelectorAll('#view-knowledge tbody tr');
    return {
      total: rows.length,
      withCite: Array.from(rows).filter(r => r.getAttribute('data-cite')).length,
      sample: rows[0] ? rows[0].getAttribute('data-cite') : null
    };
  });
  console.log('sanity:', JSON.stringify(sanityCount));

  // 1. 点击 "引用" 表头排序 (默认降序)
  await page.evaluate(() => {
    var ths = document.querySelectorAll('#view-knowledge thead th');
    for (var th of ths) {
      if (th.textContent.indexOf('引用') >= 0) { th.click(); break; }
    }
  });
  await page.waitForTimeout(500);
  var cites = await page.evaluate(() => {
    var rows = document.querySelectorAll('#view-knowledge tbody tr');
    return Array.from(rows).filter(r => r.style.display !== 'none').map(r => r.getAttribute('data-cite'));
  });
  console.log('cite desc:', cites.join(','));

  // 2. 再点一次 → 升序
  await page.evaluate(() => {
    var ths = document.querySelectorAll('#view-knowledge thead th');
    for (var th of ths) {
      if (th.textContent.indexOf('引用') >= 0) { th.click(); break; }
    }
  });
  await page.waitForTimeout(500);
  var cites2 = await page.evaluate(() => {
    var rows = document.querySelectorAll('#view-knowledge tbody tr');
    return Array.from(rows).filter(r => r.style.display !== 'none').map(r => r.getAttribute('data-cite'));
  });
  console.log('cite asc:', cites2.join(','));

  // 3. 点击 "发布时间" 升序
  await page.evaluate(() => {
    var ths = document.querySelectorAll('#view-knowledge thead th');
    for (var th of ths) {
      if (th.textContent.indexOf('发布时间') >= 0) { th.click(); break; }
    }
  });
  await page.waitForTimeout(500);
  var dates = await page.evaluate(() => {
    var rows = document.querySelectorAll('#view-knowledge tbody tr');
    return Array.from(rows).filter(r => r.style.display !== 'none').map(r => r.getAttribute('data-date'));
  });
  console.log('date asc:', dates.join(','));

  // 4. 点击 "文档标题" 升序
  await page.evaluate(() => {
    var ths = document.querySelectorAll('#view-knowledge thead th');
    for (var th of ths) {
      if (th.textContent.indexOf('文档标题') >= 0) { th.click(); break; }
    }
  });
  await page.waitForTimeout(500);
  var titles = await page.evaluate(() => {
    var rows = document.querySelectorAll('#view-knowledge tbody tr');
    return Array.from(rows).filter(r => r.style.display !== 'none').map(r => r.getAttribute('data-title'));
  });
  console.log('title asc:', titles.map(t => t.substring(0, 6)).join('|'));

  // 5. 点击 AI 洞察「知识缺口」 → 应自动填 "劳动争议" 搜索
  await page.evaluate(() => {
    var cards = document.querySelectorAll('#view-knowledge .grid-cols-3 .p-3');
    for (var c of cards) {
      if (c.textContent.indexOf('知识缺口') >= 0) { c.click(); break; }
    }
  });
  await page.waitForTimeout(500);
  var searchVal = await page.evaluate(() => document.getElementById('kb-search-input').value);
  var visibleCount = await page.evaluate(() => {
    var rows = document.querySelectorAll('#view-knowledge tbody tr');
    return Array.from(rows).filter(r => r.style.display !== 'none').length;
  });
  console.log('AI 知识缺口 input:', searchVal, '可见行:', visibleCount);
  await page.screenshot({ path: 'E:/falvxiangmu/screenshot_kb_ai_gap.png' });

  // 6. 点击 AI 洞察「高频引用」 → 填 "民法典"
  await page.evaluate(() => {
    var cards = document.querySelectorAll('#view-knowledge .grid-cols-3 .p-3');
    for (var c of cards) {
      if (c.textContent.indexOf('高频引用') >= 0) { c.click(); break; }
    }
  });
  await page.waitForTimeout(500);
  var searchVal2 = await page.evaluate(() => document.getElementById('kb-search-input').value);
  var visibleCount2 = await page.evaluate(() => {
    var rows = document.querySelectorAll('#view-knowledge tbody tr');
    return Array.from(rows).filter(r => r.style.display !== 'none').length;
  });
  console.log('AI 高频引用 input:', searchVal2, '可见行:', visibleCount2);

  await browser.close();
})();
