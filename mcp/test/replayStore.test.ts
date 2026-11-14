import { mkdirSync, mkdtempSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { expect, it } from 'vitest';

import { createFileReplayStore } from '../src/stores/fileReplayStore.js';
import { nowSeconds } from '../src/core/time.js';

it('keeps used codes and refresh tokens rejected after a restart', async () => {
  const directory = mkdtempSync(join(tmpdir(), 'pneumatic-replay-'));
  try {
    const path = join(directory, 'used.log');
    writeFileSync(path, '');
    const expiry = nowSeconds() + 3600;
    const first = createFileReplayStore(path);
    expect(await first.markUsed('code', 'code-1', expiry)).toBe(true);
    expect(await first.markUsed('refresh', 'refresh-1', expiry)).toBe(true);

    const restarted = createFileReplayStore(path);
    expect(await restarted.markUsed('code', 'code-1', expiry)).toBe(false);
    expect(await restarted.markUsed('refresh', 'refresh-1', expiry)).toBe(false);
    expect(await restarted.markUsed('refresh', 'refresh-2', expiry)).toBe(true);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

it('serializes concurrent attempts to spend the same token', async () => {
  const directory = mkdtempSync(join(tmpdir(), 'pneumatic-replay-'));
  try {
    const path = join(directory, 'used.log');
    writeFileSync(path, '');
    const store = createFileReplayStore(path);
    const results = await Promise.all(
      Array.from({ length: 5 }, () => store.markUsed('refresh', 'same-token', nowSeconds() + 3600)),
    );
    expect(results.filter(Boolean)).toHaveLength(1);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

it('migrates existing JSON ledgers without losing spent tokens', async () => {
  const directory = mkdtempSync(join(tmpdir(), 'pneumatic-replay-'));
  try {
    const path = join(directory, 'used.json');
    const expiry = nowSeconds() + 3600;
    writeFileSync(path, JSON.stringify([['refresh:spent', expiry]]));
    const store = createFileReplayStore(path);
    expect(await store.markUsed('refresh', 'spent', expiry)).toBe(false);
    expect(readFileSync(path, 'utf8')).toMatch(/^pneumatic-replay-v1\n/);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

it('fails closed if the ledger is missing or corrupted', () => {
  const directory = mkdtempSync(join(tmpdir(), 'pneumatic-replay-'));
  try {
    const path = join(directory, 'used.log');
    expect(() => createFileReplayStore(path)).toThrow();
    writeFileSync(path, 'pneumatic-replay-v1\n["refresh:spent"]\n');
    expect(() => createFileReplayStore(path)).toThrow();
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

it('drops an unfinished last line left by a crash during an append', async () => {
  const directory = mkdtempSync(join(tmpdir(), 'pneumatic-replay-'));
  try {
    const path = join(directory, 'used.log');
    const exp = nowSeconds() + 60;
    writeFileSync(path, `pneumatic-replay-v1\n${JSON.stringify(['code:kept', exp])}\n["code:torn",`);
    const store = createFileReplayStore(path);
    expect(await store.isUsed('code', 'kept')).toBe(true);
    expect(await store.markUsed('code', 'torn', exp)).toBe(true);
    const reopened = createFileReplayStore(path);
    expect(await reopened.isUsed('code', 'kept')).toBe(true);
    expect(await reopened.isUsed('code', 'torn')).toBe(true);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

it('recovers after a failed append once the ledger is writable again', async () => {
  const directory = mkdtempSync(join(tmpdir(), 'pneumatic-replay-'));
  try {
    const path = join(directory, 'used.log');
    writeFileSync(path, '');
    const store = createFileReplayStore(path);
    const exp = nowSeconds() + 60;
    expect(await store.markUsed('code', 'first', exp)).toBe(true);
    renameSync(path, `${path}.saved`);
    mkdirSync(path);
    await expect(store.markUsed('code', 'second', exp)).rejects.toThrow();
    expect(await store.isHealthy()).toBe(false);
    rmSync(path, { recursive: true });
    renameSync(`${path}.saved`, path);
    expect(await store.markUsed('code', 'third', exp)).toBe(true);
    expect(await store.isHealthy()).toBe(true);
    expect(await store.markUsed('code', 'first', exp)).toBe(false);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
