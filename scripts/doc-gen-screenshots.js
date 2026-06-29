/**
 * W9 C1 Skill 3 文书生成 截图脚本 (lex-coder · 2026-06-29)
 *
 * 截 doc-gen 视图 (4 标签页: 起诉/答辩/合同/律师函)
 * 桌面 1440 + 移动 375 = 8 张图, 落档到 docs/qa/doc-gen-w9/screenshots/
 *
 * 跑法:
 *   1. 启 backend: cd backend/cases-crawler && py -3.14 -m uvicorn api.main:app --port 8001
 *   2. 启 frontend: py -3.14 -m http.server 8081 (yuanxing 根目录)
 *   3. node scripts/doc-gen-screenshots.js
 *
 * 修复的 2 个坑 (跟 W9 A1 backlog-screenshots.js 一样):
 * - router.js insertAdjacentHTML 不执行 <script>: 这里手动 eval 脚本块
 * - dev server 8081 + backend 8001 跨域: monkey-patch fetch 把 /api/* 代理到 backend
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const REPO_ROOT = path.resolve(__dirname, '..');
const SCREENSHOT_DIR = path.join(REPO_ROOT, 'docs', 'qa', 'doc-gen-w9', 'screenshots');
const INDEX_URL = 'http://127.0.0.1:8080/index.html';
const BACKEND_URL = 'http://127.0.0.1:8000';

const DOC_TYPES = [
    { id: 'complaint', name: '01-complaint', label: '起诉状', icon: 'mdi:gavel' },
    { id: 'defense',   name: '02-defense',   label: '答辩状', icon: 'mdi:shield-check-outline' },
    { id: 'contract',  name: '03-contract',  label: '合同',   icon: 'mdi:file-document-edit-outline' },
    { id: 'letter',    name: '04-letter',    label: '律师函', icon: 'mdi:email-fast-outline' },
];

const VIEWPORTS = [
    { name: 'desktop', width: 1440, height: 900, isMobile: false },
    { name: 'mobile',  width: 375,  height: 812, isMobile: true },
];

async function injectDocGenView(page) {
    // 1. fetch view html
    const html = await page.evaluate(async () => {
        const r = await fetch('/templates/views/doc-gen/index.html');
        return await r.text();
    });

    // 2. split html into markup + script blocks
    const scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
    const scripts = [];
    let match;
    while ((match = scriptRegex.exec(html)) !== null) {
        scripts.push(match[1]);
    }
    const markup = html.replace(scriptRegex, '');

    // 3. inject markup
    await page.evaluate((mk) => {
        document.getElementById('main-content').insertAdjacentHTML('beforeend', mk);
    }, markup);

    // 4. eval each script block manually (innerHTML script doesn't auto-execute)
    for (const s of scripts) {
        await page.evaluate((src) => {
            // eslint-disable-next-line no-new-func
            const fn = new Function(src);
            fn();
        }, s);
    }

    // 5. show view-doc-gen, hide others + monkey-patch fetch for /api/*
    await page.evaluate(() => {
        document.querySelectorAll('.view-content').forEach(el => el.classList.add('hidden'));
        const target = document.getElementById('view-doc-gen');
        if (target) target.classList.remove('hidden');
        if (!window.__fetchPatched) {
            const orig = window.fetch.bind(window);
            window.fetch = (url, opts) => {
                if (typeof url === 'string' && url.startsWith('/api/')) {
                    return orig('http://127.0.0.1:8000' + url, opts);
                }
                return orig(url, opts);
            };
            window.__fetchPatched = true;
        }
    });

    // 6. trigger health load
    const hasFn = await page.evaluate(() => typeof window.__loadDocGenHealth);
    if (hasFn === 'function') {
        await page.evaluate(() => window.__loadDocGenHealth());
    } else {
        process.stdout.write('  ⚠️  __loadDocGenHealth still undefined after eval\n');
    }

    // 7. wait for fetch + render
    await page.waitForTimeout(1500);
}

async function main() {
    if (!fs.existsSync(SCREENSHOT_DIR)) {
        fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
    }
    const browser = await chromium.launch({ headless: true });
    const summary = { captured: [], console_errors: [], backend_responses: [] };

    for (const vp of VIEWPORTS) {
        const ctx = await browser.newContext({
            viewport: { width: vp.width, height: vp.height },
            deviceScaleFactor: 1,
            isMobile: vp.isMobile,
        });
        const page = await ctx.newPage();

        page.on('console', msg => {
            if (msg.type() === 'error') {
                summary.console_errors.push(`[${vp.name}] ${msg.text()}`);
            }
        });
        page.on('pageerror', err => {
            summary.console_errors.push(`[${vp.name} PAGE] ${err.message}`);
        });
        page.on('response', resp => {
            if (resp.url().includes('/api/doc-gen/')) {
                summary.backend_responses.push({
                    status: resp.status(),
                    url: resp.url().substring(resp.url().indexOf('/api/')),
                    viewport: vp.name,
                });
            }
        });

        await page.goto(INDEX_URL, { waitUntil: 'networkidle', timeout: 30000 });
        await injectDocGenView(page);

        const subtitle = await page.evaluate(() => document.getElementById('doc-gen-subtitle')?.textContent || 'N/A');
        process.stdout.write(`  📋 subtitle: ${subtitle}\n`);

        // 截 4 个标签页
        for (const dt of DOC_TYPES) {
            await page.evaluate((type) => {
                const btn = document.querySelector(`#view-doc-gen .doc-tab[data-type="${type}"]`);
                if (btn) btn.click();
            }, dt.id);
            await page.waitForTimeout(600);
            const file = path.join(SCREENSHOT_DIR, `${dt.name}-${vp.name}.png`);
            await page.screenshot({ path: file, fullPage: false });
            summary.captured.push({ type: dt.id, viewport: vp.name, file, label: dt.label });
            process.stdout.write(`  📸 ${dt.label} (${vp.name})\n`);
        }

        await ctx.close();
    }

    await browser.close();

    // 写摘要
    const summaryFile = path.join(SCREENSHOT_DIR, '..', 'screenshot-summary.json');
    fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2), 'utf-8');
    process.stdout.write(`\n✅ W9 C1 doc-gen 截图完成, 共 ${summary.captured.length} 张图\n`);
    process.stdout.write(`   落档: ${SCREENSHOT_DIR}\n`);
    process.stdout.write(`   摘要: ${summaryFile}\n`);
    process.stdout.write(`   后端响应: ${summary.backend_responses.length} 个 /api/doc-gen/* 请求\n`);
    process.stdout.write(`   控制台错误: ${summary.console_errors.length}\n`);
    if (summary.console_errors.length > 0) {
        summary.console_errors.forEach(e => process.stdout.write(`     - ${e}\n`));
    }
}

main().catch(err => {
    process.stderr.write('❌ 截图失败: ' + err.message + '\n' + err.stack + '\n');
    process.exit(1);
});