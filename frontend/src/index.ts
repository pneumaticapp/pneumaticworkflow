import { initServer } from './server';

initServer().catch((error: unknown) => {
  const message = error instanceof Error ? error.stack || error.message : String(error);
  process.stderr.write(`Failed to start frontend: ${message}\n`);
  process.exitCode = 1;
});
