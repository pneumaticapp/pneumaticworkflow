import { Request, Response } from 'express';

import { ERoutes } from '../../public/constants/routes';
import { serverConfigToBrowser } from '../../public/utils/getConfig';
import { getAuthHeader } from '../utils/getAuthHeader';
import { getInviteId } from '../service/checkInvite';
import { mapToCamelCase } from '../../public/utils/mappers';
import { identifyAppPartOnServer } from '../../public/utils/identifyAppPart/identifyAppPartOnServer';
import { isEnvAnalytics } from '../../public/constants/enviroment';
import { resetCookie } from '../middleware';
import { getPages } from '../middleware/utils/getPages';
import { readMcpContinuation } from '../utils/mcpSecurity';
import { mcpContinuation } from '../../public/utils/safeRedirect';

export async function mainHandler(req: Request, res: Response) {
  try {
    const appPart = identifyAppPartOnServer(req);
    const env = process.env.MCS_RUN_ENV || 'local';
    const context = (req.res && req.res.locals.user) || {};
    const { token, ...withoutToken } = context;
    const user =
      req.path?.startsWith('/mcp/') || mcpContinuation(req.query?.redirectUrl) || readMcpContinuation(req)
        ? withoutToken
        : context;
    const pages = await getPages();

    const dataToRender = {
      config: JSON.stringify(serverConfigToBrowser()),
      invitedUser: JSON.stringify({}),
      user: JSON.stringify(mapToCamelCase(user)).replace(/</g, '\\u003c'),
      pages: JSON.stringify(pages),
      isBuildAnalytics: !isEnvAnalytics,
      env,
    };

    if (req.url.includes(ERoutes.SignUpInvite)) {
      const inviteInfo = await getInviteId(req.url, res, {
        json: true,
        headers: getAuthHeader({ token: req.get('token'), appPart, userAgent: req.headers['user-agent'] }),
      });

      if (inviteInfo) {
        dataToRender.invitedUser = JSON.stringify(inviteInfo);
      } else {
        return res;
      }
    }

    return res.render('main', dataToRender);
  } catch (err) {
    resetCookie('token', req, res);
    return res.redirect(ERoutes.Login);
  }
}
