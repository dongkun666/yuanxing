import { test, expect } from '@playwright/test';

test.describe('案件列表页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: '以 Demo 模式进入' }).click();
    await expect(page).toHaveURL('/workstation');
  });

  test('导航到案件列表', async ({ page }) => {
    await page.getByText('最近案件').click();
    await page.waitForNavigation({ waitUntil: 'networkidle' });
  });

  test('案件列表表格交互', async ({ page }) => {
    const tableRows = page.locator('tbody tr');
    await expect(tableRows).toHaveCount(5);

    const firstRow = tableRows.first();
    await expect(firstRow).toContainText('李明诉XX公司买卖合同纠纷');
    await expect(firstRow).toContainText('代理原告');
    await expect(firstRow).toContainText('2026-06-10');
  });

  test('案件状态标签', async ({ page }) => {
    const statusBadges = page.locator('[class*="bg-brand-tint"], [class*="bg-warning-tint"], [class*="bg-success-tint"], [class*="bg-wiki-tint"]');
    await expect(statusBadges).toHaveCount(5);
  });

  test('点击案件行', async ({ page }) => {
    const firstRow = page.locator('tbody tr').first();
    await firstRow.click();
  });
});
