import { hashApiKey } from '../core/keys.js';
import { PneumaticApiError, type ClientFactory } from '../pneumatic/client.js';
import { createMemoryRateLimiter } from '../stores/memoryRateLimiter.js';

const CACHE_TTL_MS = 5 * 60 * 1000;
const REJECTED_TTL_MS = 60 * 1000;
const MAX_CACHE_ENTRIES = 10_000;
// Unknown keys cost a Pneumatic call each; the cap keeps key guessing from flooding Pneumatic via the connector.
const MAX_NEW_KEY_CHECKS_PER_MINUTE = 300;

export interface PneumaticUser {
  id: number;
  email?: string;
  first_name?: string;
  last_name?: string;
}

export class ValidatorBusyError extends Error {
  constructor() {
    super('Too many API key checks; try again later');
    this.name = 'ValidatorBusyError';
  }
}

export function createApiKeyValidator(clientFor: ClientFactory) {
  const cache = new Map<string, { user: PneumaticUser | null; expiresAt: number }>();
  const inFlight = new Map<string, Promise<PneumaticUser | null>>();
  const newKeyChecks = createMemoryRateLimiter(MAX_NEW_KEY_CHECKS_PER_MINUTE);

  function remember(cacheKey: string, user: PneumaticUser | null) {
    if (cache.size >= MAX_CACHE_ENTRIES) {
      cache.clear();
    }
    cache.set(cacheKey, { user, expiresAt: Date.now() + (user ? CACHE_TTL_MS : REJECTED_TTL_MS) });
  }

  async function check(cacheKey: string, apiKey: string): Promise<PneumaticUser | null> {
    try {
      const user = await clientFor(apiKey).get<PneumaticUser>('/accounts/user');
      remember(cacheKey, user);
      return user;
    } catch (error) {
      if (error instanceof PneumaticApiError && (error.status === 401 || error.status === 403)) {
        remember(cacheKey, null);
        return null;
      }
      throw error;
    }
  }

  return {
    async validate(apiKey: string): Promise<PneumaticUser | null> {
      const cacheKey = hashApiKey(apiKey);
      const cached = cache.get(cacheKey);
      if (cached && cached.expiresAt > Date.now()) {
        return cached.user;
      }
      const pending = inFlight.get(cacheKey);
      if (pending) {
        return pending;
      }
      // Registered before the first await, so concurrent checks of one key share a single Pneumatic call.
      const request = (async () => {
        if (!cached?.user && !(await newKeyChecks.acquire('new-keys'))) {
          throw new ValidatorBusyError();
        }
        return check(cacheKey, apiKey);
      })().finally(() => inFlight.delete(cacheKey));
      inFlight.set(cacheKey, request);
      return request;
    },
  };
}

export type ApiKeyValidator = ReturnType<typeof createApiKeyValidator>;
