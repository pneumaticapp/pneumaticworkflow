/* Anonymous production smoke. No auth state, credentials, form submissions or writes.
   Start the production frontend, then run: node tests/e2e/rtl-public.cjs
   Locale is selected through the browser config only; backend data is never mocked. */
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('@playwright/test');

const frontend = path.resolve(__dirname, '../..');
const baseURL = process.env.RTL_BASE_URL || 'http://localhost:8000';
const backendURL = process.env.RTL_PUBLIC_API_URL || 'http://localhost:8001';
const outputDir = path.resolve(frontend, process.env.RTL_OUTPUT_DIR || 'test-results/rtl-public');
const allowedOrigins = new Set([new URL(baseURL).origin, new URL(backendURL).origin]);
const locales = (process.env.RTL_LOCALES || 'en,ar-sy').split(',');
const widths = (process.env.RTL_WIDTHS || '1280,375').split(',').map(Number);
const defaultRoutes = [
  ['signin', '/auth/signin/', '/auth/signin/'],
  ['forgot-password', '/auth/forgot-password/', '/auth/forgot-password/'],
  ['missing-reset-link', '/auth/reset-password/', '/auth/forgot-password/'],
  ['missing-public-form', '/forms/rtl-nonexistent-fixture', '/forms/rtl-nonexistent-fixture'],
];
const requestedRoutes = process.env.RTL_PUBLIC_ROUTES?.split(',');
const routes = requestedRoutes ? defaultRoutes.filter(([name]) => requestedRoutes.includes(name)) : defaultRoutes;

function safeError(error) {
  return String(error.message || error)
    .split('Call log:')[0]
    .replace(/([?&](?:token|auth_token|access_token)=)[^&\s]+/gi, '$1[redacted]')
    .trim();
}

async function configureContext(context, locale, observed) {
  const lang = locale === 'ar-sy' ? 'ar-SY' : 'en-US';
  const dir = locale === 'ar-sy' ? 'rtl' : 'ltr';
  await context.addInitScript((selectedLocale) => {
    let config;
    Object.defineProperty(window, '__pneumaticConfig', {
      configurable: true,
      get: () => config,
      set: (value) => {
        config = value;
        config.config.featureFlags = { ...config.config.featureFlags, LANGUAGE_CODE: selectedLocale };
      },
    });
  }, locale);
  await context.grantPermissions(['local-network-access'], { origin: new URL(baseURL).origin });
  await context.routeWebSocket('**/*', (socket) => socket.close({ code: 1000, reason: 'Anonymous layout check' }));
  await context.route('**/*', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    try {
      if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method())) {
        observed.blockedWrites.push({ method: request.method(), origin: url.origin, path: url.pathname });
        await route.fulfill({ status: 409, contentType: 'application/json', body: '{"code":"RTL_READ_ONLY_CHECK"}' });
        return;
      }
      if (!allowedOrigins.has(url.origin)) {
        observed.blockedExternal.push({ method: request.method(), origin: url.origin, path: url.pathname });
        await route.abort('blockedbyclient');
        return;
      }
      if (request.isNavigationRequest() && url.origin === new URL(baseURL).origin) {
        const response = await route.fetch({ timeout: 30000 });
        if (response.headers()['content-type']?.includes('text/html')) {
          let html = await response.text();
          const htmlTag = /<html\b[^>]*>/i.exec(html)?.[0] || '';
          observed.serverDocuments.push({
            path: url.pathname,
            lang: /\blang="([^"]*)"/i.exec(htmlTag)?.[1],
            dir: /\bdir="([^"]*)"/i.exec(htmlTag)?.[1],
          });
          // The production server uses its configured default. English is an
          // isolated client selection; Arabic verifies the unmodified SSR tag.
          if (locale === 'en') html = html.replace(/<html\b[^>]*>/i, `<html lang="${lang}" dir="${dir}">`);
          const headers = { ...response.headers() };
          delete headers['content-length'];
          delete headers['content-encoding'];
          await route.fulfill({ response, headers, body: html });
          return;
        }
        await route.fulfill({ response });
        return;
      }
      await route.continue();
    } catch (error) {
      observed.routeErrors.push(safeError(error));
      await route.abort('failed').catch(() => {});
    }
  });
}

async function geometry(page) {
  return page.evaluate(() => {
    const bounds = (element) => {
      if (!element) return null;
      const rect = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      return { x: rect.x, y: rect.y, width: rect.width, height: rect.height, direction: style.direction };
    };
    return {
      lang: document.documentElement.lang,
      dir: document.documentElement.dir,
      title: document.title,
      width: innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      bodyFont: getComputedStyle(document.body).fontFamily,
      form: bounds(document.querySelector('form')),
      heading: bounds(document.querySelector('h1,h2')),
      arabicCharacters: (document.body.innerText.match(/[\u0600-\u06ff]/g) || []).length,
      fontFaces: [...document.fonts]
        .filter((font) => font.family.includes('Hayyakum Allah'))
        .map((font) => ({ weight: font.weight, status: font.status })),
      inputs: [...document.querySelectorAll('input')].map((input) => ({
        name: input.name,
        type: input.type,
        dir: input.dir,
        direction: getComputedStyle(input).direction,
        bounds: bounds(input),
      })),
    };
  });
}

async function run() {
  if (!routes.length || requestedRoutes?.some((name) => !defaultRoutes.some(([known]) => known === name)))
    throw new Error(
      `RTL_PUBLIC_ROUTES must select route names from: ${defaultRoutes.map(([name]) => name).join(', ')}`,
    );
  fs.mkdirSync(outputDir, { recursive: true });
  const report = { baseURL, startedAt: new Date().toISOString(), cases: [], limitations: [] };
  const browser = await chromium.launch({ channel: process.env.RTL_CHANNEL || 'chrome', headless: true });
  try {
    for (const locale of locales) {
      for (const width of widths) {
        for (const [name, routePath, expectedPath] of routes) {
          const observed = { blockedWrites: [], blockedExternal: [], serverDocuments: [], routeErrors: [] };
          const context = await browser.newContext({ viewport: { width, height: 960 } });
          await configureContext(context, locale, observed);
          const page = await context.newPage();
          const result = { name, locale, width, routePath, pageErrors: [], failures: [], observed };
          page.on('pageerror', (error) => result.pageErrors.push(safeError(error)));
          try {
            const response = await page.goto(new URL(routePath, baseURL).href, {
              waitUntil: 'domcontentloaded',
              timeout: 45000,
            });
            result.httpStatus = response?.status();
            if (name === 'missing-public-form') {
              await page
                .getByRole('heading', { name: locale === 'ar-sy' ? 'حدث خطأ' : 'Oh, nooooooo...!', exact: true })
                .waitFor({ timeout: 20000 });
            } else {
              await page.locator('form input[name="email"]').waitFor({ timeout: 20000 });
            }
            if (locale === 'ar-sy') {
              await page.evaluate(() =>
                Promise.all(
                  [300, 400, 500, 700].map((weight) => document.fonts.load(`${weight} 16px "Hayyakum Allah"`)),
                ),
              );
            }
            await page.evaluate(() => document.fonts.ready);
            await page.waitForTimeout(300);
            result.actualPath = new URL(page.url()).pathname;
            result.geometry = await geometry(page);
            if (result.actualPath !== expectedPath) result.failures.push('Unexpected route or missing reset guard');
            const expected = locale === 'ar-sy' ? { lang: 'ar-SY', dir: 'rtl' } : { lang: 'en-US', dir: 'ltr' };
            if (result.geometry.lang !== expected.lang || result.geometry.dir !== expected.dir)
              result.failures.push('Document locale or direction mismatch');
            if (result.geometry.documentWidth > width + 1) result.failures.push('Horizontal document overflow');
            if (name !== 'missing-public-form') {
              const hasArabicTitle = /[\u0600-\u06ff]/.test(result.geometry.title);
              if (hasArabicTitle !== (locale === 'ar-sy')) result.failures.push('Browser title locale mismatch');
              const email = result.geometry.inputs.find((input) => input.name === 'email');
              if (email?.type !== 'email') result.failures.push('Email field is missing its semantic type');
            }
            if (locale === 'ar-sy') {
              if (result.geometry.arabicCharacters < 10) result.failures.push('Arabic interface text missing');
              if (!result.geometry.bodyFont.includes('Hayyakum Allah'))
                result.failures.push('Arabic body font missing');
              const loadedWeights = new Set(
                result.geometry.fontFaces.filter((font) => font.status === 'loaded').map((font) => font.weight),
              );
              if (![300, 400, 500, 700].every((weight) => loadedWeights.has(String(weight))))
                result.failures.push('Arabic font weights did not load');
              if (observed.serverDocuments.some((document) => document.lang !== 'ar-SY' || document.dir !== 'rtl'))
                result.failures.push('Native server Arabic document attributes missing');
            }
            if (result.geometry.inputs.some((input) => input.type === 'email' && input.direction !== 'ltr'))
              result.failures.push('Technical email field is not LTR');
            if (locale === 'en' && result.geometry.bodyFont.includes('Hayyakum Allah'))
              result.failures.push('English body font changed');
          } catch (error) {
            result.failures.push(safeError(error));
          }
          result.failures.push(...observed.routeErrors);
          result.screenshot = `${locale}-${width}-${name}.png`;
          await page.screenshot({ path: path.join(outputDir, result.screenshot), fullPage: true }).catch(() => {});
          report.cases.push(result);
          fs.writeFileSync(path.join(outputDir, 'report.json'), JSON.stringify(report, null, 2));
          console.log(
            JSON.stringify({ name, locale, width, failures: result.failures, pageErrors: result.pageErrors }),
          );
          await context.close();
        }
      }
    }
  } finally {
    await browser.close();
    report.finishedAt = new Date().toISOString();
    report.limitations = [
      'Anonymous render-only checks; no login, password reset request, valid reset link or form submission is exercised.',
      'No auth state is supplied or persisted; the missing public-form URL is deliberately invalid and its real error is used.',
      'English selects the client environment language and initial document tag; Arabic additionally checks native SSR attributes.',
      'External requests, writes and WebSocket connections are blocked; CAPTCHA, OAuth and realtime behavior are excluded.',
      'Screenshots are review captures, not approved visual baselines; only the installed Chrome channel is checked.',
    ];
    fs.writeFileSync(path.join(outputDir, 'report.json'), JSON.stringify(report, null, 2));
  }
  if (report.cases.some((result) => result.failures.length || result.pageErrors.length)) process.exitCode = 1;
}

run().catch((error) => {
  console.error(safeError(error));
  process.exitCode = 1;
});
