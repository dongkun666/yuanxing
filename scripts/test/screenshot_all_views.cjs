const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://127.0.0.1:8080/?dev=1&v=' + Date.now());
  await page.waitForTimeout(800);

  const views = [
    { name: 'workstation', click: 'text=工作台', expect: '工作台' },
    { name: 'case_list', click: 'text=案件管理', expect: '案件' },
    { name: 'schedule', click: 'text=日程管理', expect: '日程' },
    { name: 'client', click: 'text=客户管理', expect: '客户' },
    { name: 'archive', click: 'text=归档管理', expect: '归档' },
    { name: 'template', click: 'text=模板管理', expect: '模板' },
    { name: 'knowledge', click: 'text=知识库管理', expect: '知识库' },
  ];

  for (const v of views) {
    await page.click(v.click).catch(() => {});
    await page.waitForTimeout(500);
    await page.screenshot({ path: `E:/falvxiangmu/screenshot_${v.name}.png` });
    console.log('  ✓', v.name);
  }
  await browser.close();
})();
