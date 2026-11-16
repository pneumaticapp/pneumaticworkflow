import { buildQueryString } from '../buildQueryString';

describe('buildQueryString', () => {
  it('joins arrays with commas and keeps booleans', () => {
    expect(buildQueryString({ status: ['active', 'invited'], is_ai: false })).toBe(
      '?status=active%2Cinvited&is_ai=false',
    );
  });

  it('skips empty, null and undefined values', () => {
    expect(buildQueryString({ type: '', status: [], limit: null, offset: undefined })).toBe('');
  });

  it('keeps zero', () => {
    expect(buildQueryString({ offset: 0 })).toBe('?offset=0');
  });

  it('escapes values', () => {
    expect(buildQueryString({ type: 'user & admin' })).toBe('?type=user+%26+admin');
  });
});
