/* Isolated vendor-direction regression: no application server, auth, or API access. */
const assert = require('assert/strict');
const fs = require('fs');
const path = require('path');
const sass = require('sass');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const Switch = require('rc-switch').default;
const { chromium } = require('@playwright/test');

const root = path.resolve(__dirname, '../..');
const artifacts = path.join(root, 'test-results', 'rtl-legacy');
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), 'utf8');
const close = (actual, expected, message) =>
  assert(Math.abs(actual - expected) < 0.1, `${message}: ${actual} != ${expected}`);

const theme = sass.compile(path.join(root, 'src/public/assets/css/sass/themes/gogo.light.yellow.scss'), {
  logger: { warn() {}, debug() {} },
}).css;
const baseCSS = [
  read('src/public/assets/css/vendor/bootstrap.min.css'),
  read('node_modules/rc-switch/assets/index.css'),
  theme,
].join('\n');
const legacyCSS = read('src/public/assets/css/legacy-direction.css');
const settleAnimations = (page) =>
  page.evaluate(async () => {
    await Promise.all(
      document
        .getAnimations()
        .filter((animation) => animation.effect?.getTiming().iterations !== Infinity)
        .map((animation) => animation.finished.catch(() => {})),
    );
  });
const variants = ['large', 'small'].flatMap((size) =>
  [false, true].flatMap((disabled) =>
    [false, true].map((checked) => ({
      size,
      disabled,
      checked,
      id: `${size}-${disabled ? 'disabled' : 'enabled'}-${checked ? 'on' : 'off'}`,
    })),
  ),
);

const markup = variants
  .map(
    ({ id, size, checked, disabled }) => `<section class="case">
  <span>${id}</span>${renderToStaticMarkup(
    React.createElement(Switch, {
      id,
      checked,
      disabled,
      className: `custom-switch custom-switch-primary${size === 'small' ? ' custom-switch-small' : ''}`,
    }),
  )}</section>`,
  )
  .join('');

async function geometry(page) {
  return page.evaluate(() => {
    const px = (value) => Number.parseFloat(value) || 0;
    const switches = Array.from(document.querySelectorAll('button.rc-switch')).map((element) => {
      const button = getComputedStyle(element);
      const thumb = getComputedStyle(element, '::after');
      const width = element.getBoundingClientRect().width;
      const thumbWidth = px(thumb.width);
      const left =
        thumb.left === 'auto'
          ? width - px(button.borderRightWidth) - px(thumb.right) - px(thumb.marginRight) - thumbWidth
          : px(button.borderLeftWidth) + px(thumb.left) + px(thumb.marginLeft);
      return {
        id: element.id,
        width,
        height: element.getBoundingClientRect().height,
        thumbLeft: left,
        thumbWidth,
        thumbHeight: px(thumb.height),
        background: button.backgroundColor,
        disabled: element.disabled,
        checked: element.getAttribute('aria-checked'),
        left: thumb.left,
        right: thumb.right,
        marginLeft: thumb.marginLeft,
        marginRight: thumb.marginRight,
      };
    });
    const row = document.getElementById('flex-row').getBoundingClientRect();
    const first = document.getElementById('flex-first').getBoundingClientRect();
    const last = document.getElementById('flex-last').getBoundingClientRect();
    return {
      switches,
      flex: { width: row.width, first: first.x - row.x, last: last.x - row.x, lastWidth: last.width },
    };
  });
}

async function main() {
  fs.mkdirSync(artifacts, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const report = {};
  try {
    for (const direction of ['ltr', 'rtl']) {
      const context = await browser.newContext({ viewport: { width: 960, height: 720 } });
      // This fixture needs only locally read CSS; deny every network request.
      await context.route('**/*', (route) => route.abort());
      const page = await context.newPage();
      await page.setContent(`<!doctype html><html lang="${direction === 'rtl' ? 'ar-SY' : 'en-US'}" dir="${direction}">
        <head><meta charset="utf-8"></head><body><main>
        <h1>Legacy widgets: ${direction}</h1><div class="cases">${markup}</div>
        <div id="flex-row"><span id="flex-first">First</span><span id="flex-last" class="ml-auto">Last</span></div>
        </main></body></html>`);
      await page.addStyleTag({ content: baseCSS });
      await page.addStyleTag({
        content: `
        body { margin: 0; background: #f6f6f6; font-family: sans-serif; }
        main { padding: 24px; } h1 { font-size: 24px; margin: 0 0 24px; }
        .cases { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
        .case { display: flex; align-items: center; justify-content: space-between; padding: 16px; background: white; }
        #flex-row { display: flex; width: 300px; margin-top: 24px; background: white; }
        #flex-row span { display: block; width: 60px; height: 40px; background: #fec336; }
      `,
      });
      await settleAnimations(page);
      const baseline = await geometry(page);
      await page.addStyleTag({ content: legacyCSS });
      await settleAnimations(page);
      const corrected = await geometry(page);
      report[direction] = { baseline, corrected };
      if (direction === 'ltr')
        assert.deepEqual(corrected, baseline, 'English geometry and widget state must remain unchanged');
      await page.screenshot({ path: path.join(artifacts, `${direction}.png`), animations: 'disabled' });
      report[direction].toggleMotion = await page.evaluate(() => {
        return ['large-enabled-off', 'small-enabled-off'].map((id) => {
          const element = document.getElementById(id);
          element.classList.add('rc-switch-checked');
          element.setAttribute('aria-checked', 'true');
          const transition = getComputedStyle(element, '::after').transitionProperty;
          return {
            id,
            transition,
            activeProperties: document
              .getAnimations()
              .filter(
                (animation) => animation.effect?.target === element && animation.effect?.pseudoElement === '::after',
              )
              .map((animation) => animation.transitionProperty),
          };
        });
      });
      await context.close();
    }

    const english = report.ltr.corrected;
    const arabic = report.rtl.corrected;
    for (const ltr of english.switches) {
      const rtl = arabic.switches.find(({ id }) => id === ltr.id);
      close(rtl.width, ltr.width, `${ltr.id} width`);
      close(rtl.height, ltr.height, `${ltr.id} height`);
      close(rtl.thumbWidth, ltr.thumbWidth, `${ltr.id} thumb width`);
      close(rtl.thumbHeight, ltr.thumbHeight, `${ltr.id} thumb height`);
      close(rtl.thumbLeft + ltr.thumbLeft, ltr.width - ltr.thumbWidth, `${ltr.id} mirrors the thumb`);
      assert.equal(rtl.checked, ltr.checked, `${ltr.id} checked state`);
      assert.equal(rtl.disabled, ltr.disabled, `${ltr.id} disabled state`);
      assert.equal(rtl.background, ltr.background, `${ltr.id} theme color`);
    }
    close(english.flex.first, 0, 'English first item stays at start');
    close(english.flex.last, english.flex.width - english.flex.lastWidth, 'English ml-auto item at end');
    close(arabic.flex.first, arabic.flex.width - 60, 'Arabic first item stays at start');
    close(arabic.flex.last, 0, 'Arabic ml-auto item at end');
    fs.writeFileSync(path.join(artifacts, 'report.json'), JSON.stringify(report, null, 2));
    for (const direction of ['ltr', 'rtl']) {
      for (const motion of report[direction].toggleMotion) {
        const property = direction === 'rtl' ? 'right' : 'left';
        assert.equal(motion.transition, property, `${direction} ${motion.id} preserves directional animation`);
        assert(motion.activeProperties.includes(property), `${direction} ${motion.id} animates its thumb`);
      }
    }
    console.log(
      JSON.stringify({
        result: 'passed',
        switches: english.switches.length * 2,
        directions: ['ltr', 'rtl'],
        englishUnchanged: true,
        artifacts,
      }),
    );
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
