import { Request, Response } from 'express';
import { serverApi } from '../utils';
import { logServerError } from '../utils/expectedErrors';
import { ERoutes } from '../../public/constants/routes';
import { setAuthCookie } from '../utils/cookie';
import { mcpContinuation } from '../../public/utils/safeRedirect';
import { consumeMcpOAuth, mcpPrivacy, readMcpContinuation, rememberMcpOAuth } from '../utils/mcpSecurity';

interface IAuthURIResponse {
  auth_uri: string;
}

interface IAuthTokenResponse {
  token: string;
}

export function oAuthHandler(getAuthUri: string, getAuthTokenUri: string) {
  return async function oauthMicrosoftHandler(req: Request, res: Response) {
    const continuation = mcpContinuation(req.query.redirectUrl) || readMcpContinuation(req);
    if (continuation) mcpPrivacy(res);
    if (req.query.code !== undefined || req.query.error !== undefined) {
      const target = consumeMcpOAuth(req, res, getAuthUri);
      if (target !== undefined) mcpPrivacy(res);
      if (target === '' || (continuation && target === undefined))
        return res.status(400).send('Invalid sign-in request');
      // Provider callbacks use the OAuth query contract, never a business body.
      if (req.query.error !== undefined) {
        return res.redirect(target ? `${ERoutes.Login}?redirectUrl=${encodeURIComponent(target)}` : ERoutes.Login);
      }
      if (typeof req.query.code !== 'string' || !req.query.code) return res.status(400).send('Invalid sign-in request');
      try {
        const { code, client_info: clientInfo, state, session_state: sessionState } = req.query;

        const params = [
          `code=${encodeURIComponent(String(code))}`,
          `client_info=${encodeURIComponent(String(clientInfo))}`,
          `state=${encodeURIComponent(String(state))}`,
          `session_state=${encodeURIComponent(String(sessionState))}`,
        ].join('&');

        const responseDataToken: string = await serverApi.get(`${getAuthTokenUri}?${params}`);
        const tokenResponse: IAuthTokenResponse = JSON.parse(responseDataToken);
        if (target && (typeof tokenResponse.token !== 'string' || !tokenResponse.token)) {
          return res.status(502).send('Sign-in unavailable');
        }

        setAuthCookie(req, res, tokenResponse);

        return res.redirect(target || ERoutes.Main);
      } catch (error) {
        if (!continuation && target === undefined) logServerError(error);
      }

      return res.redirect(target ? `${ERoutes.Login}?redirectUrl=${encodeURIComponent(target)}` : ERoutes.Register);
    }

    try {
      const responseData: string = await serverApi.get(getAuthUri);

      const { auth_uri: redirectUri }: IAuthURIResponse = JSON.parse(responseData);
      if (continuation) rememberMcpOAuth(res, continuation, redirectUri, getAuthUri);
      return res.send(JSON.stringify({ redirectUri }));
    } catch (error) {
      if (!continuation) logServerError(error);
    }

    return res.redirect(ERoutes.Register);
  };
}
