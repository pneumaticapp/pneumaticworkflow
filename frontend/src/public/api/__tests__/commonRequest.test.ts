import { isExpectedAuthFailure } from '../commonRequest';

describe('isExpectedAuthFailure', () => {
  it('returns true for 401 with detail "Invalid login or password."', () => {
    expect(
      isExpectedAuthFailure({
        status: 401,
        data: { detail: 'Invalid login or password.' },
      }),
    ).toBe(true);
  });

  it('returns true for 401 with detail starting with "Invalid login or password"', () => {
    expect(
      isExpectedAuthFailure({
        status: 401,
        data: { detail: 'Invalid login or password' },
      }),
    ).toBe(true);
  });

  it('returns false for 401 with other detail', () => {
    expect(
      isExpectedAuthFailure({
        status: 401,
        data: { detail: 'Token is invalid.' },
      }),
    ).toBe(false);
  });

  it('returns false for 403', () => {
    expect(
      isExpectedAuthFailure({
        status: 403,
        data: { detail: 'Invalid login or password.' },
      }),
    ).toBe(false);
  });

  it('returns false when response is undefined', () => {
    expect(isExpectedAuthFailure(undefined)).toBe(false);
  });

  it('returns false when data has no detail', () => {
    expect(isExpectedAuthFailure({ status: 401, data: {} })).toBe(false);
  });
});
