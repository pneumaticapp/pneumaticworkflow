import { createCipheriv, createDecipheriv, createHmac, hkdfSync, randomBytes, timingSafeEqual } from 'node:crypto';

import { nowSeconds } from '../core/time.js';

const IV_LENGTH = 12;
const TAG_LENGTH = 16;

export type SealedKind = 'client' | 'code' | 'access' | 'refresh' | 'upload';

interface SealedEnvelope {
  kind: SealedKind;
  exp?: number;
}

export function createSealer(secret: string) {
  const encryptionKey = Buffer.from(hkdfSync('sha256', secret, 'pneumatic-mcp', 'seal', 32));
  const signingKey = Buffer.from(hkdfSync('sha256', secret, 'pneumatic-mcp', 'sign', 32));
  const sign = (value: string) => createHmac('sha256', signingKey).update(value).digest('base64url');

  return {
    seal<T extends object>(kind: SealedKind, payload: T, ttlSeconds?: number): string {
      const envelope = { ...payload, kind, exp: ttlSeconds === undefined ? undefined : nowSeconds() + ttlSeconds };
      const iv = randomBytes(IV_LENGTH);
      const cipher = createCipheriv('aes-256-gcm', encryptionKey, iv);
      const ciphertext = Buffer.concat([cipher.update(JSON.stringify(envelope), 'utf8'), cipher.final()]);
      // Existing tokens store IV, authentication tag, then ciphertext.
      return Buffer.concat([iv, cipher.getAuthTag(), ciphertext]).toString('base64url');
    },

    open<T extends object>(kind: SealedKind, token: string): (T & SealedEnvelope) | null {
      try {
        const bytes = Buffer.from(token, 'base64url');
        if (bytes.length <= IV_LENGTH + TAG_LENGTH) {
          return null;
        }
        const iv = bytes.subarray(0, IV_LENGTH);
        const tag = bytes.subarray(IV_LENGTH, IV_LENGTH + TAG_LENGTH);
        const ciphertext = bytes.subarray(IV_LENGTH + TAG_LENGTH);
        const decipher = createDecipheriv('aes-256-gcm', encryptionKey, iv);
        decipher.setAuthTag(tag);
        const plaintext = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
        const payload = JSON.parse(plaintext.toString('utf8')) as T & SealedEnvelope;
        if (payload.kind !== kind) {
          return null;
        }
        if (payload.exp !== undefined && payload.exp < nowSeconds()) {
          return null;
        }
        return payload;
      } catch {
        return null;
      }
    },

    sign,

    verifySignature(value: string, signature: string): boolean {
      const expected = Buffer.from(sign(value));
      const actual = Buffer.from(signature);
      return expected.length === actual.length && timingSafeEqual(expected, actual);
    },
  };
}

export type Sealer = ReturnType<typeof createSealer>;
