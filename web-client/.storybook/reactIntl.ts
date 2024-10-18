import { AppLocale } from '../src/public/lang';

const locales = ['en', 'ru'];

const messages = locales.reduce((acc, lang) => ({
  ...acc,
  [lang]: AppLocale[lang].messages, // whatever the relative path to your messages json is
}), {});

const formats = {}; // optional, if you have any formats

export const reactIntl = {
  defaultLocale: 'en',
  locales,
  messages,
  formats,
};
