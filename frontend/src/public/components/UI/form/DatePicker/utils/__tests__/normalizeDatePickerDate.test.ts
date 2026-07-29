import moment from 'moment-timezone';

import {
  formatDatePickerDisplayValue,
  formatDatePickerRangeDisplayValue,
  normalizeDatePickerDate,
  toCalendarDate,
} from '../normalizeDatePickerDate';

describe('toCalendarDate', () => {
  it('keeps the same calendar day for end-of-day timestamps across timezones', () => {
    const timezone = 'America/New_York';
    const endOfDayNy = moment.tz('2024-07-15 23:59:59', timezone).toDate();
    const calendarDate = toCalendarDate(endOfDayNy, timezone);

    expect(calendarDate).not.toBeNull();
    expect(calendarDate!.getFullYear()).toBe(2024);
    expect(calendarDate!.getMonth()).toBe(6);
    expect(calendarDate!.getDate()).toBe(15);
  });
});

describe('normalizeDatePickerDate', () => {
  const timezone = 'America/New_York';

  it('returns null for empty date', () => {
    expect(normalizeDatePickerDate({ date: null, timezone })).toBeNull();
  });

  it('keeps start-of-day when startDay is true', () => {
    const date = new Date(2024, 5, 15);
    const result = normalizeDatePickerDate({ date, timezone, mode: 'start', startDay: true });

    expect(moment(result).tz(timezone).format('YYYY-MM-DD HH:mm:ss')).toBe('2024-06-15 00:00:00');
  });

  it('sets end of day for mode end', () => {
    const date = new Date(2024, 5, 15);
    const result = normalizeDatePickerDate({ date, timezone, mode: 'end' });

    expect(moment(result).tz(timezone).format('YYYY-MM-DD HH:mm:ss')).toBe('2024-06-15 23:59:59');
  });

  it('sets end of day for single picker without startDay', () => {
    const date = new Date(2024, 5, 15);
    const result = normalizeDatePickerDate({ date, timezone, mode: 'start', startDay: false });

    expect(moment(result).tz(timezone).format('YYYY-MM-DD HH:mm:ss')).toBe('2024-06-15 23:59:59');
  });
});

describe('formatDatePickerDisplayValue', () => {
  it('formats zoned calendar day without shifting to the next day', () => {
    const timezone = 'America/New_York';
    const endOfDayNy = moment.tz('2024-07-15 23:59:59', timezone).toDate();

    expect(formatDatePickerDisplayValue(endOfDayNy, timezone)).toBe('Jul 15, 2024');
  });
});

describe('formatDatePickerRangeDisplayValue', () => {
  const timezone = 'America/New_York';
  const startDate = moment.tz('2024-06-10 00:00:00', timezone).toDate();
  const endDate = moment.tz('2024-06-20 23:59:59', timezone).toDate();

  it('returns empty string when both dates are missing', () => {
    expect(formatDatePickerRangeDisplayValue(null, null, timezone)).toBe('');
  });

  it('formats full range', () => {
    expect(formatDatePickerRangeDisplayValue(startDate, endDate, timezone)).toBe('Jun 10, 2024 — Jun 20, 2024');
  });

  it('formats only start date when end is missing', () => {
    expect(formatDatePickerRangeDisplayValue(startDate, null, timezone)).toBe('Jun 10, 2024');
  });
});
