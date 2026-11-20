import { describe, expect, it } from 'vitest';

import { createMemoryRateLimiter } from '../src/stores/memoryRateLimiter.js';

describe('createMemoryRateLimiter', () => {
  it('limits calls per key within a rolling minute', async () => {
    let now = 0;
    const limiter = createMemoryRateLimiter(2, () => now);
    expect(await limiter.acquire('a')).toBe(true);
    expect(await limiter.acquire('a')).toBe(true);
    expect(await limiter.acquire('a')).toBe(false);
    expect(await limiter.acquire('b')).toBe(true);
    now = 60_001;
    expect(await limiter.acquire('a')).toBe(true);
  });

  it('is disabled with a zero limit', async () => {
    const limiter = createMemoryRateLimiter(0);
    for (let index = 0; index < 5; index += 1) {
      expect(await limiter.acquire('a')).toBe(true);
    }
  });
});
