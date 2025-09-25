import { CookieOptions, Request, Response } from 'express';
import { getConfig } from '../../public/utils/getConfig';

export const COOKIE_MAX_AGE = 14 * 24 * 60 * 60 * 1000;
export const COOKIE_OPTIONS: CookieOptions = {
  maxAge: COOKIE_MAX_AGE,
  // sameSite and secure attrubites are crutial if Public Form App is embedded in iframe
  sameSite: getConfig().env !== 'local' ? 'none' : undefined,
  secure: getConfig().env !== 'local',
};

export interface ITokens {
  token: string;
}

export function setAuthCookie(req: Request, res: Response, { token }: ITokens) {
  const isHTTPS = req.protocol === 'https';
  
  // For localhost development, always use .localhost domain to work across subdomains
  const cookieDomain = (req.hostname === 'localhost' || req.hostname === 'form.localhost') ? '.localhost' : req.hostname;

  // Simple approach: always set maxAge for persistence
  const cookieOptions: CookieOptions = {
    maxAge: COOKIE_MAX_AGE,
    domain: cookieDomain,
  };

  // For localhost development
  if (cookieDomain === '.localhost') {
    cookieOptions.httpOnly = false;
    cookieOptions.sameSite = 'lax';
  } else if (isHTTPS) {
    // For production HTTPS
    cookieOptions.sameSite = getConfig().env !== 'local' ? 'none' : 'lax';
    cookieOptions.secure = true;
  }

  console.log('setAuthCookie debug:', {
    hostname: req.hostname,
    protocol: req.protocol,
    isHTTPS,
    token: token ? token.substring(0, 8) + '...' : 'none',
    domain: cookieDomain,
    options: cookieOptions
  });

  res.cookie('token', token, cookieOptions);
}

export function setGuestCookie(req: Request, res: Response, token: string) {
  const isHTTPS = req.protocol === 'https';
  
  // For localhost development, always use .localhost domain to work across subdomains
  const cookieDomain = (req.hostname === 'localhost' || req.hostname === 'form.localhost') ? '.localhost' : req.hostname;

  res.cookie('guest-token', token, {
    maxAge: COOKIE_MAX_AGE,
    domain: cookieDomain,
    ...(isHTTPS && COOKIE_OPTIONS),
  });
}

export function setPublicAuthCookie(req: Request, res: Response, token: string) {
  const isHTTPS = req.protocol === 'https';
  
  // For localhost development, always use .localhost domain to work across subdomains
  const cookieDomain = (req.hostname === 'localhost' || req.hostname === 'form.localhost') ? '.localhost' : req.hostname;

  const cookieOptions: CookieOptions = {
    maxAge: COOKIE_MAX_AGE,
    domain: cookieDomain,
    ...(isHTTPS && COOKIE_OPTIONS),
    // For localhost development, explicitly set basic options
    ...(req.hostname === 'form.localhost' && {
      httpOnly: false, // Allow JavaScript to read the cookie
      sameSite: 'lax',
    })
  };

  console.log('Setting cookie with options:', {
    token: token.substring(0, 8) + '...',
    domain: cookieDomain,
    options: cookieOptions
  });

  res.cookie('public-token', token, cookieOptions);
}