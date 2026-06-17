import { isExpectedClientError } from '../expectedClientErrors';

describe('isExpectedClientError', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns true for string matching an auth pattern', () => {
    expect(isExpectedClientError('token_not_valid')).toBe(true);
  });

  it('returns true for object containing an auth pattern in a nested field', () => {
    const responseData = { detail: 'Given token not valid for any token type', code: 'token_not_valid' };

    expect(isExpectedClientError(responseData)).toBe(true);
  });

  it('returns true for "Authentication credentials were not provided"', () => {
    expect(isExpectedClientError('Authentication credentials were not provided')).toBe(true);
  });

  it('returns true for "You do not have permission"', () => {
    expect(isExpectedClientError({ detail: 'You do not have permission to perform this action.' })).toBe(true);
  });

  it('returns true for throttled request', () => {
    expect(isExpectedClientError('Request was throttled. Expected available in 30 seconds.')).toBe(true);
  });

  it('returns true for validation error pattern', () => {
    expect(isExpectedClientError({ code: 'validation_error', detail: 'invalid field' })).toBe(true);
  });

  it('returns false for string without any expected pattern', () => {
    expect(isExpectedClientError('Internal Server Error')).toBe(false);
  });

  it('returns false for object without any expected pattern', () => {
    expect(isExpectedClientError({ detail: 'Not found', status: 404 })).toBe(false);
  });
});
