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

    it('sends to Sentry with level info when error message is "No error message"', () => {
      logger.error('Request Error:', {});

      expect(mockSetLevel).toHaveBeenCalledWith('info');
      expect(captureException).toHaveBeenCalledTimes(1);
    });

    it('sends to Sentry with level info when error message is empty or only "Error"', () => {
      logger.error(new Error('No error message'));

      expect(mockSetLevel).toHaveBeenCalledWith('info');
      expect(captureException).toHaveBeenCalledTimes(1);
    });

    it('sends to Sentry as error when args are other response error', () => {
      logger.error('Response Error:', { detail: 'Not found.' });

      expect(mockSetLevel).not.toHaveBeenCalled();
      expect(captureException).toHaveBeenCalledTimes(1);
    });

    it('sends to Sentry as error when args contain an Error with meaningful message', () => {
      const err = new Error('Something broke');
      logger.error(err);

      expect(mockSetLevel).not.toHaveBeenCalled();
      expect(captureException).toHaveBeenCalledWith(err);
    });
  });
});
