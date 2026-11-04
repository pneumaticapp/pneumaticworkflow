import type { RateLimiter, RateLimiterFactory } from '../core/ports.js';

const WINDOW_MS = 60_000;
const MAX_TRACKED_KEYS = 10_000;

// Per process: with several replicas each one enforces the limit separately.
export function createMemoryRateLimiter(limitPerMinute: number, now: () => number = Date.now): RateLimiter {
  const hits = new Map<string, number[]>();

  const recentHits = (key: string) => {
    const cutoff = now() - WINDOW_MS;
    return (hits.get(key) ?? []).filter((time) => time > cutoff).length;
  };

  return {
    async exhausted(key: string) {
      return limitPerMinute > 0 && recentHits(key) >= limitPerMinute;
    },
    async acquire(key: string) {
      if (limitPerMinute <= 0) {
        return true;
      }
      const cutoff = now() - WINDOW_MS;
      const recent = (hits.get(key) ?? []).filter((time) => time > cutoff);
      if (recent.length >= limitPerMinute) {
        hits.set(key, recent);
        return false;
      }
      if (!hits.has(key) && hits.size >= MAX_TRACKED_KEYS) {
        for (const [trackedKey, times] of hits) {
          if (!times.some((time) => time > cutoff)) {
            hits.delete(trackedKey);
          }
        }
      }
      recent.push(now());
      hits.set(key, recent);
      return true;
    },
  };
}

// Separate instances per scope already keep independent limits apart in memory.
export const memoryRateLimiterFactory: RateLimiterFactory = (_scope, limitPerMinute) =>
  createMemoryRateLimiter(limitPerMinute);
