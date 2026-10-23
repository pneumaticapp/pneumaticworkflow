import { Request, Response } from 'express';
import { createProxyMiddleware, fixRequestBody } from 'http-proxy-middleware';

import { logger } from '../../public/utils/logger';
import { isRouteAllowed, serverApi } from '../utils';
import { ERoutes } from '../../public/constants/routes';

export function apiProxy() {
  const proxy = createProxyMiddleware<Request, Response>({
    router: (req) => new URL(serverApi.getProxyUrl(req.originalUrl)).origin,
    pathRewrite: (_path, req) => {
      const parsed = new URL(serverApi.getProxyUrl(req.originalUrl));
      return parsed.pathname + parsed.search;
    },
    changeOrigin: true,
    on: {
      proxyReq: fixRequestBody,
      error: (err, _req, res) => {
        const msg = 'Error on connecting to API.';
        logger.error(msg, err);
        const serverRes = res as Response;
        if (serverRes && !serverRes.headersSent) {
          if (typeof serverRes.status === 'function') {
            serverRes.status(500).send(msg);
          } else if (typeof serverRes.writeHead === 'function') {
            serverRes.writeHead(500, { 'Content-Type': 'text/plain' });
            serverRes.end(msg);
          }
        }
      },
    },
  });

  return (req: Request, res: Response) => {
    if (!isRouteAllowed(req.originalUrl)) {
      return res.redirect(ERoutes.Error);
    }

    return proxy(req, res, () => {});
  };
}
