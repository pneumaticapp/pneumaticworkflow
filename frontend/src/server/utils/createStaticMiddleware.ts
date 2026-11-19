import path from 'path';
import express from 'express';

export function createStaticMiddleware(directory: string) {
  return express.static(directory, {
    setHeaders(res, filePath) {
      const hasContentHash = /\.[a-f0-9]{8,}\.(?:js|css)$/.test(path.basename(filePath));
      res.setHeader('Cache-Control', hasContentHash ? 'public, max-age=31536000, immutable' : 'no-cache');
    },
  });
}
