import { Request, Response } from 'express';
import { google } from 'googleapis';
import { getGoogleOauthClient } from '../service/getGoogleOauthClient';
import { ERoutes } from '../../public/constants/routes';
import { logger } from '../../public/utils/logger';
import { serverApi } from '../utils';
import { mapGooglePeopleResponse } from '../mappers';
import { ITokens, setAuthCookie } from '../utils/cookie';
import { mapToSnakeCase } from '../../public/utils/mappers';

interface IGoogleAuthResponse {
  token: string;
}

const scopes = ['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'];

export async function oauthGoogleHandler(req: Request, res: Response) {
  const auth = getGoogleOauthClient();
  if (req.query.code) {
    try {
      const { tokens } = await auth.getToken(req.query.code as string);
      auth.credentials = tokens;
      const people = google.people({
        version: 'v1',
        auth,
      });
      const { data } = await people.people.get({
        resourceName: 'people/me',
        personFields: 'emailAddresses,names,photos,phoneNumbers,organizations',
      });
      const { companyName: company, ...authInfo } = mapGooglePeopleResponse(data);

      const googleAuthUserInfo = { ...authInfo, company };

      try {
        const tokensGoogle = await serverApi.post<ITokens>('googleSignIn', {
          headers: {
            'User-Agent': req.headers['user-agent'],
          },
          body: { email: googleAuthUserInfo.email },
          json: true,
        });

        setAuthCookie(req, res, tokensGoogle);

        return res.redirect(ERoutes.Main);
      } catch (err) {
        logger.error(err);
      }
      const { token } = await serverApi.post<IGoogleAuthResponse>('googleAuth', {
        headers: {
          'User-Agent': req.headers['user-agent'],
        },
        body: mapToSnakeCase({ ...googleAuthUserInfo, fromEmail: false }),
        json: true,
      });

      return res.redirect(`${ERoutes.SignUpGoogle}?token=${token}`);
    } catch (err) {
      logger.error(err);
    }

    return res.redirect(ERoutes.Register);
  }

  const redirectUri = auth.generateAuthUrl({
    access_type: 'offline',
    scope: scopes.join(' '),
  });

  return res.send(JSON.stringify({ redirectUri }));
}
