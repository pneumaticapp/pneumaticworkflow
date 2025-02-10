import moment, { duration as momentDuration } from 'moment';
import 'moment-timezone';
import 'moment-duration-format';
import {
  endOfMonth,
  endOfToday,
  endOfWeek,
  endOfYesterday,
  startOfMonth,
  startOfToday,
  startOfWeek,
  startOfYesterday,
  isAfter,
} from 'date-fns';

import { useIntl } from 'react-intl';
import { IWorkflowDelay } from '../types/workflow';
import { EHighlightsDateFilter } from '../types/highlights';

import { getDate } from './strings';

export const SEC_IN_DAY = 24 * 60 * 60;
export const SEC_IN_HOUR = 60 * 60;
export const SEC_IN_MINUTE = 60;

export const PROCESS_HIGHLIGHTS_DATE_RANGE_MAP = {
  [EHighlightsDateFilter.Today]: {
    startDate: startOfToday(),
    endDate: endOfToday(),
  },
  [EHighlightsDateFilter.Yesterday]: {
    startDate: startOfYesterday(),
    endDate: endOfYesterday(),
  },
  [EHighlightsDateFilter.Week]: {
    startDate: startOfWeek(new Date()),
    endDate: endOfWeek(new Date()),
  },
  [EHighlightsDateFilter.Month]: {
    startDate: startOfMonth(new Date()),
    endDate: endOfMonth(new Date()),
  },
};

export const formatDateToQuery = (date?: Date | null) => {
  if (!date) return null;

  const ISOFormattedDate = moment(date).format('YYYY-MM-DDTHH:mm:ss');
  const query = encodeURIComponent(ISOFormattedDate);

  return query;
};

export interface IDurationFormatSettings extends moment.DurationFormatSettings {}

export interface ISplittedDuration {
  days: number;
  hours: number;
  minutes: number;
}

export const DEFAULT_PRECISION = 0;

export const DELAY_TITLE_TEMPLATE = 'D[d] H[h] m[m]';
export const DELAY_TITLE_OPTIONS: IDurationFormatSettings = { trim: false };

export const PROCESSES_LOG_TEMPLATE = 'D[d] H[h] m[m]';

export const DELAY_REQUEST_TEMPLATE = 'DD hh:mm:ss';
export const DELAY_REQUEST_OPTIONS: IDurationFormatSettings = { trim: false };

export const parseDuration = (duration: string): ISplittedDuration => {
  const re = /(\d*\s?)(\d{2}):(\d{2})/im;
  const parsed = duration.match(re);

  if (!parsed) return { days: 0, hours: 0, minutes: 0 };

  const START_INDEX = 1;
  const END_INDEX = 4;
  const [days, hours, minutes] = parsed.slice(START_INDEX, END_INDEX).map(Number);

  return { days, hours, minutes };
};

export const isEmptyDuration = (duration: string | null) => {
  if (!duration) return true;

  const { days, hours, minutes } = parseDuration(duration);
  return [days, hours, minutes].every((value) => value === 0);
};

const removeZeroParts = (formattedDuration: string) => {
  return formattedDuration.replace(/(^0d|\D0h|\D0m)/g, '').trim();
};

export const formatDuration = (duration: string | null, template: string) => {
  if (!duration) return '';

  const { days, hours, minutes } = parseDuration(duration);
  const seconds = getSeconds({ days, hours, minutes });

  return removeZeroParts(momentDuration(seconds, 'seconds').format(template, DEFAULT_PRECISION, DELAY_TITLE_OPTIONS));
};

export const formatDurationMonths = (value: number | null) => {
  if (!value) return '';

  return `${value}${value === 1 ? 'mo' : 'mos'}`;
};

export const getZeroDuration = (duration: string | null, durationMonths: number | null): string | null => {
  const regexNotDueDate: RegExp = /[1-9]/;
  if (durationMonths || (duration && regexNotDueDate?.test(duration))) return null;

  const { formatMessage } = useIntl();
  const zeroDuration = `0${formatMessage({ id: 'tasks.task-zero-due-date' })}`;
  return zeroDuration;
};

export const formatDelayRequest = ({ days, hours, minutes }: ISplittedDuration) => {
  const seconds = getSeconds({ days, hours, minutes });

  return momentDuration(seconds, 'seconds').format(DELAY_REQUEST_TEMPLATE, DEFAULT_PRECISION, DELAY_REQUEST_OPTIONS);
};

export const getSeconds = ({ days, hours, minutes }: ISplittedDuration) => {
  return days * SEC_IN_DAY + hours * SEC_IN_HOUR + minutes * SEC_IN_MINUTE;
};

export const getSnoozedUntilDate = (delay: IWorkflowDelay | null, locale?: string) => {
  if (!delay) return '';
  const { estimatedEndDate } = delay;
  const currentLocale = locale || undefined;
  return getDate(estimatedEndDate, undefined, currentLocale);
};

export const getTimeDiff = (template: string, start: string, end?: string | null, timezone?: string) => {
  const startDate = moment(start);
  const endDate = end ? moment(end) : moment.tz(new Date(), timezone || '').utc();
  const diff = Math.abs(startDate.diff(endDate, 'seconds'));

  return removeZeroParts(momentDuration(diff, 'seconds').format(template));
};

export const isExpired = (deadlineDateISO: string | null, compareDateISO?: string | null) => {
  if (!deadlineDateISO) return false;

  const compareDate = compareDateISO ? new Date(compareDateISO) : new Date();
  const deadLineDate = new Date(deadlineDateISO);

  return isAfter(compareDate, deadLineDate);
};

export const DATE_STRING_MOMENT_TEMPLATE = 'MMM DD, YYYY';
export const DATE_STRING_FNS_TEMPLATE = 'MMM dd, yyyy';

export const getEndOfDayTsp = (date: string | Date): number | null => {
  if (!date) return null;

  if (typeof date === 'string' && /^[0-9]+(\.[0-9]+)?$/.test(date)) {
    return +date;
  }
  const momentDate = moment(date);

  if (!momentDate.isValid()) {
    throw new Error(`getEndOfDayTsp: Invalid date. Received: ${date} (type: ${typeof date})`);
  }

  return momentDate.endOf('day').unix();
};

export const toDate = (date: number | string | null): Date | null => {
  if (!date) return null;
  if (typeof date === 'number' || (typeof date === 'string' && /^[0-9]+(\.[0-9]+)?$/.test(date))) {
    return moment(+date * 1000).toDate();
  }
  if (typeof date === 'string') {
    return moment(date).toDate();
  }
  throw new Error(`toDate: Invalid date format. Received: ${date} (type: ${typeof date})`);
};

export const toDateString = (date: Date | number | string, timezone?: string): string | null => {
  if (!date) return null;

  let momentDate;
  if (date instanceof Date) {
    momentDate = moment(date);
  } else {
    momentDate = moment.tz(+date * 1000, timezone || 'UTC');
  }

  if (!momentDate.isValid()) {
    throw new Error(`toDateString: Invalid data format. Received: date: ${date}, timezone: ${timezone}`);
  }
  return momentDate.format(DATE_STRING_MOMENT_TEMPLATE);
};

export const toTspDate = (date?: string | Date | null): number | null => {
  if (!date) return null;
  const momentDate = moment(date);
  if (!momentDate.isValid()) {
    throw new Error(`toTspDate: Invalid date format. Received: ${date} (type: ${typeof date})`);
  }
  return momentDate.unix();
};

export const formatDateToISOInObject = <T extends { dueDateTsp: number | null }>(
  resWitTsp: T,
): Omit<T, 'dueDateTsp'> & { dueDate: string | null } => {
  const { dueDateTsp, ...rest } = resWitTsp;
  return {
    ...rest,
    dueDate: dueDateTsp ? toISOStringFromTsp(dueDateTsp) : null,
  };
};

export function toISOStringFromTsp(dueDateTsp: number) {
  return moment.unix(dueDateTsp).utc().format('YYYY-MM-DDTHH:mm:ss[Z]');
}
