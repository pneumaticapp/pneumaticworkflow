export type TFlushableDebouncedFn<T extends unknown[]> = ((...args: T) => void) & {
  cancel: () => void;
  flush: () => void;
};

export function createFlushableDebounce<T extends unknown[]>(
  delay: number,
  callback: (...args: T) => void,
): TFlushableDebouncedFn<T> {
  let pendingArgs: T | null = null;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  const clearPendingTimeout = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  };

  const invokePending = () => {
    const args = pendingArgs;
    pendingArgs = null;
    timeoutId = null;

    if (args) {
      callback(...args);
    }
  };

  const fn = (...args: T) => {
    pendingArgs = args;
    clearPendingTimeout();
    timeoutId = setTimeout(invokePending, delay);
  };

  fn.cancel = () => {
    clearPendingTimeout();
    pendingArgs = null;
  };

  fn.flush = () => {
    if (pendingArgs) {
      clearPendingTimeout();
      invokePending();
    }
  };

  return fn;
}
