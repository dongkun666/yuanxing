/**
 * W6 Score App 截图脚本 (lex-coder · 2026-06-29)
 *
 * 用法:
 *   1. 启前端静态服务: python -m http.server 8080 (后台)
 *   2. node scripts/test/screenshot_score_app.cjs
 *
 * 输出:
 *   - score-app-desktop-1440.png  (1440x900 桌面)
 *   - score-app-desktop-1440-full.png  (1440 fullpage)
 *   - score-app-mobile-375.png  (375x812 移动)
 *   - score-app-mobile-375-full.png  (375 fullpage)
 *   - score-app-after-submit.png  (桌面, 提交样例后)
 *   - score-app-help-modal.png  (桌面, help modal)
 *
 * 浏览器控制台错误同时记录
 */
const { chromium, devices } = require('playwright');

const BASE_URL = process.env.SCORE_URL || 'http://127.0.0.1:8080';
const OUTPUT_DIR = process.env.SCREENSHOT_DIR || 'C:/Users/42081/.mavis/plans/plan_55ca4e00/outputs/w6-review-score-app';

(async () => {
    const browser = await chromium.launch({ headless: true });
    const errors = [];

    async function newPage(viewport) {
        const page = await browser.newPage({ viewport });
        page.on('pageerror', e => errors.push(`PAGE[${viewport.width}x${viewport.height}]: ${e.message}`));
        page.on('console', msg => {
            if (msg.type() === 'error') errors.push(`CON[${viewport.width}x${viewport.height}]: ${msg.text()}`);
        });
        return page;
    }

    // ============= Desktop 1440 =============
    console.log('\n[1/4] Desktop 1440x900 ...');
    {
        const page = await newPage({ width: 1440, height: 900 });
        await page.goto(`${BASE_URL}/index.html`, { waitUntil: 'load' });
        await page.waitForTimeout(500);
        // 触发 switchView (JS 路由)
        await page.evaluate(() => {
            if (typeof window.switchView === 'function') {
                window.switchView('review-score-app');
            }
        });
        await page.waitForTimeout(500);
        // 等 view 显示
        await page.waitForSelector('#view-review-score-app:not(.hidden)', { timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(800);
        await page.screenshot({
            path: `${OUTPUT_DIR}/score-app-desktop-1440.png`,
            fullPage: false
        });
        console.log('  - score-app-desktop-1440.png (viewport 1440x900)');

        await page.screenshot({
            path: `${OUTPUT_DIR}/score-app-desktop-1440-full.png`,
            fullPage: true
        });
        console.log('  - score-app-desktop-1440-full.png (full page)');

        // 提交样例 (模拟律师现场填表)
        await page.evaluate(() => {
            // 选律师 + 填 5 维度
            const sel = document.getElementById('lawyer-select');
            if (sel) sel.value = 'L1';
            sel.dispatchEvent(new Event('change'));
            // 切换合同到 demo-rental
            const rentalTab = document.querySelector('[data-contract-id="demo-rental-beijing-2026"]');
            if (rentalTab) rentalTab.click();
            // 拉 5 个滑块
            document.querySelectorAll('[data-dim-slider]').forEach((s, i) => {
                const val = [9, 8, 7, 10, 6][i] || 7;
                s.value = val;
                s.dispatchEvent(new Event('input'));
            });
            // 填 2 个评论
            const c1 = document.querySelector('[data-dim-comment="fatal_accuracy"]');
            if (c1) c1.value = '致命准确率: 4/4 致命条款都识别到了 (房屋租赁单方解除权判断精准)';
            const c2 = document.querySelector('[data-dim-comment="suggestion_practicality"]');
            if (c2) c2.value = '建议实用: 法条引用准确, modified_clause_template 可直接套用';
        });
        await page.waitForTimeout(500);
        await page.screenshot({
            path: `${OUTPUT_DIR}/score-app-after-submit.png`,
            fullPage: false
        });
        console.log('  - score-app-after-submit.png (5 维度 + 评论填好)');

        // 帮助 Modal
        await page.evaluate(() => {
            const helpBtn = document.getElementById('score-help-btn');
            if (helpBtn) helpBtn.click();
        });
        await page.waitForTimeout(400);
        await page.screenshot({
            path: `${OUTPUT_DIR}/score-app-help-modal.png`,
            fullPage: false
        });
        console.log('  - score-app-help-modal.png (帮助弹窗)');
        await page.close();
    }

    // ============= Mobile 375 =============
    console.log('\n[2/4] Mobile 375x812 ...');
    {
        const page = await newPage({ width: 375, height: 812 });
        await page.goto(`${BASE_URL}/index.html`, { waitUntil: 'load' });
        await page.waitForTimeout(500);
        await page.evaluate(() => {
            if (typeof window.switchView === 'function') {
                window.switchView('review-score-app');
            }
        });
        await page.waitForTimeout(500);
        await page.waitForSelector('#view-review-score-app:not(.hidden)', { timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(800);
        await page.screenshot({
            path: `${OUTPUT_DIR}/score-app-mobile-375.png`,
            fullPage: false
        });
        console.log('  - score-app-mobile-375.png (viewport 375x812)');

        await page.screenshot({
            path: `${OUTPUT_DIR}/score-app-mobile-375-full.png`,
            fullPage: true
        });
        console.log('  - score-app-mobile-375-full.png (full page)');

        await page.close();
    }

    // ============= Mobile 横屏 + 进度条 =============
    console.log('\n[3/4] Mobile 横屏 812x375 ...');
    {
        const page = await newPage({ width: 812, height: 375 });
        await page.goto(`${BASE_URL}/index.html`, { waitUntil: 'load' });
        await page.waitForTimeout(500);
        await page.evaluate(() => {
            if (typeof window.switchView === 'function') {
                window.switchView('review-score-app');
            }
        });
        await page.waitForTimeout(800);
        await page.screenshot({
            path: `${OUTPUT_DIR}/score-app-tablet-812.png`,
            fullPage: false
        });
        console.log('  - score-app-tablet-812.png (viewport 812x375)');
        await page.close();
    }

    // ============= 检查 5 维度滑块可拖 =============
    console.log('\n[4/4] 验证 5 维度滑块交互 ...');
    {
        const page = await newPage({ width: 1440, height: 900 });
        await page.goto(`${BASE_URL}/index.html`, { waitUntil: 'load' });
        await page.evaluate(() => {
            if (typeof window.switchView === 'function') {
                window.switchView('review-score-app');
            }
        });
        await page.waitForTimeout(500);
        await page.waitForSelector('#view-review-score-app:not(.hidden)', { timeout: 5000 }).catch(() => {});

        // 验证 5 维度滑块存在
        const sliderCount = await page.evaluate(() => document.querySelectorAll('[data-dim-slider]').length);
        const textAreaCount = await page.evaluate(() => document.querySelectorAll('[data-dim-comment]').length);
        const tabCount = await page.evaluate(() => document.querySelectorAll('[data-contract-id]').length);
        console.log(`  - 滑块数: ${sliderCount} (期望 5)`);
        console.log(`  - 评论 textarea 数: ${textAreaCount} (期望 5)`);
        console.log(`  - 合同 Tab 数: ${tabCount} (期望 5)`);
        if (sliderCount !== 5) errors.push(`维度滑块数不对: ${sliderCount}`);
        if (textAreaCount !== 5) errors.push(`评论 textarea 数不对: ${textAreaCount}`);
        if (tabCount !== 5) errors.push(`合同 Tab 数不对: ${tabCount}`);

        // 拖动第一个滑块
        await page.evaluate(() => {
            const s = document.querySelector('[data-dim-slider="fatal_accuracy"]');
            s.value = 3;
            s.dispatchEvent(new Event('input'));
        });
        await page.waitForTimeout(300);
        const aggregate = await page.evaluate(() => document.getElementById('score-aggregate-display')?.textContent);
        console.log(`  - 拖动 fatal_accuracy=3 后综合: ${aggregate}`);
        if (!aggregate || aggregate === '0.0') {
            errors.push('滑块拖动后综合未更新');
        }
        await page.close();
    }

    await browser.close();

    console.log('\n=== W6 Score App 截图完成 ===');
    console.log(`输出目录: ${OUTPUT_DIR}`);
    console.log(`截图文件数: 6 (4 desktop + 2 mobile)`);
    console.log(`控制台错误数: ${errors.length}`);
    errors.forEach(e => console.log(`  - ${e}`));

    if (errors.length > 0) {
        console.log('\n[FAIL] 有错误 - 请检查后重跑');
        process.exit(1);
    }
    console.log('[PASS] 全部通过 ✓');
    process.exit(0);
})();
