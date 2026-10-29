import { EHighlightsDateFilter } from '../../../../types/highlights';
import { parseIdsQueryParam, parseTimeRangeQueryParam } from '../highlightsQueryParams';

describe('parseTimeRangeQueryParam', () => {
  it('keeps a known time range', () => {
    expect(parseTimeRangeQueryParam('week')).toBe(EHighlightsDateFilter.Week);
    expect(parseTimeRangeQueryParam('custom')).toBe(EHighlightsDateFilter.Custom);
  });

  it('falls back to Today for an unknown value', () => {
    expect(parseTimeRangeQueryParam('foo')).toBe(EHighlightsDateFilter.Today);
  });
});

describe('parseIdsQueryParam', () => {
  it('parses a comma-separated id list', () => {
    expect(parseIdsQueryParam('1,23,4')).toEqual([1, 23, 4]);
  });

  it('drops values that are not positive integers', () => {
    expect(parseIdsQueryParam('1,abc,,2.5,-3, ,7')).toEqual([1, 7]);
  });

  it('returns an empty list when nothing is valid', () => {
    expect(parseIdsQueryParam('abc')).toEqual([]);
  });
});
