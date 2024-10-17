/* eslint-disable */
/* prettier-ignore */
type AnyFn = (...args: any[]) => any;
type Awaited<T> = T extends PromiseLike<infer U> ? U : T;
type DelayFn = (retry: number) => number;
type CheckShouldRetryFn = (error: Error) => boolean;

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function retry<Fn extends AnyFn>(
  fn: Fn,
  maxRetries: number,
  getDelay: DelayFn = () => 5000,
  checkShouldRetry: CheckShouldRetryFn = () => true,
) {
  let retries = 0;

  return async function wrapped(...args: Parameters<Fn>): Promise<Awaited<ReturnType<Fn>>> {
    try {
      return await fn(...args);
    } catch (error) {
      retries = retries + 1;
      if (retries > maxRetries || !checkShouldRetry(error)) {
        throw error;
      }

      console.error(error);

      const delayTime = getDelay(retries);
      await delay(delayTime);

      return wrapped(...args);
    }
  };
}
