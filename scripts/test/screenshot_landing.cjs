const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGE: ' + e.message));
  page.on('console', msg => { if (msg.type() === 'error') errors.push('CON: ' + msg.text()); });

  // 1. Hero 区
  await page.goto('file:///E:/falvxiangmu/docs/marketing/landing.html');
  await page.waitForTimeout(1500);
  await page.screenshot({ path: 'E:/falvxiangmu/screenshot_landing_hero.png', fullPage: false });
  console.log('  ✓ Hero');

  // 2. 全页
  await page.screenshot({ path: 'E:/falvxiangmu/screenshot_landing_full.png', fullPage: true });
  console.log('  ✓ Full page');

  // 3. Pricing 滚到中间
  await page.evaluate(() => document.getElementById('pricing').scrollIntoView());
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'E:/falvxiangmu/screenshot_landing_pricing.png', fullPage: false });
  console.log('  ✓ Pricing');

  console.log('\n  Errors:', errors.length);
  errors.forEach(e => console.log('   !', e));
  await browser.close();
})();
