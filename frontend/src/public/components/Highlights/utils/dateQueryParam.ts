import moment from 'moment';

const LEGACY_GMT_PLUS_DECODED_AS_SPACE_PATTERN = /GMT /;
const LEGACY_TIMEZONE_NAME_PATTERN = /\(.*?\)/;

export const serializeDateQueryParam = (date?: Date | null): string => (date ? date.toISOString() : '');

const restoreLegacyParam = (queryParam: string): string =>
  queryParam.replace(LEGACY_TIMEZONE_NAME_PATTERN, '').replace(LEGACY_GMT_PLUS_DECODED_AS_SPACE_PATTERN, 'GMT+').trim();

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
