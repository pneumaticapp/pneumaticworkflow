import * as Sentry from '@sentry/react';
import { logger, DETAIL_NO_PERMISSION } from '../logger';

let mockScope: { setLevel: jest.Mock };
jest.mock('@sentry/react', () => ({
  captureException: jest.fn(),
  withScope: jest.fn((cb: (scope: { setLevel: jest.Mock }) => void) => {
    mockScope = { setLevel: jest.fn() };
    cb(mockScope);
  }),
}));

describe('logger', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('sends permission-denied response as info to Sentry (RA)', () => {
    logger.error('Response Error:', { detail: DETAIL_NO_PERMISSION });

    expect(Sentry.withScope).toHaveBeenCalledTimes(1);
    expect(mockScope.setLevel).toHaveBeenCalledWith('info');
    expect(Sentry.captureException).toHaveBeenCalledTimes(1);
  });

  it('sends other errors as exception without withScope', () => {
    logger.error('Response Error:', { detail: 'Not found.' });

    expect(Sentry.withScope).not.toHaveBeenCalled();
    expect(Sentry.captureException).toHaveBeenCalledTimes(1);
  });
});
