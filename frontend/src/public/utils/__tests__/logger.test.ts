import * as Sentry from '@sentry/react';
import { logger } from '../logger';

jest.mock('@sentry/react', () => ({
  captureException: jest.fn(),
  captureMessage: jest.fn(),
}));

describe('logger', () => {
  const captureException = Sentry.captureException as jest.Mock;
  const captureMessage = Sentry.captureMessage as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('handleSentryLogging', () => {
    it('sends validation_error response to Sentry as info', () => {
      logger.error('Response Error:', {
        code: 'validation_error',
        message: 'A template with "Workflow starter" can not be shared.',
      });

      expect(captureMessage).toHaveBeenCalledTimes(1);
      expect(captureMessage).toHaveBeenCalledWith(
        expect.stringContaining('validation_error'),
        'info',
      );
      expect(captureException).not.toHaveBeenCalled();
    });

    it('sends validationError (camelCase) response to Sentry as info', () => {
      logger.error('Response Error:', { code: 'validationError' });

      expect(captureMessage).toHaveBeenCalledTimes(1);
      expect(captureMessage).toHaveBeenCalledWith(
        expect.any(String),
        'info',
      );
      expect(captureException).not.toHaveBeenCalled();
    });

    it('sends non-validation Response Error to Sentry as exception', () => {
      logger.error('Response Error:', { code: 'server_error' });

      expect(captureMessage).not.toHaveBeenCalled();
      expect(captureException).toHaveBeenCalledTimes(1);
    });

    it('sends generic error to Sentry as exception', () => {
      logger.error('Error:', new Error('fail'));

      expect(captureMessage).not.toHaveBeenCalled();
      expect(captureException).toHaveBeenCalledTimes(1);
    });
  });
});
