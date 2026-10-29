import { Request, Response } from 'express';
import { serverApi } from '../utils';
import { logServerError } from '../utils/expectedErrors';
import { ERoutes } from '../../public/constants/routes';
import { setAuthCookie } from '../utils/cookie';

interface IAuthURIResponse {
  auth_uri: string;
}

interface IAuthTokenResponse {
  token: string;
}

export function oAuthHandler(getAuthUri: string, getAuthTokenUri: string) {
  return async function oauthMicrosoftHandler(req: Request, res: Response) {
    if (req.query.code) {
      try {
        const { code, client_info: clientInfo, state, session_state: sessionState } = req.query;

        const params = [
          `code=${code}`,
          `client_info=${clientInfo}`,
          `state=${state}`,
          `session_state=${sessionState}`,
        ].join('&');

        const tokenResponse = await serverApi.get<IAuthTokenResponse>(`${getAuthTokenUri}?${params}`);

        setAuthCookie(req, res, tokenResponse);

        return res.redirect(ERoutes.Main);
      } catch (error) {
        logServerError(error);
      }

      return res.redirect(ERoutes.Register);
    }

    try {
      const { auth_uri: redirectUri } = await serverApi.get<IAuthURIResponse>(getAuthUri);
      return res.send(JSON.stringify({ redirectUri }));
    } catch (error) {
      logServerError(error);
    }

    return res.redirect(ERoutes.Register);
  };
}
