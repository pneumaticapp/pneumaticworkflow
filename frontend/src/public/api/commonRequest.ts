import axios, { AxiosInstance, AxiosRequestConfig, AxiosHeaders } from 'axios';
import * as Sentry from '@sentry/react';
import { logger } from '../utils/logger';
import { ETimeouts } from '../constants/defaultValues';
import { getAuthHeader } from '../../server/utils/getAuthHeader';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapToCamelCase } from '../utils/mappers';
import { mergePaths } from '../utils/urls';
import { identifyAppPartOnClient } from '../utils/identifyAppPart/identifyAppPartOnClient';
import { getCurrentToken } from '../utils/auth';
import { envBackendURL } from '../constants/enviroment';
import { isRequestCanceled } from '../utils/isRequestCanceled';

const HTTP_STATUS_UNAUTHORIZED = 401;
const EXPECTED_AUTH_FAILURE_DETAIL = 'Invalid login or password.';

export function isExpectedAuthFailure(
  response: { status?: number; data?: { detail?: string } } | undefined,
): boolean {
  if (!response || response.status !== HTTP_STATUS_UNAUTHORIZED) {
    return false;
  }
  const detail = response.data?.detail;
  const expectedPrefix = EXPECTED_AUTH_FAILURE_DETAIL.replace(/\.$/, '');
  return (
    typeof detail === 'string' &&
    (detail === EXPECTED_AUTH_FAILURE_DETAIL ||
      detail.startsWith(expectedPrefix))
  );
}

export type TRequestType = 'public' | 'local';
export type TResponseType = 'json' | 'text' | 'empty';

interface ICommonRequestOptions {
  type: TRequestType;
  successStatusCodes: number[];
  shouldThrow: boolean;
  timeOut: number;
  responseType: TResponseType;
}

const DEFAULT_OPTIONS: ICommonRequestOptions = {
  type: 'public',
  successStatusCodes: [200, 201, 204],
  shouldThrow: false,
  timeOut: ETimeouts.Default,
  responseType: 'json',
};

const axiosInstance: AxiosInstance = axios.create({
  timeout: ETimeouts.Default,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

axiosInstance.interceptors.request.use(
  (config) => {
    const appPart = identifyAppPartOnClient();
    const token = getCurrentToken();
    const authHeaders = getAuthHeader({ token, appPart });
    const headers = new AxiosHeaders();

    Object.entries(authHeaders).forEach(([key, value]) => {
      if (value) {
        headers.set(key, value);
      }
    });

    if (config.headers) {
      Object.entries(config.headers).forEach(([key, value]) => {
        if (value) {
          headers.set(key, value);
        }
      });
    }

    config.headers = headers;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

axiosInstance.interceptors.response.use(
  (response) => {
    if (response.config.responseType === 'json') {
      response.data = mapToCamelCase(response.data);
    }
    return response;
  },

  (error) => {
    if (isRequestCanceled(error)) {
      return Promise.reject(error);
    }

    if (error.response) {
      if (isExpectedAuthFailure(error.response)) {
        console.error('Response Error:', error.response.data);
        Sentry.withScope((scope) => {
          scope.setLevel('info');
          Sentry.captureException(
            new Error(
              `Response Error: ${JSON.stringify(error.response!.data)}`,
            ),
          );
        });
      } else {
        logger.error('Response Error:', error.response.data);
      }
    } else if (error.request) {
      logger.error('Request Error:', error.request);
    } else {
      logger.error('Error:', error.message);
    }

    const data = error.response?.data;
    const payload = typeof data === 'string' ? { error: data } : data ?? {};
    return Promise.reject(Object.assign(new Error(), payload, { status: error.response?.status }));
  },
);

export async function commonRequest<T>(
  rawUrl: string,
  params: Partial<AxiosRequestConfig> = {},
  options: Partial<ICommonRequestOptions> = {},
): Promise<T> {
  const {
    api: { publicUrl, urls },
  } = getBrowserConfigEnv();
  const { type, shouldThrow, successStatusCodes, timeOut } = { ...DEFAULT_OPTIONS, ...options };
  const requestBaseUrlsMap: { [key in TRequestType]: string } = {
    public: envBackendURL || publicUrl,
    local: '',
  };

  try {
    const url = (urls as { [key in string]: string })[rawUrl] || rawUrl;
    const fullUrl = mergePaths(requestBaseUrlsMap[type], url);

    const config: AxiosRequestConfig = {
      ...params,
      timeout: timeOut,
      responseType: options.responseType === 'text' ? 'text' : 'json',
      validateStatus: (status) => successStatusCodes.includes(status),
    };

    const response = await axiosInstance(fullUrl, config);

    if (options.responseType === 'text') {
      return response.data as T;
    }

    return response.data as T;
  } catch (error) {
    if (shouldThrow) {
      throw error;
    }
    logger.error(error);
    return undefined as unknown as T;
  }
}
