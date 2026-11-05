import { createCipheriv, hkdfSync } from 'node:crypto';

import { afterEach, describe, expect, it, vi } from 'vitest';

import { createSealer } from '../src/http/sealer.js';

const secret = 's'.repeat(32);

afterEach(() => vi.restoreAllMocks());

describe('sealer', () => {
  it('reads tokens in the existing IV + tag + ciphertext format', () => {
    const iv = Buffer.alloc(12, 7);
    const key = Buffer.from(hkdfSync('sha256', secret, 'pneumatic-mcp', 'seal', 32));
    const cipher = createCipheriv('aes-256-gcm', key, iv);
    const payload = { kind: 'access', clientId: 'client-1', apiKey: 'key-1' };
    const ciphertext = Buffer.concat([cipher.update(JSON.stringify(payload), 'utf8'), cipher.final()]);
    const token = Buffer.concat([iv, cipher.getAuthTag(), ciphertext]).toString('base64url');

    expect(createSealer(secret).open('access', token)).toEqual(payload);
  });

  it('rejects changed, expired and wrong-kind tokens', () => {
    vi.spyOn(Date, 'now').mockReturnValue(1_700_000_000_000);
    const sealer = createSealer(secret);
    const token = sealer.seal('code', { value: 'one' }, 60);
    expect(sealer.open('code', token)).toMatchObject({ value: 'one', exp: 1_700_000_060 });
    expect(sealer.open('access', token)).toBeNull();
    expect(createSealer('other-secret').open('code', token)).toBeNull();

    const changed = Buffer.from(token, 'base64url');
    changed[changed.length - 1] = changed[changed.length - 1]! ^ 1;
    expect(sealer.open('code', changed.toString('base64url'))).toBeNull();
    expect(sealer.open('code', 'invalid')).toBeNull();

    vi.spyOn(Date, 'now').mockReturnValue(1_700_000_061_000);
    expect(sealer.open('code', token)).toBeNull();
  });

  it('verifies client signatures', () => {
    const sealer = createSealer(secret);
    const signature = sealer.sign('client-1');
    expect(sealer.verifySignature('client-1', signature)).toBe(true);
    expect(sealer.verifySignature('client-2', signature)).toBe(false);
  });
});
