import { parseDateQueryParam, serializeDateQueryParam } from '../dateQueryParam';
import { getQueryStringByParams, getQueryStringParams } from '../../../../utils/history';

describe('date query params', () => {
  it('serializes a date as an ISO 8601 UTC string', () => {
    expect(serializeDateQueryParam(new Date('2024-11-27T18:59:59.000Z'))).toBe('2024-11-27T18:59:59.000Z');
  });

  it('round-trips an instant through the query string without losing precision', () => {
    const endOfDay = new Date('2024-11-27T18:59:59.000Z');

    const search = getQueryStringByParams({ 'end-date': serializeDateQueryParam(endOfDay) });
    const restored = parseDateQueryParam(getQueryStringParams(search)['end-date']);

    expect(search).toBe('?end-date=2024-11-27T18:59:59.000Z');
    expect(restored!.toISOString()).toBe(endOfDay.toISOString());
  });

  it('survives the query string turning "+" into a space, which broke the old text format', () => {
    const date = new Date('2024-11-26T19:00:00.000Z');
    const legacyParam = 'Wed Nov 27 2024 00:00:00 GMT+0500 (Yekaterinburg Standard Time)';

    const legacySearch = getQueryStringByParams({ 'start-date': legacyParam });
    const decodedLegacyParam = getQueryStringParams(legacySearch)['start-date'];

    expect(decodedLegacyParam).toContain('GMT 0500');
    expect(parseDateQueryParam(serializeDateQueryParam(date))!.toISOString()).toBe(date.toISOString());
  });

  it('accepts an ISO string with an explicit offset', () => {
    expect(parseDateQueryParam('2024-11-27T00:00:00+05:00')!.toISOString()).toBe('2024-11-26T19:00:00.000Z');
  });

  it('still reads the legacy Date.toString() format so existing links keep working', () => {
    const restored = parseDateQueryParam('Wed Nov 27 2024 00:00:00 GMT 0500 (Yekaterinburg Standard Time)');

    expect(restored!.toISOString()).toBe('2024-11-26T19:00:00.000Z');
  });

  it('serializes an absent date to an empty param', () => {
    expect(serializeDateQueryParam(null)).toBe('');
    expect(serializeDateQueryParam(undefined)).toBe('');
  });

  it('returns null for an empty, whitespace-only, numeric or unparsable param', () => {
    expect(parseDateQueryParam('')).toBeNull();
    expect(parseDateQueryParam(' ')).toBeNull();
    expect(parseDateQueryParam('1732647600000')).toBeNull();
    expect(parseDateQueryParam('not-a-date')).toBeNull();
  });
});
