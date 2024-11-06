import { getByRegEx } from '../getByRegEx';

describe('getByRegex', () => {
  it('returns an empty string if no value is provided.', () => {
    const result = getByRegEx(undefined, /\d+/);

    expect(result).toEqual('');
  });
  it('returns the result of applying the regular expression to the string.', () => {
    const result = getByRegEx('10h', /\d+/);

    expect(result).toEqual('10');
  });
  it('returns the provided fallback if nothing was found.', () => {
    const result = getByRegEx('10h', /^\D+/, 'fallback');

    expect(result).toEqual('fallback');
  });
});
