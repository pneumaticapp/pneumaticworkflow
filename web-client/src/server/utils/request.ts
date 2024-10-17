/* eslint-disable no-promise-executor-return */
/* eslint-disable class-methods-use-this */
import * as request from 'request';
import { mergePaths } from '../../public/utils/urls';
import { getConfig } from '../../public/utils/getConfig';
import { PROXY_ALLOWED_ROUTES, PROXY_URL_PREFIX } from '../constants/proxy';
import { isInRange } from './helpers';
import { envBackendPrivateIP } from '../../public/constants/enviroment';

export type TRequestType = 'get' | 'post' | 'patch' | 'put';
type TOptions = Pick<request.CoreOptions, 'body' | 'headers' | 'rejectUnauthorized'>;
type TRequestMethod = (uri: string, options?: TOptions, cb?: Function) => request.Request;

const REQUEST_MAP: { [key in TRequestType]: TRequestMethod } = {
  get: request.get,
  post: request.post,
  patch: request.patch,
  put: request.put,
};

export class HttpRequest {
  public constructor() {
    const {
      api: { privateUrl, urls },
    } = getConfig();
    this.baseUrl = (envBackendPrivateIP && `http://${envBackendPrivateIP}/`) || privateUrl;
    this.urls = urls;
  }

  private readonly baseUrl: string;

  private readonly urls: { [key: string]: string };

  public getUrl = (url: string) => mergePaths(this.baseUrl, url);

  public getProxyPath = (path: string) => mergePaths('', path.replace(new RegExp(`^${PROXY_URL_PREFIX}`), ''));

  public getProxyUrl = (path: string) => this.getUrl(this.getProxyPath(path));

  private makeRequest = (type: TRequestType) => {
    const requestMethod = REQUEST_MAP[type];

    return <T>(uri: string, options?: request.CoreOptions, isPrivate?: boolean, isExternal?: boolean): Promise<T> =>
      new Promise((resolve, reject) => {
        let path = this.urls[uri] || uri;
        if (isPrivate) {
          path = this.getProxyPath(path);
        }
        const url = isExternal ? path : this.getUrl(path);

        return requestMethod(url, options, (error: object | void, response: request.Response, body: object) => {
          if (error || !isInRange(response.statusCode, 200, 299)) {
            reject(body);
          } else {
            resolve(body as unknown as T);
          }
        });
      });
  };

  public get = this.makeRequest('get');

  public post = this.makeRequest('post');

  public patch = this.makeRequest('patch');

  public put = this.makeRequest('put');
}

export const serverApi = new HttpRequest();

export function getPostMessageScript(message: string) {
  return `<script>window.opener.postMessage(${message}, '*');window.close();</script>`;
}

export function isRouteAllowed(url: string): boolean {
  const path = serverApi.getProxyPath(url);

  return PROXY_ALLOWED_ROUTES.some((route) => new RegExp(`^${route}$`).test(path));
}
