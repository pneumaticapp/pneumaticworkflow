import { spawnSync } from 'node:child_process';
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { afterEach, describe, expect, it } from 'vitest';

const directories: string[] = [];
const startupScript = fileURLToPath(new URL('../../start.sh', import.meta.url));
const decidedModules = 'LOGS_ENABLE=no\nMCP_ENABLE=no';

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
`,
    { mode: 0o755 },
  );

  const spawn = (answers: string[], overrides: NodeJS.ProcessEnv) => {
    writeFileSync(dockerLog, '');
    const result = spawnSync('bash', [join(directory, 'start.sh')], {
      input: [...answers, '3'].map((answer) => `${answer}\n`).join(''),
      encoding: 'utf8',
      env: {
        ...process.env,
        PATH: `${binDirectory}:${process.env.PATH}`,
        COMPOSE_PROFILES: undefined,
        MCP_TEST_DOCKER_LOG: dockerLog,
        ...overrides,
      },
    });
    return { result, commands: readFileSync(dockerLog, 'utf8') };
  };

  return {
    directory,
    run(answers: string[] = [], overrides: NodeJS.ProcessEnv = {}) {
      const { result, commands } = spawn(answers, overrides);
      expect(result.status, result.stderr).toBe(0);
      return { output: result.stdout, commands };
    },
    interrupt(answers: string[]) {
      const { result } = spawn(answers, {});
      expect(result.status).not.toBe(0);
    },
    env() {
      return readFileSync(envFile, 'utf8');
    },
    value(name: string) {
      return new RegExp(`^${name}=(.*)$`, 'm').exec(readFileSync(envFile, 'utf8'))?.[1];
    },
  };
}

describe('MCP startup configuration', () => {
  it('generates and preserves an independent secret for an existing installation', () => {
    const installation = createInstallation('DJANGO_SECRET_KEY=django-secret\nLOGS_ENABLE=no\nMCP_ENABLE=yes');
    const { output } = installation.run([], { MCP_SECRET: 'inherited-secret' });
    const secret = installation.value('MCP_SECRET');
    expect(secret).toMatch(/^[a-f0-9]{64}$/);
    expect(output).not.toContain(secret);
    installation.run();
    expect(installation.value('MCP_SECRET')).toBe(secret);
  });

  it('keeps a configured secret unchanged', () => {
    const secret = 'configured-secret'.repeat(4);
    const installation = createInstallation(`LOGS_ENABLE=no\nMCP_ENABLE=yes\nMCP_SECRET=${secret}`);
    installation.run();
    expect(installation.value('MCP_SECRET')).toBe(secret);
  });

  it('starts compose without --profile flags', () => {
    const installation = createInstallation(decidedModules);
    const { commands } = installation.run();
    expect(commands).toContain('compose -f docker-compose.src.yml up -d');
    expect(commands).not.toContain('--profile');
  });

  it('ignores exported COMPOSE_PROFILES', () => {
    const installation = createInstallation('');
    installation.run(['n', 'y'], { COMPOSE_PROFILES: 'logs-otlp' });
    expect(installation.value('COMPOSE_PROFILES')).toBe('mcp');
  });
});

describe('Optional modules dialogs', () => {
  it('configures OTLP logging with an authorization header', () => {
    const installation = createInstallation('');
    installation.run(['y', '1', 'http://storage:3100/otlp', 'Bearer token', 'n']);
    expect(installation.value('LOGS_ENABLE')).toBe('yes');
    expect(installation.value('LOGS_BACKEND')).toBe('otlp');
    expect(installation.value('LOGS_OTLP_EXPORT_ENDPOINT')).toBe('http://storage:3100/otlp');
    expect(installation.value('LOGS_OTLP_EXPORT_AUTH')).toBe('Bearer token');
    expect(installation.value('COMPOSE_PROFILES')).toBe('logs-otlp');
  });

  it('writes an empty OTLP authorization header', () => {
    const installation = createInstallation('');
    installation.run(['y', '1', 'http://storage:3100/otlp', '', 'n']);
    expect(installation.value('LOGS_OTLP_EXPORT_AUTH')).toBe('');
  });

  it('configures Elasticsearch with an API key', () => {
    const installation = createInstallation('');
    installation.run(['y', '2', 'https://es.example:9200', '1', 'api-key', 'y']);
    expect(installation.value('LOGS_BACKEND')).toBe('elasticsearch');
    expect(installation.value('LOGS_ELASTICSEARCH_URL')).toBe('https://es.example:9200');
    expect(installation.value('LOGS_ELASTICSEARCH_API_KEY')).toBe('api-key');
    expect(installation.value('LOGS_ELASTICSEARCH_USER')).toBe('');
    expect(installation.value('LOGS_ELASTICSEARCH_PASSWORD')).toBe('');
    expect(installation.value('COMPOSE_PROFILES')).toBe('logs-elasticsearch,mcp');
  });

  it('configures Elasticsearch with a login and password', () => {
    const installation = createInstallation('');
    installation.run(['y', '2', 'https://es.example:9200', '2', 'elastic', 'p&ss|w\\rd', 'n']);
    expect(installation.value('LOGS_ELASTICSEARCH_USER')).toBe('elastic');
    expect(installation.value('LOGS_ELASTICSEARCH_PASSWORD')).toBe('p&ss|w\\rd');
    expect(installation.value('LOGS_ELASTICSEARCH_API_KEY')).toBe('');
  });

  it('records declined modules and asks nothing on the next run', () => {
    const installation = createInstallation('');
    installation.run(['n', 'n']);
    expect(installation.value('LOGS_ENABLE')).toBe('no');
    expect(installation.value('MCP_ENABLE')).toBe('no');
    const before = installation.env();
    installation.run();
    expect(installation.env()).toBe(before);
  });

  it('migrates an installation configured before the toggles existed', () => {
    const installation = createInstallation('LOGS_BACKEND=otlp\nCOMPOSE_PROFILES=mcp');
    installation.run(['y']);
    expect(installation.value('LOGS_ENABLE')).toBe('yes');
    expect(installation.value('MCP_ENABLE')).toBe('yes');
    expect(installation.value('COMPOSE_PROFILES')).toBe('logs-otlp,mcp');
  });

  it('leaves .env untouched when the logging dialog is interrupted', () => {
    const installation = createInstallation('COMPOSE_PROFILES=custom');
    const before = installation.env();
    installation.interrupt(['y', '2']);
    expect(installation.env()).toBe(before);
    expect(readdirSync(installation.directory).filter((name) => name.includes('.tmp.'))).toEqual([]);
  });

  it('keeps logging answers when the MCP dialog is interrupted', () => {
    const installation = createInstallation('COMPOSE_PROFILES=custom');
    installation.interrupt(['y', '1', 'http://storage:3100/otlp', '']);
    expect(installation.value('LOGS_ENABLE')).toBe('yes');
    expect(installation.value('MCP_ENABLE')).toBeUndefined();
    expect(installation.value('COMPOSE_PROFILES')).toBe('custom');
    installation.run(['n']);
    expect(installation.value('MCP_ENABLE')).toBe('no');
    expect(installation.value('COMPOSE_PROFILES')).toBe('logs-otlp');
  });

  it('leaves COMPOSE_PROFILES alone when no dialog runs', () => {
    const installation = createInstallation(`${decidedModules}\nCOMPOSE_PROFILES=custom`);
    installation.run();
    expect(installation.value('COMPOSE_PROFILES')).toBe('custom');
  });

  it('rewrites COMPOSE_PROFILES entirely after a dialog', () => {
    const installation = createInstallation('COMPOSE_PROFILES=custom');
    installation.run(['n', 'n']);
    expect(installation.value('COMPOSE_PROFILES')).toBe('');
  });

  it('hands the queue directory to the collector on every Elasticsearch run', () => {
    const installation = createInstallation('LOGS_ENABLE=yes\nLOGS_BACKEND=elasticsearch\nMCP_ENABLE=no');
    const chown = `run --rm -v ${installation.directory}/otel-queue:/q alpine chown 10001:10001 /q`;
    const { output, commands } = installation.run();
    expect(existsSync(join(installation.directory, 'otel-queue'))).toBe(true);
    expect(commands).toContain(chown);
    expect(output).not.toContain('otel-queue');
    expect(installation.run().commands).toContain(chown);
  });

  it('does not touch the queue directory outside Elasticsearch mode', () => {
    for (const settings of ['LOGS_ENABLE=yes\nLOGS_BACKEND=otlp\nMCP_ENABLE=no', decidedModules]) {
      const installation = createInstallation(settings);
      const { commands } = installation.run();
      expect(existsSync(join(installation.directory, 'otel-queue'))).toBe(false);
      expect(commands).not.toContain('chown');
    }
  });
});
