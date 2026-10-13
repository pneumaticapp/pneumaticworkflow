import moment from 'moment-timezone';

export type TDatePickerDayMode = 'start' | 'end';

interface INormalizeDatePickerDateParams {
  date: Date | null;
  timezone: string;
  mode?: TDatePickerDayMode;
  /**
   * When true (single picker), keep calendar day start without forcing 23:59:59.
   * Ignored for mode === 'end'.
   */
  startDay?: boolean;
}

/**
 * Convert a stored zoned timestamp into a local calendar Date for react-datepicker.
 * Uses the calendar day in the user timezone (so 23:59:59 does not shift to the next day).
 */
export const toCalendarDate = (date: Date | null | undefined, timezone: string): Date | null => {
  if (!date) {
    return null;
  }

  const zonedDate = moment(date).tz(timezone);

  return new Date(zonedDate.year(), zonedDate.month(), zonedDate.date());
};

/**
 * Normalize a date coming from react-datepicker (local Y-M-D wall date) into a zoned Date.
 */
export const normalizeDatePickerDate = ({
  date,
  timezone,
  mode = 'start',
  startDay = false,
}: INormalizeDatePickerDateParams): Date | null => {
  if (!date) {
    return null;
  }

  const dayStart = moment.tz(
    {
      year: date.getFullYear(),
      month: date.getMonth(),
      day: date.getDate(),
    },
    timezone,
  );

  if (mode === 'end' || !startDay) {
    return dayStart.clone().set({ hour: 23, minute: 59, second: 59, millisecond: 0 }).toDate();
  }

  return dayStart.toDate();
};

export const formatDatePickerDisplayValue = (date: Date, timezone: string): string => {
  return moment(date).tz(timezone).format('MMM DD, yyyy');
};

export const formatDatePickerRangeDisplayValue = (
  startDate: Date | null | undefined,
  endDate: Date | null | undefined,
  timezone: string,
): string => {
  if (!startDate && !endDate) {
    return '';
  }

  if (startDate && endDate) {
    return `${formatDatePickerDisplayValue(startDate, timezone)} — ${formatDatePickerDisplayValue(endDate, timezone)}`;
  }

  if (startDate) {
    return formatDatePickerDisplayValue(startDate, timezone);
  }

  return endDate ? formatDatePickerDisplayValue(endDate, timezone) : '';
};
