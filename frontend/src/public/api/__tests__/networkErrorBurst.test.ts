const mockSetExtra = jest.fn();
jest.mock('@sentry/react', () => ({
  withScope: (callback: (scope: { setExtra: jest.Mock }) => void) => {
    callback({ setExtra: mockSetExtra });
  },
}));

const mockLoggerError = jest.fn();
jest.mock('../../utils/logger', () => ({
  logger: {
    error: (...args: unknown[]) => mockLoggerError(...args),
    info: jest.fn(),
  },
}));

import { bufferNetworkError, flushNetworkErrors, resetNetworkErrorBuffer } from '../networkErrorBuffer';

describe('ERR_NETWORK deduplication (networkErrorBuffer)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    resetNetworkErrorBuffer();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('single ERR_NETWORK is buffered and flushed after 5s as one logger.error with extras', () => {
    bufferNetworkError({ method: 'get', url: '/test-endpoint' });

    expect(mockLoggerError).not.toHaveBeenCalled();

    jest.advanceTimersByTime(5000);

    expect(mockLoggerError).toHaveBeenCalledTimes(1);
    expect(mockLoggerError).toHaveBeenCalledWith('Network Error Burst: 1 request failed');
    expect(mockSetExtra).toHaveBeenCalledWith('count', 1);
    expect(mockSetExtra).toHaveBeenCalledWith('requests', [{ method: 'get', url: '/test-endpoint' }]);
  });

  it('5 simultaneous ERR_NETWORK errors produce one logger.error with count:5 and all URLs in extras', () => {
    const urls = ['/url-1', '/url-2', '/url-3', '/url-4', '/url-5'];
    urls.forEach((url) => bufferNetworkError({ method: 'get', url }));

    expect(mockLoggerError).not.toHaveBeenCalled();

    jest.advanceTimersByTime(5000);

    expect(mockLoggerError).toHaveBeenCalledTimes(1);
    expect(mockLoggerError).toHaveBeenCalledWith('Network Error Burst: 5 requests failed');
    expect(mockSetExtra).toHaveBeenCalledWith('count', 5);
    expect(mockSetExtra).toHaveBeenCalledWith(
      'requests',
      urls.map((url) => ({ method: 'get', url })),
    );
  });

  it('debounce resets timer on each new ERR_NETWORK, flush happens 5s after the last one', () => {
    bufferNetworkError({ method: 'get', url: '/first' });

    jest.advanceTimersByTime(3000);
    bufferNetworkError({ method: 'get', url: '/second' });

    jest.advanceTimersByTime(2000);
    expect(mockLoggerError).not.toHaveBeenCalled();

    jest.advanceTimersByTime(3000);
    expect(mockLoggerError).toHaveBeenCalledTimes(1);
    expect(mockSetExtra).toHaveBeenCalledWith('requests', [
      { method: 'get', url: '/first' },
      { method: 'get', url: '/second' },
    ]);
  });

  it('flushNetworkErrors on empty buffer does not call logger.error', () => {
    flushNetworkErrors();

    expect(mockLoggerError).not.toHaveBeenCalled();
  });

  it('maxWait forces flush after 30s even if ERR_NETWORK keeps arriving', () => {
    for (let i = 0; i < 11; i++) {
      bufferNetworkError({ method: 'get', url: `/poll-${i}` });
      jest.advanceTimersByTime(3000);
    }

    expect(mockLoggerError).toHaveBeenCalledTimes(1);
    expect(mockSetExtra).toHaveBeenCalledWith('count', 11);

    mockLoggerError.mockClear();
    mockSetExtra.mockClear();
    bufferNetworkError({ method: 'get', url: '/after-flush' });

    jest.advanceTimersByTime(5000);
    expect(mockLoggerError).toHaveBeenCalledTimes(1);
    expect(mockSetExtra).toHaveBeenCalledWith('count', 1);
  });
});
