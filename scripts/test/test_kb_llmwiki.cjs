// 测试 LLM Wiki 3 Tab 切换 + AI 编译交互
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-cache']
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, bypassCSP: true });
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
  await page.evaluate(() => {
    var links = document.querySelectorAll('.sidebar-item');
    for (var l of links) {
      if (l.textContent && l.textContent.includes('知识库')) { l.click(); break; }
    }
  });
  await page.waitForTimeout(2500);

  // 1. 默认 Ingest Tab 截图
  await page.screenshot({ path: 'E:/falvxiangmu/screenshot_kb_llm_ingest.png' });
  console.log('1. ingest tab OK');

  // 2. 点击「AI 编译」按钮 (第一个待编译)
  await page.evaluate(() => {
    var btns = document.querySelectorAll('button');
    for (var b of btns) {
      if (b.textContent.trim() === 'AI 编译') { b.click(); break; }
    }
  });
  await page.waitForTimeout(800);
  await page.screenshot({ path: 'E:/falvxiangmu/screenshot_kb_compile_start.png' });
  console.log('2. compile started OK');

  // 等编译完成
  await page.waitForTimeout(6000);
  await page.screenshot({ path: 'E:/falvxiangmu/screenshot_kb_compile_done.png' });
  console.log('3. compile done OK');

  // 3. 切到 Wiki Tab
  await page.evaluate(() => { document.getElementById('kb-tab-wiki').click(); });
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'E:/falvxiangmu/screenshot_kb_wiki.png' });
  console.log('4. wiki tab OK');

  // 4. 切到 Lint Tab
  await page.evaluate(() => { document.getElementById('kb-tab-lint').click(); });
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'E:/falvxiangmu/screenshot_kb_lint.png' });
  console.log('5. lint tab OK');

  // 5. 滚到 lint 底部看建议
  await page.evaluate(() => {
    var main = document.getElementById('main-content');
    if (main) main.scrollTop = main.scrollHeight;
  });
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'E:/falvxiangmu/screenshot_kb_lint_bottom.png' });
  console.log('6. lint bottom OK');

  await browser.close();
})();
