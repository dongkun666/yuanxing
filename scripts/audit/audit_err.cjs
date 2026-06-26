const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox']
  });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const loc = msg.location();
      console.log('  [error]', JSON.stringify({text: msg.text(), url: loc.url, line: loc.lineNumber}));
    }
  });
  page.on('response', resp => {
    if (resp.status() >= 400) {
      console.log('  [resp ' + resp.status() + ']', resp.url());
    }
  });
  page.on('requestfailed', req => {
    console.log('  [reqfail]', req.url(), req.failure()?.errorText);
  });
  await page.goto('http://127.0.0.1:8080/', { waitUntil: 'load' });
  await page.waitForTimeout(3000);
  await browser.close();
})();
