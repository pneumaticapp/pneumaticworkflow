// Legacy params were `Date.toString()`, whose "GMT+0500" the query parser turns into "GMT 0500".
const LEGACY_GMT_SIGN_PATTERN = /GMT /;
const LEGACY_TIMEZONE_NAME_PATTERN = /\(.*?\)/;

export const serializeDateQueryParam = (date?: Date | null): string => (date ? String(date.getTime()) : '');

const restoreLegacyParam = (queryParam: string): string =>
  queryParam.replace(LEGACY_TIMEZONE_NAME_PATTERN, '').replace(LEGACY_GMT_SIGN_PATTERN, 'GMT+').trim();

export const parseDateQueryParam = (queryParam: string): Date | null => {
  if (!queryParam.trim()) {
    return null;
  }

  const timestamp = Number(queryParam);
  const date = Number.isFinite(timestamp) ? new Date(timestamp) : new Date(restoreLegacyParam(queryParam));

  return Number.isNaN(date.getTime()) ? null : date;
};
