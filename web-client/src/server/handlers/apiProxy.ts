import { Request, Response } from 'express';
import * as request from 'request';

import { logger } from '../../public/utils/logger';
import { isRouteAllowed, serverApi } from '../utils';
import { ERoutes } from '../../public/constants/routes';

export type TRequestType = 'get' | 'post' | 'patch' | 'delete';
type TOptions = Pick<request.CoreOptions, 'body' | 'headers' | 'rejectUnauthorized' | 'json'>;
type TRequestMethod = (uri: string, options?: TOptions) => request.Request;

const REQUEST_MAP: { [key in TRequestType]: TRequestMethod } = {
  get: request.get,
  post: request.post,
  patch: request.patch,
  delete: request.delete,
};

export function apiProxy(type: TRequestType) {
  const requestMethod = REQUEST_MAP[type];

  return (req: Request, res: Response) => {
    const { body, originalUrl } = req;

    if (!isRouteAllowed(originalUrl)) {
      return res.redirect(ERoutes.Error);
    }

    const url = serverApi.getProxyUrl(originalUrl);

    const headers = {
      ...req.headers,
      Host: new URL(url).hostname,
      'Content-Type': 'application/json',
    };

    const result: request.Request = requestMethod(url, { body, headers, rejectUnauthorized: false, json: true });

    return result
      .on('error', (err) => {
        const msg = 'Error on connecting to API.';
        logger.error(msg, err);
        res.status(500).send(msg);
      })
      .pipe(res);
  };
}
