import { getTimeDiff, isExpired } from '../../../utils/dateTime';
import { ELocale } from '../../../types/redux';

export interface IDueInData {
  timeLeft: string;
  dueDate: string;
  statusTitle: string;
  isOverdue: boolean;
}

type DateFormat = string;

export function getDueInData(
  dueDates: (DateFormat | null)[],
  factialEndDate?: DateFormat | null,
  timezone?: string,
  locale: string = ELocale.English,
): IDueInData | null {
  const DUE_IN_TEMPLATE = locale === ELocale.English ? 'D[d] H[h] m[m]' : 'D[д] H[ч] m[м]';
  const hasSomeDates = dueDates.some(Boolean);
  if (!hasSomeDates) return null;

  const [earliestDate] = dueDates
    .filter(Boolean)
    .sort((a: string, b: string) => new Date(a).valueOf() - new Date(b).valueOf()) as DateFormat[];

  const isOverdue = isExpired(earliestDate, factialEndDate);
  const timeDiff = getTimeDiff(DUE_IN_TEMPLATE, earliestDate, factialEndDate, timezone);

  return {
    timeLeft: isOverdue ? timeDiff.replace(/\s(.*)/, '') : timeDiff,
    dueDate: earliestDate,
    statusTitle: isOverdue ? 'tasks.overdue' : 'tasks.due-in',
    isOverdue,
  };
}
