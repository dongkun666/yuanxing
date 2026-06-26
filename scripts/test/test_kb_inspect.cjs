const { chromium } = require('playwright');
(async () => {
    const browser = await chromium.launch({
        executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        headless: true,
        args: ['--no-sandbox']
    });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
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

    // 检查 view-knowledge 内部结构
    const info = await page.evaluate(() => {
        var v = document.getElementById('view-knowledge');
        if (!v) return 'NONE';
        var max = v.querySelector('.max-w-6xl');
        var grid = v.querySelector('.grid.grid-cols-4');
        return {
            v_class: v.className,
            v_children: v.children.length,
            v_firstChild: v.firstElementChild ? v.firstElementChild.className.substring(0, 60) : 'no',
            max_class: max ? max.className : 'no max',
            max_children: max ? max.children.length : 0,
            grid_class: grid ? grid.className : 'no grid',
            grid_children: grid ? grid.children.length : 0
        };
    });
    console.log('inspect:', JSON.stringify(info, null, 2));

    await browser.close();
})();
