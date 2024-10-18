import { Request, Response } from 'express';
import { serverApi } from '../utils';
import { getConfig } from '../../public/utils/getConfig';
import { logger } from '../../public/utils/logger';
import { ERoutes } from '../../public/constants/routes';
import { setAuthCookie } from '../utils/cookie';

const {
  api: { urls },
} = getConfig();

export async function oauthMicrosoftHandler(req: Request, res: Response) {
  if (req.query.code) {
    try {
      const { code, client_info: clientInfo, state, session_state: sessionState } = req.query;

      const params = [
        `code=${code}`,
        `client_info=${clientInfo}`,
        `state=${state}`,
        `session_state=${sessionState}`,
      ].join('&');

      const responseDataToken: string = await serverApi.get(`${urls.getMicrosoftAuthToken}?${params}`);
      const tokenResponse: IMicrosoftAuthTokenResponse = JSON.parse(responseDataToken);

      setAuthCookie(req, res, tokenResponse);

      return res.redirect(ERoutes.Main);
    } catch (err) {
      logger.error(err);
    }

    return res.redirect(ERoutes.Register);
  }

  try {
    const responseData: string = await serverApi.get(urls.getMicrosoftAuthUri);
    const { auth_uri: redirectUri }: IMicrosoftAuthURIResponse = JSON.parse(responseData);
    return res.send(JSON.stringify({ redirectUri }));
  } catch(err) {
    logger.error(err);
  }

  return res.redirect(ERoutes.Register);
}

interface IMicrosoftAuthTokenResponse {
  token: string;
}

interface IMicrosoftAuthURIResponse {
  auth_uri: string;
}
