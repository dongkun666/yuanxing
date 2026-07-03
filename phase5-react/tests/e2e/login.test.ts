import { test, expect } from '@playwright/test';

test.describe('登录页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('显示登录页面标题', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('LexPrime');
    await expect(page.locator('h1')).toContainText('元枢法智');
  });

  test('登录表单验证', async ({ page }) => {
    const emailInput = page.locator('#login-email');
    const passwordInput = page.locator('#login-password');
    const submitButton = page.locator('form[aria-label="登录表单"] button[type="submit"]');

    await emailInput.fill('');
    await passwordInput.fill('');
    await submitButton.click();

    await expect(page.locator('[role="alert"]')).toContainText('请填写邮箱和密码');
  });

  test('Demo 模式登录', async ({ page }) => {
    await page.getByRole('button', { name: '以 Demo 模式进入' }).click();

    await expect(page).toHaveURL('/workstation');
    await expect(page.locator('h2')).toContainText('工作台');
  });

  test('切换到注册标签', async ({ page }) => {
    await page.getByRole('button', { name: '注册' }).click();

    await expect(page.locator('form[aria-label="注册表单"]')).toBeVisible();
    await expect(page.locator('#register-name')).toBeVisible();
    await expect(page.locator('#register-email')).toBeVisible();
    await expect(page.locator('#register-password')).toBeVisible();
  });

  test('注册表单验证', async ({ page }) => {
    await page.getByRole('button', { name: '注册' }).click();

    const nameInput = page.locator('#register-name');
    const emailInput = page.locator('#register-email');
    const passwordInput = page.locator('#register-password');
    const submitButton = page.locator('form[aria-label="注册表单"] button[type="submit"]');

    await nameInput.fill('');
    await emailInput.fill('');
    await passwordInput.fill('');
    await submitButton.click();

    await expect(page.locator('[role="alert"]')).toContainText('请填写姓名');
  });

  test('密码长度验证', async ({ page }) => {
    await page.getByRole('button', { name: '注册' }).click();

    const nameInput = page.locator('#register-name');
    const emailInput = page.locator('#register-email');
    const passwordInput = page.locator('#register-password');
    const submitButton = page.locator('form[aria-label="注册表单"] button[type="submit"]');

    await nameInput.fill('测试用户');
    await emailInput.fill('test@example.com');
    await passwordInput.fill('123');
    await submitButton.click();

    await expect(page.locator('[role="alert"]')).toContainText('密码至少');
  });
});
