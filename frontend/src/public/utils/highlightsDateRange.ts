import moment from 'moment-timezone';

import { EHighlightsDateFilter } from '../types/highlights';

export interface IHighlightsDateRange {
  startDate: Date;
  endDate: Date;
}

const DAYS_IN_WEEK = 7;

/**
 * The range picker stores the closing edge of a day as 23:59:59.000 (see normalizeDatePickerDate),
 * so presets must produce the same shape or a custom range and a preset would not be comparable.
 */
const LAST_SECOND_OF_DAY = { hour: 23, minute: 59, second: 59, millisecond: 0 };

const getNow = (timezone: string) => (timezone ? moment.tz(timezone) : moment());

/** `dateFdw` comes from the profile as '0' (Sunday) or '1' (Monday). */
const parseFirstDayOfWeek = (dateFdw?: string): number => {
  const firstDayOfWeek = Number(dateFdw);

  return Number.isInteger(firstDayOfWeek) && firstDayOfWeek >= 0 && firstDayOfWeek < DAYS_IN_WEEK
    ? firstDayOfWeek
    : 0;
};

const toDayRange = (dayStart: moment.Moment, lastDayStart: moment.Moment = dayStart): IHighlightsDateRange => ({
  startDate: dayStart.toDate(),
  endDate: lastDayStart.clone().set(LAST_SECOND_OF_DAY).toDate(),
});

/** Today in the given timezone. Split out so callers that only need it avoid a nullable result. */
export const getTodayDateRange = (timezone: string): IHighlightsDateRange =>
  toDayRange(getNow(timezone).startOf('day'));

/**
 * Build the [startDate, endDate] pair for a Highlights date preset.
 *
 * Always evaluated at call time and always in the user's profile timezone, so the range matches the
 * calendar day the user actually sees rather than the browser's day at the moment the bundle loaded.
 * Returns null for Custom, where the range belongs to the user.
 */
export const getHighlightsDateRange = (
  filter: EHighlightsDateFilter,
  timezone: string,
  dateFdw?: string,
): IHighlightsDateRange | null => {
  const now = getNow(timezone);

  switch (filter) {
    case EHighlightsDateFilter.Today:
      return toDayRange(now.startOf('day'));

    case EHighlightsDateFilter.Yesterday:
      return toDayRange(now.clone().subtract(1, 'day').startOf('day'));

    case EHighlightsDateFilter.Week: {
      const firstDayOfWeek = parseFirstDayOfWeek(dateFdw);
      const daysSinceWeekStart = (now.day() - firstDayOfWeek + DAYS_IN_WEEK) % DAYS_IN_WEEK;
      const weekStart = now.clone().startOf('day').subtract(daysSinceWeekStart, 'days');

      return toDayRange(weekStart, weekStart.clone().add(DAYS_IN_WEEK - 1, 'days'));
    }

    case EHighlightsDateFilter.Month: {
      const monthStart = now.clone().startOf('month');

      return toDayRange(monthStart, monthStart.clone().endOf('month').startOf('day'));
    }

    default:
      return null;
  }
};
