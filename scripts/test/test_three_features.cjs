const { chromium } = require('playwright');
(async () => {
    const browser = await chromium.launch({
        executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        headless: true,
        args: ['--no-sandbox']
    });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const client = await page.context().newCDPSession(page);
    await client.send('Network.setCacheDisabled', { cacheDisabled: true });
    page.on('console', m => console.log(`[${m.type()}] ${m.text()}`));
    page.on('pageerror', e => console.log(`[err] ${e.message}`));
    await page.goto('http://127.0.0.1:8080/?dev=1', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    await page.evaluate(() => {
        var links = document.querySelectorAll('.sidebar-item, [onclick*="switchView"]');
        for (var l of links) {
            if (l.textContent && l.textContent.includes('模板管理')) { l.click(); break; }
        }
    });
    await page.waitForTimeout(2000);

    // 1. 上传模板测试
    console.log('=== 1. 上传模板 ===');
    await page.evaluate(() => openUploadTemplateModal());
    await page.waitForTimeout(500);
    // 填表 + 上传一个文件
    await page.evaluate(async () => {
        document.getElementById('upload-template-name').value = '测试模板-新版本 v1';
        document.getElementById('upload-template-category').value = '诉状类';
        // 模拟文件上传
        var dt = new DataTransfer();
        var file = new File(['test content'], '测试模板.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
        dt.items.add(file);
        var input = document.getElementById('upload-template-file');
        input.files = dt.files;
        input.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await page.waitForTimeout(300);
    await page.screenshot({ path: 'E:\\falvxiangmu\\screenshot_upload_filled.png' });
    // 提交
    await page.evaluate(() => submitUploadTemplate());
    await page.waitForTimeout(800);
    await page.screenshot({ path: 'E:\\falvxiangmu\\screenshot_after_upload.png' });

    // 2. 按时间排序测试
    console.log('=== 2. 按时间排序 ===');
    // 第一次点 - 降序
    await page.evaluate(() => {
        var btns = document.querySelectorAll('.sort-btn');
        if (btns.length) btns[0].click();
    });
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'E:\\falvxiangmu\\screenshot_sort_desc.png' });
    // 第二次点 - 升序
    await page.evaluate(() => {
        var btns = document.querySelectorAll('.sort-btn');
        if (btns.length) btns[0].click();
    });
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'E:\\falvxiangmu\\screenshot_sort_asc.png' });

    // 3. 分类管理测试 - 添加一个分类
    console.log('=== 3. 分类管理 ===');
    await page.evaluate(() => openCategoryManageModal());
    await page.waitForTimeout(500);
    await page.evaluate(() => {
        document.getElementById('new-category-input').value = '劳动仲裁类';
        addCategory();
    });
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'E:\\falvxiangmu\\screenshot_add_category.png' });
    // 关闭
    await page.evaluate(() => closeCategoryManageModal());
    await page.waitForTimeout(500);

    // 4. 验证: 切换到"劳动仲裁类" (0 个) + 点全部
    console.log('=== 4. filter 联动 ===');
    await page.evaluate(() => {
        var tabs = document.querySelectorAll('.personal-category-tab');
        for (var t of tabs) {
            if (t.textContent.indexOf('劳动仲裁类') === 0) { t.click(); break; }
        }
    });
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'E:\\falvxiangmu\\screenshot_new_category_filter.png' });

    // 5. 验证: 点诉状类 (应该 1 行 - 新上传的)
    await page.evaluate(() => {
        var tabs = document.querySelectorAll('.personal-category-tab');
        for (var t of tabs) {
            if (t.textContent.indexOf('诉状类') === 0) { t.click(); break; }
        }
    });
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'E:\\falvxiangmu\\screenshot_suzhuang_after_upload.png' });

    // 6. 点全部看全部
    await page.evaluate(() => {
        var tabs = document.querySelectorAll('.personal-category-tab');
        for (var t of tabs) {
            if (t.textContent.indexOf('全部') === 0) { t.click(); break; }
        }
    });
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'E:\\falvxiangmu\\screenshot_all_after_upload.png' });

    await browser.close();
})();
