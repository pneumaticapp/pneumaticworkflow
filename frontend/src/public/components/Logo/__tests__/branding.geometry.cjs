/* Actual React logos + supplied artwork/font; no server, authentication or session state. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const ts = require('typescript');
const postcss = require('postcss');
const localByDefault = require('postcss-modules-local-by-default');
const scope = require('postcss-modules-scope');
const { chromium } = require('@playwright/test');

const frontend = path.resolve(__dirname, '../../../../..');
const workspace = path.dirname(frontend);
const artifacts = path.join(frontend, 'test-results/branding-logos');
const assets = path.join(frontend, 'src/public/assets');
require('ts-node').register({ transpileOnly: true, compilerOptions: { module: 'commonjs' } });
const postcssConfig = require(path.join(frontend, 'postcss.config.ts')).default;
const hash = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const luminance = (color) =>
  color
    .match(/[\d.]+/g)
    .slice(0, 3)
    .map((value) => {
      const channel = Number(value) / 255;
      return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
    })
    .reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0);
const contrast = (foreground, background) => {
  const levels = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  return (levels[0] + 0.05) / (levels[1] + 0.05);
};
for (const color of ['gold', 'white', 'black']) {
  assert.equal(
    hash(path.join(assets, `img/branding/logos/eagle-${color}.svg`)),
    hash(path.join(workspace, `docs/branding/source/Logos/SVG/Syrian_logo_icon_${color}.svg`)),
    'The approved official artwork must remain unchanged',
  );
}
assert.equal(
  hash(path.join(assets, 'img/branding/flags/syrian-flag.svg')),
  hash(path.join(workspace, 'docs/branding/source/flags/syrian-flag-proportions.svg')),
  'The supplied flag must remain unchanged',
);
assert(!fs.readdirSync(path.join(assets, 'img/branding/logos')).some((name) => name.startsWith('._')));

async function bundle() {
  // Compile actual source modules with the project's TypeScript/CSS pipeline. Vendor
  // UMD builds below supply real React, ReactDOM, react-intl and classnames in Chrome.
  const modules = new Map();
  const external = new Set(['react', 'react-dom', 'react-intl', 'classnames']);
  async function collect(file, suppliedSource) {
    const id = path.relative(frontend, file).replace(/\\/g, '/');
    if (modules.has(id)) return id;
    modules.set(id, '');
    // Narrow barrel imports to the actual components used by UserLayout. History
    // contributes only the fixture route; no application store/router is started.
    if (id === 'src/public/components/UI/index.ts') {
      const header = await collect(path.join(frontend, 'src/public/components/UI/Typeography/Header/Header.tsx'));
      modules.set(id, `module.exports={Header:require(${JSON.stringify(header)}).Header};`);
    } else if (id === 'src/public/components/icons/index.ts') {
      const entries = [];
      for (const name of ['LogoCircle', 'LogoWide', 'UserIcon']) {
        const component = await collect(path.join(frontend, `src/public/components/icons/${name}.tsx`));
        entries.push(`${name}:require(${JSON.stringify(component)}).${name}`);
      }
      modules.set(id, `module.exports={${entries.join(',')}};`);
    } else if (id === 'src/public/utils/history.ts') {
      const routes = await collect(path.join(frontend, 'src/public/constants/routes.ts'));
      modules.set(
        id,
        `module.exports={history:{location:{pathname:require(${JSON.stringify(routes)}).ERoutes.Login}}};`,
      );
    } else if (file.endsWith('.svg')) {
      modules.set(
        id,
        `module.exports={__esModule:true,default:${JSON.stringify(`data:image/svg+xml;base64,${fs.readFileSync(file).toString('base64')}`)}};`,
      );
    } else if (file.endsWith('.css')) {
      // Webpack runs PostCSS before css-loader's module export pass.
      const flattened = await postcss(postcssConfig({ file }).plugins).process(fs.readFileSync(file, 'utf8'), {
        from: file,
      });
      const result = await postcss([localByDefault(), scope({ generateScopedName: (name) => name })]).process(
        flattened.css,
        { from: file },
      );
      const names = {};
      result.root.walkRules(':export', (rule) => {
        rule.walkDecls(({ prop, value }) => {
          names[prop] = value;
        });
        rule.remove();
      });
      modules.set(
        id,
        `const style=document.createElement('style');style.textContent=${JSON.stringify(result.root.toString())};document.head.appendChild(style);module.exports={__esModule:true,default:${JSON.stringify(names)}};`,
      );
    } else {
      let code = ts.transpileModule(suppliedSource ?? fs.readFileSync(file, 'utf8'), {
        fileName: file,
        compilerOptions: {
          module: ts.ModuleKind.CommonJS,
          jsx: ts.JsxEmit.React,
          esModuleInterop: true,
          target: ts.ScriptTarget.ES2019,
        },
      }).outputText;
      const imports = [...code.matchAll(/require\(["']([^"']+)["']\)/g)];
      for (const [statement, specifier] of imports) {
        if (external.has(specifier)) continue;
        assert(specifier.startsWith('.'), `Unexpected fixture dependency: ${specifier}`);
        const resolved = require.resolve(path.resolve(path.dirname(file), specifier));
        const dependency = await collect(resolved);
        code = code.split(statement).join(`require(${JSON.stringify(dependency)})`);
      }
      modules.set(id, code);
    }
    return id;
  }
  const entry = await collect(
    path.join(frontend, 'brand-fixture.tsx'),
    `import React from 'react';
        import ReactDOM from 'react-dom';
        import {IntlProvider} from 'react-intl';
        import {LogoCircle} from './src/public/components/icons/LogoCircle';
        import {LargeLogo} from './src/public/components/icons/LargeLogo';
        import {LogoWide} from './src/public/components/icons/LogoWide';
        import {Logo} from './src/public/components/Logo/Logo';
        import {BRAND_ASSETS} from './src/public/components/Logo/brandAssets';
        import {PneumaticAvatarIcon} from './src/public/components/icons/PneumaticAvatarIcon';
        import {UserLayout} from './src/public/layout/UserLayout/UserLayout';
        import {getBrandName,getOrganizationName} from './src/public/constants/branding';
        window.renderBrandFixture = (locale) => ReactDOM.render(<IntlProvider locale={locale}><main>
          <section className="dark">
            <div data-logo="32"><LogoCircle size={32} theme="light" /></div>
            <div data-logo="40"><LogoCircle size={40} theme="light" /></div>
            <div data-logo="wide"><LogoWide /></div>
          </section>
          <section className="light">
            <div data-logo="standard"><LargeLogo /></div>
            <div data-logo="system-avatar"><PneumaticAvatarIcon /></div>
            <div data-logo="custom-wide"><Logo size="lg" theme="light" partnerLogoLg={BRAND_ASSETS.eagleBlack} partnerLogoSm={null} /></div>
            <div data-logo="custom-small"><Logo size="sm" theme="light" partnerLogoLg={null} partnerLogoSm={BRAND_ASSETS.eagleBlack} /></div>
          </section>
          <img id="flag" src={BRAND_ASSETS.syrianFlag} width="120" height="80" alt="Syrian flag" />
          <div id="populated-info"><UserLayout pages={[{slug:'signin',title:getBrandName(locale),description:getOrganizationName(locale)}]}><p>Authentication form fixture</p></UserLayout></div>
        </main></IntlProvider>,document.getElementById('root'));`,
  );
  return `(()=>{const modules={${[...modules].map(([id, code]) => `${JSON.stringify(id)}:function(module,exports,require){${code}\n}`).join(',')}};
    const cache={'react':{exports:window.React},'react-dom':{exports:window.ReactDOM},'react-intl':{exports:window.ReactIntl},'classnames':{exports:window.classNames}};
    function require(id){if(cache[id])return cache[id].exports;const module={exports:{}};cache[id]=module;modules[id](module,module.exports,require);return module.exports;}require(${JSON.stringify(entry)});})();`;
}

async function main() {
  const script = await bundle();
  const fonts = [400, 700]
    .map((weight) => {
      const name = weight === 400 ? 'Regular' : 'Bold';
      const data = fs
        .readFileSync(path.join(assets, `fonts/hayyakum-allah/HayyakumAllah-${name}.woff2`))
        .toString('base64');
      return `@font-face{font-family:'Hayyakum Allah';font-style:normal;font-weight:${weight};src:url(data:font/woff2;base64,${data}) format('woff2');}`;
    })
    .join('\n');
  fs.mkdirSync(artifacts, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const page = await browser.newPage();
    await page.route('**/*', (route) => route.abort());
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    const cases = [];
    for (const locale of ['en', 'ar-SY']) {
      for (const width of [375, 960, 1280]) {
        await page.setViewportSize({ width, height: 720 });
        await page.setContent(`<!doctype html><html lang="${locale}" dir="${locale === 'en' ? 'ltr' : 'rtl'}"><head><meta charset="utf-8"><style>
          ${fonts}
          html {font-size:10px;--pneumatic-font-sans:'Hayyakum Allah',sans-serif;--pneumatic-font-serif:'Hayyakum Allah',serif;--pneumatic-color-black88:#002623;--pneumatic-color-link:#054239;--pneumatic-color-gold:#b9a779;--pneumatic-color-link-text:#fff;}
          * {box-sizing:border-box;}body {margin:0;background:#f4f1e9;}svg {display:block;}
          main {padding:24px;display:grid;gap:24px;justify-content:center;}
          section {padding:24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;max-width:100%;}
          .dark {background:#002623;}.light {background:white;}
        </style></head><body><div id="root"></div></body></html>`);
        for (const vendor of [
          'react/umd/react.production.min.js',
          'react-dom/umd/react-dom.production.min.js',
          'react-intl/react-intl.iife.js',
          'classnames/index.js',
        ]) {
          await page.addScriptTag({ path: path.join(frontend, 'node_modules', vendor) });
        }
        await page.addScriptTag({ content: script });
        await page.evaluate((language) => window.renderBrandFixture(language), locale);
        await page.evaluate(async () => {
          await Promise.all(
            [400, 700].map((weight) =>
              document.fonts.load(`${weight} 22px "Hayyakum Allah"`, '\u0645\u0633\u0627\u0631\u0627\u062a'),
            ),
          );
          await Promise.all([...document.images].map((image) => image.decode()));
          await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        });
        const result = await page.evaluate(() => {
          const logos = [...document.querySelectorAll('[data-logo]')].map((surface) => {
            const element = surface.querySelector('svg,img');
            const bounds = element.getBoundingClientRect();
            const copy = element.querySelector('.brand-copy');
            const children = copy ? [...copy.children] : [];
            const copyBounds = copy?.getBoundingClientRect();
            return {
              name: surface.dataset.logo,
              width: bounds.width,
              height: bounds.height,
              direction: getComputedStyle(element).direction,
              objectFit: getComputedStyle(element).objectFit,
              product: copy?.querySelector('.brand-copy__product').textContent,
              organization: copy?.querySelector('.brand-copy__organization').textContent,
              copyHeight: copy?.clientHeight,
              scrollHeight: copy?.scrollHeight,
              textHeights: children.map((child) => child.getBoundingClientRect().height),
              copyFits:
                !copy ||
                (copy.scrollHeight <= copy.clientHeight &&
                  children.every((child) => {
                    const range = document.createRange();
                    range.selectNodeContents(child);
                    const text = range.getBoundingClientRect();
                    return (
                      text.left >= copyBounds.left - 0.6 &&
                      text.right <= copyBounds.right + 0.6 &&
                      child.getBoundingClientRect().bottom <= copyBounds.bottom + 0.6
                    );
                  })),
              imagePreserve: element.querySelector('image')?.getAttribute('preserveAspectRatio'),
            };
          });
          const flag = document.querySelector('#flag');
          const canvas = document.createElement('canvas');
          canvas.width = 900;
          canvas.height = 600;
          const context = canvas.getContext('2d');
          context.drawImage(flag, 0, 0);
          const info = document.querySelector('#populated-info .info');
          const color = (selector) => {
            const element = info.querySelector(selector);
            if (!element) throw new Error(`Missing populated info element ${selector}: ${info.textContent}`);
            return getComputedStyle(element).color;
          };
          const background = getComputedStyle(document.querySelector('#populated-info .container')).backgroundColor;
          const logo = info.querySelector('a svg');
          const logoBounds = logo.getBoundingClientRect();
          const logoCopy = logo.querySelector('.brand-copy');
          const logoText = [...logoCopy.children].map((child) => {
            const range = document.createRange();
            range.selectNodeContents(child);
            const bounds = range.getBoundingClientRect();
            // DOM Range includes the font's em box, which is taller than its
            // actual glyphs. Verify painted ink, including wrapped ministry lines.
            const font = getComputedStyle(child);
            context.font = `${font.fontWeight} ${font.fontSize} ${font.fontFamily}`;
            const metrics = context.measureText(child.textContent);
            const scale = logo.getScreenCTM().d;
            const lineHeight = parseFloat(font.lineHeight);
            const lines = Math.round(child.getBoundingClientRect().height / (lineHeight * scale));
            const top = bounds.top + (metrics.fontBoundingBoxAscent - metrics.actualBoundingBoxAscent) * scale;
            const bottom =
              bounds.top +
              ((lines - 1) * lineHeight + metrics.fontBoundingBoxAscent + metrics.actualBoundingBoxDescent) * scale;
            return {
              text: child.textContent,
              ink: { top, bottom },
              inside:
                bounds.left >= logoBounds.left - 0.6 &&
                bounds.right <= logoBounds.right + 0.6 &&
                top >= logoBounds.top - 0.6 &&
                bottom <= logoBounds.bottom + 0.6,
            };
          });
          const panelGeometry = () =>
            ['.container', '.info', '.info__inner', '.content', '.card', '.info__title', '.info__description'].map(
              (selector) => {
                const bounds = document.querySelector(`#populated-info ${selector}`).getBoundingClientRect();
                return { selector, x: bounds.x, y: bounds.y, width: bounds.width, height: bounds.height };
              },
            );
          const after = panelGeometry();
          // Compare the existing 40×40 band footprint with the new 170×40 lockup;
          // only identity content may change, not the surrounding panel/copy geometry.
          logo.setAttribute('width', '40');
          const before = panelGeometry();
          logo.setAttribute('width', '170');
          return {
            logos,
            info: {
              foreground: getComputedStyle(info).color,
              heading: color('.info__title'),
              description: color('.info__description'),
              link: color('a'),
              background,
              divider: getComputedStyle(info.querySelector('hr')).borderTopColor,
              logo: {
                width: logoBounds.width,
                height: logoBounds.height,
                viewBox: logo.getAttribute('viewBox'),
                marginBottom: parseFloat(getComputedStyle(logo).marginBottom),
                text: logoText,
              },
              panelGeometryUnchanged: before.every(
                (bounds, index) =>
                  !['.container', '.info', '.content', '.card'].includes(bounds.selector) ||
                  ['x', 'y', 'width', 'height'].every((key) => Math.abs(bounds[key] - after[index][key]) < 0.6),
              ),
              verticalGeometryUnchanged: before.every((bounds, index) =>
                ['y', 'height'].every((key) => Math.abs(bounds[key] - after[index][key]) < 0.6),
              ),
              panelGeometry: { before, after },
            },
            overflow: document.documentElement.scrollWidth - innerWidth,
            flag: {
              natural: [flag.naturalWidth, flag.naturalHeight],
              box: [flag.width, flag.height],
              colors: [
                [450, 100],
                [100, 300],
                [450, 500],
                [225, 300],
              ].map(([x, y]) => [...context.getImageData(x, y, 1, 1).data]),
            },
          };
        });
        const sizes = {
          32: [32, 32],
          40: [40, 40],
          standard: [170, 48],
          wide: [210, 60],
          'system-avatar': [32, 32],
          'custom-wide': [170, 48],
          'custom-small': [32, 32],
        };
        for (const logo of result.logos) {
          assert.deepEqual([logo.width, logo.height], sizes[logo.name]);
          assert(logo.copyFits, JSON.stringify(logo));
          if (logo.product) {
            assert.equal(logo.product, locale === 'en' ? 'Masarat' : '\u0645\u0633\u0627\u0631\u0627\u062a');
            assert(logo.organization && logo.organization !== logo.product);
          }
          if (logo.imagePreserve) {
            assert.equal(logo.direction, 'ltr');
            assert.equal(logo.imagePreserve, 'xMidYMid meet');
          } else assert.equal(logo.objectFit, 'contain');
        }
        assert(result.overflow <= 1, 'Logo fixture must fit narrow viewport');
        assert.deepEqual(result.flag.natural, [900, 600]);
        assert.deepEqual(result.flag.box, [120, 80]);
        assert.deepEqual(result.flag.colors, [
          [0, 122, 61, 255],
          [255, 255, 255, 255],
          [0, 0, 0, 255],
          [206, 17, 38, 255],
        ]);
        assert.equal(result.info.foreground, 'rgb(255, 255, 255)');
        assert.equal(result.info.heading, 'rgb(255, 255, 255)');
        assert.equal(result.info.description, 'rgb(255, 255, 255)');
        assert.equal(result.info.background, 'rgb(5, 66, 57)');
        assert.equal(result.info.link, 'rgb(185, 167, 121)');
        assert.equal(result.info.divider, 'rgba(255, 255, 255, 0.32)');
        assert.deepEqual([result.info.logo.width, result.info.logo.height], [170, 40]);
        assert.equal(result.info.logo.viewBox, '0 0 170 48');
        assert.equal(result.info.logo.marginBottom, 80);
        assert.equal(
          result.info.logo.text[0].text,
          locale === 'en' ? 'Masarat' : '\u0645\u0633\u0627\u0631\u0627\u062a',
        );
        assert(result.info.logo.text[1].text.length > 15, 'The separate Ministry name must be visible in the logo');
        await page
          .locator('#populated-info .info a')
          .screenshot({ path: path.join(artifacts, `${locale}-${width}-populated-lockup.png`) });
        assert(
          result.info.logo.text.every(({ inside }) => inside),
          JSON.stringify(result.info.logo.text),
        );
        assert(result.info.panelGeometryUnchanged, JSON.stringify(result.info.panelGeometry));
        assert(result.info.verticalGeometryUnchanged, JSON.stringify(result.info.panelGeometry));
        result.info.copyContrast = contrast(result.info.foreground, result.info.background);
        result.info.linkContrast = contrast(result.info.link, result.info.background);
        assert(result.info.copyContrast >= 4.5, 'Populated info copy must meet normal-text contrast');
        assert(result.info.linkContrast >= 4.5, 'Info links must meet normal-text contrast');
        await page.locator('#populated-info .info a').hover();
        assert.equal(
          await page.locator('#populated-info .info a').evaluate((link) => getComputedStyle(link).color),
          'rgb(255, 255, 255)',
        );
        await page.screenshot({ path: path.join(artifacts, `${locale}-${width}.png`), fullPage: true });
        cases.push({ locale, width, ...result });
      }
    }
    assert.deepEqual(errors, []);
    const normal = fs.readFileSync(path.join(assets, 'favicon.png'));
    const alert = fs.readFileSync(path.join(assets, 'favicon-alert.png'));
    assert.deepEqual([normal.readUInt32BE(16), normal.readUInt32BE(20)], [70, 70]);
    assert.deepEqual([alert.readUInt32BE(16), alert.readUInt32BE(20)], [70, 70]);
    assert(!normal.equals(alert), 'Notification favicon must remain distinct');
    const ico = fs.readFileSync(path.join(assets, 'favicon.ico'));
    assert.equal(ico.readUInt16LE(2), 1);
    assert.equal(ico.readUInt16LE(4), 4);
    fs.writeFileSync(path.join(artifacts, 'report.json'), JSON.stringify({ artworkUnchanged: true, cases }, null, 2));
    console.log(
      JSON.stringify(
        {
          cases: cases.length,
          actualReact: true,
          artworkUnchanged: true,
          flagColorsAndRatioPreserved: true,
          faviconsChecked: true,
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
