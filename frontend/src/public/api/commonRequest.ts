import axios, { AxiosInstance, AxiosRequestConfig, AxiosHeaders } from 'axios';
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
import { isExpectedClientError } from '../utils/expectedClientErrors';

import { InterceptorError } from './InterceptorError';
import { createApiError } from './utils/createApiError';

export { InterceptorError };

export type TRequestType = 'public' | 'local' | 'fileService';
export type TResponseType = 'json' | 'text' | 'empty';

export class ApiError extends InterceptorError {
  status?: number;

  data?: unknown;

  [key: string]: unknown;

  constructor(message: string, payload: unknown, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.data = payload;
    this.status = status;
    if (payload && typeof payload === 'object') {
      Object.assign(this, payload);
    }
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

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

    if (config.data instanceof FormData) {
      headers.delete('Content-Type');
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
      const responseData = error.response.data;
      if (isExpectedClientError(responseData)) {
        logger.info('Response Error:', error.response.status, responseData);
      } else {
        logger.error('Response Error:', error.response.status, responseData);
      }
    } else if (error.request) {
      // Don't log error.request (XMLHttpRequest) — contains auth tokens via __sentry_xhr_v3__
      // Don't log error.config.headers — contains Authorization Bearer token
      logger.error('Request Error:', {
        message: error.message,
        code: error.code,
        status: error.status,
        method: error.config?.method,
        url: error.config?.url,
        baseURL: error.config?.baseURL,
        timeout: error.config?.timeout,
      });
    } else {
      logger.error('Error:', error.message);
    }

    return Promise.reject(createApiError(error.response?.data, error.response?.status));
  },
);

let cachedRequestBaseUrlsMap: { [key in TRequestType]: string } | null = null;

export async function commonRequest(
  rawUrl: string,
  params: Partial<AxiosRequestConfig>,
  options: Partial<ICommonRequestOptions> & { responseType: 'empty' },
): Promise<void>;
export async function commonRequest<T>(
  rawUrl: string,
  params?: Partial<AxiosRequestConfig>,
  options?: Partial<ICommonRequestOptions>,
): Promise<T>;

/* eslint-disable consistent-return */
export async function commonRequest<T>(
  rawUrl: string,
  params: Partial<AxiosRequestConfig> = {},
  options: Partial<ICommonRequestOptions> = {},
): Promise<T | void> {
  if (!cachedRequestBaseUrlsMap) {
    const {
      api: { publicUrl, fileServiceUrl },
    } = getBrowserConfigEnv();
    cachedRequestBaseUrlsMap = {
      public: envBackendURL || publicUrl,
      local: '',
      fileService: fileServiceUrl,
    };
  }

  const { type, shouldThrow, successStatusCodes, timeOut } = { ...DEFAULT_OPTIONS, ...options };
  const requestBaseUrlsMap = cachedRequestBaseUrlsMap;

  try {
    const { api: { urls } } = getBrowserConfigEnv();
    const url = (urls as { [key in string]: string })[rawUrl] || rawUrl;
    const fullUrl = mergePaths(requestBaseUrlsMap[type], url);

    const config: AxiosRequestConfig = {
      ...params,
      timeout: timeOut,
      withCredentials: type !== 'fileService',
      responseType: options.responseType === 'text' || options.responseType === 'empty' ? 'text' : 'json',
      validateStatus: (status) => successStatusCodes.includes(status),
    };

    const response = await axiosInstance(fullUrl, config);

    if (options.responseType === 'empty') {
      return;
    }

    return response.data as T;
  } catch (error) {
    if (shouldThrow) {
      throw error;
    }
    if (!(error instanceof InterceptorError)) {
      logger.error(error);
    }
    
  }
}
/* eslint-enable consistent-return */
