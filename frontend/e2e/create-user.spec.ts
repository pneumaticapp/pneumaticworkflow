/**
 * E2E tests for PR 44397 — Add Users Manually (Create User)
 * Team > Users: button "Create User", modal form, validation, copy password.
 *
 * Precondition: run against dev with an admin account (login before or via storageState).
 */

import { test, expect } from '@playwright/test';

test.describe('Team > Users — Create User (PR 44397)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/team/');
    await page.waitForURL('**/team/**');

    await page.evaluate(() => {
      const style = document.createElement('style');
      style.textContent = `
        .pw-cursor {
          position: fixed !important; z-index: 999999 !important;
          width: 28px; height: 28px;
          background: rgba(255, 50, 50, 0.6);
          border: 3px solid red;
          border-radius: 50%;
          pointer-events: none;
          transform: translate(-50%, -50%);
          transition: transform 0.08s, background 0.08s;
        }
        .pw-cursor.click {
          transform: translate(-50%, -50%) scale(0.5) !important;
          background: rgba(255, 165, 0, 0.9) !important;
        }
      `;
      document.head.appendChild(style);

      const cursor = document.createElement('div');
      cursor.className = 'pw-cursor';
      cursor.style.left = '0px';
      cursor.style.top = '0px';
      document.body.appendChild(cursor);

      document.addEventListener('mousemove', (e) => {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
      });
      document.addEventListener('mousedown', () => cursor.classList.add('click'));
      document.addEventListener('mouseup', () => cursor.classList.remove('click'));
    });
  });

  test('5.2.1 — Create User button and Invite Team are visible on Team > Users', async ({ page }) => {
    await expect(page.getByRole('button', { name: /invite team/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /create user/i }).first()).toBeVisible();
  });

  test('5.2.1 — Opening create user modal: fields and auto password', async ({ page }) => {
    await page
      .getByRole('button', { name: /create user/i })
      .first()
      .click();
    await expect(page.getByTestId('create-user-modal-header')).toBeVisible();
    await expect(page.getByText('Create User').first()).toBeVisible();

    await expect(page.getByLabel(/first name/i)).toBeVisible();
    await expect(page.getByLabel(/last name/i)).toBeVisible();
    await expect(page.getByLabel(/email/i).first()).toBeVisible();
    await expect(page.getByLabel(/password/i).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /^copy$/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /create user/i }).last()).toBeVisible();

    const passwordInput = page.getByLabel(/password/i).first();
    await expect(passwordInput).toBeVisible();
    const passwordValue = await passwordInput.inputValue();
    expect(passwordValue.length).toBe(8);
    expect(/[a-z]/.test(passwordValue)).toBe(true);
    expect(/[A-Z]/.test(passwordValue)).toBe(true);
    expect(/\d/.test(passwordValue)).toBe(true);
    expect(/[!@#$%^&*]/.test(passwordValue)).toBe(true);
  });

  test('5.2.4 — Copy password shows notification', async ({ page }) => {
    await page
      .getByRole('button', { name: /create user/i })
      .first()
      .click();
    await expect(page.getByTestId('create-user-modal-header')).toBeVisible();
    await page.getByRole('button', { name: /^copy$/i }).click();
    await expect(page.getByText(/password copied/i)).toBeVisible();
  });

  test('5.2.5 — Reopening modal generates new password', async ({ page }) => {
    await page
      .getByRole('button', { name: /create user/i })
      .first()
      .click();
    await expect(page.getByTestId('create-user-modal-header')).toBeVisible();
    const password1 = await page
      .getByLabel(/password/i)
      .first()
      .inputValue();
    await page.keyboard.press('Escape');
    await page
      .getByRole('button', { name: /create user/i })
      .first()
      .click();
    await expect(page.getByTestId('create-user-modal-header')).toBeVisible();
    const password2 = await page
      .getByLabel(/password/i)
      .first()
      .inputValue();
    expect(password1).not.toBe(password2);
  });

  test('5.3.1 — Empty email: Create user button disabled or validation error', async ({ page }) => {
    await page
      .getByRole('button', { name: /create user/i })
      .first()
      .click();
    await expect(page.getByTestId('create-user-modal-header')).toBeVisible();
    const emailInput = page.getByLabel(/email/i).first();
    await emailInput.clear();
    const submitBtn = page.getByRole('button', { name: /create user/i }).last();
    await expect(submitBtn).toBeDisabled();
  });

  test('5.3.2 — Invalid email shows validation error', async ({ page }) => {
    await page
      .getByRole('button', { name: /create user/i })
      .first()
      .click();
    await expect(page.getByTestId('create-user-modal-header')).toBeVisible();
    await page.getByLabel(/email/i).first().fill('invalid');
    await page.getByLabel(/email/i).first().press('Tab');
    await expect(page.getByText('Please enter a valid Email')).toBeVisible();
  });

  test('5.3.3 — Password with spaces shows error', async ({ page }) => {
    await page
      .getByRole('button', { name: /create user/i })
      .first()
      .click();
    await expect(page.getByTestId('create-user-modal-header')).toBeVisible();
    await page
      .getByLabel(/password/i)
      .first()
      .fill('pass word');
    await page
      .getByLabel(/password/i)
      .first()
      .press('Tab');
    await expect(page.getByText('Passwords cannot contain spaces')).toBeVisible();
  });

  test('5.3.4 — Password too short shows error', async ({ page }) => {
    await page
      .getByRole('button', { name: /create user/i })
      .first()
      .click();
    await expect(page.getByTestId('create-user-modal-header')).toBeVisible();
    await page
      .getByLabel(/password/i)
      .first()
      .fill('12345');
    await page
      .getByLabel(/password/i)
      .first()
      .press('Tab');
    await expect(page.getByText('Passwords must be at least 6 characters long')).toBeVisible();
  });

  test('5.2.2 — Create user (User role): success flow', async ({ page }) => {
    const uniqueEmail = `e2e-user-${Date.now()}@example.com`;
    await page
      .getByRole('button', { name: /create user/i })
      .first()
      .click();
    await expect(page.getByTestId('create-user-modal-header')).toBeVisible();

    await page.getByLabel(/first name/i).fill('E2E');
    await page.getByLabel(/last name/i).fill('User');
    await page.getByLabel(/email/i).first().fill(uniqueEmail);
    await page
      .getByRole('button', { name: /create user/i })
      .last()
      .click();

    await expect(page.getByText(/successfully created|has been successfully created/i)).toBeVisible();
    await expect(page.getByTestId('create-user-modal-header')).not.toBeVisible();
    await expect(page.getByText(uniqueEmail)).toBeVisible();
  });

  test('5.2.3 — Create user with Admin role', async ({ page }) => {
    const uniqueEmail = `e2e-admin-${Date.now()}@example.com`;
    await page
      .getByRole('button', { name: /create user/i })
      .first()
      .click();
    await expect(page.getByTestId('create-user-modal-header')).toBeVisible();

    await page.getByLabel(/first name/i).fill('E2E');
    await page.getByLabel(/last name/i).fill('Admin');
    await page.getByLabel(/email/i).first().fill(uniqueEmail);
    await page.locator('.react-select__control').click();
    await page.getByRole('option', { name: /admin/i }).click();
    await page
      .getByRole('button', { name: /create user/i })
      .last()
      .click();

    await expect(page.getByText(/successfully created|has been successfully created/i)).toBeVisible();
    await expect(page.getByTestId('create-user-modal-header')).not.toBeVisible();
    await expect(page.getByText(uniqueEmail)).toBeVisible();
  });
});
