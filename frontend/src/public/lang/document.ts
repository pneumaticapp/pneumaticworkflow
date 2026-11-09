import moment from 'moment';
import './momentLocale';

import { getLocaleAttributes } from './locale';

/** Call before React renders, including when the Redux locale changes. */
export function applyDocumentLocale(locale: string): void {
  const { lang, dir } = getLocaleAttributes(locale);
  document.documentElement.lang = lang;
  document.documentElement.dir = dir;
  moment.locale(lang.toLowerCase());
}
