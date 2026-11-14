// Defers every call like a network round trip, so check-then-act races in callers and contracts show up.
export function delayed<T extends object>(target: T): T {
  return new Proxy(target, {
    get(object, property) {
      const value = Reflect.get(object, property) as unknown;
      return typeof value === 'function'
        ? async (...args: unknown[]) => {
            await new Promise((resolve) => setTimeout(resolve, 1));
            return (value as (...parameters: unknown[]) => unknown).apply(object, args);
          }
        : value;
    },
  });
}
