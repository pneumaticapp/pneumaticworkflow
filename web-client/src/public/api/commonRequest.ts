/* eslint-disable @typescript-eslint/no-throw-literal */
// @ts-ignore
import * as merge from 'lodash.merge';

import { logger } from '../utils/logger';
import { ETimeouts } from '../constants/defaultValues';
import { getAuthHeader } from '../../server/utils/getAuthHeader';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapToCamelCase } from '../utils/mappers';
import { mergePaths } from '../utils/urls';
import { promiseTimeout } from '../utils/timeouts';
import { retry } from '../utils/retry';
import { identifyAppPartOnClient } from '../utils/identifyAppPart/identifyAppPartOnClient';
import { getCurrentToken } from '../utils/auth';
import { envBackendURL } from '../constants/enviroment';

const MAX_FETCH_RETRIES = 3;
const getFetchRetryDelay = () => 1000;

const DEFAULT_FETCH_PARAMS: RequestInit = {
  credentials: 'include',
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
  },
};

export type TRequestType = 'public' | 'local';

const DEFAULT_SUCCESS_STATUS_CODES = [200, 201, 204];

type TResponseType = 'json' | 'text' | 'empty';

export interface ICommonRequestOptions {
  type: TRequestType;
  successStatusCodes: number[];
  shouldThrow: boolean;
  timeOut: number;
  responseType: TResponseType;
}

const DEFAULT_OPTIONS: ICommonRequestOptions = {
  type: 'public',
  successStatusCodes: DEFAULT_SUCCESS_STATUS_CODES,
  shouldThrow: false,
  timeOut: ETimeouts.Default,
  responseType: 'json',
};

const fetchWithTimeoutCreator =
  (timeout: number) =>
    (...args: Parameters<typeof fetch>) =>
    promiseTimeout(timeout, fetch(...args)) as Promise<Response>;

export async function commonRequest<T>(
  rawUrl: string,
  params: Partial<RequestInit> = DEFAULT_FETCH_PARAMS,
  options: Partial<ICommonRequestOptions> = DEFAULT_OPTIONS,
) {
  const { type, shouldThrow, successStatusCodes, timeOut } = { ...DEFAULT_OPTIONS, ...options };
  const {
    api: { publicUrl, urls },
  } = getBrowserConfigEnv();

  const fetchWithRetry = retry(fetchWithTimeoutCreator(timeOut), MAX_FETCH_RETRIES, getFetchRetryDelay);

  const requestBaseUrlsMap: { [key in TRequestType]: string } = {
    public: envBackendURL || publicUrl,
    local: '',
  };
  try {
    const url = (urls as { [key in string]: string })[rawUrl] || rawUrl;
    const fetchUrl = mergePaths(requestBaseUrlsMap[type], url);

    const headers = getRequestHeaders();
    const fetchParams = merge({}, DEFAULT_FETCH_PARAMS, { headers }, params);
    const response = await fetchWithRetry(fetchUrl, fetchParams);

    if (!response) {
      throw response;
    }

    let responseBody;

    if (options.responseType !== 'empty' || !response.ok) {
      responseBody = options.responseType === 'text' ? await response.text() : await response.json().catch(() => ({}));
    }

    if (!successStatusCodes.includes(response.status)) {
      throw typeof responseBody === 'object' ? { ...responseBody, status: response.status } : responseBody;
    }

    return options.responseType !== 'text'
      ? (mapToCamelCase(responseBody) as unknown as T)
      : (responseBody as unknown as T);
  } catch (e) {
    if (shouldThrow) {
      throw e;
    }
    logger.error(e);

    return undefined;
  }
}

function getRequestHeaders() {
  const appPart = identifyAppPartOnClient();


  const { userAgent } = window.navigator;
  const token = getCurrentToken();

  return getAuthHeader({ token, appPart, userAgent });
}





