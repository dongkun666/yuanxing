const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox']
  });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const networkErrors = [];
  page.on('response', resp => {
    if (resp.status() >= 400 && !resp.url().includes('favicon')) {
      networkErrors.push({ status: resp.status(), url: resp.url() });
    }
  });
  page.on('requestfailed', req => {
    networkErrors.push({ status: 'FAILED', url: req.url(), error: req.failure()?.errorText });
  });
  await page.goto('http://127.0.0.1:8080/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);
  // 走几个 view
  for (const v of ['case-list', 'workstation', 'ai', 'template']) {
    await page.evaluate((vid) => { try { switchView(vid); } catch (e) {} }, v);
    await page.waitForTimeout(500);
  }
  console.log('=== Network issues ===');
  networkErrors.forEach(e => console.log(' ', JSON.stringify(e)));
  await browser.close();
})();
