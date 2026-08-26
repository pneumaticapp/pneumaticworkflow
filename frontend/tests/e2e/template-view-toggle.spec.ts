import path from 'path';
import { config } from 'dotenv';
import { test, expect, Page } from '@playwright/test';

config({ path: path.resolve(__dirname, '../../.env') });

const E2E_TEMPLATE_ID = process.env.E2E_TEMPLATE_ID;
const GRAPH_POSITIONS_STORAGE_KEY = 'template_graph_node_positions';
const GRAPH_VIEW_MODE_STORAGE_KEY = 'template_graph_view_mode';
const TIMEOUT = { medium: 5_000, nav: 20_000 } as const;

const openTemplateEditor = async (page: Page) => {
  if (E2E_TEMPLATE_ID) {
    await page.goto(`/templates/edit/${E2E_TEMPLATE_ID}/`);
    await page.waitForLoadState('domcontentloaded');
  } else {
    await page.goto('/templates/');
    await page.waitForURL(/\/templates\/$/);
    const link = page.locator('a[href*="/templates/edit/"]').first();
    await expect(link).toBeVisible({ timeout: TIMEOUT.nav });
    await link.click();
    await page.waitForURL(/\/templates\/edit\/\d+/, { timeout: TIMEOUT.nav });
  }

  await expect(page.getByTestId('template-view-toggle')).toBeVisible({ timeout: TIMEOUT.nav });
};

test.describe('Template view toggle', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/templates/');
    await page.waitForURL(/\/templates\/$/);
    await page.evaluate(
      ([positionsKey, viewModeKey]) => {
        localStorage.removeItem(positionsKey);
        localStorage.removeItem(viewModeKey);
      },
      [GRAPH_POSITIONS_STORAGE_KEY, GRAPH_VIEW_MODE_STORAGE_KEY],
    );

    await openTemplateEditor(page);
  });

  test('should switch template editor from Line to Graph and back', async ({ page }) => {
    const toggle = page.getByTestId('template-view-toggle');
    const lineButton = toggle.getByRole('button', { name: 'Line' });
    const graphButton = toggle.getByRole('button', { name: 'Graph' });

    await expect(lineButton).toBeVisible();
    await expect(page.locator('#task-form-1')).toBeVisible({ timeout: TIMEOUT.medium });

    await graphButton.click();
    await expect(page.getByTestId('template-graph-editor')).toBeVisible({ timeout: TIMEOUT.medium });
    await expect(page.getByTestId('graph-kickoff-node')).toBeVisible({ timeout: TIMEOUT.medium });
    await expect(page.locator('.react-flow__minimap')).toHaveCount(0);
    await expect(page.locator('.react-flow__controls')).toHaveCount(0);
    await expect(page.locator('#task-form-1')).toHaveCount(0);

    await lineButton.click();
    await expect(page.locator('#task-form-1')).toBeVisible({ timeout: TIMEOUT.medium });
    await expect(page.getByTestId('template-graph-editor')).toHaveCount(0);
  });

  test('should open the task editor panel over the graph and close it', async ({ page }) => {
    await page.getByTestId('template-view-toggle').getByRole('button', { name: 'Graph' }).click();
    await expect(page.getByTestId('template-graph-editor')).toBeVisible({ timeout: TIMEOUT.medium });

    await page.getByTestId('graph-node-edit').first().click();
    await expect(page.getByTestId('graph-task-editor')).toBeVisible({ timeout: TIMEOUT.medium });
    await expect(page.getByTestId('template-graph-editor')).toBeVisible();

    await page.getByTestId('graph-task-editor-close').click();
    await expect(page.getByTestId('graph-task-editor')).toHaveCount(0);
    await expect(page.getByTestId('template-graph-editor')).toBeVisible();
  });

  test('should add a task from a leaf plus and open the editor panel', async ({ page }) => {
    await page.getByTestId('template-view-toggle').getByRole('button', { name: 'Graph' }).click();
    await expect(page.getByTestId('template-graph-editor')).toBeVisible({ timeout: TIMEOUT.medium });

    const taskCount = await page.getByTestId('graph-task-node').count();
    await page.locator('[data-test-id="graph-add-task"][data-kind="continue"]').first().click();

    await expect(page.getByTestId('graph-task-editor')).toBeVisible({ timeout: TIMEOUT.medium });
    await expect(page.getByTestId('graph-task-node')).toHaveCount(taskCount + 1);
    await expect(page.getByTestId('template-graph-editor')).toBeVisible();
  });

  test('should restore a moved graph card after switching views', async ({ page }) => {
    await page.evaluate((storageKey) => localStorage.removeItem(storageKey), GRAPH_POSITIONS_STORAGE_KEY);

    const toggle = page.getByTestId('template-view-toggle');
    const lineButton = toggle.getByRole('button', { name: 'Line' });
    const graphButton = toggle.getByRole('button', { name: 'Graph' });

    await graphButton.click();

    const taskNode = page.locator('.react-flow__node-task').first();
    await expect(taskNode).toBeVisible({ timeout: TIMEOUT.medium });

    const nodeId = await taskNode.getAttribute('data-id');
    const initialTransform = await taskNode.evaluate((element) => (element as HTMLElement).style.transform);
    const nodeBox = await taskNode.boundingBox();

    expect(nodeId).not.toBeNull();
    expect(nodeBox).not.toBeNull();

    await page.mouse.move(nodeBox!.x + 20, nodeBox!.y + 20);
    await page.mouse.down();
    await page.mouse.move(nodeBox!.x + 140, nodeBox!.y + 80, { steps: 10 });
    await page.mouse.up();

    const movedTransform = await taskNode.evaluate((element) => (element as HTMLElement).style.transform);
    const storedPositions = await page.evaluate(
      (storageKey) => localStorage.getItem(storageKey),
      GRAPH_POSITIONS_STORAGE_KEY,
    );

    expect(movedTransform).not.toBe(initialTransform);
    expect(storedPositions).toContain(`"${nodeId}"`);

    await lineButton.click();
    await graphButton.click();

    const restoredNode = page.locator(`.react-flow__node-task[data-id="${nodeId}"]`);
    await expect(restoredNode).toBeVisible({ timeout: TIMEOUT.medium });
    await expect.poll(
      () => restoredNode.evaluate((element) => (element as HTMLElement).style.transform),
    ).toBe(movedTransform);

    await page.reload();
    await expect(page.getByTestId('template-view-toggle')).toBeVisible({ timeout: TIMEOUT.nav });
    await expect(page.getByTestId('template-graph-editor')).toBeVisible({ timeout: TIMEOUT.medium });

    const reloadedNode = page.locator(`.react-flow__node-task[data-id="${nodeId}"]`);
    await expect(reloadedNode).toBeVisible({ timeout: TIMEOUT.medium });
    await expect.poll(
      () => reloadedNode.evaluate((element) => (element as HTMLElement).style.transform),
    ).toBe(movedTransform);
  });

  test('should keep Line selected when the active segment is clicked again', async ({ page }) => {
    const lineButton = page.getByTestId('template-view-toggle').getByRole('button', { name: 'Line' });

    await lineButton.click();
    await expect(page.locator('#task-form-1')).toBeVisible({ timeout: TIMEOUT.medium });
  });

  test('should restore Graph view after reload and after leaving the editor', async ({ page }) => {
    await page.getByTestId('template-view-toggle').getByRole('button', { name: 'Graph' }).click();
    await expect(page.getByTestId('template-graph-editor')).toBeVisible({ timeout: TIMEOUT.medium });

    await page.reload();
    await expect(page.getByTestId('template-view-toggle')).toBeVisible({ timeout: TIMEOUT.nav });
    await expect(page.getByTestId('template-graph-editor')).toBeVisible({ timeout: TIMEOUT.medium });

    await page.getByRole('link', { name: 'All Templates' }).click();
    await page.waitForURL(/\/templates\/$/);
    await openTemplateEditor(page);

    await expect(page.getByTestId('template-graph-editor')).toBeVisible({ timeout: TIMEOUT.medium });
  });
});
