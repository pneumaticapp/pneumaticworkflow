import { spawnSync } from 'node:child_process';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { afterEach, describe, expect, it } from 'vitest';

const directories: string[] = [];
const startupScript = fileURLToPath(new URL('../../start.sh', import.meta.url));

afterEach(() => {
  for (const directory of directories.splice(0)) {
    rmSync(directory, { recursive: true, force: true });
  }
});

function createInstallation(settings: string) {
  const directory = mkdtempSync(join(tmpdir(), 'pneumatic-startup-'));
  directories.push(directory);
  const binDirectory = join(directory, 'bin');
  const envFile = join(directory, '.env');
  const dockerLog = join(directory, 'docker.log');
  mkdirSync(binDirectory);
  copyFileSync(startupScript, join(directory, 'start.sh'));
  writeFileSync(envFile, `FRONTEND_URL=https://app.example.com\n${settings}\n`);
  writeFileSync(
    join(binDirectory, 'docker'),
    `#!/bin/sh
printf '%s\\n' "$*" >> "$MCP_TEST_DOCKER_LOG"
if [ "$1" = container ]; then
  [ "$MCP_TEST_HAS_CONTAINER" = true ]
fi
`,
    { mode: 0o755 },
  );

  return {
    run(overrides: NodeJS.ProcessEnv = {}) {
      writeFileSync(dockerLog, '');
      const result = spawnSync('bash', [join(directory, 'start.sh')], {
        input: '3\n',
        encoding: 'utf8',
        env: {
          ...process.env,
          PATH: `${binDirectory}:${process.env.PATH}`,
          COMPOSE_PROFILES: undefined,
          MCP_TEST_DOCKER_LOG: dockerLog,
          MCP_TEST_HAS_CONTAINER: 'false',
          ...overrides,
        },
      });
      expect(result.status, result.stderr).toBe(0);
      return { output: result.stdout, commands: readFileSync(dockerLog, 'utf8') };
    },
    readSecret() {
      return /^MCP_SECRET=(.+)$/m.exec(readFileSync(envFile, 'utf8'))?.[1];
    },
  };
}

describe('MCP startup configuration', () => {
  it('generates and preserves an independent secret for an existing installation', () => {
    const installation = createInstallation('DJANGO_SECRET_KEY=django-secret');
    const { output } = installation.run({ MCP_SECRET: 'inherited-secret' });
    const secret = installation.readSecret();
    expect(secret).toMatch(/^[a-f0-9]{64}$/);
    expect(output).not.toContain(secret);
    installation.run();
    expect(installation.readSecret()).toBe(secret);
  });

  it('keeps a configured secret unchanged', () => {
    const secret = 'configured-secret'.repeat(4);
    const installation = createInstallation(`MCP_SECRET=${secret}`);
    installation.run();
    expect(installation.readSecret()).toBe(secret);
  });

  it('enables MCP through the profile alongside the log collector', () => {
    const installation = createInstallation('COMPOSE_PROFILES="logs-otlp,mcp"\nLOGS_BACKEND=otlp');
    const { commands } = installation.run({ MCP_TEST_HAS_CONTAINER: 'true' });
    expect(commands).toContain('--profile logs-otlp --profile mcp up -d');
    expect(commands).not.toContain('rm -f pneumatic-mcp');
  });

  it('removes a previously running connector when its profile is disabled', () => {
    const installation = createInstallation('');
    const { commands } = installation.run({ MCP_TEST_HAS_CONTAINER: 'true' });
    expect(commands).toContain('rm -f pneumatic-mcp');
    expect(commands).not.toContain('--profile mcp');
  });

  it('honors exported profiles over the env file', () => {
    const installation = createInstallation('COMPOSE_PROFILES=mcp');
    const { commands } = installation.run({ COMPOSE_PROFILES: '' });
    expect(commands).not.toContain('--profile mcp');
    expect(installation.run({ COMPOSE_PROFILES: '*' }).commands).toContain('--profile mcp up -d');
  });
});
