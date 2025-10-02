import { NextFunction, Request, Response } from 'express';

import { ERoutes } from '../../public/constants/routes';
import { parseCookies } from '../../public/utils/cookie';
import { setAuthCookie, setGuestCookie } from '../utils/cookie';
import { identifyAppPartOnServer } from '../../public/utils/identifyAppPart/identifyAppPartOnServer';
import { EAppPart } from '../../public/utils/identifyAppPart/types';
import { getUser } from './utils/getUser';
import { IAuthenticatedUser } from '../utils/types';

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

export async function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const isEnvBilling = process.env.BILLING !== 'no';

  // We determine the type of the requested application.
  const appPart = identifyAppPartOnServer(req);
  if (appPart === EAppPart.GuestTaskApp) return handleGuestAuth(req, res, next);

  // We define the category of the requested url.
  const isUnsignedUserRoute = UNSIGNED_USER_ROUTES.some((route) => req.url.includes(route));
  const isPaymentDetailsRoute = PAYMENT_ROUTES.some((route) => req.url.includes(route));

  // We determine the presence of a token in a cookie or a mobile application.
  const { mobile_app_token: mobileAppToken } = req.query || '';
  const token = (mobileAppToken as string) || parseCookies(req.get('cookie')).token;
  // If we find an authorization token from a mobile application request, we record it in cookies.
  if (mobileAppToken) setAuthCookie(req, res, { token: req.query.mobile_app_token as string });

  // If there is no token, we will render the front depending on the url category.
  if (!token) return isUnsignedUserRoute ? next() : res.redirect(getLoginUrl(req));

  try {
    // We receive the data of the authorized user using a token and record it in the response further.
    const user = await getUser(req, token, req.headers['user-agent']);
    const { is_subscribed: isSubscribed, billing_plan: billingPlan } = user.account;
    res.locals.user = { ...user, token };

    // If the user has a subscription or it is a free plan and tries to get to the page of an unauthorized user,
    // we redirect him to the product page depending on the status.
    if ((isSubscribed || billingPlan === 'free') && isUnsignedUserRoute) return redirectToUserDefaulRoute(user, res);

    // If the user does not have a tariff set and billing is enabled,
    // the user does not try to access the page of an unauthorized user or the payment card page, we redirect him to the payment card page.
    if (isEnvBilling && !billingPlan && (isUnsignedUserRoute || !isPaymentDetailsRoute))
      return res.redirect(ERoutes.CollectPaymentDetails);

    return next();
  } catch (err) {
    resetCookie('token', req, res);

    res.locals.user = { token };
    return isUnsignedUserRoute ? next() : res.redirect(ERoutes.Login);
  }
}

function redirectToUserDefaulRoute(user: IAuthenticatedUser, res: Response) {
  if (user.is_account_owner) return res.redirect(ERoutes.Main);

  return res.redirect(ERoutes.Tasks);
}

// We create a login url with a redirect url after authorization.
function getLoginUrl(req: Request) {
  const shouldRedirectAfterLogin = req.url !== '/';
  const redirectQuery = shouldRedirectAfterLogin ? `?redirectUrl=${encodeURIComponent(req.url)}` : '';
  const redirectUrl = `${ERoutes.Login}${redirectQuery}`;

  return redirectUrl;
}

async function handleGuestAuth(req: Request, res: Response, next: NextFunction) {
  const { token } = req.query;
  if (!token) return res.redirect(ERoutes.Error);

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
