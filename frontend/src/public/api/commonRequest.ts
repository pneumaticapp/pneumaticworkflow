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
    if (error.response) {
      logger.error('Response Error:', error.response.data);
    } else if (error.request) {
      logger.error('Request Error:', error.request);
    } else {
      logger.error('Error:', error.message);
    }

    return Promise.reject(Object.assign(new Error(), error.response?.data || {}, { status: error.response?.status }));
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
