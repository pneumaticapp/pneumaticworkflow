import { describe, expect, it } from 'vitest';

import { createApiKeyValidator, ValidatorBusyError } from '../src/http/apiKeyValidator.js';
import { createClientFactory } from '../src/pneumatic/client.js';

function fakeUserApi() {
  const calls: string[] = [];
  const fetchFn: typeof fetch = async (_input, init) => {
    const key = new Headers(init?.headers).get('authorization') ?? '';
    calls.push(key);
    await new Promise((resolve) => setTimeout(resolve, 5));
    return key === 'Bearer good'
      ? Response.json({ id: 1 })
      : Response.json({ detail: 'Invalid token.' }, { status: key === 'Bearer guest' ? 403 : 401 });
  };
  return { calls, fetchFn };
}

describe('createApiKeyValidator', () => {
  it('caches rejected keys and treats 403 as a rejection', async () => {
    const { calls, fetchFn } = fakeUserApi();
    const validator = createApiKeyValidator(createClientFactory({ apiUrl: 'https://pneumatic.test', fetchFn }));
    expect(await validator.validate('bad')).toBeNull();
    expect(await validator.validate('bad')).toBeNull();
    expect(await validator.validate('guest')).toBeNull();
    expect(calls).toEqual(['Bearer bad', 'Bearer guest']);
  });

  it('shares one Pneumatic call between concurrent checks of a key', async () => {
    const { calls, fetchFn } = fakeUserApi();
    const validator = createApiKeyValidator(createClientFactory({ apiUrl: 'https://pneumatic.test', fetchFn }));
    const users = await Promise.all([validator.validate('good'), validator.validate('good')]);
    expect(users).toEqual([{ id: 1 }, { id: 1 }]);
    expect(calls).toHaveLength(1);
  });

  it('caps checks of unknown keys but keeps serving cached ones', async () => {
    const { fetchFn } = fakeUserApi();
    const validator = createApiKeyValidator(createClientFactory({ apiUrl: 'https://pneumatic.test', fetchFn }));
    await validator.validate('good');
    await Promise.all(Array.from({ length: 299 }, (_, index) => validator.validate(`guess-${index}`)));
    await expect(validator.validate('guess-next')).rejects.toBeInstanceOf(ValidatorBusyError);
    expect(await validator.validate('good')).toEqual({ id: 1 });
  });
});
