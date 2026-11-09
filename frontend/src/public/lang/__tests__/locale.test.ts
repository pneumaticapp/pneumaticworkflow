import moment from 'moment';
import { format, parse } from 'date-fns';
import { ELocale } from '../../types/redux';
import { getLocaleAttributes, normalizeLocale, resolveLocale } from '../locale';
import { getLocaleDirection, resolveDirectionalPlacement } from '../direction';
import { applyDocumentLocale } from '../document';
import { arSY, syrianMonths } from '../dateLocale';

describe('locale resolution and initial document attributes', () => {
  afterEach(() => applyDocumentLocale('en'));

  it('registers locales without changing an existing global date preference', () => {
    jest.isolateModules(() => {
      const isolatedMoment = require('moment');
      isolatedMoment.locale('en');
      require('../momentLocale');
      expect(isolatedMoment.locale()).toBe('en');
    });
  });

  it.each(['ar', 'ar-SY', 'ar_SY', 'AR-sy'])('normalizes %s to the persisted Syrian language', (value) => {
    expect(normalizeLocale(value)).toBe(ELocale.Arabic);
    expect(getLocaleAttributes(value)).toEqual({ lang: 'ar-SY', dir: 'rtl' });
  });

  it('preserves preference precedence and ignores unsupported languages', () => {
    expect(resolveLocale('ru', 'ar-sy', 'en')).toBe(ELocale.Russian);
    expect(resolveLocale('unsupported', 'ar-sy', 'en')).toBe(ELocale.Arabic);
    expect(resolveLocale(undefined, undefined, 'ar_SY')).toBe(ELocale.Arabic);
    expect(resolveLocale('unsupported')).toBe(ELocale.English);
  });

  it('updates the document and date locale together when switching back to English', () => {
    applyDocumentLocale('ar-sy');
    expect(document.documentElement.lang).toBe('ar-SY');
    expect(document.documentElement.dir).toBe('rtl');
    expect(moment.locale()).toBe('ar-sy');
    expect(moment('2026-01-05').format('MMMM')).toBe('كانون الثاني');
    expect(format(new Date(2026, 0, 5), 'MMMM', { locale: arSY })).toBe('كانون الثاني');
    applyDocumentLocale('en');
    expect(document.documentElement.dir).toBe('ltr');
    expect(moment('2026-01-05').format('MMMM')).toBe('January');
  });

  it('resolves authored popup placements once and leaves physical centers unchanged', () => {
    expect(resolveDirectionalPlacement('bottom-start', getLocaleDirection('ar-SY'))).toBe('bottom-end');
    expect(resolveDirectionalPlacement('right-start', 'rtl')).toBe('left-start');
    expect(resolveDirectionalPlacement('top', 'rtl')).toBe('top');
    expect(resolveDirectionalPlacement('bottom-start', 'ltr')).toBe('bottom-start');
  });

  it.each(syrianMonths.map((month, index) => [month, index] as const))(
    'round-trips the Syrian calendar month %s in editable date fields',
    (month, index) => {
      const value = `${month} 05, 2026`;
      const date = parse(value, 'MMM dd, yyyy', new Date(2026, 0, 1), { locale: arSY });
      expect(date.getMonth()).toBe(index);
      expect(format(date, 'MMM dd, yyyy', { locale: arSY })).toBe(value);
    },
  );
});
