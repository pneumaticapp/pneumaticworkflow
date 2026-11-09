import { ELocale } from '../types/redux';
import { EnLang } from './entries/en-US';
import { RuLang } from './entries/ru-RU';
import { ArLang } from './entries/ar-SY';

export const AppLocale = {
  [ELocale.English]: EnLang,
  [ELocale.Russian]: RuLang,
  [ELocale.Arabic]: ArLang,
};
