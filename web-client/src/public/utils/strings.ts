import { isSameYear } from 'date-fns';
import moment from 'moment';
import 'moment/locale/ru';

import { PNEUMATIC_SUFFIX } from '../constants/titles';
import { getPairedArrayItems } from './helpers';

export const sanitizeText = (textContent?: string | null) => (textContent && textContent.replace(/\u00A0/g, ' ')) || '';

export const capitalize = (text?: string) => (text ? text.charAt(0).toUpperCase() + text.slice(1) : '');

export const formatToFixed = (value: number, decimals: number) => value.toFixed(decimals).replace(/[.,]00$/, '');

export function getDate(dateString?: string, config?: { view: 'date' | 'day' }, currentLocale?: string) {
  const date = dateString ? moment(dateString) : moment();

  const { view } = config || { view: 'date' };

  if (!currentLocale) {
    currentLocale = 'eng';
  }
  date.locale(currentLocale);

  const getFormatString = () => {
    if (view === 'day') return 'MMM DD';
    return isSameYear(date.toDate(), new Date()) ? 'MMM DD, HH:mm' : 'MMM DD YYYY, HH:mm';
  };

  const formattedDate = date.format(getFormatString());
  const result = formattedDate.charAt(0).toUpperCase() + formattedDate.slice(1);

  return result;
}

export function getTime(dateString: string, timezone: string, formatTime: string) {
  return moment(dateString)
    .tz(timezone, false)
    .format(formatTime.split(', ')[2] === 'p' ? 'h:mma' : 'HH:mm');
}

export function toTitleCase(phrase: string) {
  return phrase
    .toLowerCase()
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export const removePneumaticSuffix = (s: string) => {
  return s.replace(PNEUMATIC_SUFFIX, '').trim();
};

export const replaceStringRange = (s: string, start: number, end: number, substitute: string) => {
  return s.substring(0, start) + substitute + s.substring(end);
};

export const breakAt = (places: number[], str: string) => {
  return getPairedArrayItems([0, ...places, str.length]).map(([a, b]) => str.substring(a, b));
};

export const addDotsForBigText = (text: string) => (text.length > 20 ? `${text.slice(0, 20)}...` : text);

export const isMatchingSearchQuery = (query: string, strings: string[]) => {
  const normalizedQuery = query.toLowerCase();

  return strings.some((str) => str.toLowerCase().includes(normalizedQuery));
};
