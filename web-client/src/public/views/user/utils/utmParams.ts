/* eslint-disable */
/* prettier-ignore */
import { getQueryStringParams, history } from '../../../utils/history';
export const UTM_LOCKALSTORAGE_KEY = 'utm';

export interface IUserUtm {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
  gclid?: string;
}

const UTM_PARAMS = [
  'utm_source',
  'utm_medium',
  'utm_campaign',
  'utm_term',
  'utm_content',
  'gclid',
];

export const saveUTMParams = () => {
  const queryString = history.location.search;
  const queryParams = getQueryStringParams(queryString);

  if (!queryParams) {
    return;
  }

  const currentUTMParams: IUserUtm = UTM_PARAMS.reduce((acc, key) => {
    const value = queryParams[key];
    if (!value) {
      return acc;
    }

    return { ...acc, [key]: value };
  }, {});

  if (Object.keys(currentUTMParams).length === 0) {
    return;
  }

  localStorage.setItem(UTM_LOCKALSTORAGE_KEY, JSON.stringify(currentUTMParams));
};

export const getUTMParams = (): IUserUtm => {
  const stringifiedParams = localStorage.getItem(UTM_LOCKALSTORAGE_KEY);

  if (!stringifiedParams) {
    return {};
  }

  const params = JSON.parse(stringifiedParams);

  const utmParams = Object.keys(params).reduce((acc, key) => {
    if (!UTM_PARAMS.includes(key) || !params[key]) {
      return acc;
    }

    return { ...acc, [key]: params[key] };
  }, {});

  return utmParams;
};
