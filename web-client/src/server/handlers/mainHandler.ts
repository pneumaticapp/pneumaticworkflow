import { Request, Response } from 'express';

import { ERoutes } from '../../public/constants/routes';
import { serverConfigToBrowser } from '../../public/utils/getConfig';
import { getAuthHeader } from '../utils/getAuthHeader';
import { mapAuthProfiles } from '../service/getProfiles';
import { setAuthCookie } from '../utils/cookie';
import { mapToCamelCase } from '../../public/utils/mappers';
import { identifyAppPartOnServer } from '../../public/utils/identifyAppPart/identifyAppPartOnServer';
import { isEnvAnalytics } from '../../public/constants/enviroment';
import { resetCookie } from '../middleware';
import { getPages } from '../middleware/utils/getPages';

export async function mainHandler(req: Request, res: Response) {
  try {
    const appPart = identifyAppPartOnServer(req);
    const env = process.env.MCS_RUN_ENV || 'local';
    const user = (req.res && req.res.locals.user) || {};
    const pages = await getPages();

    // We check the user's authorization via invite or google
    const mapAuth = await mapAuthProfiles(req.url, res, {
      json: true,
      headers: getAuthHeader({ token: req.get('token'), appPart, userAgent: req.headers['user-agent'] }),
    });

    if (!mapAuth) return res;

    // If there is a google token, we will authorize the user and redirect them to the dashboard.
    if (mapAuth.googleAuthUserInfo?.token) {
      setAuthCookie(req, res, { token: mapAuth.googleAuthUserInfo.token });
      return res.redirect(ERoutes.Main);
    }

    return res.render('main', {
      config: JSON.stringify(serverConfigToBrowser()),
      invitedUser: JSON.stringify(mapAuth.invitedUser),
      googleAuthUserInfo: JSON.stringify(mapAuth.googleAuthUserInfo),
      user: JSON.stringify(mapToCamelCase(user)),
      pages: JSON.stringify(pages),
      isBuildAnalytics: !isEnvAnalytics,
      env,
    });
  } catch (err) {
    resetCookie('token', req, res);
    return res.redirect(ERoutes.Login);
  }
}
