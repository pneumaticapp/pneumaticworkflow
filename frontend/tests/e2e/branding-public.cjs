/* Production-client branding fixture. No application services, credentials, cookies,
   authentication flows or real backend are used. All backend GETs below are mocks. */
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const ejs = require('ejs');
const { chromium } = require('@playwright/test');

require('ts-node').register({ transpileOnly: true, compilerOptions: { module: 'commonjs' } });
const { getBrandName, getOrganizationName } = require('../../src/public/constants/branding.ts');
const { getLocaleAttributes, resolveLocale } = require('../../src/public/lang/locale.ts');

const frontend = path.resolve(__dirname, '../..');
const phase = process.env.BRANDING_PHASE || 'after';
if (!['baseline', 'after'].includes(phase)) throw new Error('BRANDING_PHASE must be baseline or after');
const pagesMode = process.env.BRANDING_PAGES || 'populated';
if (!['populated', 'empty'].includes(pagesMode)) throw new Error('BRANDING_PAGES must be populated or empty');
const outputRoot = path.resolve(frontend, process.env.BRANDING_OUTPUT_DIR || 'test-results/branding-public');
const assetsRoot = path.resolve(
  frontend,
  process.env.BRANDING_ASSETS_DIR || (phase === 'baseline' ? 'test-results/branding-public/baseline-assets' : 'public'),
);
const output = path.join(outputRoot, pagesMode === 'empty' ? `${phase}-empty-pages` : phase);
const locales = (process.env.BRANDING_LOCALES || 'en,ar-sy').split(',');
const widths = (process.env.BRANDING_WIDTHS || '1280,375').split(',').map(Number);
const common = JSON.parse(fs.readFileSync(path.join(frontend, 'config/common.json'), 'utf8'));
const templates = Object.fromEntries(
  ['main', 'forms'].map((name) => [name, fs.readFileSync(path.join(assetsRoot, `${name}.ejs`), 'utf8')]),
);
const assetDigest = (filename) => crypto.createHash('sha256').update(fs.readFileSync(filename)).digest('hex');
const sourceWhiteDigest = assetDigest(path.join(frontend, 'src/public/assets/img/branding/logos/eagle-white.svg'));
const routes = [
  ['signin', '/auth/signin/', '/auth/signin/'],
  ['forgot', '/auth/forgot-password/', '/auth/forgot-password/'],
  ['missing-reset-redirect', '/auth/reset-password/', '/auth/forgot-password/'],
  ['missing-public-form', '/forms/branding-unavailable-fixture', '/forms/branding-unavailable-fixture'],
];
const requested = process.env.BRANDING_ROUTES?.split(',');
const selectedRoutes = requested ? routes.filter(([name]) => requested.includes(name)) : routes;
if (!selectedRoutes.length || (requested && selectedRoutes.length !== requested.length))
  throw new Error('Unknown or empty BRANDING_ROUTES');
if (locales.some((locale) => !['en', 'ar-sy'].includes(locale)))
  throw new Error('Only en and ar-sy fixtures are defined');
if (widths.some((width) => !Number.isFinite(width) || width < 320)) throw new Error('Invalid fixture width');

let origin;
let locale = 'en';
let observed;

function pages() {
  if (pagesMode === 'empty') return [];
  // Fixed anonymous Page fixtures exercise the actual information-panel layout.
  // They are deliberately not presented as stored Ministry or application copy.
  const title =
    locale === 'ar-sy' ? '\u0639\u0646\u0648\u0627\u0646 \u062a\u062c\u0631\u064a\u0628\u064a' : 'Fixture headline';
  const description =
    locale === 'ar-sy'
      ? '\u0645\u0639\u0627\u064a\u0646\u0629 \u062a\u062c\u0631\u064a\u0628\u064a\u0629 \u062f\u0648\u0646 \u062a\u0633\u062c\u064a\u0644 \u062f\u062e\u0648\u0644.'
      : 'Anonymous branding layout fixture.';
  return ['signin', 'forgot-password', 'reset-password'].map((slug) => ({ slug, title, description }));
}

function config() {
  return {
    ...common,
    host: origin,
    mainPage: '/',
    formSubdomain: '',
    analyticsId: '',
    recaptchaSecret: '',
    api: {
      urls: common.api.urls,
      publicUrl: `${origin}/api`,
      privateUrl: `${origin}/api`,
      wsPublicUrl: origin.replace('http:', 'ws:'),
      fileServiceUrl: `${origin}/files`,
    },
    firebase: { vapidKey: '', config: {} },
    featureFlags: {
      LANGUAGE_CODE: locale,
      BACKEND_URL: `${origin}/api`,
      WSS_URL: origin.replace('http:', 'ws:'),
      HOST: origin,
      CAPTCHA: 'no',
      GOOGLE_AUTH: 'no',
      MS_AUTH: 'no',
      SSO_AUTH: 'no',
      SIGNUP: 'yes',
      BILLING: 'no',
      AI: 'no',
      PUSH: 'no',
      ANALYTICS: 'no',
      SENTRY_DSN: '',
    },
  };
}

function sendJSON(res, status, body, pathname) {
  observed?.api.push({ pathname, status });
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(body));
}

function serveStatic(res, root, relativePath) {
  const filename = path.resolve(root, `.${relativePath}`);
  if (!filename.startsWith(`${root}${path.sep}`) || !fs.existsSync(filename) || !fs.statSync(filename).isFile()) {
    res.writeHead(404);
    res.end();
    return;
  }
  const contentTypes = {
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.woff2': 'font/woff2',
    '.woff': 'font/woff',
    '.ttf': 'font/ttf',
  };
  res.writeHead(200, { 'Content-Type': contentTypes[path.extname(filename)] || 'application/octet-stream' });
  if (/eagle-(gold|white|black)\.svg$/.test(filename)) {
    observed?.eagleAssets.push({
      path: relativePath,
      sha256: crypto.createHash('sha256').update(fs.readFileSync(filename)).digest('hex'),
    });
  }
  fs.createReadStream(filename).pipe(res);
}

const server = http.createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://fixture.invalid').pathname);
  if (!['GET', 'HEAD', 'OPTIONS'].includes(req.method)) {
    observed?.writes.push({ method: req.method, pathname });
    sendJSON(res, 409, { code: 'FIXTURE_READ_ONLY' }, pathname);
    return;
  }
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }
  if (req.headers.cookie && /(?:^|;\s*)(?:token|sessionid|auth_token)=/i.test(req.headers.cookie)) {
    observed?.cookieFailures.push('Unexpected authentication cookie');
    sendJSON(res, 409, { code: 'FIXTURE_NO_AUTH' }, pathname);
    return;
  }
  if (pathname.startsWith('/static/')) return serveStatic(res, assetsRoot, pathname.slice('/static'.length));
  if (pathname.startsWith('/assets/'))
    return serveStatic(res, path.join(frontend, 'assets'), pathname.slice('/assets'.length));
  if (pathname === '/favicon.ico') {
    res.writeHead(204);
    res.end();
    return;
  }
  if (pathname.startsWith('/api/')) {
    const apiPath = pathname.replace(/^\/api(?:\/api)*/, '');
    if (apiPath === '/pages/public') return sendJSON(res, 200, pages(), pathname);
    if (apiPath === '/accounts/public/users') return sendJSON(res, 200, [], pathname);
    if (apiPath === '/accounts/public/account') return sendJSON(res, 200, {}, pathname);
    if (apiPath === '/auth/context') return sendJSON(res, 401, { code: 'FIXTURE_ANONYMOUS' }, pathname);
    if (apiPath === '/templates/public') return sendJSON(res, 404, { code: 'FIXTURE_FORM_NOT_FOUND' }, pathname);
    observed?.unknownGETs.push(pathname);
    return sendJSON(res, 404, { code: 'FIXTURE_UNMOCKED_GET' }, pathname);
  }
  const name = pathname.startsWith('/forms/') ? 'forms' : 'main';
  const html = ejs.render(templates[name], {
    documentLocale: getLocaleAttributes(resolveLocale(locale)),
    brandName: getBrandName(locale),
    config: JSON.stringify(config()),
    user: '{}',
    invitedUser: '{}',
    pages: JSON.stringify(pages()),
    env: 'local',
    isBuildAnalytics: false,
  });
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(html);
});
server.on('upgrade', (_req, socket) => socket.destroy());

async function geometry(page) {
  return page.evaluate(() => {
    const bounds = (element) => {
      if (!element) return null;
      const { x, y, width, height } = element.getBoundingClientRect();
      return { x, y, width, height };
    };
    const form = document.querySelector('form');
    const inner = form?.closest('[class*="card__inner--"]');
    const card = inner?.parentElement;
    const content = card?.parentElement;
    const shell = content?.parentElement;
    const notification = document.querySelector('[class*="notification--"]');
    const lockup = shell?.firstElementChild.querySelector('svg[class*="brand-lockup--"]');
    const brandCopy = (selector) => {
      const element = lockup?.querySelector(selector);
      if (!element) return null;
      const rect = bounds(element);
      const computed = getComputedStyle(element);
      return {
        text: element.textContent.trim(),
        bounds: rect,
        visible:
          rect.width > 0 &&
          rect.height > 0 &&
          computed.display !== 'none' &&
          computed.visibility === 'visible' &&
          Number(computed.opacity) > 0,
        // Font ink can extend beyond the line box without being clipped. Check
        // horizontal wrapping/clipping separately from that font-metric overhang.
        overflowing: element.scrollWidth > element.clientWidth + 1,
      };
    };
    const style = getComputedStyle(document.documentElement);
    return {
      lang: document.documentElement.lang,
      dir: document.documentElement.dir,
      title: document.title,
      width: innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      bodyFont: getComputedStyle(document.body).fontFamily,
      panels: {
        shell: bounds(shell),
        info: bounds(shell?.firstElementChild),
        content: bounds(content),
        card: bounds(card),
        notification: bounds(notification),
      },
      form: bounds(form),
      heading: bounds(document.querySelector('h1,h2')),
      lockup: lockup
        ? {
            bounds: bounds(lockup),
            linkHref: lockup.closest('a')?.getAttribute('href'),
            product: brandCopy('[class*="brand-copy__product--"]'),
            organization: brandCopy('[class*="brand-copy__organization--"]'),
          }
        : null,
      primary: style.getPropertyValue('--pneumatic-color-link').trim(),
      forest: style.getPropertyValue('--brand-forest-dark').trim(),
      wheat: style.getPropertyValue('--brand-wheat').trim(),
      infoBackground: shell?.firstElementChild ? getComputedStyle(shell.firstElementChild).backgroundColor : null,
      infoColors: shell?.firstElementChild
        ? [...shell.firstElementChild.querySelectorAll('h1,p')].map((element) => ({
            tag: element.tagName,
            color: getComputedStyle(element).color,
          }))
        : [],
      shellBackground: shell ? getComputedStyle(shell).backgroundColor : null,
      buttonBackground: document.querySelector('button[type="submit"]')
        ? getComputedStyle(document.querySelector('button[type="submit"]')).backgroundColor
        : null,
      email: [...document.querySelectorAll('input')]
        .filter((input) => input.name === 'email')
        .map((input) => ({
          type: input.type,
          direction: getComputedStyle(input).direction,
        })),
      images: [...document.querySelectorAll('svg image')].map((image) => ({
        href: image.getAttribute('href'),
        width: image.getBoundingClientRect().width,
        height: image.getBoundingClientRect().height,
        label: image.closest('svg')?.getAttribute('aria-label'),
      })),
      fonts: [...document.fonts]
        .filter((font) => font.family.includes('Hayyakum Allah'))
        .map((font) => ({
          weight: font.weight,
          status: font.status,
        })),
    };
  });
}

async function main() {
  fs.mkdirSync(output, { recursive: true });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  origin = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({ channel: process.env.BRANDING_CHANNEL || 'chrome', headless: true });
  const baselinePath = path.join(outputRoot, 'baseline', 'report.json');
  const baseline =
    phase === 'after' && pagesMode === 'populated' && fs.existsSync(baselinePath)
      ? JSON.parse(fs.readFileSync(baselinePath, 'utf8'))
      : null;
  const report = {
    phase,
    pagesMode,
    assetsRoot,
    startedAt: new Date().toISOString(),
    cases: [],
    templateDigests: Object.fromEntries(
      ['main', 'forms'].map((name) => [name, assetDigest(path.join(assetsRoot, `${name}.ejs`))]),
    ),
    scope:
      'Actual production React client with explicit anonymous backend GET fixtures. No real backend or authentication.',
    comparison: baseline
      ? 'Main layout panel rectangles compared to preserved pre-brand production assets; brand wordmarks/text excluded.'
      : 'No previous baseline comparison.',
  };
  try {
    for (const selectedLocale of locales) {
      locale = selectedLocale;
      for (const width of widths) {
        for (const [name, routePath, expectedPath] of selectedRoutes) {
          observed = { api: [], unknownGETs: [], writes: [], external: [], cookieFailures: [], eagleAssets: [] };
          const result = { name, locale, width, routePath, failures: [], pageErrors: [], observed };
          const context = await browser.newContext({ viewport: { width, height: 900 } });
          await context.grantPermissions(['local-network-access'], { origin });
          await context.routeWebSocket('**/*', (socket) => socket.close({ code: 1000, reason: 'Anonymous fixture' }));
          await context.route('**/*', async (route) => {
            const request = route.request();
            const url = new URL(request.url());
            if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method())) {
              observed.writes.push({ method: request.method(), pathname: url.pathname });
              return route.fulfill({
                status: 409,
                contentType: 'application/json',
                body: '{"code":"FIXTURE_READ_ONLY"}',
              });
            }
            if (url.origin !== origin) {
              observed.external.push({ origin: url.origin, pathname: url.pathname });
              return route.abort('blockedbyclient');
            }
            return route.continue();
          });
          const page = await context.newPage();
          page.on('pageerror', (error) => result.pageErrors.push(error.message));
          try {
            await page.goto(`${origin}${routePath}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
            if (name === 'missing-public-form') await page.locator('h1').waitFor({ timeout: 15000 });
            else await page.locator('form input[name="email"]').waitFor({ timeout: 15000 });
            if (locale === 'ar-sy')
              await page.evaluate(() =>
                Promise.all(
                  [300, 400, 500, 700].map((weight) => document.fonts.load(`${weight} 16px "Hayyakum Allah"`)),
                ),
              );
            await page.evaluate(() => document.fonts.ready);
            await page.waitForTimeout(200);
            result.actualPath = new URL(page.url()).pathname;
            result.geometry = await geometry(page);
            const value = result.geometry;
            if (result.actualPath !== expectedPath) result.failures.push('Unexpected client route/redirect');
            if (
              value.lang !== (locale === 'ar-sy' ? 'ar-SY' : 'en-US') ||
              value.dir !== (locale === 'ar-sy' ? 'rtl' : 'ltr')
            )
              result.failures.push('Locale/direction mismatch');
            if (value.documentWidth > width + 1) result.failures.push('Horizontal document overflow');
            if (value.email.some((input) => input.type !== 'email' || input.direction !== 'ltr'))
              result.failures.push('Email technical direction/type changed');
            if (locale === 'ar-sy') {
              const weights = new Set(
                value.fonts.filter((font) => font.status === 'loaded').map((font) => font.weight),
              );
              if (
                ![300, 400, 500, 700].every((weight) => weights.has(String(weight))) ||
                !value.bodyFont.includes('Hayyakum Allah')
              )
                result.failures.push('Arabic font faces/body family missing');
            }
            const cookies = await context.cookies();
            if (cookies.some((cookie) => /^(token|sessionid|auth_token|access_token)$/i.test(cookie.name)))
              result.failures.push('Authentication cookie created');
            if (phase === 'after') {
              if (!value.title.endsWith(getBrandName(locale))) result.failures.push('Display title brand mismatch');
              if (value.forest.toLowerCase() !== '#054239' || value.wheat.toLowerCase() !== '#b9a779')
                result.failures.push('Approved palette tokens missing');
              if (name !== 'missing-public-form') {
                if (value.shellBackground !== 'rgb(5, 66, 57)' || value.buttonBackground !== 'rgb(5, 66, 57)')
                  result.failures.push('Primary visible color mismatch');
                if (
                  pagesMode === 'populated' &&
                  (value.infoColors.length !== 2 ||
                    value.infoColors.some((element) => element.color !== 'rgb(255, 255, 255)'))
                )
                  result.failures.push('Populated info-panel heading/description contrast color missing');
                if (pagesMode === 'empty' && value.infoColors.length)
                  result.failures.push('Empty-Pages preview contains fixture headline/description');
                const white = value.images.find((image) => image.href?.endsWith('eagle-white.svg'));
                if (
                  !white ||
                  white.width <= 0 ||
                  !white.label?.includes(getBrandName(locale)) ||
                  !white.label.includes(getOrganizationName(locale))
                )
                  result.failures.push('Canonical brand/eagle image missing');
                const whiteAssets = observed.eagleAssets.filter((asset) => asset.path.endsWith('eagle-white.svg'));
                if (!whiteAssets.length) result.failures.push('White eagle asset was not served');
                if (whiteAssets.some((asset) => asset.sha256 !== sourceWhiteDigest))
                  result.failures.push('Served white eagle differs from supplied source asset');
                if (
                  !value.lockup?.product?.visible ||
                  value.lockup.product.text !== getBrandName(locale) ||
                  !value.lockup?.organization?.visible ||
                  value.lockup.organization.text !== getOrganizationName(locale)
                )
                  result.failures.push('Visible product/full Ministry DOM text missing from lockup');
                if (value.lockup?.product?.overflowing || value.lockup?.organization?.overflowing)
                  result.failures.push('Visible lockup text overflows');
                const expectedLogo =
                  pagesMode === 'populated' ? { width: 170, height: 40 } : { width: 210, height: 60 };
                if (
                  !value.lockup ||
                  Math.abs(value.lockup.bounds.width - expectedLogo.width) > 0.01 ||
                  Math.abs(value.lockup.bounds.height - expectedLogo.height) > 0.01
                )
                  result.failures.push('Brand lockup footprint changed');
                if (pagesMode === 'populated' && value.lockup?.linkHref !== '/')
                  result.failures.push('Populated brand lockup must link to internal home');
              }
              const previous = baseline?.cases.find(
                (entry) => entry.name === name && entry.locale === locale && entry.width === width,
              );
              if (previous?.geometry && !previous.failures.length && !previous.pageErrors.length) {
                result.geometryComparison = [];
                for (const [panel, before] of Object.entries(previous.geometry.panels)) {
                  const after = value.panels[panel];
                  if (!before) continue;
                  if (!after) {
                    result.failures.push(`Main layout ${panel} disappeared`);
                    continue;
                  }
                  for (const property of ['x', 'y', 'width', 'height']) {
                    const delta = Math.abs(after[property] - before[property]);
                    result.geometryComparison.push({ panel, property, delta });
                    if (delta > 0.75) result.failures.push(`Main layout ${panel}.${property} changed by ${delta}px`);
                  }
                }
              } else if (baseline) result.failures.push('Valid matching baseline case unavailable');
            }
            if (observed.unknownGETs.length || observed.writes.length || observed.cookieFailures.length)
              result.failures.push('Unexpected backend dependency/write/auth cookie');
          } catch (error) {
            result.failures.push(
              String(error.message || error)
                .split('Call log:')[0]
                .trim(),
            );
          }
          result.screenshot = `${locale}-${width}-${name}.png`;
          await page.screenshot({ path: path.join(output, result.screenshot), fullPage: true }).catch(() => {});
          report.cases.push(result);
          fs.writeFileSync(path.join(output, 'report.json'), JSON.stringify(report, null, 2));
          console.log(
            JSON.stringify({ phase, name, locale, width, failures: result.failures, pageErrors: result.pageErrors }),
          );
          await context.close();
        }
      }
    }
  } finally {
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
    report.finishedAt = new Date().toISOString();
    report.counts = {
      total: report.cases.length,
      passed: report.cases.filter((entry) => !entry.failures.length && !entry.pageErrors.length).length,
      failed: report.cases.filter((entry) => entry.failures.length || entry.pageErrors.length).length,
    };
    report.limitations = [
      'Fixture backend GETs are mocks, including the deliberate public-form404; this does not verify real API/auth/integration behavior.',
      'No credentials, authentication storageState, real backend requests or application-service start/restart are used.',
      'No sign-in, reset request, valid reset link or public-form submission is performed. Mutations409, external requests and WebSockets are blocked.',
      'Only installed Chrome and the specified anonymous routes/locales/sizes are covered. English external font downloads are blocked in both phases.',
      'Panel rectangle comparisons exclude brand-wordmark/text bounds and are not approved screenshot pixel baselines.',
    ];
    fs.writeFileSync(path.join(output, 'report.json'), JSON.stringify(report, null, 2));
  }
  if (report.cases.some((entry) => entry.failures.length || entry.pageErrors.length)) process.exitCode = 1;
}

main().catch((error) => {
  console.error(String(error.message || error));
  server.close();
  process.exitCode = 1;
});
