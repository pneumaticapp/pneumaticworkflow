import { getHighlightsDateRange, getTodayDateRange } from '../highlightsDateRange';
import { EHighlightsDateFilter } from '../../types/highlights';

/** +05:00 all year, so the expected instants stay readable and DST never enters the assertions. */
const TIMEZONE = 'Asia/Yekaterinburg';
const SUNDAY = '0';
const MONDAY = '1';

/** Wednesday, 27 Nov 2024, 15:03 in +05:00. */
const MIDDAY_IN_ZONE = '2024-11-27T10:03:00.000Z';
/** Still 27 Nov in UTC, but already 00:30 on 28 Nov in +05:00. */
const AFTER_MIDNIGHT_IN_ZONE = '2024-11-27T19:30:00.000Z';

let nowSpy: jest.SpyInstance;

/** moment reads the clock through Date.now, so stubbing it is enough to pin "now". */
const setNow = (iso: string) => {
  nowSpy.mockReturnValue(new Date(iso).getTime());
};

const toISO = (date: Date) => date.toISOString();

describe('getHighlightsDateRange', () => {
  beforeAll(() => {
    nowSpy = jest.spyOn(Date, 'now');
  });

  afterAll(() => {
    nowSpy.mockRestore();
  });

  it('starts Today at midnight in the profile timezone, not at the current time', () => {
    setNow(MIDDAY_IN_ZONE);

    const range = getHighlightsDateRange(EHighlightsDateFilter.Today, TIMEZONE);

    expect(toISO(range!.startDate)).toBe('2024-11-26T19:00:00.000Z');
    expect(toISO(range!.endDate)).toBe('2024-11-27T18:59:59.000Z');
  });

  it('resolves Today against the profile timezone when the browser is still on the previous day', () => {
    setNow(AFTER_MIDNIGHT_IN_ZONE);

    const range = getHighlightsDateRange(EHighlightsDateFilter.Today, TIMEZONE);

    expect(toISO(range!.startDate)).toBe('2024-11-27T19:00:00.000Z');
    expect(toISO(range!.endDate)).toBe('2024-11-28T18:59:59.000Z');
  });

  it('ends Yesterday on the previous day, not at the start of today', () => {
    setNow(MIDDAY_IN_ZONE);

    const range = getHighlightsDateRange(EHighlightsDateFilter.Yesterday, TIMEZONE);

    expect(toISO(range!.startDate)).toBe('2024-11-25T19:00:00.000Z');
    expect(toISO(range!.endDate)).toBe('2024-11-26T18:59:59.000Z');
  });

  it('closes every range on a whole second so the timestamp cannot round up to the next day', () => {
    setNow(MIDDAY_IN_ZONE);

    const filters = [
      EHighlightsDateFilter.Today,
      EHighlightsDateFilter.Yesterday,
      EHighlightsDateFilter.Week,
      EHighlightsDateFilter.Month,
    ];

    filters.forEach((filter) => {
      const { endDate } = getHighlightsDateRange(filter, TIMEZONE)!;

      expect(endDate.getMilliseconds()).toBe(0);
      expect(Math.floor(endDate.getTime() / 1000)).toBe(endDate.getTime() / 1000);
    });
  });

  it('starts the Week on the day the profile calendar starts on', () => {
    setNow(MIDDAY_IN_ZONE);

    const mondayWeek = getHighlightsDateRange(EHighlightsDateFilter.Week, TIMEZONE, MONDAY);
    const sundayWeek = getHighlightsDateRange(EHighlightsDateFilter.Week, TIMEZONE, SUNDAY);

    expect(toISO(mondayWeek!.startDate)).toBe('2024-11-24T19:00:00.000Z');
    expect(toISO(mondayWeek!.endDate)).toBe('2024-12-01T18:59:59.000Z');
    expect(toISO(sundayWeek!.startDate)).toBe('2024-11-23T19:00:00.000Z');
    expect(toISO(sundayWeek!.endDate)).toBe('2024-11-30T18:59:59.000Z');
  });

  it('falls back to a Sunday week start when the profile value is missing or unusable', () => {
    setNow(MIDDAY_IN_ZONE);

    const withoutFdw = getHighlightsDateRange(EHighlightsDateFilter.Week, TIMEZONE);
    const withGarbageFdw = getHighlightsDateRange(EHighlightsDateFilter.Week, TIMEZONE, 'monday');

    expect(toISO(withoutFdw!.startDate)).toBe('2024-11-23T19:00:00.000Z');
    expect(toISO(withGarbageFdw!.startDate)).toBe('2024-11-23T19:00:00.000Z');
  });

  it('spans the calendar month in the profile timezone', () => {
    setNow(MIDDAY_IN_ZONE);

    const range = getHighlightsDateRange(EHighlightsDateFilter.Month, TIMEZONE);

    expect(toISO(range!.startDate)).toBe('2024-10-31T19:00:00.000Z');
    expect(toISO(range!.endDate)).toBe('2024-11-30T18:59:59.000Z');
  });

  it('leaves the range to the user for the Custom filter', () => {
    setNow(MIDDAY_IN_ZONE);

    expect(getHighlightsDateRange(EHighlightsDateFilter.Custom, TIMEZONE)).toBeNull();
  });

  it('re-reads the clock on every call instead of freezing the range at import time', () => {
    setNow(MIDDAY_IN_ZONE);
    const beforeMidnight = getHighlightsDateRange(EHighlightsDateFilter.Today, TIMEZONE);

    setNow(AFTER_MIDNIGHT_IN_ZONE);
    const afterMidnight = getHighlightsDateRange(EHighlightsDateFilter.Today, TIMEZONE);

    expect(toISO(afterMidnight!.startDate)).not.toBe(toISO(beforeMidnight!.startDate));
  });
});

describe('getTodayDateRange', () => {
  beforeAll(() => {
    nowSpy = jest.spyOn(Date, 'now');
  });

  afterAll(() => {
    nowSpy.mockRestore();
  });

  it('matches the Today preset', () => {
    setNow(MIDDAY_IN_ZONE);

    const today = getTodayDateRange(TIMEZONE);
    const preset = getHighlightsDateRange(EHighlightsDateFilter.Today, TIMEZONE)!;

    expect(toISO(today.startDate)).toBe(toISO(preset.startDate));
    expect(toISO(today.endDate)).toBe(toISO(preset.endDate));
  });

  it('falls back to the browser timezone when the profile has none yet', () => {
    setNow(MIDDAY_IN_ZONE);

    const { startDate, endDate } = getTodayDateRange('');

    expect(startDate.getHours()).toBe(0);
    expect(startDate.getMinutes()).toBe(0);
    expect(endDate.getHours()).toBe(23);
    expect(endDate.getSeconds()).toBe(59);
  });
});
