// <reference types="jest" />
import { isUserError, USER_ERROR_STATUSES } from '../isUserError';

describe('isUserError', () => {
  it.each([401, 403, 404])('status %d returns true (user error)', (status) => {
    expect(isUserError(status)).toBe(true);
  });

  it.each([400, 500, 502, 503])('status %d returns false (app/server error)', (status) => {
    expect(isUserError(status)).toBe(false);
  });

  it('USER_ERROR_STATUSES contains only 401, 403, 404', () => {
    expect(USER_ERROR_STATUSES).toEqual([401, 403, 404]);
  });
});
