import { mkdtempSync, rmSync, writeFileSync } from 'fs';
import { createServer, get, type IncomingHttpHeaders, type Server } from 'http';
import type { AddressInfo } from 'net';
import { tmpdir } from 'os';
import path from 'path';
import express from 'express';

import { createStaticMiddleware } from '../createStaticMiddleware';

describe('static asset caching', () => {
  let directory: string;
  let server: Server;
  let origin: string;

  beforeAll(async () => {
    directory = mkdtempSync(path.join(tmpdir(), 'pneumatic-static-'));
    for (const filename of ['main.12345678abcdef01.js', 'main.12345678abcdef01.css', 'main.js', 'main.ejs']) {
      writeFileSync(path.join(directory, filename), 'asset content');
    }
    const app = express();
    app.use('/static', createStaticMiddleware(directory));
    server = createServer(app);
    await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
    origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  });

  afterAll(async () => {
    if (server?.listening) await new Promise<void>((resolve) => server.close(() => resolve()));
    if (directory) rmSync(directory, { recursive: true, force: true });
  });

  function request(filename: string, headers: IncomingHttpHeaders = {}) {
    return new Promise<{ status: number | undefined; headers: IncomingHttpHeaders }>((resolve, reject) => {
      get(`${origin}/static/${filename}`, { headers }, (response) => {
        response.resume();
        response.on('end', () => resolve({ status: response.statusCode, headers: response.headers }));
      }).on('error', reject);
    });
  }

  it.each(['main.12345678abcdef01.js', 'main.12345678abcdef01.css'])(
    'keeps content-hashed asset %s immutable for one year',
    async (filename) => {
      const response = await request(filename);
      expect(response.status).toBe(200);
      expect(response.headers['cache-control']).toBe('public, max-age=31536000, immutable');
    },
  );

  it.each(['main.js', 'main.ejs'])('revalidates asset %s without a content hash', async (filename) => {
    const response = await request(filename);
    expect(response.headers['cache-control']).toBe('no-cache');
    expect(response.headers.etag).toBeDefined();
    const cached = await request(filename, { 'if-none-match': response.headers.etag });
    expect(cached.status).toBe(304);
    expect(cached.headers['cache-control']).toBe('no-cache');
  });
});
