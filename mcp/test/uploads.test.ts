import { randomBytes } from 'node:crypto';

import { describe, expect, it } from 'vitest';

import { uploadLinksFor } from '../src/http/uploads.js';
import { createSealer } from '../src/http/sealer.js';
import { createMemoryUploadStore } from '../src/stores/memoryUploadStore.js';

describe('uploadLinksFor', () => {
  it('binds upload links to the API key that created them', async () => {
    const sealer = createSealer(randomBytes(32).toString('hex'));
    const store = createMemoryUploadStore();
    const publicUrl = new URL('https://mcp.example.com');
    const owner = uploadLinksFor(store, sealer, publicUrl, 'pn-owner');
    const { uploadId, uploadUrl } = await owner.create('a.txt');
    expect(await owner.get(uploadId)).toMatchObject({ status: 'pending', filename: 'a.txt' });
    expect(await uploadLinksFor(store, sealer, publicUrl, 'pn-other').get(uploadId)).toBeUndefined();

    const token = new URL(uploadUrl).pathname.split('/').at(-1) ?? '';
    expect(sealer.open<{ uploadId: string; apiKey: string }>('upload', token)).toMatchObject({
      uploadId,
      apiKey: 'pn-owner',
    });
    expect(sealer.open('upload', `${token.slice(0, -2)}xx`)).toBeNull();
  });
});
