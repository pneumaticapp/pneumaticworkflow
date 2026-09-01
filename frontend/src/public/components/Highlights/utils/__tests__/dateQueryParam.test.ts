import { parseDateQueryParam, serializeDateQueryParam } from '../dateQueryParam';
import { getQueryStringByParams, getQueryStringParams } from '../../../../utils/history';

describe('date query params', () => {
  it('round-trips an instant through the query string without losing precision', () => {
    const endOfDay = new Date('2024-11-27T18:59:59.000Z');

    const search = getQueryStringByParams({ 'end-date': serializeDateQueryParam(endOfDay) });
    const restored = parseDateQueryParam(getQueryStringParams(search)['end-date']);

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

  it('still reads the legacy Date.toString() format so existing links keep working', () => {
    const restored = parseDateQueryParam('Wed Nov 27 2024 00:00:00 GMT 0500 (Yekaterinburg Standard Time)');

    expect(restored!.toISOString()).toBe('2024-11-26T19:00:00.000Z');
  });

  it('serializes an absent date to an empty param', () => {
    expect(serializeDateQueryParam(null)).toBe('');
    expect(serializeDateQueryParam(undefined)).toBe('');
  });

  it('returns null for an empty or unparsable param', () => {
    expect(parseDateQueryParam('')).toBeNull();
    expect(parseDateQueryParam('not-a-date')).toBeNull();
  });
});
