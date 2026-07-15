import { createFlushableDebounce } from '../createFlushableDebounce';

describe('createFlushableDebounce', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('flushes a pending call immediately', () => {
    const callback = jest.fn();
    const debounced = createFlushableDebounce(300, callback);

    debounced('first');
    debounced.flush();

    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('first');
  });

  it('does not invoke callback on flush when nothing is pending', () => {
    const callback = jest.fn();
    const debounced = createFlushableDebounce(300, callback);

    debounced.flush();

    expect(callback).not.toHaveBeenCalled();
  });

  it('cancels a pending call without invoking callback', () => {
    const callback = jest.fn();
    const debounced = createFlushableDebounce(300, callback);

    debounced('pending');
    debounced.cancel();

    jest.advanceTimersByTime(300);

    expect(callback).not.toHaveBeenCalled();
  });

  it('uses the latest arguments when flushed', () => {
    const callback = jest.fn();
    const debounced = createFlushableDebounce(300, callback);

    debounced('first');
    debounced('second');
    debounced.flush();

    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('second');
  });

  it('can schedule another call after flushing', () => {
    const callback = jest.fn();
    const debounced = createFlushableDebounce(300, callback);

    debounced('first');
    debounced.flush();
    debounced('second');
    jest.advanceTimersByTime(300);

    expect(callback).toHaveBeenNthCalledWith(1, 'first');
    expect(callback).toHaveBeenNthCalledWith(2, 'second');
  });

  it('can schedule another call after cancellation', () => {
    const callback = jest.fn();
    const debounced = createFlushableDebounce(300, callback);

    debounced('cancelled');
    debounced.cancel();
    debounced('saved');
    jest.advanceTimersByTime(300);

    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('saved');
  });
});
