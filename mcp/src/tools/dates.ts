import { ConnectorError } from '../core/errors.js';

export function toTimestamp(value: string | number): number {
  const invalidDate = () =>
    new ConnectorError('invalid_arguments', `Invalid date-time "${value}". Use ISO 8601, e.g. 2026-10-15T09:00:00Z`);
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) {
      throw invalidDate();
    }
    return Math.abs(value) >= 1e12 ? value / 1000 : value;
  }

  const trimmed = value.trim();
  if (/^-?\d+(\.\d+)?$/.test(trimmed)) {
    return toTimestamp(Number(trimmed));
  }
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(trimmed)) {
    throw invalidDate();
  }
  const year = Number(trimmed.slice(0, 4));
  const month = Number(trimmed.slice(5, 7));
  const day = Number(trimmed.slice(8, 10));
  const isLeapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [31, isLeapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1];
  if (!daysInMonth || day < 1 || day > daysInMonth) {
    throw invalidDate();
  }
  const parsed = Date.parse(trimmed);
  if (!Number.isFinite(parsed)) {
    throw invalidDate();
  }
  return parsed / 1000;
}

export function optionalTimestamp(value: string | number | null | undefined): number | null | undefined {
  return value === undefined || value === null ? value : toTimestamp(value);
}

export function periodQuery(
  dateFrom: string | number | undefined,
  dateTo: string | number | undefined,
  currentOnly: boolean,
) {
  if (currentOnly) {
    return { now: true };
  }
  return { date_from_tsp: optionalTimestamp(dateFrom), date_to_tsp: optionalTimestamp(dateTo) };
}
