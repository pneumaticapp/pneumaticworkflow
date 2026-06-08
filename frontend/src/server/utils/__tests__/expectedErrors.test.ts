import { isExpectedError, logServerError } from '../expectedErrors';
import { logger } from '../../../public/utils/logger';

jest.mock('../../../public/utils/logger', () => ({
  logger: { error: jest.fn(), info: jest.fn() },
}));

describe('isExpectedError', () => {
  it.each([
    ['token_not_valid', '{"code":"token_not_valid","detail":"Given token not valid"}'],
    ['Token is invalid', '{"code":"validation_error","message":"Token is invalid."}'],
    ['Token is expired', '{"code":"validation_error","message":"Token is expired."}'],
    ['Request was throttled', '{"detail":"Request was throttled. Expected available in 5 seconds."}'],
  ])('returns true for known pattern "%s"', (_name, errorMessage) => {
    expect(isExpectedError(errorMessage)).toBe(true);
  });

  it.each([
    ['Server Error (500)', '<h1>Server Error (500)</h1>'],
    ['502 Bad Gateway', '<html><head><title>502 Bad Gateway</title></head></html>'],
    ['Not Found', '<h1>Not Found</h1>'],
    ['undefined', 'undefined'],
    ['random error', 'Something completely unexpected happened'],
  ])('returns false for unknown pattern "%s"', (_name, errorMessage) => {
    expect(isExpectedError(errorMessage)).toBe(false);
  });

  it('returns false for non-string primitives', () => {
    expect(isExpectedError(null)).toBe(false);
    expect(isExpectedError(undefined)).toBe(false);
    expect(isExpectedError(42)).toBe(false);
  });

  it('matches pattern in Error.message', () => {
    expect(isExpectedError(new Error('token_not_valid'))).toBe(true);
  });

  it('matches expected patterns in plain objects (json: true body)', () => {
    expect(isExpectedError({ code: 'token_not_valid', detail: 'Given token not valid' })).toBe(true);
    expect(isExpectedError({ message: 'Token is invalid.' })).toBe(true);
    expect(isExpectedError({ message: 'Token is expired.' })).toBe(true);
    expect(isExpectedError({ detail: 'Request was throttled. Expected available in 5 seconds.' })).toBe(true);
  });

  it('returns false for plain objects without expected patterns', () => {
    expect(isExpectedError({ detail: 'Not found.' })).toBe(false);
    expect(isExpectedError({ error: 'Server Error' })).toBe(false);
    expect(isExpectedError({})).toBe(false);
  });
});

describe('logServerError', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('uses logger.info for expected errors', () => {
    const error = '{"code":"token_not_valid"}';

    logServerError('context: ', error);

    expect(logger.info).toHaveBeenCalledTimes(1);
    expect(logger.info).toHaveBeenCalledWith('context: ', error);
    expect(logger.error).not.toHaveBeenCalled();
  });

  it('uses logger.error for unexpected errors', () => {
    const error = '<h1>Server Error (500)</h1>';

    logServerError('context: ', error);

    expect(logger.error).toHaveBeenCalledTimes(1);
    expect(logger.error).toHaveBeenCalledWith('context: ', error);
    expect(logger.info).not.toHaveBeenCalled();
  });

  it('checks the last argument when multiple args are passed', () => {
    logServerError('prefix: ', '{"message":"Token is expired."}');

    expect(logger.info).toHaveBeenCalledTimes(1);
    expect(logger.error).not.toHaveBeenCalled();
  });

  it('uses logger.info when error is a plain object with expected pattern (json: true)', () => {
    const error = { code: 'token_not_valid', detail: 'Given token not valid' };

    logServerError('failed to get user context: ', error);

    expect(logger.info).toHaveBeenCalledTimes(1);
    expect(logger.info).toHaveBeenCalledWith('failed to get user context: ', error);
    expect(logger.error).not.toHaveBeenCalled();
  });

  it('checks the single argument when only one arg is passed', () => {
    logServerError('{"message":"Token is invalid."}');

    expect(logger.info).toHaveBeenCalledTimes(1);
    expect(logger.error).not.toHaveBeenCalled();
  });
});
