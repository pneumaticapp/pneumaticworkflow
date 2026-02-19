/* eslint-disable */
/* tslint:disable:no-any */
import * as Sentry from '@sentry/react';
import { logger } from '../logger';

const mockSetLevel = jest.fn();
jest.mock('@sentry/react', () => ({
  captureException: jest.fn(),
  withScope: jest.fn((cb) => {
    cb({ setLevel: mockSetLevel });
  }),
}));

describe('logger', () => {
  const captureException = Sentry.captureException as jest.Mock;

  beforeEach(() => {
    captureException.mockClear();
    mockSetLevel.mockClear();
  });

  describe('error', () => {
    it('sends to Sentry with level info when args contain auth credentials not provided', () => {
      logger.error('Response Error:', {
        detail: 'Authentication credentials were not provided.',
      });

      expect(mockSetLevel).toHaveBeenCalledWith('info');
      expect(captureException).toHaveBeenCalledTimes(1);
    });

    it('sends to Sentry when args are other response error', () => {
      logger.error('Response Error:', { detail: 'Not found.' });

      expect(captureException).toHaveBeenCalledTimes(1);
    });

    it('sends to Sentry when args contain an Error instance', () => {
      const err = new Error('Something broke');
      logger.error(err);

      expect(captureException).toHaveBeenCalledWith(err);
    });
  });
});
