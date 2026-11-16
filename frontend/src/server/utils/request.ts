import axios, { AxiosRequestConfig } from 'axios';
import * as dotenv from 'dotenv';
import { mergePaths } from '../../public/utils/urls';
import { getConfig } from '../../public/utils/getConfig';
import { PROXY_ALLOWED_ROUTES, PROXY_URL_PREFIX } from '../constants/proxy';
import { ETimeouts } from '../../public/constants/defaultValues';

dotenv.config();

export interface IHttpRequestOptions extends AxiosRequestConfig {
  json?: boolean;
}

export class HttpRequest {
  public constructor() {
    const {
      api: { privateUrl, urls },
    } = getConfig();

    this.baseUrl = privateUrl;
    this.urls = urls;
  }

  private readonly baseUrl: string;

  private readonly urls: { [key: string]: string };

  public getUrl = (url: string) => mergePaths(this.baseUrl, url);

  public getProxyPath = (path: string) => mergePaths('', path.replace(new RegExp(`^${PROXY_URL_PREFIX}`), ''));

  public getProxyUrl = (path: string) => this.getUrl(this.getProxyPath(path));

  public get = async <T>(
    uri: string,
    options?: IHttpRequestOptions,
    isPrivate?: boolean,
    isExternal?: boolean,
  ): Promise<T> => {
    let path = this.urls[uri] || uri;
    if (isPrivate) {
      path = this.getProxyPath(path);
    }
    const url = isExternal ? path : this.getUrl(path);

    try {
      const response = await axios.request<T>({
        ...options,
        method: 'get',
        url,
        timeout: options?.timeout ?? ETimeouts.Default,
      });
      return response.data;
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        throw err.response.data || new Error(`Request failed with status ${err.response.status}`);
      }
      throw err;
    }
  };
}

export const serverApi = new HttpRequest();

export function getPostMessageScript(message: string) {
  return `<script>window.opener.postMessage(${message}, '*');window.close();</script>`;
}

export function isRouteAllowed(url: string): boolean {
  const path = serverApi.getProxyPath(url);

  return PROXY_ALLOWED_ROUTES.some((route) => new RegExp(`^${route}$`).test(path));
}
