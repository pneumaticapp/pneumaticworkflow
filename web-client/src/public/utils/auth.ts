import { getSuperuserToken } from '../redux/auth/utils/superuserToken';
import { EOAuthType } from '../types/auth';
import { parseCookies } from './cookie';
import { history, isGoogleAuth } from './history';
import { identifyAppPartOnClient } from './identifyAppPart/identifyAppPartOnClient';
import { EAppPart } from './identifyAppPart/types';

export const isOAuth = () => isGoogleAuth();

export const getOAuthId = (): string | null =>
  isOAuth() && history.location.pathname.split('/').slice(-1)[0] || null;

export const getOAuthType = (): EOAuthType | null => {
  if (isGoogleAuth()) {
    return EOAuthType.Google;
  }

  return null;
};

export function getCurrentToken() {
  const superUserToken = getSuperuserToken();

  if (superUserToken) {
    return superUserToken;
  }

  const appPart = identifyAppPartOnClient();
  const parsedCookies = parseCookies(document.cookie);

  // For public forms, try to get token from URL if cookie is not available
  let publicTokenFromUrl: string | undefined;
  if (appPart === EAppPart.PublicFormApp) {
    const urlToken = /[^$/]+$/.exec(window.location.pathname)?.[0];
    if (urlToken && urlToken.length >= 8) {
      publicTokenFromUrl = urlToken;
    }
  }

  const tokenMap = {
    [EAppPart.MainApp]: parsedCookies['token'],
    [EAppPart.PublicFormApp]: parsedCookies['public-token'] || publicTokenFromUrl,
    [EAppPart.GuestTaskApp]: parsedCookies['guest-token'],
  };

  const token = tokenMap[appPart];

  // Debug logging for token issues
  console.log('getCurrentToken debug:', {
    appPart,
    hostname: window.location.hostname,
    allCookies: document.cookie,
    parsedCookies,
    publicTokenFromUrl,
    selectedToken: token,
    tokenMap
  });

  // Fix: Store token in localStorage for cross-domain access if cookie domain is localhost
  if (appPart === EAppPart.MainApp && token && window.location.hostname === 'localhost') {
    const hasTokenCookie = document.cookie.includes('token=');
    if (hasTokenCookie) {
      console.log('Storing token in localStorage for cross-subdomain access');
      // Store token in localStorage as fallback for cross-subdomain access
      localStorage.setItem('pneumatic_auth_token', token);
    }
  }

  // For main app, check localStorage as fallback if no cookie token
  if (appPart === EAppPart.MainApp && !token) {
    const localStorageToken = localStorage.getItem('pneumatic_auth_token');
    if (localStorageToken) {
      console.log('Using token from localStorage as fallback');
      return localStorageToken;
    }
  }

  return token;
}
