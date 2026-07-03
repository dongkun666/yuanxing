import { test, expect } from '@playwright/test';

test.describe('合同审查页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: '以 Demo 模式进入' }).click();
    await expect(page).toHaveURL('/workstation');
  });

  test('访问合同审查页面', async ({ page }) => {
    await page.getByText('文书生成').click();
    await page.waitForNavigation({ waitUntil: 'networkidle' });
  });

  test('合同审查功能入口', async ({ page }) => {
    await expect(page).toHaveURL('/workstation');
  });
});
