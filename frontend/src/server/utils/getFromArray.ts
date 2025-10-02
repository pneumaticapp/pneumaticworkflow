export function getFromArray<T>(key: keyof T, dataArray: T[] | void | null, fallback: string = '') {
  if (!Array.isArray(dataArray) || !dataArray[0]) {
    return fallback;
  }

  const { [key]: value } = dataArray[0];

  return value ? String(value) : fallback;
}
