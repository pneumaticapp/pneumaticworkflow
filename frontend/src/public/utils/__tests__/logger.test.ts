import * as Sentry from '@sentry/react';
import { logger, MSG_FAILED_FETCH_PUBLIC_FORM } from '../logger';

const mockScope = { setLevel: jest.fn() };

jest.mock('@sentry/react', () => ({
  captureException: jest.fn(),
  withScope: jest.fn((callback: (s: { setLevel: jest.Mock }) => void) => {
    callback(mockScope);
  }),
}));

describe('logger', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('handleSentryLogging', () => {
    it('sends "Failed to fetch public form." to Sentry as info', () => {
      logger.error(MSG_FAILED_FETCH_PUBLIC_FORM);

      expect(Sentry.withScope).toHaveBeenCalledTimes(1);
      expect(mockScope.setLevel).toHaveBeenCalledWith('info');
      expect(Sentry.captureException).toHaveBeenCalledTimes(1);
    });

    it('sends message containing "Failed to fetch public form" to Sentry as info', () => {
      logger.error('Failed to fetch public form.');

      expect(Sentry.withScope).toHaveBeenCalledTimes(1);
      expect(mockScope.setLevel).toHaveBeenCalledWith('info');
      expect(Sentry.captureException).toHaveBeenCalledTimes(1);
    });

    it('sends other errors to Sentry as error (no withScope)', () => {
      logger.error('Other error message');

      expect(Sentry.withScope).not.toHaveBeenCalled();
      expect(Sentry.captureException).toHaveBeenCalledTimes(1);
    });

    it('sends Error instance with other message to Sentry as error', () => {
      logger.error(new Error('Something broke'));

      expect(Sentry.withScope).not.toHaveBeenCalled();
      expect(Sentry.captureException).toHaveBeenCalledTimes(1);
    });
  });
});
