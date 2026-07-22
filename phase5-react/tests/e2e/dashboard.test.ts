import { test, expect } from '@playwright/test';

test.describe('仪表盘页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: '以 Demo 模式进入' }).click();
    await expect(page).toHaveURL('/workstation');
  });

  test('显示统计卡片', async ({ page }) => {
    const statCards = page.locator('.arco-card').filter({ has: page.locator('h3') });
    await expect(statCards).toHaveCount(4);
  });

  test('显示当前案件数', async ({ page }) => {
    await expect(page.getByText('当前案件数').locator('..').locator('h3')).toHaveText('12');
  });

  test('显示今日日程', async ({ page }) => {
    await expect(page.getByText('今日日程')).toBeVisible();
    const schedules = page.locator('[type="checkbox"]');
    await expect(schedules).toHaveCount(5);
  });

  test('切换日程筛选', async ({ page }) => {
    const pendingButton = page.getByRole('button', { name: '待办' });
    const doneButton = page.getByRole('button', { name: '已完成' });
    const allButton = page.getByRole('button', { name: '全部' });

    await doneButton.click();
    await expect(page.getByText('客户咨询会')).toBeVisible();
    await expect(page.getByText('李明案证据整理')).toBeHidden();

    await pendingButton.click();
    await expect(page.getByText('李明案证据整理')).toBeVisible();
    await expect(page.getByText('客户咨询会')).toBeHidden();

    await allButton.click();
    await expect(page.getByText('李明案证据整理')).toBeVisible();
    await expect(page.getByText('客户咨询会')).toBeVisible();
  });

  test('显示需要关注的提醒', async ({ page }) => {
    await expect(page.getByText('需要关注')).toBeVisible();
    const alerts = page.locator('.border-red-100, .border-orange-100');
    await expect(alerts).toHaveCount(2);
  });

  test('显示案件动态', async ({ page }) => {
    await expect(page.getByText('案件动态')).toBeVisible();
    const dynamics = page.locator('.border-b.border-bg-border');
    await expect(dynamics).toHaveCount(4);
  });

  test('显示最近案件列表', async ({ page }) => {
    await expect(page.getByText('最近案件')).toBeVisible();
    const tableRows = page.locator('tbody tr');
    await expect(tableRows).toHaveCount(5);
  });

  test('案件列表表头', async ({ page }) => {
    const headers = page.locator('thead th');
    await expect(headers).toHaveCount(4);
    await expect(headers.nth(0)).toHaveText('案件名称');
    await expect(headers.nth(1)).toHaveText('角色');
    await expect(headers.nth(2)).toHaveText('立案日期');
    await expect(headers.nth(3)).toHaveText('状态');
  });

  test('显示本周效率统计', async ({ page }) => {
    await expect(page.getByText('本周效率')).toBeVisible();
    const stats = page.locator('.bg-bg-subtle.border.border-bg-border');
    await expect(stats).toHaveCount(3);
  });
});
