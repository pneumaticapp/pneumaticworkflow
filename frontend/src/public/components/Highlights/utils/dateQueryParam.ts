import moment from 'moment';

// Legacy params were `Date.toString()`, whose "GMT+0500" the query parser turns into "GMT 0500".
const LEGACY_GMT_SIGN_PATTERN = /GMT /;
const LEGACY_TIMEZONE_NAME_PATTERN = /\(.*?\)/;

export const serializeDateQueryParam = (date?: Date | null): string => (date ? date.toISOString() : '');

const restoreLegacyParam = (queryParam: string): string =>
  queryParam.replace(LEGACY_TIMEZONE_NAME_PATTERN, '').replace(LEGACY_GMT_SIGN_PATTERN, 'GMT+').trim();

export const parseDateQueryParam = (queryParam: string): Date | null => {
  if (!queryParam.trim()) {
    return null;
  }

  const isoDate = moment.utc(queryParam, moment.ISO_8601, true);

  if (isoDate.isValid()) {
    return isoDate.toDate();
  }

  const legacyDate = new Date(restoreLegacyParam(queryParam));

  return Number.isNaN(legacyDate.getTime()) ? null : legacyDate;
};
