import { deleteCookie, setCookie, ICookieOptions } from './cookie';

function getSecondsByDays(days: number) {
  return days * 24 * 60 * 60;
}

export function setJwtCookie(token: string, rememberMeMode: boolean = true) {
  const ONE_DAY = getSecondsByDays(1);
  const HUNDRED_DAYS = getSecondsByDays(100);

  const COOKIE_EXPIRES = rememberMeMode ? HUNDRED_DAYS : ONE_DAY;
  const COOKIE_OPTIONS: ICookieOptions = {
    domain: window.location.hostname,
    expires: COOKIE_EXPIRES,
    samesite: 'none',
    secure: true
  };

  setCookie('token', token, COOKIE_OPTIONS);
}

export function removeAuthCookies() {
  const REMOVE_COOKIE_LIST = [
    'token',
    'ajs_user_id',
    'ajs_group_id',
    'ajs_anonymous_id',
  ];

  REMOVE_COOKIE_LIST.forEach(key => deleteCookie(key, { domain: window.location.hostname }));
}
