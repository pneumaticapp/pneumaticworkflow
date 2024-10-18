export function promiseTimeout<T>(ms: number, promise: T) {
  const timeout = new Promise((resolve, reject) => {
    const id = setTimeout(() => {
      clearTimeout(id);
      reject(new Error(`Timed out in ${ms} ms.`));
    }, ms);
  });

  return Promise.race([
    promise,
    timeout,
  ]);
}
