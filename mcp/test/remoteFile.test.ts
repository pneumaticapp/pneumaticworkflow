import { describe, expect, it } from 'vitest';

import { filenameFromDisposition } from '../src/core/files.js';
import { assertPublicHttpsUrl, fetchRemoteFile, isPublicAddress, publicLookup } from '../src/pneumatic/remoteFile.js';

describe('isPublicAddress', () => {
  it('accepts public addresses', () => {
    for (const address of ['8.8.8.8', '93.184.216.34', '2606:4700:4700::1111']) {
      expect(isPublicAddress(address), address).toBe(true);
    }
  });

  it('rejects private, loopback, link-local, mapped and reserved addresses', () => {
    for (const address of [
      '127.0.0.1',
      '10.1.2.3',
      '172.20.0.1',
      '192.168.1.1',
      '169.254.169.254',
      '100.64.0.1',
      '0.0.0.0',
      '224.0.0.1',
      '::1',
      '::',
      '::ffff:127.0.0.1',
      'fc00::1',
      'fe80::1',
      'fec0::1',
      '::127.0.0.1',
      '2001:db8::1',
      'not-an-ip',
    ]) {
      expect(isPublicAddress(address), address).toBe(false);
    }
  });
});

describe('assertPublicHttpsUrl', () => {
  it('accepts public HTTPS URLs on the default port', () => {
    expect(() => assertPublicHttpsUrl(new URL('https://example.com/report.pdf'))).not.toThrow();
    expect(() => assertPublicHttpsUrl(new URL('https://example.com:443/a'))).not.toThrow();
  });

  it('rejects other schemes, ports, credentials and private IP literals', () => {
    for (const url of [
      'http://example.com/a',
      'https://example.com:8443/a',
      'https://user:pass@example.com/a',
      'https://127.0.0.1/a',
      'https://[::1]/a',
      'https://169.254.169.254/latest/meta-data',
      'file:///etc/passwd',
    ]) {
      expect(() => assertPublicHttpsUrl(new URL(url)), url).toThrow('public HTTPS URL');
    }
  });
});

describe('filenameFromDisposition', () => {
  it('prefers the RFC 5987 encoded filename', () => {
    expect(
      filenameFromDisposition(`attachment; filename="a.txt"; filename*=UTF-8''%D0%BE%D1%82%D1%87%D1%91%D1%82.pdf`),
    ).toBe('отчёт.pdf');
    expect(filenameFromDisposition('inline; filename="plan v2.docx"')).toBe('plan v2.docx');
    expect(filenameFromDisposition("attachment; filename*=Utf-8''a%20b.txt")).toBe('a b.txt');
    expect(filenameFromDisposition(undefined)).toBeUndefined();
  });
});

describe('publicLookup', () => {
  it('refuses hosts that resolve to non-public addresses at connect time', async () => {
    const error = await new Promise<NodeJS.ErrnoException | null>((resolve) =>
      publicLookup('localhost', { all: true }, (lookupError) => resolve(lookupError)),
    );
    expect(error?.code).toBe('EBLOCKED');
  });
});

describe('fetchRemoteFile', () => {
  it('rejects private IP literals before connecting', async () => {
    await expect(fetchRemoteFile(new URL('https://10.0.0.1/a'), 1024)).rejects.toMatchObject({
      code: 'invalid_arguments',
    });
  });
});
