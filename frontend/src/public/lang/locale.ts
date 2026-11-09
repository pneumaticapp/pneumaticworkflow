import { ELocale } from '../types/redux';
import { getLocaleDirection } from './direction';

export function normalizeLocale(locale?: string | null): ELocale | undefined {
  switch (locale?.toLowerCase().replace(/_/g, '-')) {
    case 'en':
    case 'en-us':
      return ELocale.English;
    case 'ru':
    case 'ru-ru':
      return ELocale.Russian;
    case 'ar':
    case 'ar-sy':
      return ELocale.Arabic;
    default:
      return undefined;
  }
}

/** First supported preference wins; server and browser use the same aliases. */
export function resolveLocale(...preferences: (string | null | undefined)[]): ELocale {
  return preferences.map(normalizeLocale).find(Boolean) || ELocale.English;
}

export function getLocaleAttributes(locale: string) {
  const normalized = resolveLocale(locale);
  return {
    lang: normalized === ELocale.Arabic ? 'ar-SY' : normalized === ELocale.Russian ? 'ru-RU' : 'en-US',
    dir: getLocaleDirection(normalized),
  };
}
