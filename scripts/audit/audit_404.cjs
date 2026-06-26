const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox']
  });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const all404 = [];
  page.on('response', async resp => {
    if (resp.status() === 404) {
      all404.push(resp.url());
    }
  });
  await page.goto('http://127.0.0.1:8080/', { waitUntil: 'load' });
  await page.waitForTimeout(2000);
  // 切到 case-list 触发 case-list.html fetch
  await page.evaluate(() => { try { switchView('case-list'); } catch(e) {} });
  await page.waitForTimeout(1500);
  // 切回 workstation
  await page.evaluate(() => { try { switchView('workstation'); } catch(e) {} });
  await page.waitForTimeout(1500);
  console.log('=== 404 URLs ===');
  all404.forEach(u => console.log(' ', u));
  await browser.close();
})();
