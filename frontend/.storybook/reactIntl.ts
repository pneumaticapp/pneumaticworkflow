import { AppLocale } from '../src/public/lang';

const locales = ['en', 'ru', 'ar-sy'];
const formats = {};
const messages = locales.reduce(
  (acc, lang) => ({
    ...acc,
    [lang]: AppLocale[lang].messages,
  }),
  {},
);

export const reactIntl = {
  defaultLocale: 'en',
  locales,
  messages,
  formats,
};
