import { Request, Response } from 'express';
import { serverApi } from '../utils';
import { logger } from '../../public/utils/logger';
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
  
        const responseDataToken: string = await serverApi.get(`${getAuthTokenUri}?${params}`);
        const tokenResponse: IAuthTokenResponse = JSON.parse(responseDataToken);
  
        setAuthCookie(req, res, tokenResponse);
  
        return res.redirect(ERoutes.Main);
      } catch (err) {
        logger.error(err);
      }
  
      return res.redirect(ERoutes.Register);
    }
  
    try {
      const responseData: string = await serverApi.get(getAuthUri);

      const { auth_uri: redirectUri }: IAuthURIResponse = JSON.parse(responseData);
      return res.send(JSON.stringify({ redirectUri }));
    } catch(err) {
      logger.error(err);
    }
  
    return res.redirect(ERoutes.Register);
  }
}

