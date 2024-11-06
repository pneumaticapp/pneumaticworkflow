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
  res.cookie('token', token, {
    ...COOKIE_OPTIONS,
    domain: req.hostname,
  });
}

export function setGuestCookie(req: Request, res: Response, token: string) {
  res.cookie('guest-token', token, {
    ...COOKIE_OPTIONS,
    domain: req.hostname,
  });
}

export function setPublicAuthCookie(req: Request, res: Response, token: string) {
  res.cookie('public-token', token, {
    ...COOKIE_OPTIONS,
    domain: req.hostname,
  });
}
