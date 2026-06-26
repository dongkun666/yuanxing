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
    await page.evaluate(() => {
        var links = document.querySelectorAll('.sidebar-item');
        for (var l of links) {
            if (l.textContent && l.textContent.includes('知识库')) { l.click(); break; }
        }
    });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: 'E:\\falvxiangmu\\screenshot_kb_top.png' });
    await browser.close();
})();
