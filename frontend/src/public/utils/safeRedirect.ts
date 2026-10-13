function hasUnsafeCharacters(value: string) {
  return Array.from(value).some(
    (character) => character.charCodeAt(0) <= 32 || character.charCodeAt(0) === 127 || character === '\\',
  );
}

// Login query parameters and sessionStorage are both untrusted input.
export function safeRedirect(value: unknown, fileServiceUrl?: string): string {
  if (typeof value !== 'string' || !value || value.length > 2048 || hasUnsafeCharacters(value)) return '';
  try {
    const decoded = decodeURIComponent(value);
    if (hasUnsafeCharacters(decoded) || decoded.startsWith('//')) return '';
    if (value.startsWith('/') && !value.startsWith('//')) {
      const url = new URL(value, 'https://frontend.invalid');
      if (url.origin !== 'https://frontend.invalid') return '';
      if (url.pathname.startsWith('/mcp/')) return mcpContinuation(value);
      // OAuth initiation endpoints must not become continuation/open-redirect gadgets.
      if (url.pathname.startsWith('/oauth/') || url.pathname.startsWith('/api/')) return '';
      return `${url.pathname}${url.search}${url.hash}`;
    }
    if (!fileServiceUrl) return '';
    const url = new URL(value);
    const trusted = new URL(fileServiceUrl);
    const prefix = trusted.pathname.replace(/\/$/, '') || '/files';
    const suffix = url.pathname.slice(prefix.length);
    if (
      !['https:', 'http:'].includes(url.protocol) ||
      url.origin !== trusted.origin ||
      url.username ||
      url.password ||
      !url.pathname.startsWith(`${prefix}/`) ||
      !/^\/[A-Za-z0-9_-]+(?:\/download)?\/?$/.test(suffix) ||
      url.search ||
      url.hash
    )
      return '';
    return url.href;
  } catch {
    return '';
  }
}

export function isMcpId(value: unknown): value is string {
  return typeof value === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
}

export function mcpContinuation(value: unknown): string {
  if (typeof value !== 'string' || hasUnsafeCharacters(value)) return '';
  try {
    const url = new URL(value, 'https://frontend.invalid');
    if (!value.startsWith('/') || url.origin !== 'https://frontend.invalid' || url.hash) return '';
    if (url.pathname === '/mcp/connections' && !url.search) return '/mcp/connections';
    const uploadId = /^\/mcp\/uploads\/([^/]+)$/.exec(url.pathname)?.[1];
    if (isMcpId(uploadId) && !url.search) return url.pathname;
    const ids = url.searchParams.getAll('request_id');
    if (
      url.pathname === '/mcp/connect' &&
      ids.length === 1 &&
      isMcpId(ids[0]) &&
      Array.from(url.searchParams.keys()).every((key) => ['request_id', 'step'].includes(key)) &&
      (url.searchParams.getAll('step').length === 0 ||
        (url.searchParams.getAll('step').length === 1 && url.searchParams.get('step') === 'consent'))
    )
      return `/mcp/connect?request_id=${encodeURIComponent(ids[0])}${url.searchParams.has('step') ? '&step=consent' : ''}`;
    return '';
  } catch {
    return '';
  }
}
