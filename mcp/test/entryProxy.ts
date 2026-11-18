import { createServer, request } from 'node:http';

export function createEntryProxy(upstream: string) {
  return createServer((req, res) => {
    let path = req.url ?? '/';
    const pathname = new URL(path, 'http://localhost').pathname;
    if (pathname.startsWith('/.well-known/oauth-')) {
      path = `/mcp${path}`;
    } else if (pathname === '/mcp') {
      path = path.replace(/^\/mcp(?=\?|$)/, '/mcp/');
    }
    if (!new URL(path, 'http://localhost').pathname.startsWith('/mcp/')) {
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
