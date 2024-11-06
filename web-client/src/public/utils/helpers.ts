/* eslint-disable */
/* prettier-ignore */
/* tslint:disable:max-file-line-count */
import { RefObject } from 'react';
import { diff } from 'deep-object-diff';

import { EPayPeriod } from '../types/pricing';
import { TAX_RATES } from '../constants/taxRates';
import { NAVBAR_HEIGHT, MOBILE_NAVBAR_HEIGHT } from '../constants/defaultValues';
const { MOBILE_MAX_WIDTH_BREAKPOINT } = require('../constants/breakpoints');
import { ERoutes } from '../constants/routes';

export const isClient = (): boolean => typeof window !== 'undefined';

export type TGetPluralNounParams = {
  counter: number;
  single: string;
  plural: string;
  includeCounter?: boolean;
};
export function getPluralNoun({ counter, single, plural, includeCounter = false }: TGetPluralNounParams) {
  const correctNoun = counter === 1 ? single : plural;

  return includeCounter ? `${counter} ${correctNoun}` : correctNoun;
}

export function removeFromArrayByKey<T, K extends keyof T>(value: Pick<T, K>, arr: T[], key: K) {
  return arr.filter((v) => v[key] !== value[key]);
}

export function findByKey<T, K extends keyof T>(value: Pick<T, K>, arr: T[], key: K): T | void {
  return arr.find((v) => v[key] === value[key]);
}

export function addValueInArrayByKey<T>(value: T, arr: T[], key: keyof T) {
  return findByKey<T, keyof T>(value, arr, key) ? arr : [...arr, value];
}

export function toggleValueInArray<T>(value: T, arr?: T[], key?: keyof T) {
  if (!arr) {
    return [value];
  } else if (key) {
    return findByKey<T, keyof T>(value, arr, key) ? removeFromArrayByKey<T, keyof T>(value, arr, key) : [...arr, value];
  }

  return arr.includes(value) ? arr.filter((v) => v !== value) : [...arr, value];
}

export type IProgressColorMap = { [breakpoint: number]: string };

export const DEFAULT_MAP_PROGRESS_COLOR: IProgressColorMap = {
  0: '#24d5a1',
  40: '#fec336',
  80: '#fc5b67',
};

export const calculateProgressColor = (percentage: number | undefined, colorMap?: IProgressColorMap) => {
  let cMap = colorMap ? colorMap : DEFAULT_MAP_PROGRESS_COLOR;

  return Object.keys(cMap).reduce((acc, key) => {
    const colorKey = Number(key);
    if (percentage && percentage > colorKey) {
      return cMap[colorKey];
    } else {
      return acc;
    }
  }, cMap[0]);
};

export const calculateAvatarsWidth = (amount: number, max: number, avatarsWidth: number, extraSpace: number) => {
  return amount > max ? max * avatarsWidth + extraSpace : amount * avatarsWidth;
};

export function isArrayWithItems<T>(items?: T[] | null): items is T[] {
  return Array.isArray(items) && items.length > 0;
}

export function isArrayItemsNonEmpty<T>(items?: T[] | null): items is T[] {
  if (!isArrayWithItems(items)) {
    return false;
  }

  return Boolean(items.filter((x) => x).length);
}

// tslint:disable-next-line: no-any
export function isEmptyArray(items: any) {
  return Array.isArray(items) && items.length === 0;
}

export const getPercent = (value: number, limit: number) => Math.round((value / limit) * 100);

export const getRegionTax = (region: string) => {
  if (TAX_RATES[region]) {
    return TAX_RATES[region];
  }

  return 0;
};

export const calculateSummaryTax = (cost: number, discountPercent: number, region: string, payType: EPayPeriod) => {
  const period = payType === EPayPeriod.Annually ? 12 : 1;
  const taxValue = getRegionTax(region);
  const discountValue = (cost * discountPercent) / 100;

  if (discountPercent > 0) {
    return Number(((cost - discountValue) * period * taxValue) / 100);
  }

  return Number((cost * period * taxValue) / 100);
};

export const calculateSummaryTotal = ({
  cost,
  discountPercent,
  region,
  payType,
}: {
  cost: number;
  discountPercent: number;
  region: string;
  payType: EPayPeriod;
}) => {
  const tax = calculateSummaryTax(cost, discountPercent, region, payType);
  const period = payType === EPayPeriod.Annually ? 12 : 1;
  const discountValue = (cost * discountPercent) / 100;

  if (discountPercent > 0) {
    return Number((cost - discountValue) * period + tax);
  }

  return Number(cost * period + tax);
};

export const isLessEqualThanUserLimit = (users: number, currentUsersLimit: number, isSubscribed: boolean) => {
  if (isSubscribed) {
    return users < currentUsersLimit;
  }

  return false;
};

export const connectGoogle = async () => {
  const windowParams = 'width=620,height=620,resizable,scrollbars=yes,status=1';
  window.open(ERoutes.InvitesGoogle, undefined, windowParams);
};

export function findAncestor(el: Element, className: string) {
  let parent: Element | null = el;
  while (parent && !parent.classList.contains(className)) {
    parent = parent.parentElement;
  }

  return parent === el ? null : parent;
}

export const isObjectEmpty = (o?: object | null) => !Boolean(Object.keys(o || {}).length);
export const isObjectChanged = (initialObject: object, newObject: object) => {
  return !isObjectEmpty(diff(initialObject, newObject));
};

export const copyToClipboard = (str: string) => {
  const el = document.createElement('textarea');
  el.value = str;
  document.body.appendChild(el);
  el.select();
  document.execCommand('copy');
  document.body.removeChild(el);
};

export const deepCopy = <T>(o: T) => JSON.parse(JSON.stringify(o)) as T;

export const scrollToTop = () => {
  window.scroll({ top: 0, behavior: 'smooth' });
};

export const convertEnumToObject = (e: object): { [key: string]: string } => {
  return Object(e);
};

export const zip = <T, G>(array1: T[], array2: G[]) => {
  return array1.map((array1Value, array1Index) => [array1Value, array2[array1Index]] as const);
};

// tslint:disable-next-line: no-any
export function flatten(arr: any[]) {
  return [].concat(...arr);
}

export const isEllipsisActive = (e: RefObject<HTMLElement>) => {
  if (!e.current) {
    return false;
  }

  return e.current.offsetWidth < e.current.scrollWidth;
};

export const getTruncatedText = (source: string, size = 50) => {
  if (!source) {
    return null;
  }

  if (!source.length) {
    return source;
  }

  return source.length > size ? `${source.slice(0, size - 1)}…` : source;
};

// tslint:disable-next-line: no-any
export const getPairedArrayItems = (arr: any[]) => arr.slice(1).map((item, index) => [arr[index], item]);

export const scrollToElement = (
  element: HTMLElement,
  delay: number | null = null,
  behavior: 'auto' | 'smooth' = 'smooth',
) => {
  window.requestAnimationFrame(() => {
    const elementTopOffset = window.innerWidth > MOBILE_MAX_WIDTH_BREAKPOINT ? NAVBAR_HEIGHT : MOBILE_NAVBAR_HEIGHT;

    let offset = element.offsetTop - elementTopOffset;

    try {
      let bodyRect = document.body.getBoundingClientRect();
      let bodyStyle = window.getComputedStyle(document.body, null);

      // need to handle the padding for the top of the body
      let paddingTop = parseFloat(bodyStyle.getPropertyValue('padding-top'));

      let elementRect = element.getBoundingClientRect();
      offset = elementRect.top - paddingTop - bodyRect.top - elementTopOffset;
    } catch (err) {
      element.scrollIntoView({ behavior });

      return;
    }

    if (delay) {
      setTimeout(() => {
        window.scrollTo({ top: offset, left: 0, behavior });
      }, delay);
    } else {
      window.scrollTo({ top: offset, left: 0, behavior });
    }
  });
};

export const omit = <T, U extends keyof T>(obj: T, keys: U[]): Omit<T, U> => {
  return (Object.keys(obj as {}) as U[]).reduce(
    (acc, currentKey) => (keys.includes(currentKey) ? acc : { ...acc, [currentKey]: obj[currentKey] }),
    {} as Omit<T, U>,
  );
};

// export const omit = <T, U extends keyof T>(obj: T, keys: U[]): Omit<T, U> =>
//   (Object.keys(obj) as U[]).reduce(
//     (acc, curr) => (keys.includes(curr) ? acc : { ...acc, [curr]: obj[curr] }),
//     {} as Omit<T, U>,
//   );

// export const omit = (key: any, obj: any) => {
//   const { [key]: omitted, ...rest } = obj;
//   return rest;
// }

export const areObjectsEqual = (originalObj: object, updatedObj: object): boolean => {
  const diffProps = diff(originalObj, updatedObj);

  return isObjectEmpty(diffProps);
};
