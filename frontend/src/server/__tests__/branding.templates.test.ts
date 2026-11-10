import fs from 'fs';
import path from 'path';

import { BRAND, getBrandName } from '../../public/constants/branding';
import { getLocaleAttributes, resolveLocale } from '../../public/lang/locale';

const ejs = require('ejs') as { render(template: string, values: Record<string, unknown>): string };

describe('initial branded document titles', () => {
  it.each(['index.ejs', 'forms.ejs'])('renders locale-aware titles and keeps technical globals in %s', (filename) => {
    const template = fs.readFileSync(path.resolve(__dirname, '../../public', filename), 'utf8');
    for (const locale of ['en-US', 'ru-RU', 'ar-SY']) {
      const values = {
        documentLocale: getLocaleAttributes(resolveLocale(locale)),
        brandName: getBrandName(locale),
        config: '{}',
        user: '{}',
        invitedUser: '{}',
        pages: '{}',
        env: 'test',
      };
      const document = ejs.render(template, values);
      expect(document).toContain(`<title>${getBrandName(locale)}</title>`);
      expect(document).toContain('window.__pneumaticConfig');
      expect(document).toContain('id="pneumatic-frontend"');

      const { brandName: _brandName, ...fallbackValues } = values;
      expect(ejs.render(template, fallbackValues)).toContain(`<title>${BRAND.name}</title>`);
    }
  });
});
