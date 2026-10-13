import { createHmac, randomBytes, timingSafeEqual } from 'crypto';
import { Request, Response } from 'express';
import { getConfig } from '../../public/utils/getConfig';
import { mcpContinuation } from '../../public/utils/safeRedirect';

export const MCP_CONTINUATION_COOKIE = 'mcp-continuation';
const CSRF_COOKIE = 'mcp-csrf';
const OAUTH_COOKIE = 'mcp-oauth';

export function mcpEnabled() {
  return process.env.MCP_ENABLED === 'yes';
}

export function mcpPrivacy(res: Response) {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
}

export function mcpCookies(req: Request): Record<string, string> {
  try {
    const result: Record<string, string> = Object.create(null);
    for (const entry of (req.get('cookie') || '').split(';')) {
      const delimiter = entry.indexOf('=');
      if (delimiter < 0) continue;
      const key = entry.slice(0, delimiter).trim();
      if (Object.prototype.hasOwnProperty.call(result, key)) return {};
      result[key] = decodeURIComponent(entry.slice(delimiter + 1).trim());
    }
    return result;
  } catch {
    return {};
  }
}

function cookieOptions(path: string) {
  return {
    path,
    httpOnly: true,
    secure: getConfig().env !== 'local',
    sameSite: 'lax' as const,
    maxAge: 15 * 60 * 1000,
  };
}

export function rememberMcpContinuation(res: Response, target: string) {
  const safe = mcpContinuation(target);
  if (safe) res.cookie(MCP_CONTINUATION_COOKIE, safe, cookieOptions('/'));
}

export function readMcpContinuation(req: Request) {
  return mcpContinuation(mcpCookies(req)[MCP_CONTINUATION_COOKIE]);
}

export function clearMcpContinuation(res: Response) {
  const { maxAge, ...options } = cookieOptions('/');
  res.clearCookie(MCP_CONTINUATION_COOKIE, options);
}

export function rememberMcpOAuth(res: Response, target: string, authUri: string, provider: string) {
  const state = new URL(authUri).searchParams.get('state');
  if (!state || state.length > 2048 || !mcpContinuation(target)) throw new Error('Invalid OAuth continuation');
  res.cookie(OAUTH_COOKIE, JSON.stringify({ target, state, provider }), cookieOptions('/'));
}

export function consumeMcpOAuth(req: Request, res: Response, provider: string): string | undefined {
  const raw = mcpCookies(req)[OAUTH_COOKIE];
  if (!raw) return undefined;
  const { maxAge, ...options } = cookieOptions('/');
  res.clearCookie(OAUTH_COOKIE, options);
  try {
    const data = JSON.parse(raw);
    if (typeof req.query.state !== 'string' || data.state !== req.query.state || data.provider !== provider) return '';
    return mcpContinuation(data.target);
  } catch {
    return '';
  }
}

export function issueMcpCsrf(req: Request, res: Response, token: string) {
  const current = mcpCookies(req)[CSRF_COOKIE];
  const nonce = current && /^[a-f0-9]{64}$/.test(current) ? current : randomBytes(32).toString('hex');
  res.cookie(CSRF_COOKIE, nonce, { ...cookieOptions('/mcp'), sameSite: 'strict' });
  return createHmac('sha256', token).update(nonce).digest('hex');
}

export function validMcpCsrf(req: Request, token: string) {
  try {
    const trusted = new URL(getConfig().host);
    const origin = req.get('origin');
    const site = req.get('sec-fetch-site');
    if (origin !== trusted.origin || (site && site !== 'same-origin')) return false;
    const nonce = mcpCookies(req)[CSRF_COOKIE];
    const supplied = req.get('x-mcp-csrf');
    if (!/^[a-f0-9]{64}$/.test(nonce || '') || !/^[a-f0-9]{64}$/.test(supplied || '')) return false;
    const expected = createHmac('sha256', token).update(nonce).digest();
    return timingSafeEqual(expected, Buffer.from(supplied!, 'hex'));
  } catch {
    return false;
  }
}

export function mcpLoginRedirect(
  result: { code: unknown; request_id: unknown; expires_in: number },
  requestId: string,
) {
  if (
    typeof result.request_id !== 'string' ||
    result.request_id.toLowerCase() !== requestId.toLowerCase() ||
    !Number.isFinite(result.expires_in) ||
    result.expires_in <= 0 ||
    result.expires_in > 60 ||
    typeof result.code !== 'string' ||
    !/^[A-Za-z0-9._~-]{1,1024}$/.test(result.code)
  )
    throw new Error('Invalid MCP response');
  const base = new URL(process.env.MCP_PUBLIC_URL || '');
  if (
    base.username ||
    base.password ||
    base.search ||
    base.hash ||
    (base.protocol !== 'https:' && !(getConfig().env === 'local' && base.protocol === 'http:'))
  )
    throw new Error('Invalid MCP configuration');
  const url = new URL('/oauth/mcp/login', base.origin);
  url.searchParams.set('code', result.code);
  url.searchParams.set('request_id', requestId);
  return url.href;
}
