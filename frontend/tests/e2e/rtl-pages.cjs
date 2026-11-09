/* Read-only source-application smoke checks using an existing, isolated session.
   Run from frontend: node tests/e2e/rtl-pages.cjs
   RTL_AUTH_STATE must point to ignored Playwright storage state. The default is
   tests/e2e/.auth/rtl-session.json. This script never creates an account, signs in,
   saves preferences, edits content, or sends notifications. */
const fs = require('node:fs');
const path = require('node:path');
const { chromium, selectors } = require('@playwright/test');

selectors.setTestIdAttribute('data-test-id');

const frontend = path.resolve(__dirname, '../..');
const baseURL = process.env.RTL_BASE_URL || 'http://localhost:8000';
const authState = path.resolve(frontend, process.env.RTL_AUTH_STATE || 'tests/e2e/.auth/rtl-session.json');
const outputDir = path.resolve(frontend, process.env.RTL_OUTPUT_DIR || 'test-results/rtl-pages');
const locales = (process.env.RTL_LOCALES || 'en,ar-sy').split(',');
const widths = (process.env.RTL_WIDTHS || '1280,375').split(',').map(Number);
const defaultRoutes = [
  ['dashboard', '/dashboard/'],
  ['tasks', '/tasks/'],
  ['templates', '/templates/'],
  ['team', '/team/'],
  ['profile', '/settings/profile/'],
  ['integrations', '/integrations/'],
  ['template-line-fixture', '/templates/create/'],
  ['template-graph-fixture', '/templates/create/?showcase=graph'],
];
const requestedRoutes =
  process.env.RTL_ROUTES === undefined ? undefined : process.env.RTL_ROUTES.split(',').map((name) => name.trim());
const routes = requestedRoutes ? defaultRoutes.filter(([name]) => requestedRoutes.includes(name)) : defaultRoutes;

function safeMessage(message, state) {
  let result = String(message);
  for (const cookie of state.cookies || []) {
    if (cookie.value) result = result.split(cookie.value).join('[redacted]');
  }
  return result.replace(/([?&](?:token|auth_token|access_token)=)[^&\s]+/gi, '$1[redacted]');
}

async function readGeometry(page) {
  return page.evaluate(() => {
    const rect = (element) => {
      if (!element) return null;
      const bounds = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      return {
        x: bounds.x,
        y: bounds.y,
        width: bounds.width,
        height: bounds.height,
        right: bounds.right,
        direction: style.direction,
        display: style.display,
        fontFamily: style.fontFamily,
      };
    };
    return {
      lang: document.documentElement.lang,
      dir: document.documentElement.dir,
      viewport: innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      apiOrigin: new URL(
        window.__pneumaticConfig.config.featureFlags.BACKEND_URL || window.__pneumaticConfig.config.api.publicUrl,
        location.origin,
      ).origin,
      body: rect(document.body),
      main: rect(document.querySelector('main')),
      navbar: rect(document.querySelector('.navbar')),
      sidebar: rect(document.querySelector('.sidebar .main-menu')),
      templateInfo: rect(document.querySelector('[class*="template-wrapper__info"]')),
      templateTasks: rect(document.querySelector('[class*="template-wrapper__tasks"]')),
      canvas: rect(document.querySelector('.react-flow')),
      arabicCharacters: (document.body.innerText.match(/[\u0600-\u06ff]/g) || []).length,
      arabicFontLoaded: document.fonts.check('400 16px "Hayyakum Allah"'),
      arabicFontFaces: [...document.fonts]
        .filter((font) => font.family.includes('Hayyakum Allah'))
        .map((font) => ({ weight: font.weight, status: font.status })),
      scrollers: [...document.querySelectorAll('body *')]
        .filter((element) => {
          const style = getComputedStyle(element);
          return ['auto', 'scroll'].includes(style.overflowY) && element.scrollHeight > element.clientHeight + 1;
        })
        .slice(0, 8)
        .map((element) => ({
          tagName: element.tagName,
          className: element.className,
          clientHeight: element.clientHeight,
          scrollHeight: element.scrollHeight,
        })),
    };
  });
}

async function installReadOnlyLocale(context, locale, observed) {
  const direction = locale === 'ar-sy' ? 'rtl' : 'ltr';
  const lang = locale === 'ar-sy' ? 'ar-SY' : 'en-US';
  await context.addInitScript(
    ({ selectedLocale, selectedLang, selectedDirection }) => {
      localStorage.setItem('currentLanguage', selectedLocale);
      localStorage.removeItem('template_graph_view_mode');
      let config;
      Object.defineProperty(window, '__pneumaticConfig', {
        configurable: true,
        get: () => config,
        set: (value) => {
          config = value;
          if (config.user) config.user.language = selectedLocale;
          document.documentElement.lang = selectedLang;
          document.documentElement.dir = selectedDirection;
        },
      });
    },
    { selectedLocale: locale, selectedLang: lang, selectedDirection: direction },
  );
  await context.route('**/*', async (route) => {
    try {
      const request = route.request();
      const url = new URL(request.url());
      if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method())) {
        observed.blockedMutations.push({ method: request.method(), path: url.pathname });
        await route.fulfill({
          status: 409,
          contentType: 'application/json',
          body: JSON.stringify({
            code: 'RTL_READ_ONLY_CHECK',
            message: 'Mutation blocked during read-only verification',
          }),
        });
        return;
      }
      if (request.isNavigationRequest() && url.origin === new URL(baseURL).origin) {
        const response = await route.fetch();
        if (response.headers()['content-type']?.includes('text/html')) {
          const html = (await response.text()).replace(/<html\b[^>]*>/i, `<html lang="${lang}" dir="${direction}">`);
          const headers = { ...response.headers() };
          delete headers['content-length'];
          delete headers['content-encoding'];
          await route.fulfill({ response, headers, body: html });
          return;
        }
        await route.fulfill({ response });
        return;
      }
      if (/\/auth\/context\/?$/.test(url.pathname)) {
        const response = await route.fetch();
        if (response.ok()) {
          const data = await response.json();
          if (data && typeof data === 'object') data.language = locale;
          await route.fulfill({ response, json: data });
          return;
        }
        await route.fulfill({ response });
        return;
      }
      await route.continue();
    } catch (error) {
      observed.routeErrors.push(String(error.message).split('Call log:')[0].trim());
      await route.abort('failed').catch(() => {});
    }
  });
}

async function run() {
  if (requestedRoutes && requestedRoutes.some((name) => !defaultRoutes.some(([known]) => known === name))) {
    throw new Error(`RTL_ROUTES must contain route names from: ${defaultRoutes.map(([name]) => name).join(', ')}`);
  }
  if (!routes.length) throw new Error('RTL_ROUTES must select at least one route');
  if (!fs.existsSync(authState)) throw new Error('An ignored, isolated RTL_AUTH_STATE file is required');
  const state = JSON.parse(fs.readFileSync(authState, 'utf8'));
  fs.mkdirSync(outputDir, { recursive: true });
  const browser = await chromium.launch({ channel: process.env.RTL_CHANNEL || 'chrome', headless: true });
  const report = { baseURL, startedAt: new Date().toISOString(), cases: [], limitations: [] };
  try {
    for (const locale of locales) {
      for (const width of widths) {
        const observed = { blockedMutations: [], routeErrors: [] };
        const context = await browser.newContext({
          storageState: state,
          viewport: { width, height: 1000 },
          extraHTTPHeaders: { 'Accept-Language': locale },
        });
        await context.grantPermissions(['local-network-access'], { origin: new URL(baseURL).origin });
        await context.routeWebSocket('**/*', (socket) =>
          socket.close({ code: 1000, reason: 'Read-only layout check' }),
        );
        await installReadOnlyLocale(context, locale, observed);
        const page = await context.newPage();
        for (const [name, routePath] of routes) {
          const errors = [];
          const consoleErrors = [];
          const failedResponses = [];
          const apiRequests = new Map();
          const requestFailures = [];
          const onPageError = (error) => errors.push(safeMessage(error.message, state));
          const onConsole = (message) => {
            if (message.type() === 'error') consoleErrors.push(safeMessage(message.text(), state));
          };
          const onRequest = (request) => {
            if (['xhr', 'fetch'].includes(request.resourceType())) {
              apiRequests.set(request, { method: request.method(), path: new URL(request.url()).pathname });
            }
          };
          const onRequestFinished = (request) => apiRequests.delete(request);
          const onRequestFailed = (request) => {
            apiRequests.delete(request);
            if (['xhr', 'fetch'].includes(request.resourceType())) {
              requestFailures.push({
                method: request.method(),
                origin: new URL(request.url()).origin,
                path: new URL(request.url()).pathname,
                error: safeMessage(request.failure()?.errorText, state),
              });
            }
          };
          const onResponse = (response) => {
            if (response.status() >= 400) {
              failedResponses.push({
                path: new URL(response.url()).pathname,
                status: response.status(),
                resourceType: response.request().resourceType(),
              });
            }
          };
          page.on('pageerror', onPageError);
          page.on('console', onConsole);
          page.on('request', onRequest);
          page.on('requestfinished', onRequestFinished);
          page.on('requestfailed', onRequestFailed);
          page.on('response', onResponse);
          const result = {
            name,
            locale,
            width,
            routePath,
            errors,
            consoleErrors,
            failedResponses,
            requestFailures,
            failures: [],
          };
          const mutationsBefore = observed.blockedMutations.length;
          const routeErrorsBefore = observed.routeErrors.length;
          try {
            const response = await page.goto(new URL(routePath, baseURL).href, {
              waitUntil: 'domcontentloaded',
              timeout: 180000,
            });
            result.httpStatus = response?.status();
            result.actualPath = new URL(page.url()).pathname;
            if (result.actualPath !== new URL(routePath, baseURL).pathname)
              throw new Error('Unexpected redirect; source authentication or route is unavailable');
            await page.locator('.sidebar').first().waitFor({ state: 'attached', timeout: 90000 });
            await page.waitForTimeout(700);
            const apiDeadline = Date.now() + 5000;
            while (apiRequests.size && Date.now() < apiDeadline) await page.waitForTimeout(100);
            await page.evaluate(() => document.fonts.ready);
            if (locale === 'ar-sy') {
              await page.evaluate(() =>
                Promise.all(
                  [300, 400, 500, 700].map((weight) => document.fonts.load(`${weight} 16px "Hayyakum Allah"`)),
                ),
              );
            }
            await page.waitForTimeout(700);
            result.actualPath = new URL(page.url()).pathname;
            result.geometry = await readGeometry(page);
            const expectedDirection = locale === 'ar-sy' ? 'rtl' : 'ltr';
            if (result.geometry.dir !== expectedDirection) result.failures.push('Unexpected document direction');
            if (locale === 'ar-sy' && result.geometry.arabicCharacters < 10)
              result.failures.push('Arabic interface missing');
            if (locale === 'ar-sy' && !result.geometry.arabicFontLoaded) result.failures.push('Arabic font not loaded');
            if (result.geometry.main && result.geometry.main.width <= 0)
              result.failures.push('Main content has no width');
            if (result.geometry.documentWidth > width + 1) result.failures.push('Document overflows horizontally');
            if (result.actualPath !== new URL(routePath, baseURL).pathname) result.failures.push('Unexpected redirect');
            const info = result.geometry.templateInfo;
            const tasks = result.geometry.templateTasks;
            if (width >= 1000 && info && tasks) {
              const overlap = Math.min(info.right, tasks.right) - Math.max(info.x, tasks.x);
              const verticalOverlap =
                Math.min(info.y + info.height, tasks.y + tasks.height) - Math.max(info.y, tasks.y);
              if (overlap > 1 && verticalOverlap > 1) result.failures.push('Template columns overlap');
              if (expectedDirection === 'rtl' && verticalOverlap > 1 && info.x < tasks.x)
                result.failures.push('Template info column is on the wrong side');
            }
            if (name === 'template-graph-fixture') {
              await page.getByTestId('template-graph-editor').waitFor({ timeout: 15000 });
              result.geometry = await readGeometry(page);
              if (result.geometry.canvas?.direction !== 'ltr')
                result.failures.push('Graph coordinate surface is not LTR');
              const actions = page.getByTestId('graph-task-actions').first();
              await actions.waitFor({ state: 'visible', timeout: 15000 });
              await actions.click();
              const edit = page.getByRole('menuitem', {
                name: locale === 'ar-sy' ? 'تعديل المهمة' : 'Edit task',
                exact: true,
              });
              await edit.waitFor({ state: 'visible', timeout: 15000 });
              await edit.click();
              await page.getByTestId('graph-task-editor').waitFor();
              await page.screenshot({
                path: path.join(outputDir, `${locale}-${width}-graph-panel.png`),
                fullPage: true,
              });
              result.graphPanelOpened = true;
              await page.getByTestId('graph-task-editor-close').click();
            }
          } catch (error) {
            result.failures.push(safeMessage(error.message, state));
          }
          result.blockedMutations = observed.blockedMutations.slice(mutationsBefore);
          result.pendingApiRequests = [...apiRequests.values()];
          result.routeErrors = observed.routeErrors.slice(routeErrorsBefore);
          result.failures.push(...result.routeErrors.map((error) => safeMessage(error, state)));
          if (requestFailures.some((request) => request.error !== 'net::ERR_ABORTED'))
            result.failures.push('API request failed; loaded content coverage is incomplete');
          if (result.pendingApiRequests.length) result.failures.push('API content is still pending');
          if (
            failedResponses.some(
              (response) =>
                ['fetch', 'xhr'].includes(response.resourceType) &&
                !(response.status === 404 && response.path === '/navigation/menu/help-center'),
            )
          )
            result.failures.push('API returned an error response');
          if (
            consoleErrors.some((error) =>
              /TypeError:|Tasks cancelled due to error|timeout of \d+ms exceeded/.test(error),
            )
          )
            result.failures.push('Application runtime logged an error');
          const screenshot = `${locale}-${width}-${name}.png`;
          await page.screenshot({ path: path.join(outputDir, screenshot), fullPage: true }).catch(() => {});
          result.screenshot = screenshot;
          const scrolled = await page
            .evaluate(() => {
              const main = document.querySelector('main');
              const scroller = [...document.querySelectorAll('body *')].find((element) => {
                const style = getComputedStyle(element);
                return (
                  element.contains(main) &&
                  ['auto', 'scroll'].includes(style.overflowY) &&
                  element.scrollHeight > element.clientHeight + 1
                );
              });
              if (!scroller) return false;
              scroller.scrollTop = scroller.scrollHeight;
              return true;
            })
            .catch(() => false);
          if (scrolled) {
            await page.waitForTimeout(100);
            result.scrollScreenshot = `${locale}-${width}-${name}-bottom.png`;
            await page.screenshot({ path: path.join(outputDir, result.scrollScreenshot) }).catch(() => {});
          }
          report.cases.push(result);
          fs.writeFileSync(path.join(outputDir, 'report.json'), JSON.stringify(report, null, 2));
          console.log(
            JSON.stringify({
              name,
              locale,
              width,
              failures: result.failures,
              pageErrors: errors,
              blockedMutations: result.blockedMutations.length,
            }),
          );
          page.off('pageerror', onPageError);
          page.off('console', onConsole);
          page.off('request', onRequest);
          page.off('requestfinished', onRequestFinished);
          page.off('requestfailed', onRequestFailed);
          page.off('response', onResponse);
        }
        await context.close();
      }
    }
  } finally {
    await browser.close();
    report.finishedAt = new Date().toISOString();
    report.limitations = [
      'Language is intercepted for inspection; this does not validate persisted preference changes or server locale selection.',
      'Mutating HTTP requests are blocked; save, submit, notification-read, and other write behavior are not verified.',
      'WebSocket transports are closed locally; realtime delivery is not part of this layout check.',
      'Create/showcase template routes use in-memory source fixtures, not an existing persisted template.',
      'Snapshots are captured for review and are not automatically approved visual baselines.',
    ];
    fs.writeFileSync(path.join(outputDir, 'report.json'), JSON.stringify(report, null, 2));
  }
  if (report.cases.some((item) => item.failures.length || item.errors.length)) process.exitCode = 1;
}

run().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
