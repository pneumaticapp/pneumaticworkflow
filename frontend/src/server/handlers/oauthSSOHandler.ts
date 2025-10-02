import { Request, Response } from 'express';
import { serverApi } from '../utils';
import { getConfig } from '../../public/utils/getConfig';
import { logger } from '../../public/utils/logger';
import { ERoutes } from '../../public/constants/routes';
import { setAuthCookie } from '../utils/cookie';

const {
  api: { urls },
} = getConfig();

export async function oauthSSOHandler(req: Request, res: Response) {
  if (req.query.code) {
    try {
      const { code, state } = req.query;
      const params = [`code=${code}`, `state=${state}`].join('&');
      const responseDataToken: string = await serverApi.get(`${urls.getSSOAuthToken}?${params}`);
      const tokenResponse: ISSOAuthTokenResponse = JSON.parse(responseDataToken);

      setAuthCookie(req, res, tokenResponse);

      return res.redirect(ERoutes.Main);
    } catch (err) {
      logger.error(err);
    }

    return res.redirect(ERoutes.Register);
  }

  try {
    const responseData: string = await serverApi.get(urls.getSSOAuthUri);
    const { auth_uri: redirectUri }: ISSOAuthURIResponse = JSON.parse(responseData);
    return res.send(JSON.stringify({ redirectUri }));
  } catch (err) {
    logger.error(err);
  }

  return res.redirect(ERoutes.Register);
}

interface ISSOAuthTokenResponse {
  token: string;
}

interface ISSOAuthURIResponse {
  auth_uri: string;
}
