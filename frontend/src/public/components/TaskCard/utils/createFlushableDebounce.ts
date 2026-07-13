import { debounce } from 'throttle-debounce';

export type TFlushableDebouncedFn<T extends unknown[]> = ((...args: T) => void) & {
  cancel: () => void;
  flush: () => void;
};

export function createFlushableDebounce<T extends unknown[]>(
  delay: number,
  callback: (...args: T) => void,
): TFlushableDebouncedFn<T> {
  let pendingArgs: T | null = null;
  const debounced = debounce(delay, (...args: T) => {
    callback(...args);
    pendingArgs = null;
  });

  const fn = (...args: T) => {
    pendingArgs = args;
    debounced(...args);
  };

  fn.cancel = () => {
    pendingArgs = null;
    debounced.cancel();
  };

  fn.flush = () => {
    if (pendingArgs) {
      debounced.cancel();
      callback(...pendingArgs);
      pendingArgs = null;
    }
  };

  return fn;
}
