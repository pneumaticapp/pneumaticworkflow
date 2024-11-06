import { Request, Response } from 'express';

import { ERoutes } from '../../public/constants/routes';
import { getConfig, serverConfigToBrowser } from '../../public/utils/getConfig';
import { logger } from '../../public/utils/logger';
import { getAuthHeader } from '../utils/getAuthHeader';
import { mapAuthProfiles } from '../service/getProfiles';
import { setAuthCookie } from '../utils/cookie';
import { isObject, mapToCamelCase } from '../../public/utils/mappers';
import { identifyAppPartOnServer } from '../../public/utils/identifyAppPart/identifyAppPartOnServer';
import { serverApi } from '../utils';
import { isEnvAnalytics } from '../../public/constants/enviroment';

const {
  api: { urls },
} = getConfig();

export async function mainHandler(req: Request, res: Response) {

  const {
    url,
    headers: { 'user-agent': reqUserAgent },
  } = req;
  const appPart = identifyAppPartOnServer(req);
  const options = {
    json: true,
    headers: getAuthHeader({ token: req.get('token'), appPart, userAgent: reqUserAgent }),
  };

  let redirect = false;

  const onError = (err: IErrorInvite | Error) => {
    logger.error(err);

    if (isObject(err) && 'code' in err && err.code === EErrorCode.Validation) {
      return res.redirect(ERoutes.ExpiredInvite);
    }

    if (isObject(err) && 'code' in err && err.code === EErrorCode.Accepted) {
      return res.redirect(ERoutes.Main);
    }

    redirect = true;
    return res.redirect(ERoutes.Register);
  };

  const { invitedUser, googleAuthUserInfo } = await mapAuthProfiles(url, onError, options);

  if (redirect) return res;

  let token = '';

  if (googleAuthUserInfo.token) token = googleAuthUserInfo.token;

  if (token) {
    setAuthCookie(req, res, { token });

    return res.redirect(ERoutes.Main);
  }

  const user = (req.res && req.res.locals.user) || {};
  const env = process.env.MCS_RUN_ENV || 'local';

  const pages = await new Promise((resolve) => {
    const localPages = serverApi.get(urls.getPages);
    resolve(localPages);
  }).then((value) => {
    return value;
  }).catch(()=>{
    return `[{}]`;
  })

  return res.render('main', {
    config: JSON.stringify(serverConfigToBrowser()),
    invitedUser: JSON.stringify(invitedUser),
    googleAuthUserInfo: JSON.stringify(googleAuthUserInfo),
    user: JSON.stringify(mapToCamelCase(user)),
    pages: JSON.stringify(pages),
    isBuildAnalytics: !isEnvAnalytics,
    env,
  });
}

interface IErrorInvite {
  code: string;
  message: string;
}

const enum EErrorCode {
  Validation = 'validation_error',
  Accepted = 'invite_already_accepted',
}
