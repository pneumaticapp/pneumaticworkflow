import { NextFunction, Request, Response } from 'express';

import { ERoutes } from '../../public/constants/routes';
import { parseCookies } from '../../public/utils/cookie';
import { setAuthCookie, setGuestCookie } from '../utils/cookie';
import { identifyAppPartOnServer } from '../../public/utils/identifyAppPart/identifyAppPartOnServer';
import { EAppPart } from '../../public/utils/identifyAppPart/types';
import { getUser } from './utils/getUser';
import { IAuthenticatedUser } from '../utils/types';
import { isEnvBilling } from '../../public/constants/enviroment';

const UNSIGNED_USER_ROUTES = [
  ERoutes.Login,
  ERoutes.Register,
  ERoutes.ForgotPassword,
  ERoutes.ResetPassword,
  ERoutes.AccountVerification,
  ERoutes.AccountVerificationLink,
  ERoutes.ExpiredInvite,
];

const PAYMENT_ROUTES = [ERoutes.CollectPaymentDetails, ERoutes.AfterPaymentDetailsProvided];

const EXCLUDED_ROUTES = ['/assets/', '/static/', ERoutes.Iframes];

export async function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const appPart = identifyAppPartOnServer(req);

  if (appPart === EAppPart.GuestTaskApp) {
    return handleGuestAuth(req, res, next);
  }

  const isRouteNotAllowed = EXCLUDED_ROUTES.some((route) => req.url.includes(route));
  if (isRouteNotAllowed) {
    return next();
  }

  const { mobile_app_token: mobileAppToken } = req.query || '';
  const token = (mobileAppToken as string) || parseCookies(req.get('cookie')).token;

  if (mobileAppToken) {
    setAuthCookie(req, res, { token: req.query.mobile_app_token as string });
  }

  const isUnsignedUserRoute = UNSIGNED_USER_ROUTES.some((route) => req.url.includes(route));
  const isPaymentDetailsRoute = PAYMENT_ROUTES.some((route) => req.url.includes(route));

  if (!token) {
    return isUnsignedUserRoute ? next() : res.redirect(getLoginUrl(req));
  }

  try {
    const user = await getUser(req, token, req.headers['user-agent']);
    res.locals.user = { ...user, token };
    const paymentDetailsProvided = user.account.payment_card_provided;

    if (isEnvBilling && !paymentDetailsProvided) {
      return isUnsignedUserRoute || isPaymentDetailsRoute ? next() : res.redirect(ERoutes.CollectPaymentDetails);
    }

    return isUnsignedUserRoute ? redirectToUserDefaulRoute(user, res) : next();
  } catch (err) {
    resetCookie('token', req, res);

    res.locals.user = { token };

    return isUnsignedUserRoute ? next() : res.redirect(ERoutes.Login);
  }
}

function redirectToUserDefaulRoute(user: IAuthenticatedUser, res: Response) {
  if (user.is_account_owner) {
    return res.redirect(ERoutes.Main);
  }

  return res.redirect(ERoutes.Tasks);
}

function getLoginUrl(req: Request) {
  const shouldRedirectAfterLogin = req.url !== '/';
  const redirectQuery = shouldRedirectAfterLogin ? `?redirectUrl=${encodeURIComponent(req.url)}` : '';
  const redirectUrl = `${ERoutes.Login}${redirectQuery}`;

  return redirectUrl;
}

async function handleGuestAuth(req: Request, res: Response, next: NextFunction) {
  const { token } = req.query;
  if (!token) {
    return res.redirect(ERoutes.Error);
  }

  try {
    const user = await getUser(req, token as string);
    setGuestCookie(req, res, token as string);
    res.locals.user = user;

    return next();
  } catch (error) {
    resetCookie('guest-token', req, res);

    return res.redirect(ERoutes.Error);
  }
}

export function resetCookie(key: string, req: Request, res: Response) {
  res.cookie(key, '', { domain: req.hostname, maxAge: 0, secure: false });
}
