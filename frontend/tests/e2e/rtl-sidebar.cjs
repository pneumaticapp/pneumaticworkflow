/* Isolated real Tippy + Popper submenu check: no application server or authentication. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const postcss = require('postcss');
const localByDefault = require('postcss-modules-local-by-default');
const scope = require('postcss-modules-scope');
const { chromium } = require('@playwright/test');

const frontend = path.resolve(__dirname, '../..');
const artifacts = path.join(frontend, 'test-results/rtl-sidebar');
const baselineRef = process.env.RTL_BASELINE_REF;
assert(baselineRef, 'Set RTL_BASELINE_REF to an approved earlier CSS commit (see RTL_README.md)');
require('ts-node').register({ transpileOnly: true, compilerOptions: { module: 'commonjs' } });
const postcssConfig = require(path.join(frontend, 'postcss.config.ts')).default;
const { resolveDirectionalPlacement } = require(path.join(frontend, 'src/public/lang/direction.ts'));
const tooltipSource = fs.readFileSync(path.join(frontend, 'src/public/components/UI/Tooltip/Tooltip.tsx'), 'utf8');
const largeArrow = tooltipSource.match(/const LARGE_ARROW_SVG_STRING = `([\s\S]*?)`;/)?.[1];
assert(largeArrow, 'Use the actual shared Tooltip large SVG arrow');

async function styles(baseline = false) {
  const compiled = [];
  for (const relative of ['UI/Tooltip/Tooltip.css', 'Sidebar/SubMenuItemTooltip.css']) {
    const file = path.join(frontend, 'src/public/components', relative);
    const css = baseline
      ? cp.execFileSync('git', ['show', `${baselineRef}:frontend/src/public/components/${relative}`], {
          cwd: frontend,
          encoding: 'utf8',
        })
      : fs.readFileSync(file, 'utf8');
    const result = await postcss([
      ...postcssConfig({ file }).plugins,
      localByDefault(),
      scope({ generateScopedName: (name) => name }),
    ]).process(css, { from: file });
    compiled.push(result.css);
  }
  return compiled.join('\n');
}

async function mount(page, css, { direction, flipped, top, skid }) {
  const side = (direction === 'ltr') !== flipped ? 'left' : 'right';
  await page.setContent(`<!doctype html><html dir="${direction}" lang="${direction === 'rtl' ? 'ar-SY' : 'en-US'}"><head><meta charset="utf-8"><style>
    html {font-size:10px;--pneumatic-font-sans:Arial,sans-serif;--pneumatic-color-black72:#40403d;--pneumatic-color-beige:#fff;--sidebar-bg-premium:#40403d;--sidebar-color-premium:#fff;}
    body {margin:0;font:15px Arial,sans-serif;}
    nav {position:absolute;top:${top}px;${side}:48px;width:220px;}
    .sub-menu__trigger {height:48px;display:flex;align-items:center;background:#ddd;}
    ${css}
  </style></head><body><nav><div class="tooltip_lg"><div class="sub-menu__trigger" data-sidebar-tooltip-trigger>Sidebar submenu</div></div></nav></body></html>`);
  await page.addScriptTag({ path: path.join(frontend, 'node_modules/@popperjs/core/dist/umd/popper.min.js') });
  await page.addScriptTag({ path: path.join(frontend, 'node_modules/tippy.js/dist/tippy.umd.min.js') });
  await page.evaluate(
    ({ arrow, placement, offset }) => {
      const content = document.createElement('div');
      content.className = 'content sub-menu__inner';
      content.innerHTML = '<ul><li>First submenu item</li><li>Second menu item</li></ul>';
      window.sidebarFixture = window.tippy(document.querySelector('[data-sidebar-tooltip-trigger]'), {
        content,
        arrow,
        placement,
        appendTo: () => document.body,
        interactive: true,
        offset,
        maxWidth: 304,
        duration: 0,
        animation: false,
      });
      // @tippyjs/react puts className on the tippy-box, including for body portals.
      window.sidebarFixture.popper.querySelector('.tippy-box').classList.add('sub-menu', 'plan-premium');
    },
    { arrow: largeArrow, placement: resolveDirectionalPlacement('right', direction), offset: [skid, 8] },
  );
  await page.locator('[data-sidebar-tooltip-trigger]').hover();
  await page.locator('.tippy-box').waitFor({ state: 'visible' });
  await page.evaluate(() => window.sidebarFixture.popperInstance.update());
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}

async function geometry(page) {
  return page.evaluate(() => {
    const rect = (element) => {
      const bounds = element.getBoundingClientRect();
      return { x: bounds.x, y: bounds.y, width: bounds.width, height: bounds.height, right: bounds.right };
    };
    const box = document.querySelector('.tippy-box');
    const wrapper = box.querySelector('.tippy-svg-arrow');
    const svg = wrapper.querySelector('svg');
    const b = rect(box);
    const a = rect(wrapper);
    const s = rect(svg);
    const reference = rect(document.querySelector('[data-sidebar-tooltip-trigger]'));
    const placement = box.dataset.placement;
    return {
      placement,
      bodyPortal: window.sidebarFixture.popper.parentElement === document.body,
      box: b,
      arrow: a,
      svg: s,
      transform: getComputedStyle(svg).transform,
      tipGap: placement.startsWith('left') ? reference.x - s.right : s.x - reference.right,
      baseGap: placement.startsWith('left') ? s.x - b.right : b.x - s.right,
      centerDelta: s.y + s.height / 2 - (reference.y + reference.height / 2),
    };
  });
}

async function close(page) {
  await page.mouse.move(2, 2);
  await page.waitForFunction(() => !window.sidebarFixture.state.isVisible);
  await page.locator('.tippy-box').waitFor({ state: 'hidden' });
  await page.evaluate(() => window.sidebarFixture.destroy());
}

async function main() {
  const [baseline, current] = await Promise.all([styles(true), styles()]);
  fs.mkdirSync(artifacts, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const report = [];
  const near = (actual, expected, message) =>
    assert(Math.abs(actual - expected) < 0.6, `${message}: ${actual} != ${expected}`);
  try {
    const page = await browser.newPage({ viewport: { width: 960, height: 720 } });
    page.setDefaultTimeout(10000);
    // All vendor code, styles and SVGs are read locally. No session or network is used.
    await page.route('**/*', (route) => route.abort());
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    for (const direction of ['ltr', 'rtl']) {
      for (const flipped of [false, true]) {
        for (const top of [8, 320, 640]) {
          for (const skid of [0, 18]) {
            const fixture = { direction, flipped, top, skid };
            await mount(page, baseline, fixture);
            const before = await geometry(page);
            await close(page);
            await mount(page, current, fixture);
            const after = await geometry(page);
            assert.equal(after.bodyPortal, true);
            assert.equal(after.placement.split('-')[0], (direction === 'ltr') !== flipped ? 'right' : 'left');
            near(after.arrow.width, 8, 'Arrow container width');
            near(after.arrow.height, 24, 'Arrow container height');
            near(after.svg.width, 8, 'Rotated SVG width');
            near(after.svg.height, 24, 'Rotated SVG height');
            near(after.tipGap, 0, 'Arrow tip meets the trigger at the eight-pixel offset');
            near(after.baseGap, 0, 'Arrow base meets the popup border');
            near(after.centerDelta, 0, 'Arrow remains centered on its reference');
            assert.equal(
              after.transform,
              after.placement.startsWith('left') ? 'matrix(0, 1, -1, 0, 0, 0)' : 'matrix(0, -1, 1, 0, 0, 0)',
            );
            if (after.placement.startsWith('right'))
              assert.deepEqual(after, before, 'Existing right-side LTR geometry must stay unchanged');
            if (!flipped && top === 320 && skid === 0)
              await page.screenshot({ path: path.join(artifacts, `${direction}.png`) });
            await close(page);
            report.push({ ...fixture, before, after, closed: true });
          }
        }
      }
    }
    assert.deepEqual(errors, [], 'No Tippy/Popper runtime errors');
    fs.writeFileSync(path.join(artifacts, 'report.json'), JSON.stringify({ baselineRef, cases: report }, null, 2));
    console.log(
      JSON.stringify(
        {
          cases: report.length,
          bodyPortal: true,
          arrowPlacementAndClosePassed: true,
          existingRightGeometryPreserved: true,
          artifacts,
        },
        null,
        2,
      ),
    );
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
