/* Standalone editor geometry checks. This does not replace whole-application E2E coverage. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const os = require('node:os');
const postcss = require('postcss');
const localByDefault = require('postcss-modules-local-by-default');
const scope = require('postcss-modules-scope');
const { chromium } = require('@playwright/test');

const frontend = path.resolve(__dirname, '../../../../..');
// Require an explicit approved LTR base; HEAD would silently become a self-comparison after committing.
const baselineRef = process.env.RTL_BASELINE_REF;
assert(
  baselineRef,
  'Set RTL_BASELINE_REF to the approved commit from before the RTL changes (see tests/e2e/RTL_README.md)',
);
require('ts-node').register({ transpileOnly: true, compilerOptions: { module: 'commonjs' } });
const postcssConfig = require(path.join(frontend, 'postcss.config.ts')).default;
const sourceFiles = [
  'components/TemplateEdit/TemplateEdit.css',
  'components/TemplateEdit/InputWithVariables/InputWithVariables.css',
  'components/TemplateEdit/VariableList/VariableList.css',
  'components/RichEditor/nodes/ChecklistItemNode/ChecklistItemNode.css',
  'components/RichEditor/components/LexicalEditorContent/LexicalEditorContent.css',
  'components/TemplateEdit/TemplateGraphEditor/TemplateGraphEditor.css',
  'components/TemplateEdit/TemplateGraphEditor/components/GraphNodeCard/GraphNodeCard.css',
  'components/TemplateEdit/TemplateGraphEditor/components/GraphTaskEditorPanel/GraphTaskEditorPanel.css',
];

async function styles(baseline = false) {
  const compiled = [];
  for (const relative of sourceFiles) {
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
    compiled.push(result.css);
  }
  return compiled.join('\n');
}

const fontDir = path.join(frontend, 'src/public/assets/fonts/hayyakum-allah');
function fonts() {
  return [
    [300, 'Light'],
    [400, 'Regular'],
    [500, 'Medium'],
    [700, 'Bold'],
  ]
    .map(([weight, name]) => {
      const file = path.join(fontDir, `HayyakumAllah-${name}.woff2`);
      return `@font-face {font-family: 'Hayyakum Allah'; font-style: normal; font-weight: ${weight}; src: url(data:font/woff2;base64,${fs.readFileSync(file).toString('base64')}) format('woff2'); font-display: swap;}`;
    })
    .join('\n');
}

function documentHtml(css, direction) {
  const arabic = direction === 'rtl';
  return `<!doctype html><html lang="${arabic ? 'ar-SY' : 'en'}" dir="${direction}"><head><meta charset="utf-8"><style>
    ${fonts()}
    html {font-size: 62.5%; --pneumatic-font-sans: Nunito, Arial, sans-serif; --pneumatic-font-serif: 'Abhaya Libre', serif; --pneumatic-color-white: #fff; --pneumatic-color-black4: #f6f6f6; --pneumatic-color-black16: #dcdcdb; --pneumatic-color-black32: #b9b9b8; --pneumatic-color-black48: #979795; --pneumatic-color-black72: #62625f; --pneumatic-color-black100: #262522; }
    html[dir=rtl] {--pneumatic-font-sans: 'Hayyakum Allah', sans-serif; --pneumatic-font-serif: 'Hayyakum Allah', sans-serif;}
    *, *::before, *::after {box-sizing: border-box;}
    body {margin:0; padding:24px; color:#262522; background:#f6f6f6; font:16px/1.5 var(--pneumatic-font-sans);}
    ${fs.readFileSync(path.join(frontend, 'node_modules/@reactflow/core/dist/style.css'), 'utf8')}
    ${css}
    .fixture-title {font-size:24px; margin:0 0 24px;}
    .fixture-group {margin-block:24px;}
    .fixture-input {position:relative; width:100%; height:104px;}
    .fixture-input [data-testid=rich-editor-contenteditable] {width:100%; height:100%; padding-block:12px; padding-inline-start:16px; border:1px solid #dcdcdb; border-radius:8px; background:white;}
    .fixture-input svg {width:8px;height:8px;}
    .fixture-list {padding:0; list-style:none; margin:0;}
    .fixture-list li {margin-block:12px;}
    .fixture-panel {display:none;}
    .fixture-graph {height:260px;}
  </style></head><body>
    <h1 class="fixture-title">${arabic ? 'فحص تنسيق محرّر القوالب — العربية السورية' : 'Template editor geometry check'}</h1>
    <main class="container">
      <section class="template-wrapper">
        <aside class="template-wrapper__info"><h2>${arabic ? 'معلومات القالب' : 'Template information'}</h2><p>${arabic ? 'نموذج خاص بطلب الموافقة على المخططات.' : 'A template for reviewing submitted plans.'}</p></aside>
        <div class="template-wrapper__tasks">
          <div class="input-with-variables fixture-input"><div contenteditable="true" data-testid="rich-editor-contenteditable">${arabic ? 'اسم الخطوة في سير العمل' : 'Workflow step name'}</div><div class="variables"><button class="button"><span>${arabic ? 'إدراج' : 'Insert'}</span><svg class="button__expand-icon" viewBox="0 0 8 8"><path d="M1 2l3 3 3-3" stroke="currentColor" fill="none"/></svg></button></div></div>
          <ul class="fixture-list fixture-group"><li class="checklist-item" dir="rtl"><div class="checkbox"></div>مراجعة طلب الإسكان وإرفاق الوثائق</li><li class="checklist-item" dir="ltr"><div class="checkbox"></div>Review attachments and approve the request</li></ul>
        </div>
      </section>
      <section class="template-graph-editor fixture-group fixture-graph"><div class="react-flow" dir="ltr"><div class="react-flow__viewport" style="transform:translate(24px,20px)"><div class="react-flow__node react-flow__node-task" style="transform:translate(24px,30px)"><div class="graph-node-card"><div class="react-flow__handle react-flow__handle-left"></div><div class="graph-node-card__header">${arabic ? 'مهمة' : 'Task'}</div><div class="graph-node-card__title">${arabic ? 'مراجعة المخطط' : 'Review the plan'}</div></div></div></div></div></section>
    </main>
    <aside class="graph-task-editor fixture-panel">${arabic ? 'محرّر المهمة' : 'Task editor'}</aside>
  </body></html>`;
}

async function measure(page) {
  return page.evaluate(() => {
    const box = (selector) => {
      const rect = document.querySelector(selector).getBoundingClientRect();
      return {
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height,
        left: rect.left,
        right: rect.right,
        top: rect.top,
        bottom: rect.bottom,
      };
    };
    const checks = Array.from(document.querySelectorAll('.checklist-item')).map((li) => {
      const item = li.getBoundingClientRect();
      const check = li.querySelector('.checkbox').getBoundingClientRect();
      return {
        dir: li.dir,
        itemLeft: item.left,
        itemRight: item.right,
        checkLeft: check.left,
        checkRight: check.right,
      };
    });
    const input = document.querySelector('[data-testid=rich-editor-contenteditable]');
    const inputStyle = getComputedStyle(input);
    return {
      info: box('.template-wrapper__info'),
      tasks: box('.template-wrapper__tasks'),
      input: box('[data-testid=rich-editor-contenteditable]'),
      button: box('.variables'),
      node: box('.react-flow__node'),
      card: box('.graph-node-card'),
      handle: box('.react-flow__handle-left'),
      checks,
      paddingLeft: parseFloat(inputStyle.paddingLeft),
      paddingRight: parseFloat(inputStyle.paddingRight),
      cardDirection: getComputedStyle(document.querySelector('.graph-node-card')).direction,
    };
  });
}

async function nativeMentionChecks(page) {
  const positioner = require(
    path.join(frontend, 'src/public/components/RichEditor/plugins/MentionsPlugin/getPositionRelativeToParent.ts'),
  ).getPositionRelativeToParent;
  let passed = 0;
  for (const direction of ['ltr', 'rtl']) {
    await page.setContent(
      `<html dir="${direction}"><body><div id="host" dir="${direction}" style="position:absolute;left:100px;top:100px;width:400px;height:150px;overflow:auto;border:2px solid"><div style="width:800px;height:300px"><span id="anchor" style="display:inline-block;margin-inline-start:100px;width:40px;height:20px">Mention</span></div><div id="menu" style="position:absolute;width:192px;height:80px"></div></div></body></html>`,
    );
    for (const scroll of [0, 80]) {
      const result = await page.evaluate(
        ({ source, direction, scroll }) => {
          const position = new Function(`return (${source})`)();
          const host = document.querySelector('#host');
          const anchor = document.querySelector('#anchor');
          const menu = document.querySelector('#menu');
          host.scrollLeft = direction === 'rtl' ? -scroll : scroll;
          host.scrollTop = 20;
          const target = anchor.getBoundingClientRect();
          const coordinates = position(menu, target, 4, direction);
          Object.assign(menu.style, { left: `${coordinates.left}px`, top: `${coordinates.top}px` });
          const actual = menu.getBoundingClientRect();
          return {
            horizontalDelta: direction === 'rtl' ? actual.right - target.right : actual.left - target.left,
            verticalDelta: actual.top - target.bottom,
            scrollLeft: host.scrollLeft,
          };
        },
        { source: positioner.toString(), direction, scroll },
      );
      assert.ok(Math.abs(result.horizontalDelta) < 0.6, `${direction} mention anchor after native scrolling`);
      assert.equal(result.verticalDelta, 4);
      assert.equal(result.scrollLeft, direction === 'rtl' && scroll ? -scroll : scroll);
      passed += 1;
    }
  }
  return passed;
}

async function main() {
  const current = await styles();
  const baseline = await styles(true);
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const results = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    for (const width of [390, 768, 999, 1000, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.setContent(documentHtml(baseline, 'ltr'));
      await page.evaluate(() => document.fonts.ready);
      const before = await measure(page);
      for (const direction of ['ltr', 'rtl']) {
        await page.setContent(documentHtml(current, direction));
        await page.evaluate(() => document.fonts.ready);
        const fontWeights = await page.evaluate(async () => {
          const loaded = await Promise.all(
            [300, 400, 500, 700].map((weight) => document.fonts.load(`${weight} 16px "Hayyakum Allah"`, 'مرحبا')),
          );
          return loaded.map((faces) => faces.length > 0 && faces.every((face) => face.status === 'loaded'));
        });
        assert.ok(fontWeights.every(Boolean), 'All four provided Arabic font weights must load');
        const after = await measure(page);
        const close = (a, b, message) =>
          assert.ok(Math.abs(a - b) < 0.6, `${width} ${direction}: ${message}: ${a} vs ${b}`);
        if (direction === 'ltr') {
          for (const field of ['info', 'tasks', 'input', 'button', 'node', 'card', 'handle']) {
            for (const dimension of ['x', 'y', 'width', 'height'])
              close(before[field][dimension], after[field][dimension], `LTR ${field}.${dimension}`);
          }
        }
        if (width >= 1000) {
          close(
            direction === 'rtl' ? after.info.left - after.tasks.right : after.tasks.left - after.info.right,
            64,
            'column gap',
          );
        } else {
          assert.ok(after.tasks.top >= after.info.bottom, 'mobile columns should stack');
        }
        if (direction === 'rtl') {
          close(after.paddingLeft, 60, 'reserved insert padding');
          assert.ok(
            after.button.right <= after.input.left + after.paddingLeft + 0.6,
            `insert must fit inside reserved RTL padding: ${JSON.stringify(after)}`,
          );
          assert.equal(after.cardDirection, 'rtl');
        } else {
          close(after.paddingRight, 60, 'reserved insert padding');
          assert.ok(
            after.button.left >= after.input.left && after.button.right <= after.input.right,
            'LTR insert remains inside the unchanged field',
          );
        }
        for (const item of after.checks)
          close(
            item.dir === 'rtl' ? item.itemRight : item.itemLeft,
            item.dir === 'rtl' ? item.checkRight : item.checkLeft,
            'checklist inline start',
          );
        close(
          after.handle.left - after.card.left,
          before.handle.left - before.card.left,
          'graph handle remains physical',
        );
        await page.locator('.fixture-panel').evaluate((el) => {
          el.style.display = 'block';
        });
        const panel = await page.locator('.fixture-panel').boundingBox();
        close(direction === 'rtl' ? panel.x : width - panel.x - panel.width, 0, 'drawer edge');
        await page.locator('.fixture-panel').evaluate((el) => {
          el.style.display = 'none';
        });
        if (width === 1440 || width === 390) {
          const output = path.join(os.tmpdir(), `pneumatic-editor-rtl-${direction}-${width}.png`);
          await page.screenshot({ path: output, fullPage: true });
          results.push({ width, direction, screenshot: output });
        } else results.push({ width, direction });
      }
    }
    const mentionChecks = await nativeMentionChecks(page);
    console.log(
      JSON.stringify(
        {
          scope: 'isolated actual editor CSS + provided fonts; not full-page E2E',
          baselineRef,
          passed: results.length,
          nativeMentionChecks: mentionChecks,
          results,
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
