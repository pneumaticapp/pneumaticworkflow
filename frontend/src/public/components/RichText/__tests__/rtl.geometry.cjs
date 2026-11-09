/* Real Chrome checks of the rendered Markdown, separate from whole-application E2E. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const os = require('node:os');
const postcss = require('postcss');
const localByDefault = require('postcss-modules-local-by-default');
const scope = require('postcss-modules-scope');
const { JSDOM } = require('jsdom');
const { chromium } = require('@playwright/test');

const frontend = path.resolve(__dirname, '../../../../..');
// Require an explicit approved LTR base; HEAD would silently become a self-comparison after committing.
const baselineRef = process.env.RTL_BASELINE_REF;
assert(
  baselineRef,
  'Set RTL_BASELINE_REF to the approved commit from before the RTL changes (see tests/e2e/RTL_README.md)',
);
const dom = new JSDOM('', { url: 'http://localhost', pretendToBeVisual: true });
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

// Keep CSS module names stable in the fixture; CSS itself is compiled with the real pipeline below.
for (const extension of ['.css', '.scss']) {
  require.extensions[extension] = (module) => {
    module.exports = { __esModule: true, default: new Proxy({}, { get: (object, key) => String(key) }) };
  };
}
for (const extension of ['.svg', '.png', '.jpg']) {
  require.extensions[extension] = (module, filename) => {
    module.exports = filename;
  };
}
require('ts-node').register({ transpileOnly: true, compilerOptions: { module: 'commonjs' } });

const { createRichTextMarkdownIt } = require('../utils/createRichTextMarkdownIt');
const { prepareRichTextHtml } = require('../utils/prepareRichTextHtml');
const { sanitizeRichTextHtml } = require('../utils/sanitizeRichTextHtml');
const postcssConfig = require(path.join(frontend, 'postcss.config.ts')).default;

const options = {
  embedVideos: false,
  interactiveChecklists: false,
  checkboxPlaceholderClassName: 'checklist__inactive-placeholder',
  videoClassName: 'video',
  videoContainerClassName: 'video__container',
  mentionClassName: 'mention',
  badgeClassName: 'badge',
  specificityBadgeClassName: 'specifity',
  variables: [
    { apiName: 'applicant', title: 'اسم مقدم الطلب', type: 'string' },
    { apiName: 'reference', title: 'Request ID', type: 'string' },
  ],
  formatMessage: ({ id }) => id,
};
const renderer = createRichTextMarkdownIt(options);
const markdown = [
  '# تفاصيل طلب الإسكان',
  '',
  'مراجعة [سامر عجاج|42] و[English User|7] و{{applicant}} و{{reference}} عبر [تفاصيل الطلب](https://example.com/request).',
  '',
  'Review [English User|7], [سامر عجاج|42] and {{applicant}} at https://example.com/a?b=1&c=2 before `request_id=42`.',
  '',
  '[مراجعة الطلب](https://example.com/only-arabic-link)',
  '',
  '[سامر عجاج|42]',
  '',
  '{{applicant}}',
  '',
  '- مراجعة الوثائق',
  '- Review the supporting documents',
  '  - إرسال الإشعار',
  '  - Check the uploaded file',
  '',
  '1. Review the request',
  '2. إرسال الموافقة',
  '',
  '- مراجعة الطلب',
  '',
  '  Review supporting documents',
  '',
  '- Approve the request',
  '',
  '  إرسال الإشعار',
  '',
  '- ### تفاصيل المرفقات',
  '',
  '  Review the attachments',
  '',
  '- > إرسال الإشعار',
  '',
  '[clist:review|ar-item]مراجعة طلب الإسكان[/clist]',
  '[clist:review|en-item]Review the housing request[/clist]',
  '',
  '```js',
  'const request_id = "SY-42";',
  '```',
].join('\n');

function render(text) {
  return sanitizeRichTextHtml(renderer.render(prepareRichTextHtml(text, { ...options, replaceInlineTokens: false })));
}

async function compileStyles(baseline = false) {
  const results = [];
  for (const relative of ['components/RichText/RichText.css', 'utils/badge/Badge.css']) {
    const file = path.join(frontend, 'src/public', relative);
    const css = baseline
      ? cp.execFileSync('git', ['show', `${baselineRef}:frontend/src/public/${relative}`], {
          cwd: frontend,
          encoding: 'utf8',
        })
      : fs.readFileSync(file, 'utf8');
    const result = await postcss([
      ...postcssConfig({ file }).plugins,
      localByDefault(),
      scope({ generateScopedName: (name) => name }),
    ]).process(css, { from: file });
    results.push(result.css);
  }
  return results.join('\n');
}

function documentHtml(css, direction, html, arabicFont = true) {
  const fontFile = path.join(frontend, 'src/public/assets/fonts/hayyakum-allah/HayyakumAllah-Regular.woff2');
  const font = fs.readFileSync(fontFile).toString('base64');
  return `<!doctype html><html dir="${direction}" lang="${direction === 'rtl' ? 'ar-SY' : 'en'}"><meta charset="utf-8"><style>
    @font-face {font-family:'Hayyakum Allah';font-style:normal;font-weight:400;src:url(data:font/woff2;base64,${font}) format('woff2');}
    html {font-size:62.5%;--pneumatic-font-sans:${arabicFont ? "'Hayyakum Allah'" : 'Arial'},sans-serif;--pneumatic-color-black16:#ddd;--pneumatic-color-black72:#555;--pneumatic-color-link-dark:#147;}
    *,*::before,*::after {box-sizing:border-box;}
    /* Bootstrap's physical body alignment must not leak into mixed-content paragraphs. */
    body {margin:0;padding:24px;text-align:left;background:#f6f6f6;font:16px/1.7 var(--pneumatic-font-sans);}
    article {padding:24px;max-width:900px;margin-inline:auto;background:white;border:1px solid #ddd;border-radius:16px;}
    ${css}
  </style><article class="markdown-content">${html}</article></html>`;
}

async function verifyMixedContent(page, direction) {
  return page.evaluate((uiDirection) => {
    const article = document.querySelector('article');
    const directionOf = (element) => getComputedStyle(element).direction;
    const box = (element) => element.getBoundingClientRect();
    const contains = (outer, inner) => inner.left >= outer.left - 0.6 && inner.right <= outer.right + 0.6;
    const firstText = (element) => {
      const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
      let text;
      while ((text = walker.nextNode())) {
        if (text.textContent.trim()) {
          const range = document.createRange();
          range.selectNodeContents(text);
          return range.getBoundingClientRect();
        }
      }
      return box(element);
    };
    const paragraphs = Array.from(article.querySelectorAll(':scope > p'));
    const proseGeometry = paragraphs.map((paragraph) => {
      const range = document.createRange();
      range.selectNodeContents(paragraph);
      const text = range.getBoundingClientRect();
      const bounds = box(paragraph);
      return {
        direction: directionOf(paragraph),
        alignedToStart:
          directionOf(paragraph) === 'rtl'
            ? Math.abs(text.right - bounds.right) < 1
            : Math.abs(text.left - bounds.left) < 1,
      };
    });
    const lists = Array.from(article.querySelectorAll('li'));
    const checks = Array.from(article.querySelectorAll('.checklist__item'));
    const listGeometry = lists.map((item) => {
      const outer = box(item.parentElement);
      const itemBox = box(item);
      const style = getComputedStyle(item);
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      context.font = `bold ${style.fontSize} ${style.fontFamily}`;
      const markerWidth = context.measureText(item.parentElement.tagName === 'OL' ? '2. ' : '• ').width;
      const markerFits =
        directionOf(item) === 'rtl'
          ? itemBox.right + markerWidth <= outer.right + 0.6
          : itemBox.left - markerWidth >= outer.left - 0.6;
      return {
        text: item.textContent.trim().slice(0, 35),
        direction: directionOf(item),
        markerFits,
        textFits: contains(outer, firstText(item)),
      };
    });
    const checkGeometry = checks.map((item) => {
      const checkbox = item.querySelector('.checklist__inactive-placeholder');
      const content = item.querySelector('.checklist__content');
      return {
        direction: directionOf(item),
        contained: contains(box(article), box(item)),
        checkboxOnStart:
          directionOf(item) === 'rtl'
            ? box(checkbox).left >= box(content).right - 0.6
            : box(checkbox).right <= box(content).left + 0.6,
      };
    });
    const namedLink = article.querySelector('[href="https://example.com/only-arabic-link"]');
    const url = article.querySelector('[href="https://example.com/a?b=1&c=2"]');
    const mentionOrdering = Array.from(article.querySelectorAll('.mention')).map((mention) => {
      const character = (index) => {
        const range = document.createRange();
        range.setStart(mention.firstChild, index);
        range.setEnd(mention.firstChild, index + 1);
        return range.getBoundingClientRect();
      };
      return {
        text: mention.textContent,
        prefixOnStart: mention.textContent.includes('English')
          ? character(0).right <= character(1).left + 0.6
          : character(0).left >= character(1).right - 0.6,
      };
    });
    return {
      ui: directionOf(article),
      expectedUi: uiDirection,
      paragraphDirections: paragraphs.map(directionOf),
      proseGeometry,
      headingDirection: directionOf(article.querySelector('h1')),
      listGeometry,
      checkGeometry,
      namedLinkParentDirection: directionOf(namedLink.closest('p')),
      mentionOrdering,
      urlDirection: directionOf(url),
      codeDirections: Array.from(article.querySelectorAll('pre,code')).map(directionOf),
      scrollOverflow: document.documentElement.scrollWidth - innerWidth,
    };
  }, direction);
}

async function measureEnglish(page) {
  return page.evaluate(() =>
    Array.from(document.querySelectorAll('article, h2, p, ul, ol, li, a, code, .checklist__item')).map((element) => {
      const rect = element.getBoundingClientRect();
      return [element.tagName, rect.x, rect.y, rect.width, rect.height];
    }),
  );
}

async function main() {
  const [css, baselineCss] = await Promise.all([compileStyles(), compileStyles(true)]);
  const html = render(markdown);
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const page = await browser.newPage();
    for (const width of [390, 768, 1440]) {
      for (const direction of ['ltr', 'rtl']) {
        await page.setViewportSize({ width, height: 1500 });
        await page.setContent(documentHtml(css, direction, html));
        await page.evaluate(() => document.fonts.ready);
        const result = await verifyMixedContent(page, direction);
        assert.equal(result.ui, direction);
        assert.equal(result.headingDirection, 'rtl');
        assert.deepEqual(result.paragraphDirections.slice(0, 5), ['rtl', 'ltr', 'rtl', 'rtl', 'rtl']);
        assert.equal(result.namedLinkParentDirection, 'rtl');
        assert(
          result.mentionOrdering.every((mention) => mention.prefixOnStart),
          JSON.stringify(result.mentionOrdering),
        );
        assert(
          result.proseGeometry.every((paragraph) => paragraph.alignedToStart),
          JSON.stringify(result.proseGeometry),
        );
        assert.equal(result.urlDirection, 'ltr');
        assert(result.codeDirections.every((value) => value === 'ltr'));
        assert.deepEqual(
          result.listGeometry.map((item) => item.direction),
          ['rtl', 'ltr', 'rtl', 'ltr', 'ltr', 'rtl', 'rtl', 'ltr', 'rtl', 'rtl'],
        );
        assert(
          result.listGeometry.every((item) => item.markerFits && item.textFits),
          JSON.stringify(result.listGeometry),
        );
        assert.deepEqual(
          result.checkGeometry.map((item) => item.direction),
          ['rtl', 'ltr'],
        );
        assert(
          result.checkGeometry.every((item) => item.contained && item.checkboxOnStart),
          JSON.stringify(result.checkGeometry),
        );
        assert(result.scrollOverflow <= 1, `Horizontal overflow at ${width}/${direction}`);
        if (direction === 'rtl' && [390, 1440].includes(width)) {
          await page.screenshot({
            path: path.join(os.tmpdir(), `pneumatic-rich-text-${direction}-${width}.png`),
            fullPage: true,
          });
        }
      }
    }

    const englishMarkdown =
      '## Review the request\n\nPlease [open the request](https://example.com/request) and check `request_id=42`.\n\n- Review the documents\n- Approve the request\n\n1. Notify the applicant\n2. Close the request\n\n[clist:review|item]Review the housing request[/clist]';
    const englishHtml = render(englishMarkdown);
    // Remove only renderer-generated direction attributes to model the prior English markup.
    const baselineHtml = englishHtml.replace(/ dir="(?:auto|ltr)"/g, '');
    await page.setViewportSize({ width: 1440, height: 1200 });
    await page.setContent(documentHtml(baselineCss, 'ltr', baselineHtml, false));
    const before = await measureEnglish(page);
    await page.setContent(documentHtml(css, 'ltr', englishHtml, false));
    const after = await measureEnglish(page);
    assert.deepEqual(after, before, 'Existing English LTR geometry changed');
    console.log(
      JSON.stringify(
        {
          mixedContentCases: 6,
          englishGeometryPreserved: true,
          screenshots: [390, 1440].map((width) => path.join(os.tmpdir(), `pneumatic-rich-text-rtl-${width}.png`)),
        },
        null,
        2,
      ),
    );
  } finally {
    await browser.close();
    dom.window.close();
  }
}

main().then(
  () => process.exit(0),
  (error) => {
    console.error(error);
    process.exit(1);
  },
);
