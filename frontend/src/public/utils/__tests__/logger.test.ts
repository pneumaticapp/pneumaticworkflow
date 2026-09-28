jest.mock('../sentryCapture', () => ({
  captureException: jest.fn(),
}));

import { logger } from '../logger';
import { captureException } from '../sentryCapture';
import { InterceptorError } from '../../api/InterceptorError';
import { ApiError } from '../../api/commonRequest';

const mockCaptureException = captureException as jest.Mock;

describe('logger', () => {
  const originalConsoleError = console.error;
  const originalConsoleInfo = console.info;

  beforeEach(() => {
    jest.clearAllMocks();
    console.error = jest.fn();
    console.info = jest.fn();
  });

  afterAll(() => {
    console.error = originalConsoleError;
    console.info = originalConsoleInfo;
  });

  describe('logError with expected client errors', () => {
    it('redirects to console.info when args contain an expected error object', () => {
      logger.error('Response Error:', 401, { detail: 'token_not_valid' });

      expect(console.info).toHaveBeenCalledTimes(1);
      expect(console.info).toHaveBeenCalledWith('Response Error:', 401, { detail: 'token_not_valid' });
      expect(console.error).not.toHaveBeenCalled();
      expect(mockCaptureException).not.toHaveBeenCalled();
    });

    it('redirects to console.info when args contain "Authentication credentials were not provided"', () => {
      logger.error({ detail: 'Authentication credentials were not provided' });

      expect(console.info).toHaveBeenCalledTimes(1);
      expect(console.error).not.toHaveBeenCalled();
      expect(mockCaptureException).not.toHaveBeenCalled();
    });

    it('does not redirect non-matching errors to console.info', () => {
      logger.error('Unexpected failure');

      expect(console.error).toHaveBeenCalledTimes(1);
      expect(console.error).toHaveBeenCalledWith('Unexpected failure');
      expect(console.info).not.toHaveBeenCalled();
      expect(mockCaptureException).toHaveBeenCalledTimes(1);
    });
  });

  describe('logError sends to Sentry', () => {
    it('sends Error instance to Sentry via captureException', () => {
      const error = new Error('Something broke');

      logger.error(error);

      expect(mockCaptureException).toHaveBeenCalledTimes(1);
      expect(mockCaptureException).toHaveBeenCalledWith(error);
    });

    it('wraps string args into Error for Sentry when no Error instance is present', () => {
      logger.error('fatal crash');

      expect(mockCaptureException).toHaveBeenCalledTimes(1);
      expect(mockCaptureException).toHaveBeenCalledWith(new Error('fatal crash'));
    });

    it('serializes mixed args into a single Error message for Sentry', () => {
      logger.error('error in', { module: 'auth' });

      expect(mockCaptureException).toHaveBeenCalledTimes(1);
      expect(mockCaptureException).toHaveBeenCalledWith(new Error('error in {"module":"auth"}'));
    });
  });

  describe('logInfo', () => {
    it('logs to console.info without sending to Sentry', () => {
      logger.info('debug message');

      expect(console.info).toHaveBeenCalledTimes(1);
      expect(console.info).toHaveBeenCalledWith('debug message');
      expect(mockCaptureException).not.toHaveBeenCalled();
    });
  });

  describe('logError filters InterceptorError (deduplication)', () => {
    it('does not send InterceptorError to Sentry (already reported by interceptor)', () => {
      const error = new InterceptorError('already logged');

      logger.error(error);

      expect(console.error).toHaveBeenCalledTimes(1);
      expect(console.error).toHaveBeenCalledWith(error);
      expect(mockCaptureException).not.toHaveBeenCalled();
    });

    it('does not send ApiError to Sentry (inherits InterceptorError)', () => {
      const error = new ApiError('', { detail: 'not found' }, 404);

      logger.error(error);

      expect(console.error).toHaveBeenCalledTimes(1);
      expect(console.error).toHaveBeenCalledWith(error);
      expect(mockCaptureException).not.toHaveBeenCalled();
    });

    it('still sends regular Error to Sentry', () => {
      const error = new TypeError('Cannot read properties of undefined');

      logger.error(error);

      expect(mockCaptureException).toHaveBeenCalledTimes(1);
      expect(mockCaptureException).toHaveBeenCalledWith(error);
    });
  });
});
