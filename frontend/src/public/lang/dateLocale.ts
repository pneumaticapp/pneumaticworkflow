import { Locale, Month } from 'date-fns';
import { arSA } from 'date-fns/locale';

export const syrianMonths = [
  'كانون الثاني',
  'شباط',
  'آذار',
  'نيسان',
  'أيار',
  'حزيران',
  'تموز',
  'آب',
  'أيلول',
  'تشرين الأول',
  'تشرين الثاني',
  'كانون الأول',
];

/** date-fns has no Syrian Arabic locale; keep its Arabic rules with Levantine months. */
export const arSY: Locale = {
  ...arSA,
  code: 'ar-SY',
  localize: {
    ...arSA.localize,
    month: (month) => syrianMonths[month],
  },
  match: {
    ...arSA.match,
    month: (value, options) => {
      const month = syrianMonths.findIndex((name) => value.startsWith(name));
      if (month === -1) return arSA.match.month(value, options);
      return { value: month as Month, rest: value.slice(syrianMonths[month].length) };
    },
  },
  options: { ...arSA.options, weekStartsOn: 0 },
};
