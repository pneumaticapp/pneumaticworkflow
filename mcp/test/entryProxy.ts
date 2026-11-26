import { createServer, request, type RequestListener } from 'node:http';

// Mirrors the bundled nginx: public MCP paths reach the connector without the /mcp prefix.
function toUpstreamPath(path: string): string | null {
  const pathname = new URL(path, 'http://localhost').pathname;
  if (pathname.startsWith('/.well-known/oauth-')) {
    return path;
  }
  if (pathname === '/mcp' || pathname.startsWith('/mcp/')) {
    return path.replace(/^\/mcp\/?/, '/');
  }
  return null;
}

// Serves public URLs in-process; internal routes such as /healthz pass through unchanged.
export function behindEntry(app: RequestListener): RequestListener {
  return (req, res) => {
    req.url = toUpstreamPath(req.url ?? '/') ?? req.url;
    app(req, res);
  };
}

export function createEntryProxy(upstream: string) {
  return createServer((req, res) => {
    const path = toUpstreamPath(req.url ?? '/');
    if (path === null) {
      res.writeHead(404).end('frontend');
      return;
    }
    const forwarded = request(upstream, { path, method: req.method, headers: req.headers }, (response) => {
      res.writeHead(response.statusCode ?? 502, response.headers);
      response.pipe(res);
    });
    forwarded.on('error', () => {
      if (res.headersSent) {
        res.destroy();
      } else {
        res.writeHead(502).end();
      }
    });
    req.on('aborted', () => forwarded.destroy());
    req.pipe(forwarded);
  });
}
