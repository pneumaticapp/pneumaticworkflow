import { ELocale } from '../types/locale';
import { EnLang } from './entries/en-US';
import { RuLang } from './entries/ru-RU';

export const AppLocale = {
  [ELocale.English]: EnLang,
  [ELocale.Russian]: RuLang,
};
