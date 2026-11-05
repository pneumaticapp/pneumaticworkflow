#!/usr/bin/env node
import { serveStdio } from '@modelcontextprotocol/server/stdio';

import { ConfigError, loadConfig } from './config.js';
import { configureLog, log } from './core/log.js';
import { createHttpApp } from './http/app.js';
import { createPneumaticClient } from './pneumatic/client.js';
import { buildServer } from './server.js';

function main() {
  try {
    configureLog(process.env.LOG_LEVEL);
  } catch (error) {
    throw new ConfigError((error as Error).message);
  }
  const config = loadConfig();

  if (config.transport === 'stdio') {
    const client = createPneumaticClient(config.pneumatic, config.apiKey);
    serveStdio(() => buildServer(client, { toolsets: config.toolsets, isReadOnly: config.isReadOnly }));
    return;
  }

  const app = createHttpApp(config);
  const server = app.listen(config.port, config.host, (error?: Error) => {
    if (error) {
      log('error', 'listen_failed', { host: config.host, port: config.port, message: error.message });
      process.exit(1);
    }
    log('info', 'listening', {
      address: `http://${config.host}:${config.port}/mcp`,
      publicUrl: new URL('/mcp', config.publicUrl).href,
      apiUrl: config.pneumatic.apiUrl,
    });
  });
  // Docker sends SIGTERM first; finishing in-flight requests avoids cutting replay ledger writes.
  for (const signal of ['SIGTERM', 'SIGINT'] as const) {
    process.once(signal, () => {
      server.close(() => process.exit(0));
      setTimeout(() => process.exit(0), 10_000).unref();
    });
  }
}

try {
  main();
} catch (error) {
  if (error instanceof ConfigError) {
    log('error', 'config_error', { message: error.message });
    process.exit(1);
  }
  throw error;
}
