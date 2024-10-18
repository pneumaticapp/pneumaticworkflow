export function get<T>(target: any, path: string, fallback?: T) {
  const pathArr = path.split('.');
  const { length } = pathArr;

  let index = 0;
  let result = { ...target };

  while (result != null && index < length) {
    result = result[pathArr[index]] as INested<T>;
    index += 1;
  }

  return (result || fallback) as unknown as T;
}

export function set<T>(target: INested<T>, path: string, value?: T) {
  if (value === undefined) {
    return;
  }

  const pathArr = path.split('.');
  const { length } = pathArr;

  let index = 0;
  let result = target;

  while (index < length - 1) {
    if (pathArr[index] in result) {
      result = result[pathArr[index]] as INested<T>;
    } else {
      // eslint-disable-next-line no-multi-assign
      result = result[pathArr[index]] = {};
    }

    index += 1;
  }

  result[pathArr[index]] = value;
}

export function isInRange(value: number, min: number, max: number): boolean {
  return value >= min && value <= max;
}

export interface INested<T> {
  [key: string]: T | INested<T>;
}
