/* eslint-disable */

import { getBrowserConfig } from "./getConfig";

/* prettier-ignore */
export interface ICookieOptions {
  path?: string;
  domain?: string;
  secure?: boolean;
  expires?: number | Date;
  samesite?: "none" | "strict" | "lax";
}

const defaultCookieOptions: ICookieOptions = {
  path: '/',
  secure: true,
};

export const setCookie = (
  name: string,
  value: string,
  config?: ICookieOptions,
) => {
  const { env } = getBrowserConfig();
  const options = Object.assign({}, defaultCookieOptions, config);

  if (env === 'local') {
    options['secure'] = false;
    options['samesite'] = undefined;
  }

  const { expires, samesite } = options;
  let cookieExpires: string | undefined;

  if (expires) {
    if (typeof expires === 'number') {
      const d = new Date();
      cookieExpires = new Date(d.setTime(d.getTime() + expires * 1000)).toUTCString();
    } else if (expires instanceof Date) {
      cookieExpires = expires.toUTCString();
    }
  }
  document.cookie =
    // tslint:disable-next-line:prefer-template
    `${name}=${encodeURIComponent(value)}; ` +
    `path=${options.path}` +
    `; domain=${options.domain}${
      cookieExpires ? `; expires=${cookieExpires}` : ''
    }${samesite ? `; samesite=${samesite}` : ''}${options.secure ? '; secure' : ''}`;
};

export const deleteCookie = (
  name: string,
  config?: ICookieOptions,
) => {
  setCookie(name, '', Object.assign({}, config, {
    expires: -1,
  }));
};

export const parseCookies = (cookiesString?: string) => {
  let cookiesObject: {
    [key: string]: string;
  } = {};

  const pairs = (cookiesString || '').split(/; */);
  for (let i = 0; i < pairs.length; i++) {
    const pair = pairs[i];
    const eqIdx = pair.indexOf('=');

    // skip things that don't look like key=value
    if (eqIdx < 0) {
      continue;
    }

    const key = pair.substr(0, eqIdx).trim();
    // tslint:disable-next-line:restrict-plus-operands
    let value = pair.substr(eqIdx + 1, pair.length).trim();

    // quoted values
    if (value[0] === '"') {
      value = value.slice(1, -1);
    }

    // only assign once
    if (!(key in cookiesObject)) {
      cookiesObject[key] = decodeURIComponent(value);
    }
  }

  return cookiesObject;
};
