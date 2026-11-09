/* Read-only browser audit against the local source server. No account preferences are saved. */
const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');

const frontend = path.resolve(__dirname, '../..');
const artifacts = path.join(__dirname, '.auth', 'rtl-controls');
const baseURL = process.env.RTL_BASE_URL || 'http://localhost:8000';
const locale = process.env.RTL_LOCALE || 'ar-sy';
const width = Number(process.env.RTL_WIDTH || 1440);
const scenario = process.env.RTL_SCENARIO || 'profile';
const authState = path.resolve(
  frontend,
  process.env.RTL_STORAGE_STATE || process.env.RTL_AUTH_STATE || 'tests/e2e/.auth/rtl-session.json',
);

function assertInsideViewport(bounds, height = 1080) {
  assert(bounds && bounds.width > 0 && bounds.height > 0, 'Popup must have visible bounds');
  assert(bounds.x >= -1 && bounds.x + bounds.width <= width + 1, 'Popup must fit viewport width');
  assert(bounds.y >= -1 && bounds.y + bounds.height <= height + 1, 'Popup must fit viewport height');
}

async function main() {
  assert(['en', 'ar-sy'].includes(locale), 'RTL_LOCALE must be en or ar-sy');
  assert(['profile', 'nested'].includes(scenario), 'RTL_SCENARIO must be profile or nested');
  assert(Number.isInteger(width) && width > 0, 'RTL_WIDTH must be a positive integer');
  assert(fs.existsSync(authState), 'An ignored, manually supplied RTL_STORAGE_STATE/RTL_AUTH_STATE file is required');
  const state = JSON.parse(fs.readFileSync(authState, 'utf8'));
  const safeMessage = (error) => {
    let message = String(error.message || error)
      .split('Call log:')[0]
      .trim();
    for (const cookie of state.cookies || []) {
      if (cookie.value) message = message.split(cookie.value).join('[redacted]');
    }
    return message.replace(/([?&](?:token|auth_token|access_token)=)[^&\s]+/gi, '$1[redacted]');
  };
  const routeErrors = [];
  const errors = [];
  const failedApiRequests = [];
  const failedApiResponses = [];
  const pendingApiRequests = new Map();
  const assertHealthy = async () => {
    const deadline = Date.now() + 5000;
    while (pendingApiRequests.size && Date.now() < deadline) await page.waitForTimeout(100);
    assert.deepEqual([...pendingApiRequests.values()], [], 'API content is still pending');
    assert.deepEqual(routeErrors, [], 'Request interception failed');
    assert.deepEqual(errors, [], 'Application raised a page error');
    assert.deepEqual(failedApiRequests, [], 'An API request failed');
    assert.deepEqual(failedApiResponses, [], 'An API response failed');
  };
  fs.mkdirSync(artifacts, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const context = await browser.newContext({
    storageState: state,
    viewport: { width, height: 1080 },
  });
  await context.grantPermissions(['local-network-access'], { origin: new URL(baseURL).origin });
  await context.routeWebSocket('**/*', (socket) => socket.close({ code: 1000, reason: 'Read-only layout check' }));
  const blockedWrites = [];
  await context.route('**/*', async (route) => {
    try {
      const request = route.request();
      if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method())) {
        blockedWrites.push({ method: request.method(), path: new URL(request.url()).pathname });
        await route.fulfill({ status: 409, contentType: 'application/json', body: '{"code":"RTL_READ_ONLY_CHECK"}' });
        return;
      }
      if (request.method() === 'GET' && new URL(request.url()).pathname.includes('/auth/context')) {
        const response = await route.fetch();
        const body = await response.json();
        body.language = locale;
        if (body.user) body.user.language = locale;
        await route.fulfill({ response, json: body });
        return;
      }
      if (
        scenario === 'nested' &&
        request.method() === 'GET' &&
        /\/datasets\/?$/.test(new URL(request.url()).pathname)
      ) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            count: 2,
            next: null,
            previous: null,
            results: [1, 2].map((id) => ({
              id,
              name: `RTL dataset fixture ${id}`,
              items_count: 2,
              description: '',
              date_created_tsp: 0,
            })),
          }),
        });
        return;
      }
      await route.continue();
    } catch (error) {
      routeErrors.push(safeMessage(error));
      await route.abort().catch(() => {});
    }
  });
  await context.addInitScript(
    ({ language }) => {
      let config;
      Object.defineProperty(window, '__pneumaticConfig', {
        configurable: true,
        get: () => config,
        set: (value) => {
          config = value;
          if (config?.user) config.user.language = language;
        },
      });
    },
    { language: locale },
  );
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  const assertLocale = async () => {
    const actual = await page.evaluate(() => ({
      lang: document.documentElement.lang,
      dir: document.documentElement.dir,
    }));
    assert.equal(
      actual.lang,
      locale === 'ar-sy' ? 'ar-SY' : 'en-US',
      'Document language must match the requested locale',
    );
    assert.equal(actual.dir, locale === 'ar-sy' ? 'rtl' : 'ltr', 'Document direction must match the requested locale');
  };
  try {
    page.on('pageerror', (error) => errors.push(safeMessage(error)));
    page.on('request', (request) => {
      if (['xhr', 'fetch'].includes(request.resourceType()))
        pendingApiRequests.set(request, new URL(request.url()).pathname);
    });
    page.on('requestfinished', (request) => pendingApiRequests.delete(request));
    page.on('requestfailed', (request) => {
      pendingApiRequests.delete(request);
      if (['xhr', 'fetch'].includes(request.resourceType()) && request.failure()?.errorText !== 'net::ERR_ABORTED') {
        failedApiRequests.push({
          path: new URL(request.url()).pathname,
          error: safeMessage(request.failure()?.errorText || 'Request failed'),
        });
      }
    });
    page.on('response', (response) => {
      const request = response.request();
      const requestPath = new URL(response.url()).pathname;
      if (
        response.status() >= 400 &&
        ['xhr', 'fetch'].includes(request.resourceType()) &&
        !(response.status() === 404 && requestPath === '/navigation/menu/help-center')
      ) {
        failedApiResponses.push({ path: requestPath, status: response.status() });
      }
    });
    if (scenario === 'nested') {
      await page.goto(`${baseURL}/templates/create/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
      const heading = locale.startsWith('ar')
        ? '\u0646\u0645\u0648\u0630\u062c \u0627\u0644\u0628\u062f\u0621'
        : 'Kick-off Form';
      await page.getByText(heading, { exact: true }).first().click();
      await assertLocale();
      const kickoff = page.locator('[class^="kick-off--"]').first();
      await kickoff.locator('[class*="component-icon-container"]').nth(4).click();
      await kickoff.locator('[class*="kick-off-input--"]').first().hover();
      await page.locator('[class*="dropdown-wrapper--"] button').first().click();
      const datasetsLabel = locale.startsWith('ar')
        ? '\u0645\u062c\u0645\u0648\u0639\u0627\u062a \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a'
        : 'Datasets';
      await page.getByRole('button', { name: datasetsLabel, exact: true }).click();
      const nested = page
        .getByText('RTL dataset fixture 1', { exact: true })
        .locator('xpath=ancestor::*[@role="menu"][1]');
      await page.waitForTimeout(200);
      console.log(
        JSON.stringify({
          phase: 'nested-menu',
          locale,
          width,
          errors,
          parent: await page.getByRole('button', { name: datasetsLabel, exact: true }).boundingBox(),
          menu: await nested.boundingBox(),
          placement: await nested.getAttribute('x-placement'),
        }),
      );
      await page.screenshot({ path: path.join(artifacts, `${locale}-${width}-nested.png`), fullPage: false });
      assertInsideViewport(await nested.boundingBox());
      await page.keyboard.press('Escape');
      await page.mouse.click(width - 5, 500);
      await kickoff.locator('[class*="fieldset-picker__toggle"]').click();
      const fieldsetMenu = page.getByRole('menu').last();
      await page.waitForTimeout(200);
      console.log(
        JSON.stringify({
          phase: 'fieldset-fixed-menu',
          locale,
          width,
          bounds: await fieldsetMenu.boundingBox(),
          parent: await fieldsetMenu.evaluate((element) => ({
            bodyChild: element.parentElement === document.body,
            position: getComputedStyle(element).position,
          })),
        }),
      );
      await page.screenshot({ path: path.join(artifacts, `${locale}-${width}-fieldset-portal.png`) });
      assertInsideViewport(await fieldsetMenu.boundingBox());
      console.log(JSON.stringify({ blockedWrites }));
      await assertHealthy();
      return;
    }
    await page.goto(`${baseURL}/settings/profile/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForFunction(() => document.querySelector('h1') && document.fonts.status === 'loaded');
    await assertLocale();
    await page.screenshot({ path: path.join(artifacts, `${locale}-${width}-profile.png`), fullPage: true });
    console.log(
      JSON.stringify({
        phase: 'profile',
        locale,
        width,
        url: page.url(),
        errors,
        state: await page.evaluate(() => ({
          language: document.documentElement.lang,
          direction: document.documentElement.dir,
          overflow: document.documentElement.scrollWidth - innerWidth,
          inputs: Array.from(document.querySelectorAll('input')).map((element) => ({
            type: element.type,
            name: element.name,
            hasValue: Boolean(element.value),
            label: element.getAttribute('aria-label') || element.labels?.[0]?.textContent,
            direction: getComputedStyle(element).direction,
            paddingLeft: getComputedStyle(element).paddingLeft,
            paddingRight: getComputedStyle(element).paddingRight,
          })),
          selects: Array.from(document.querySelectorAll('[role="combobox"]')).map((element) => ({
            id: element.id,
            label: element.labels?.[0]?.textContent,
            parentText: element.closest('[class*="field"]')?.textContent,
          })),
        })),
      }),
    );
    await page.locator('[data-test-id="open-user-menu-button"]').click();
    await page.waitForTimeout(200);
    const toggleBounds = await page.locator('[data-test-id="open-user-menu-button"]').boundingBox();
    const menuBounds = await page.locator('nav [class*="dropdown-menu_show"]').boundingBox();
    assertInsideViewport(menuBounds);
    assert(menuBounds.y >= toggleBounds.y + toggleBounds.height - 1, 'Profile menu must not cover its toggle');
    console.log(
      JSON.stringify({
        phase: 'profile-menu',
        locale,
        width,
        toggle: await page.locator('[data-test-id="open-user-menu-button"]').boundingBox(),
        menu: await page.locator('nav [class*="dropdown-menu_show"]').boundingBox(),
      }),
    );
    await page.screenshot({ path: path.join(artifacts, `${locale}-${width}-menu.png`) });
    await page.locator('[data-test-id="open-user-menu-button"]').click();
    await page.locator('nav [class*="dropdown-menu_show"]').waitFor({ state: 'hidden' });
    await page.mouse.click(width - 5, 500);

    // These edits are confined to Formik state; the Save button is never pressed.
    await page.locator('input[name="absenceStatus"]').locator('..').locator('.react-select__control').click();
    await page.waitForTimeout(200);
    assertInsideViewport(await page.getByRole('listbox').boundingBox());
    console.log(
      JSON.stringify({ phase: 'status-select', locale, width, listbox: await page.getByRole('listbox').boundingBox() }),
    );
    await page.getByRole('option').nth(1).click();
    const dateInput = page.locator('.react-datepicker-wrapper input').first();
    await dateInput.evaluate((element) => element.scrollIntoView({ block: 'end' }));
    await dateInput.click();
    await page.locator('.react-datepicker').waitFor();
    await page.waitForTimeout(200);
    const readCalendar = () =>
      page.evaluate(() => {
        const rect = (selector) => {
          const element = document.querySelector(selector);
          const bounds = element.getBoundingClientRect();
          const style = getComputedStyle(element);
          return {
            x: bounds.x,
            y: bounds.y,
            width: bounds.width,
            height: bounds.height,
            direction: style.direction,
            top: style.top,
            left: style.left,
            right: style.right,
            transform: style.transform,
          };
        };
        return {
          input: rect('.react-datepicker-wrapper input'),
          popper: rect('.react-datepicker-popper'),
          calendar: rect('.react-datepicker'),
          previous: rect('.react-datepicker__navigation--previous'),
          next: rect('.react-datepicker__navigation--next'),
          month: document.querySelector('.react-datepicker__current-month').textContent,
          viewport: { width: innerWidth, height: innerHeight },
        };
      });
    const beforeCalendar = await readCalendar();
    console.log(JSON.stringify({ phase: 'datepicker-before', locale, width, state: beforeCalendar }));
    await page.screenshot({ path: path.join(artifacts, `${locale}-${width}-datepicker.png`) });
    assertInsideViewport(beforeCalendar.calendar);
    assert(
      Math.abs(beforeCalendar.previous.x - beforeCalendar.next.x) > 32,
      'Month navigation buttons must not overlap',
    );
    await page.locator('.react-datepicker__navigation--next').click();
    await page.waitForTimeout(200);
    const afterCalendar = await readCalendar();
    console.log(JSON.stringify({ phase: 'datepicker-next', locale, width, state: afterCalendar }));
    assert.notEqual(afterCalendar.month, beforeCalendar.month, 'Next month navigation must update the calendar');
    assertInsideViewport(afterCalendar.calendar);
    await page.screenshot({ path: path.join(artifacts, `${locale}-${width}-datepicker-next.png`) });
    await dateInput.press('Escape');
    await page.locator('input[name="language"]').locator('..').locator('.react-select__control').click();
    console.log(
      JSON.stringify({
        phase: 'language-select',
        locale,
        width,
        listbox: await page.getByRole('listbox').boundingBox(),
        style: await page
          .getByRole('listbox')
          .evaluate((element) => ({ direction: getComputedStyle(element).direction })),
      }),
    );
    await page.screenshot({ path: path.join(artifacts, `${locale}-${width}-language.png`) });
    console.log(JSON.stringify({ blockedWrites }));
    await assertLocale();
    await assertHealthy();
  } catch (error) {
    await page
      .screenshot({ path: path.join(artifacts, `${locale}-${width}-${scenario}-failed.png`), fullPage: true })
      .catch(() => {});
    throw error;
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
