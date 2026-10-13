import { IMcpConnection, IMcpConsent, IMcpUploadSession, IMcpUploadToken } from '../types/mcp';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { isMcpId } from '../utils/safeRedirect';

export class McpApiError extends Error {
  constructor(public readonly status: number) {
    super('MCP request failed');
  }
}

export function isMcpEnabled() {
  return getBrowserConfigEnv().featureFlags?.MCP_ENABLED === 'yes';
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'same-origin',
      cache: 'no-store',
      referrerPolicy: 'no-referrer',
      redirect: 'error',
    });
    if (!response.ok) throw new McpApiError(response.status);
    return response.status === 204 ? (undefined as T) : await response.json();
  } catch (error) {
    // No upstream error payload or request object (which may contain a capability).
    throw new McpApiError(error instanceof McpApiError ? error.status : 503);
  }
}

function id(value: string) {
  if (!isMcpId(value)) throw new McpApiError(400);
  return encodeURIComponent(value);
}

function mutation(csrf: string, body: unknown, signal?: AbortSignal): RequestInit {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-MCP-CSRF': csrf },
    body: JSON.stringify(body),
    signal,
  };
}

export const getMcpConsent = (requestId: string, signal?: AbortSignal) =>
  request<IMcpConsent>(`/mcp/connect/context?request_id=${id(requestId)}`, { signal });

export const connectMcp = (requestId: string, csrf: string) =>
  request<{ redirect_url: string }>('/mcp/connect', mutation(csrf, { request_id: requestId }));

export const approveMcp = (requestId: string, csrf: string, allow: boolean) =>
  request<{ redirect_url: string }>('/mcp/connect/consent', mutation(csrf, { request_id: requestId, allow }));

export const getMcpConnections = (signal?: AbortSignal) =>
  request<{ results: IMcpConnection[]; csrf_token: string }>('/mcp/connections/data', { signal });

export const revokeMcpConnection = (connectionId: string, csrf: string) =>
  request<void>(`/mcp/connections/${id(connectionId)}`, { ...mutation(csrf, {}), method: 'DELETE' });

export const getMcpUploadSession = (sessionId: string, signal?: AbortSignal) =>
  request<{ session: IMcpUploadSession; csrf_token: string }>(`/mcp/uploads/${id(sessionId)}/data`, { signal });

export async function uploadMcpFile(
  file: File,
  session: IMcpUploadSession,
  csrf: string,
  signal?: AbortSignal,
  onDispatch?: () => void,
) {
  const capability = await request<IMcpUploadToken>(`/mcp/uploads/${id(session.id)}/token`, mutation(csrf, {}, signal));
  const uploadUrl = new URL('/files/upload', window.location.origin).href;
  if (capability.upload_session_id !== session.id || capability.file_upload_url !== uploadUrl || signal?.aborted) {
    throw new McpApiError(400);
  }
  const body = new FormData();
  body.append('file', file, session.filename);
  try {
    onDispatch?.();
    const response = await fetch(uploadUrl, {
      method: 'POST',
      headers: { Authorization: `Bearer ${capability.access_token}`, 'X-MCP-Upload-Session': session.id },
      body,
      credentials: 'omit',
      cache: 'no-store',
      referrerPolicy: 'no-referrer',
      redirect: 'error',
      signal,
    });
    if (!response.ok) throw new McpApiError(response.status);
    // A file ID in the browser response is never completion evidence.
  } catch (error) {
    throw new McpApiError(error instanceof McpApiError ? error.status : 503);
  }
}

export function navigateMcp(url: string) {
  const expected = new URL(getBrowserConfigEnv().featureFlags.MCP_PUBLIC_URL || '');
  const target = new URL(url);
  if (
    target.origin !== expected.origin ||
    target.pathname !== '/oauth/mcp/login' ||
    target.username ||
    target.password ||
    target.hash ||
    target.searchParams.getAll('code').length !== 1 ||
    !/^[A-Za-z0-9._~-]{1,1024}$/.test(target.searchParams.get('code') || '') ||
    target.searchParams.getAll('request_id').length !== 1 ||
    !isMcpId(target.searchParams.get('request_id')) ||
    Array.from(target.searchParams.keys()).some((key) => !['code', 'request_id'].includes(key))
  )
    throw new McpApiError(400);
  window.location.assign(target.href);
}

export function mcpErrorMessage(error: unknown) {
  const status = error instanceof McpApiError ? error.status : 503;
  if (status === 401) return 'mcp.error.login';
  if (status === 403) return 'mcp.error.permission';
  if ([404, 409, 410].includes(status)) return 'mcp.error.expired';
  return 'mcp.error.unavailable';
}
