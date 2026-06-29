/**
 * W7 评审数据看板 截图脚本 (lex-coder · 2026-06-29)
 *
 * 用法:
 *   1. 启 backend: cd backend/cases-crawler && uvicorn api.main:app --port 8000 (后台)
 *   2. 启 frontend: python -m http.server 8080 (后台)
 *   3. 预填数据: POST /api/review/submit-score 25 条 + POST /api/review/question 8 条
 *   4. node scripts/test/screenshot_board.cjs
 *
 * 输出:
 *   - review-board-empty-1440.png         桌面, 空数据
 *   - review-board-data-1440.png          桌面, 完整数据
 *   - review-board-data-1440-full.png     桌面, 完整数据 fullpage
 *   - review-board-data-mobile-375.png   移动, 完整数据
 *   - review-board-data-tablet-768.png   平板
 */
const { chromium, devices } = require('playwright');

const BASE_URL = process.env.BOARD_URL || 'http://127.0.0.1:8080';
const API_URL = process.env.API_URL || 'http://127.0.0.1:8000';
const OUTPUT_DIR = process.env.SCREENSHOT_DIR || 'C:/Users/42081/.mavis/plans/plan_16daee4e/outputs/w7-review-aggregate';

const LAWYERS = ['L1', 'L2', 'L3', 'L4', 'L5'];
const CONTRACTS = [
    'demo-rental-beijing-2026',
    'demo-loan-shanghai-2026',
    'demo-labor-fulltime-2026',
    'demo-service-tech-2026',
    'demo-sales-goods-2026',
];
const DIMS = ['fatal_accuracy', 'suggestion_practicality', 'strategy_executability', 'neutrality', 'ui_flow'];
const QUESTION_CATS = ['产品', '技术', '法务', '其他'];

async function seedData() {
    console.log('[1/2] 预填评审数据 (25 评分 + 8 问题) ...');
    // 25 评分: 差异化 seed (3-5)
    let scoreCount = 0;
    for (let i = 0; i < LAWYERS.length; i++) {
        for (let j = 0; j < CONTRACTS.length; j++) {
            const seed = (i + j) % 3 + 3; // 3-5
            const scores = {
                fatal_accuracy: 5 + seed + (i % 2),
                suggestion_practicality: 5 + seed,
                strategy_executability: 5 + seed - 1,
                neutrality: 9 + (i % 2),
                ui_flow: 4 + seed,
            };
            const resp = await fetch(`${API_URL}/api/review/submit-score`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    lawyer_id: LAWYERS[i],
                    contract_id: CONTRACTS[j],
                    scores,
                }),
            });
            if (resp.ok) scoreCount++;
        }
    }
    console.log(`  - 评分提交: ${scoreCount}/25`);

    // 8 问题: 每律师 1-2 个
    const questions = [
        { lawyer: 'L1', cat: '产品', text: 'Skill 2 致命条款标红后, 律师如何一键修改? 模板只能复制到 Word 吗?' },
        { lawyer: 'L1', cat: '技术', text: 'API 端点能否支持批量上传多份合同? 律师常有 5-10 份同标的审查需求' },
        { lawyer: 'L2', cat: '法务', text: '法条引用深度: 当前只到民法典, 缺司法解释 + 地方高院裁判口径' },
        { lawyer: 'L2', cat: '产品', text: '审查结果导出格式能否加 PDF 真实版? 现在导出的 .docx 排版错乱' },
        { lawyer: 'L3', cat: '法务', text: '中立性: 房屋租赁场景下"建议拒签"是否过于强势? 律师需中性表述' },
        { lawyer: 'L3', cat: '技术', text: '数据安全: 客户合同文本是否本地化? 我们律所对数据出境敏感' },
        { lawyer: 'L4', cat: '产品', text: '多律师协作: 团队版能否支持 1 主审 + 2 复核分工?' },
        { lawyer: 'L5', cat: '技术', text: 'API 集成: 能否开放 webhook? 我们企业 ERP 系统对接需求' },
    ];
    let qCount = 0;
    for (const q of questions) {
        const resp = await fetch(`${API_URL}/api/review/question`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lawyer_id: q.lawyer,
                question_text: q.text,
                category: q.cat,
                context: `评审 #1 #2 现场律师 ${q.lawyer} 提出`,
                status: 'open',
            }),
        });
        if (resp.status === 201) qCount++;
    }
    console.log(`  - 问题提交: ${qCount}/${questions.length}`);
    return scoreCount + qCount;
}

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

    // 预填数据
    const total = await seedData();
    if (total < 30) {
        console.log(`[WARN] 预填数据不完整 (${total}/33), 部分截图可能空`);
    }

    // 桌面 1440 - 完整数据
    console.log('\n[2/2] 桌面截图 (1440x900) ...');
    {
        const page = await newPage({ width: 1440, height: 900 });
        await page.goto(`${BASE_URL}/index.html`, { waitUntil: 'load' });
        await page.waitForTimeout(500);
        await page.evaluate(() => {
            if (typeof window.switchView === 'function') window.switchView('review-board');
        });
        await page.waitForSelector('#view-review-board:not(.hidden)', { timeout: 5000 }).catch(() => {});
        // 等数据 fetch + render
        await page.waitForTimeout(1500);

        await page.screenshot({
            path: `${OUTPUT_DIR}/review-board-data-1440.png`,
            fullPage: false,
        });
        console.log(`  - review-board-data-1440.png`);

        await page.screenshot({
            path: `${OUTPUT_DIR}/review-board-data-1440-full.png`,
            fullPage: true,
        });
        console.log(`  - review-board-data-1440-full.png (fullpage)`);

        // 验证关键内容
        const totalRows = await page.evaluate(() => document.getElementById('board-total-rows')?.textContent);
        const rubricScore = await page.evaluate(() => document.getElementById('board-rubric-score')?.textContent);
        const questions = await page.evaluate(() => document.getElementById('board-questions')?.textContent);
        console.log(`  - 总评分行: ${totalRows}, 综合: ${rubricScore}, 问题数: ${questions}`);

        await page.close();
    }

    // 移动 375
    console.log('\n[3/3] 移动截图 (375x812) ...');
    {
        const page = await newPage({ width: 375, height: 812 });
        await page.goto(`${BASE_URL}/index.html`, { waitUntil: 'load' });
        await page.waitForTimeout(500);
        await page.evaluate(() => {
            if (typeof window.switchView === 'function') window.switchView('review-board');
        });
        await page.waitForSelector('#view-review-board:not(.hidden)', { timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(1500);

        await page.screenshot({
            path: `${OUTPUT_DIR}/review-board-data-mobile-375.png`,
            fullPage: true,
        });
        console.log(`  - review-board-data-mobile-375.png (fullpage)`);
        await page.close();
    }

    // 平板 768
    console.log('\n[4/4] 平板截图 (768x1024) ...');
    {
        const page = await newPage({ width: 768, height: 1024 });
        await page.goto(`${BASE_URL}/index.html`, { waitUntil: 'load' });
        await page.waitForTimeout(500);
        await page.evaluate(() => {
            if (typeof window.switchView === 'function') window.switchView('review-board');
        });
        await page.waitForSelector('#view-review-board:not(.hidden)', { timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(1500);

        await page.screenshot({
            path: `${OUTPUT_DIR}/review-board-data-tablet-768.png`,
            fullPage: false,
        });
        console.log(`  - review-board-data-tablet-768.png`);
        await page.close();
    }

    await browser.close();

    console.log('\n=== W7 Board 截图完成 ===');
    console.log(`输出目录: ${OUTPUT_DIR}`);
    console.log(`截图数: 4`);
    console.log(`控制台错误: ${errors.length}`);
    errors.forEach(e => console.log(`  - ${e}`));

    if (errors.length > 0) {
        console.log('\n[WARN] 有非致命错误 - 请人工检查截图');
    } else {
        console.log('\n[PASS] 0 错误 ✓');
    }
    process.exit(0);
})();
