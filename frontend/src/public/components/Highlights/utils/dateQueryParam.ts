/**
 * Highlights keeps its date filters in the query string.
 *
 * They used to be serialized with `Date.prototype.toString()`, which loses milliseconds and whose
 * `GMT+0500` suffix is decoded back as `GMT 0500`, because `getQueryStringByParams` does not encode
 * its values and `getQueryStringParams` turns `+` into a space. A reload therefore returned a
 * different instant than the one that was picked. Timestamps round-trip exactly and need no escaping.
 */

const LEGACY_GMT_SIGN_PATTERN = /GMT /;
const LEGACY_TIMEZONE_NAME_PATTERN = /\(.*?\)/;

export const serializeDateQueryParam = (date?: Date | null): string =>
  date ? String(date.getTime()) : '';

const restoreLegacyParam = (queryParam: string): string =>
  queryParam.replace(LEGACY_TIMEZONE_NAME_PATTERN, '').replace(LEGACY_GMT_SIGN_PATTERN, 'GMT+').trim();

/** Accepts the current timestamp format and the legacy `Date.toString()` one, so old links still open. */
export const parseDateQueryParam = (queryParam: string): Date | null => {
  if (!queryParam) {
    return null;
  }

  const timestamp = Number(queryParam);
  const date = Number.isFinite(timestamp) ? new Date(timestamp) : new Date(restoreLegacyParam(queryParam));

  return Number.isNaN(date.getTime()) ? null : date;
};
