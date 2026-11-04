import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { afterAll, describe, expect, it } from 'vitest';

import type { RateLimiter, ReplayStore, UploadStore } from '../src/core/ports.js';
import { nowSeconds } from '../src/core/time.js';
import { createFileReplayStore } from '../src/stores/fileReplayStore.js';
import { createMemoryRateLimiter } from '../src/stores/memoryRateLimiter.js';
import { createMemoryUploadStore } from '../src/stores/memoryUploadStore.js';
import { delayed } from './delayed.js';

const directory = mkdtempSync(join(tmpdir(), 'pneumatic-contract-'));
afterAll(() => rmSync(directory, { recursive: true, force: true }));

let ledgers = 0;
const replayStores: Array<[string, () => ReplayStore]> = [
  [
    'file',
    () => {
      const path = join(directory, `replay-${(ledgers += 1)}.log`);
      writeFileSync(path, '');
      return createFileReplayStore(path);
    },
  ],
];

const uploadStores: Array<[string, () => UploadStore]> = [
  ['memory', createMemoryUploadStore],
  ['memory (delayed)', () => delayed(createMemoryUploadStore())],
];

const rateLimiters: Array<[string, (limit: number) => RateLimiter]> = [
  ['memory', (limit) => createMemoryRateLimiter(limit)],
  ['memory (delayed)', (limit) => delayed(createMemoryRateLimiter(limit))],
];

replayStores.push(['file (delayed)', () => delayed(replayStores[0]![1]())]);

describe.each(replayStores)('ReplayStore contract: %s', (_name, create) => {
  it('accepts an ID once and keeps kinds apart', async () => {
    const store = create();
    const exp = nowSeconds() + 60;
    expect(await store.isUsed('code', 'a')).toBe(false);
    expect(await store.markUsed('code', 'a', exp)).toBe(true);
    expect(await store.markUsed('code', 'a', exp)).toBe(false);
    expect(await store.isUsed('code', 'a')).toBe(true);
    expect(await store.isUsed('refresh', 'a')).toBe(false);
    expect(await store.isHealthy()).toBe(true);
  });

  it('rejects expired IDs and lets exactly one of concurrent uses win', async () => {
    const store = create();
    expect(await store.markUsed('code', 'old', nowSeconds() - 1)).toBe(false);
    const results = await Promise.all(
      Array.from({ length: 5 }, () => store.markUsed('refresh', 'r', nowSeconds() + 60)),
    );
    expect(results.filter(Boolean)).toHaveLength(1);
  });
});

describe.each(uploadStores)('UploadStore contract: %s', (_name, create) => {
  const file = { fileId: 'f-1', name: 'a.pdf', contentType: 'application/pdf', size: 3, url: 'https://files/f-1' };

  it('leases a pending upload to exactly one caller and completes it once', async () => {
    const store = create();
    const record = await store.create('key-a', 'a.pdf', 3600);
    expect(await store.get(record.uploadId)).toMatchObject({ keyHash: 'key-a', filename: 'a.pdf', file: null });
    const leases = await Promise.all([store.claim(record.uploadId, 60), store.claim(record.uploadId, 60)]);
    const [lease] = leases.filter((value): value is string => value !== null);
    expect(leases.filter(Boolean)).toHaveLength(1);
    expect(await store.complete(record.uploadId, 'not-the-lease', file)).toBe(false);
    expect(await store.complete(record.uploadId, lease!, file)).toBe(true);
    expect((await store.get(record.uploadId))?.file).toEqual(file);
    expect(await store.claim(record.uploadId, 60)).toBeNull();
    expect(await store.complete(record.uploadId, lease!, file)).toBe(false);
  });

  it('frees a released lease, ignores foreign releases and rejects unknown or expired links', async () => {
    const store = create();
    const record = await store.create('key-a', null, 3600);
    const lease = await store.claim(record.uploadId, 60);
    await store.release(record.uploadId, 'someone-else');
    expect(await store.claim(record.uploadId, 60)).toBeNull();
    await store.release(record.uploadId, lease!);
    await store.release(record.uploadId, lease!);
    expect(await store.claim(record.uploadId, 60)).not.toBeNull();
    expect(await store.claim('missing', 60)).toBeNull();
    expect(await store.get('missing')).toBeUndefined();

    const expired = await store.create('key-a', null, -1);
    expect(await store.claim(expired.uploadId, 60)).toBeNull();
    expect(await store.get(expired.uploadId)).toMatchObject({ uploadId: expired.uploadId, file: null });
  });

  it('lets an abandoned lease lapse so a crashed process cannot block the link', async () => {
    const store = create();
    const record = await store.create('key-a', null, 3600);
    expect(await store.claim(record.uploadId, -1)).not.toBeNull();
    expect(await store.claim(record.uploadId, 60)).not.toBeNull();
  });

  it('caps open links per key without affecting other keys', async () => {
    const store = create();
    let error: unknown;
    for (let index = 0; index < 25 && !error; index += 1) {
      await store.create('busy-key', null, 3600).catch((caught: unknown) => {
        error = caught;
      });
    }
    expect(error).toMatchObject({ code: 'rate_limited' });
    await expect(store.create('other-key', null, 3600)).resolves.toMatchObject({ keyHash: 'other-key' });
  });
});

describe.each(rateLimiters)('RateLimiter contract: %s', (_name, create) => {
  it('allows the limit per key and reports exhaustion without consuming', async () => {
    const limiter = create(2);
    expect(await limiter.acquire('a')).toBe(true);
    expect(await limiter.exhausted('a')).toBe(false);
    expect(await limiter.acquire('a')).toBe(true);
    expect(await limiter.exhausted('a')).toBe(true);
    expect(await limiter.acquire('a')).toBe(false);
    expect(await limiter.acquire('b')).toBe(true);
  });

  it('is disabled with a zero limit', async () => {
    const limiter = create(0);
    for (let index = 0; index < 5; index += 1) {
      expect(await limiter.acquire('a')).toBe(true);
    }
    expect(await limiter.exhausted('a')).toBe(false);
  });
});
