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

  const fn = (...args: T) => {
    pendingArgs = args;
    clearPendingTimeout();
    timeoutId = setTimeout(() => {
      if (pendingArgs) {
        callback(...pendingArgs);
        pendingArgs = null;
      }
      timeoutId = null;
    }, delay);
  };

  fn.cancel = () => {
    clearPendingTimeout();
    pendingArgs = null;
  };

  fn.flush = () => {
    if (pendingArgs) {
      clearPendingTimeout();
      callback(...pendingArgs);
      pendingArgs = null;
    }
  };

  return fn;
}
