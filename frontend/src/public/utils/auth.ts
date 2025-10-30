import { getSuperuserToken } from '../redux/auth/utils/superuserToken';
import { EOAuthType } from '../types/auth';
import { parseCookies } from './cookie';
import { history } from './history';
import { identifyAppPartOnClient } from './identifyAppPart/identifyAppPartOnClient';
import { EAppPart } from './identifyAppPart/types';


export const getOAuthId = (): string | null =>
  history.location.pathname.split('/').slice(-1)[0] || null;

export const getOAuthType = (): EOAuthType | null => {
  return null;
};

export function getCurrentToken() {
  const superUserToken = getSuperuserToken();

  if (superUserToken) {
    return superUserToken;
  }

  const appPart = identifyAppPartOnClient();
  const parsedCookies = parseCookies(document.cookie);

  const tokenMap = {
    [EAppPart.MainApp]: parsedCookies['token'],
    [EAppPart.PublicFormApp]: parsedCookies['public-token'],
    [EAppPart.GuestTaskApp]: parsedCookies['guest-token'],
  };

  const token = tokenMap[appPart];

  return token;
}
