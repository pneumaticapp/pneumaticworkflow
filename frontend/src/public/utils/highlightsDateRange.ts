import moment from 'moment-timezone';

import { EHighlightsDateFilter } from '../types/highlights';

export interface IHighlightsDateRange {
  startDate: Date;
  endDate: Date;
}

const DAYS_IN_WEEK = 7;

const LAST_SECOND_OF_DAY = { hour: 23, minute: 59, second: 59, millisecond: 0 };

const getNow = (timezone: string) => (timezone ? moment.tz(timezone) : moment());

const parseFirstDayOfWeek = (dateFdw?: string): number => {
  const firstDayOfWeek = Number(dateFdw);

  return Number.isInteger(firstDayOfWeek) && firstDayOfWeek >= 0 && firstDayOfWeek < DAYS_IN_WEEK ? firstDayOfWeek : 0;
};

const toDayRange = (dayStart: moment.Moment, lastDayStart: moment.Moment = dayStart): IHighlightsDateRange => ({
  startDate: dayStart.toDate(),
  endDate: lastDayStart.clone().set(LAST_SECOND_OF_DAY).toDate(),
});

export const getTodayDateRange = (timezone: string): IHighlightsDateRange =>
  toDayRange(getNow(timezone).startOf('day'));

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
