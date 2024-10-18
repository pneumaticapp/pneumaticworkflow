export interface IIndexable<T> {
  [key: string]: T[];
}

export const groupBy = <T>(data: T[], key: keyof T): IIndexable<T> => data.reduce((acc, value: T) => {
  const valueKey = String(value[key]);

  return {
    ...acc,
    [valueKey]: (acc[valueKey] || []).concat(value),
  };
}, {} as IIndexable<T>);
