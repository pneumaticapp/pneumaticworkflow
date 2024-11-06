/* eslint-disable */
/* prettier-ignore */
// tslint:disable-next-line: no-any
const isObject = (value: any) => {
  if (!value) {
    return false;
  }

  return typeof value === 'object';
};

// tslint:disable-next-line: no-any
export const insertId = <T extends { [key: string]: any }>(initialObj: T, savedObj: T): T => {
  const EQUALTY_KEYS = ['apiName', 'predicateApiName'];
  const ID_KEYS = ['id', 'predicateId'];

  return Object.keys(savedObj).reduce((acc, key) => {
    const savedValue = savedObj[key];
    const initialValue = acc[key];

    if (Array.isArray(savedValue) && Array.isArray(initialValue)) {
      const newArr = initialValue.map(initialItem => {
        if (!isObject(initialItem)) {
          return initialItem;
        }

        const sameSavedItem = savedValue.find(savedItem => {
          return EQUALTY_KEYS
            .some(equaltyKey => savedItem[equaltyKey] && savedItem[equaltyKey] === initialItem[equaltyKey]);
        });

        if (!sameSavedItem) {
          return initialItem;
        }

        return insertId(initialItem, sameSavedItem);
      });

      return { ...acc, [key]: newArr };
    }

    if (isObject(savedValue) && isObject(initialValue)) {
      return { ...acc, [key]: insertId(initialValue, savedValue) };
    }

    if (ID_KEYS.some(idKey => idKey === key)) {
      return { ...acc, [key]: savedValue };
    }

    return acc;
  }, initialObj);
};
