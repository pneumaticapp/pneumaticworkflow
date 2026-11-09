import { createIntl } from 'react-intl';

import { getTriplePlural } from '../helpers';
import { enMessages } from '../../lang/locales/en_US';
import { ruMessages } from '../../lang/locales/ru_RU';
import { arMessages } from '../../lang/locales/ar-SY';

const forms = ['tasks.task-extra-field-single', 'tasks.task-extra-field-plural-1', 'tasks.task-extra-field-plural-2'];
const countMessageId = 'tasks.task-extra-field-count';
const arabicIntl = createIntl({ locale: 'ar-SY', messages: arMessages });
const number = (value: number) => arabicIntl.formatNumber(value);
const createFormatterMock = (intl: ReturnType<typeof createIntl>) =>
  jest.fn((descriptor: { id: string }, values?: { count: number }): string => intl.formatMessage(descriptor, values));

describe('getTriplePlural locale-aware badges', () => {
  it.each(['ar', 'ar-SY', 'ar_SY', 'AR-sy'])('uses the Arabic dual without prefixing a redundant number for %s', (locale) => {
    expect(getTriplePlural({ counter: 2, forms, countMessageId, locale, formatMessage: arabicIntl.formatMessage })).toBe('مخرجان');
  });

  it.each([
    [1, 'مخرج واحد'],
    [2, 'مخرجان'],
    [3, `${number(3)} مخرجات`],
    [10, `${number(10)} مخرجات`],
    [11, `${number(11)} مخرجًا`],
    [21, `${number(21)} مخرجًا`],
    [99, `${number(99)} مخرجًا`],
    [100, `${number(100)} مخرج`],
    [102, `${number(102)} مخرج`],
  ])('uses the actual Arabic ICU category for %s outputs', (counter, expected) => {
    expect(getTriplePlural({ counter: counter as number, forms, countMessageId, locale: 'ar-SY', formatMessage: arabicIntl.formatMessage })).toBe(expected);
  });

  it.each([
    ['tasks.task-starts-after-count', 'شرط بدء واحد', 'شرطا بدء', 'شروط بدء', 'شرط بدء'],
    ['tasks.task-check-if-count', 'شرط تحقق واحد', 'شرطا تحقق', 'شروط تحقق', 'شرط تحقق'],
  ])('supports singular, dual, few and many for %s', (messageId, singular, dual, few, many) => {
    const render = (counter: number) => getTriplePlural({ counter, forms, countMessageId: messageId, locale: 'ar-SY', formatMessage: arabicIntl.formatMessage });

    expect(render(1)).toBe(singular);
    expect(render(2)).toBe(dual);
    expect(render(3)).toBe(`${number(3)} ${few}`);
    expect(render(11)).toBe(`${number(11)} ${many}`);
  });

  it.each([undefined, 0])('keeps absent/zero counters hidden without formatting a message (%s)', (counter) => {
    const formatMessage = createFormatterMock(arabicIntl);
    expect(getTriplePlural({ counter, forms, countMessageId, locale: 'ar-SY', formatMessage })).toBe('');
    expect(formatMessage).not.toHaveBeenCalled();
  });

  it.each([
    [1, '1 результат'], [2, '2 результата'], [4, '4 результата'], [5, '5 результатов'],
    [11, '11 результатов'], [12, '12 результатов'], [14, '14 результатов'],
    [21, '21 результат'], [22, '22 результата'], [25, '25 результатов'],
  ])('preserves the existing Russian output for %s', (counter, expected) => {
    const intl = createIntl({ locale: 'ru', messages: ruMessages });
    const formatMessage = createFormatterMock(intl);
    expect(getTriplePlural({ counter: counter as number, forms, countMessageId, locale: 'ru', formatMessage })).toBe(expected);
    expect(formatMessage.mock.calls[0]).toHaveLength(1);
    expect(formatMessage.mock.calls[0][0].id).not.toBe(countMessageId);
  });

  it.each([[1, '1 output'], [2, '2 outputs'], [11, '11 outputs'], [21, '21 output']])('preserves the existing English behavior for %s', (counter, expected) => {
    const intl = createIntl({ locale: 'en', messages: enMessages });
    const formatMessage = createFormatterMock(intl);
    expect(getTriplePlural({ counter: counter as number, forms, countMessageId, locale: 'en', formatMessage })).toBe(expected);
    expect(formatMessage.mock.calls[0]).toHaveLength(1);
  });

  it('keeps the legacy no-locale API and source form IDs unchanged', () => {
    const intl = createIntl({ locale: 'en', messages: enMessages });
    const source = [...forms];
    expect(getTriplePlural({ counter: 2, forms: source, formatMessage: intl.formatMessage })).toBe('2 outputs');
    expect(source).toEqual(forms);
  });
});
