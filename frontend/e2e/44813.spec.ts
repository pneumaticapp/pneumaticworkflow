import { test, expect, APIRequestContext } from '@playwright/test';
import { injectVisualCursor } from './utils/injectVisualCursor';
import { createTestTemplate } from './utils/createTestTemplate';
import { deleteTestTemplate } from './utils/deleteTestTemplate';
import { enableTemplateIfNeeded } from './utils/enableTemplateIfNeeded';
import { runTestWorkflow } from './utils/runTestWorkflow';
import { openFieldDropdown } from './utils/openFieldDropdown';
import { resetTemplateFields } from './utils/resetTemplateFields';
import { ICreatedTemplate } from './utils/types';
import { EExtraFieldType } from '../src/public/types/template';

let template: ICreatedTemplate;

test.describe('Template editor - Hidden switch for kickoff fields (PR 44813)', () => {
  test.beforeAll(async ({ request }: { request: APIRequestContext }) => {
    template = await createTestTemplate(request, {
      kickoffFields: 2,
      taskFields: 2,
      defaultFieldType: EExtraFieldType.Text,
    });
  });

  test.afterAll(async ({ request }: { request: APIRequestContext }) => {
    await deleteTestTemplate(request, template.templateId);
  });

  test.beforeEach(async ({ page, request }) => {
    await resetTemplateFields(request, template.templateId);

    await page.goto(`/templates/edit/${template.templateId}/`);

    await page.waitForURL(`**/templates/edit/${template.templateId}/**`);

    await injectVisualCursor(page);
  });

  test('1.1 - Hidden switch exists, hidden field is not shown in run form', async ({ page }) => {
    const fieldToHide = template.kickoffFields[0];
    const fieldToKeep = template.kickoffFields[1];

    await page.locator('[class*="kick-off"]').getByText('Kick-off Form').click();

    const fieldToHideLocator = page
      .locator('[class*="kick-off-input--"]')
      .filter({ has: page.locator(`input[value="${fieldToHide.name}"]`) });

    await expect(fieldToHideLocator).toBeVisible({ timeout: 5000 });

    await openFieldDropdown(fieldToHideLocator);

    await expect(page.getByRole('menu').getByText('Hidden')).toBeVisible();

    await page.getByRole('menu').getByText('Hidden').locator('..').getByRole('switch').click();

    await expect(page.getByText(/Template was saved successfully/i)).toBeVisible({ timeout: 10000 });

    await enableTemplateIfNeeded(page);
    await page
      .getByRole('button', { name: /run workflow/i })
      .first()
      .click();
    await expect(page.locator('[class*="popup__kickoff"]')).toBeVisible({ timeout: 5000 });

    await expect(
      page.locator('[class*="popup__kickoff"]').getByRole('textbox', { name: fieldToHide.name }),
    ).not.toBeVisible();

    await expect(
      page.locator('[class*="popup__kickoff"]').getByRole('textbox', { name: fieldToKeep.name }),
    ).toBeVisible();
  });

  test('1.2 - Required and Hidden are mutually exclusive', async ({ page }) => {
    const targetField = template.kickoffFields[0];

    await page.locator('[class*="kick-off"]').getByText('Kick-off Form').click();

    const kickoffField = page
      .locator('[class*="kick-off-input--"]')
      .filter({ has: page.locator(`input[value="${targetField.name}"]`) });
    await expect(kickoffField).toBeVisible({ timeout: 5000 });
    await openFieldDropdown(kickoffField);

    await page.getByRole('switch', { name: 'Required' }).click();
    await expect(page.getByText(/Template was saved successfully/i)).toBeVisible({ timeout: 10000 });

    const hiddenSwitch = page.getByRole('switch', { name: 'Hidden' });
    await expect(hiddenSwitch).toBeDisabled();

    await page.getByRole('switch', { name: 'Required' }).click();
    await page.getByRole('switch', { name: 'Hidden' }).click();
    await expect(page.getByText(/Template was saved successfully/i)).toBeVisible({ timeout: 10000 });

    const requiredSwitch = page.getByRole('switch', { name: 'Required' });
    await expect(requiredSwitch).toBeDisabled();
  });

  test('1.3 - Save and reload: Hidden state persists', async ({ page }) => {
    const targetField = template.kickoffFields[0];

    await page.locator('[class*="kick-off"]').getByText('Kick-off Form').click();
    const kickoffField = page
      .locator('[class*="kick-off-input--"]')
      .filter({ has: page.locator(`input[value="${targetField.name}"]`) });
    await expect(kickoffField).toBeVisible({ timeout: 5000 });
    await openFieldDropdown(kickoffField);

    await page.getByRole('switch', { name: 'Hidden' }).click();
    await expect(page.getByText(/Template was saved successfully/i)).toBeVisible({ timeout: 10000 });

    await page.reload();
    await page.waitForURL(`**/templates/edit/${template.templateId}/**`);

    await page.locator('[class*="kick-off"]').getByText('Kick-off Form').click();
    await openFieldDropdown(kickoffField);

    const hiddenSwitch = page.getByRole('switch', { name: 'Hidden' });
    await expect(hiddenSwitch).toBeChecked();
  });

  test('1.4 - Hidden field is not shown in task card (task outputs)', async ({ page, request }) => {
    const fieldToHide = template.taskFields[0];
    const fieldToKeep = template.taskFields[1];

    await page.locator('[class*="task_view-title"]').first().click();

    const outputBtn = page.getByRole('button', { name: /output fields/i });
    await expect(outputBtn).toBeVisible({ timeout: 10000 });
    await outputBtn.click();

    const taskField = page
      .locator('[class*="kick-off-input--"]')
      .filter({ has: page.locator(`input[value="${fieldToHide.name}"]`) });
    await expect(taskField).toBeVisible({ timeout: 5000 });
    await openFieldDropdown(taskField);

    await page.getByRole('switch', { name: 'Hidden' }).click();
    await expect(page.getByText(/Template was saved successfully/i)).toBeVisible({ timeout: 10000 });

    await enableTemplateIfNeeded(page);
    const taskId = await runTestWorkflow(request, template.templateId);

    await page.goto(`/tasks/${taskId}/`);
    await page.waitForURL(`**/tasks/${taskId}/**`);

    const outputAccordion = page.getByRole('button', { name: /output fields/i });
    if (await outputAccordion.isVisible()) {
      await outputAccordion.click();
    }

    await expect(
      page.locator('[class*="task-output__field"]').filter({ has: page.locator(`input[value="${fieldToHide.name}"]`) }),
    ).not.toBeVisible();

    await expect(
      page.locator('[class*="task-output__field"]').filter({ has: page.locator(`input[value="${fieldToKeep.name}"]`) }),
    ).toBeVisible();
  });

  test('1.6 - API: PUT template sends isHidden, GET template returns is_hidden', async ({ page }) => {
    type PutPayload = { kickoff?: { fields?: Array<{ apiName?: string; api_name?: string; isHidden?: boolean; is_hidden?: boolean }> } };

    let putPayload: PutPayload | null = null;
    let getResponseKickoffFields: Array<{ apiName?: string; api_name?: string; is_hidden?: boolean }> | null = null;

    await page.route('**/templates/**', async (route) => {
      const request = route.request();

      if (request.method() === 'PUT') {
        try {
          putPayload = request.postDataJSON() as PutPayload;
        } catch {
        }
      }
      await route.continue();
    });

    page.on('response', async (response) => {
      const url = response.url();

      if (response.request().method() === 'GET' && url.includes('/templates/') && !url.includes('?')) {
        try {
          const json = (await response.json()) as { kickoff?: { fields?: Array<{ apiName?: string; api_name?: string; is_hidden?: boolean }> } };
          if (json?.kickoff?.fields) {
            getResponseKickoffFields = json.kickoff.fields as Array<{ apiName?: string; api_name?: string; is_hidden?: boolean }>;
          }
        } catch {
        }
      }
    });

    const targetField = template.kickoffFields[0];
    await page.locator('[class*="kick-off"]').getByText('Kick-off Form').click();
    const kickoffField = page
      .locator('[class*="kick-off-input--"]')
      .filter({ has: page.locator(`input[value="${targetField.name}"]`) });
    await expect(kickoffField).toBeVisible({ timeout: 5000 });
    await openFieldDropdown(kickoffField);
    await page.getByRole('switch', { name: 'Hidden' }).click();
    await expect(page.getByText(/Template was saved successfully/i)).toBeVisible({ timeout: 10000 });

    expect(putPayload).not.toBeNull();

    const putFields = putPayload!.kickoff?.fields ?? [];

    const hiddenField = putFields.find((f) => (f.apiName ?? f.api_name) === targetField.apiName);
    expect(hiddenField).toBeDefined();
    expect(hiddenField!.isHidden ?? hiddenField!.is_hidden).toBe(true);

    getResponseKickoffFields = null;
    await page.reload();
    await page.waitForURL(`**/templates/edit/${template.templateId}/**`);

    await expect(page.locator('[class*="kick-off"]').getByText('Kick-off Form')).toBeVisible({ timeout: 10000 });

    expect(getResponseKickoffFields).not.toBeNull();

    const hiddenFieldInResponse = getResponseKickoffFields!.find((f) => (f.apiName ?? f.api_name) === targetField.apiName);
    expect(hiddenFieldInResponse).toBeDefined();
    expect(hiddenFieldInResponse!.is_hidden).toBe(true);
  });

  test('2.1 - When Required is on, Hidden switch is disabled', async ({ page }) => {
    const targetField = template.kickoffFields[0];

    await page.locator('[class*="kick-off"]').getByText('Kick-off Form').click();
    const kickoffField = page
      .locator('[class*="kick-off-input--"]')
      .filter({ has: page.locator(`input[value="${targetField.name}"]`) });
    await expect(kickoffField).toBeVisible({ timeout: 5000 });
    await openFieldDropdown(kickoffField);

    await page.getByRole('switch', { name: 'Required' }).click();

    const hiddenSwitch = page.getByRole('switch', { name: 'Hidden' });
    await expect(hiddenSwitch).toBeDisabled();
  });

  test('2.2 - When Hidden is on, Required switch is disabled', async ({ page }) => {
    const targetField = template.kickoffFields[0];

    await page.locator('[class*="kick-off"]').getByText('Kick-off Form').click();
    const kickoffField = page
      .locator('[class*="kick-off-input--"]')
      .filter({ has: page.locator(`input[value="${targetField.name}"]`) });
    await expect(kickoffField).toBeVisible({ timeout: 5000 });
    await openFieldDropdown(kickoffField);

    await page.getByRole('switch', { name: 'Hidden' }).click();

    const requiredSwitch = page.getByRole('switch', { name: 'Required' });
    await expect(requiredSwitch).toBeDisabled();
  });

  test('2.3 - Template with no hidden fields: all fields visible in run form (regression)', async ({ page }) => {
    const field0 = template.kickoffFields[0];
    const field1 = template.kickoffFields[1];

    await page.locator('[class*="kick-off"]').getByText('Kick-off Form').click();

    for (const field of [field0, field1]) {
      const kickoffField = page
        .locator('[class*="kick-off-input--"]')
        .filter({ has: page.locator(`input[value="${field.name}"]`) });
      await openFieldDropdown(kickoffField);
      const hiddenSwitch = page.getByRole('switch', { name: 'Hidden' });
      if (await hiddenSwitch.isChecked()) {
        await hiddenSwitch.click();
        await expect(page.getByText(/Template was saved successfully/i)).toBeVisible({ timeout: 10000 });
      } else {
        await page.keyboard.press('Escape');
      }
    }

    await enableTemplateIfNeeded(page);
    await page
      .getByRole('button', { name: /run workflow/i })
      .first()
      .click();
    await expect(page.locator('[class*="popup__kickoff"]')).toBeVisible({ timeout: 5000 });

    await expect(page.locator('[class*="popup__kickoff"]').getByRole('textbox', { name: field0.name })).toBeVisible();
    await expect(page.locator('[class*="popup__kickoff"]').getByRole('textbox', { name: field1.name })).toBeVisible();
  });

  test('2.4 - Legacy API without is_hidden: no crashes, fields treated as visible', async ({ page }) => {
    await page.route('**/templates/**', async (route) => {
      if (route.request().method() !== 'GET') {
        await route.continue();
        return;
      }

      const response = await route.fetch();

      type TemplateJson = { kickoff?: { fields?: Array<Record<string, unknown>> } };
      let json: TemplateJson;
      try {
        json = (await response.json()) as TemplateJson;
      } catch {
        await route.continue();
        return;
      }

      if (json?.kickoff?.fields && Array.isArray(json.kickoff.fields)) {
        const fields = json.kickoff.fields;
        json.kickoff.fields = fields.map((f) => {
          const { is_hidden, ...rest } = f;
          return rest;
        });
      }

      await route.fulfill({ status: response.status(), body: JSON.stringify(json) });
    });

    await page.goto(`/templates/edit/${template.templateId}/`);
    await page.waitForURL(`**/templates/edit/${template.templateId}/**`);

    await page.locator('[class*="kick-off"]').getByText('Kick-off Form').click();

    await expect(page.locator('[class*="kick-off-input--"]').first()).toBeVisible({
      timeout: 5000,
    });

    await enableTemplateIfNeeded(page);
    await page
      .getByRole('button', { name: /run workflow/i })
      .first()
      .click();
    await expect(page.locator('[class*="popup__kickoff"]')).toBeVisible({ timeout: 5000 });

    const popup = page.locator('[class*="popup__kickoff"]');
    const visibleFields = popup.locator('[class*="kickoff-extra-field"]');
    await expect(visibleFields.first()).toBeVisible();
  });
});
