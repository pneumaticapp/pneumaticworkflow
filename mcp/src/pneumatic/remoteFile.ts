import { lookup as dnsLookup } from 'node:dns';
import type { IncomingMessage } from 'node:http';
import { Agent, request } from 'node:https';
import { BlockList, isIP, type LookupFunction } from 'node:net';

import { ConnectorError } from '../core/errors.js';
import { filenameFromDisposition, mediaType } from '../core/files.js';
import type { RemoteFetcher } from '../core/ports.js';
import { USER_AGENT } from './client.js';

const FETCH_TIMEOUT_MS = 30_000;
const MAX_REDIRECTS = 3;
const REDIRECT_STATUSES = new Set([301, 302, 303, 307, 308]);

// A dedicated agent keeps NODE_USE_ENV_PROXY from routing around the address check.
const agent = new Agent({ keepAlive: false });

const blockList = new BlockList();
for (const [network, prefix] of [
  ['0.0.0.0', 8],
  ['10.0.0.0', 8],
  ['100.64.0.0', 10],
  ['127.0.0.0', 8],
  ['169.254.0.0', 16],
  ['172.16.0.0', 12],
  ['192.0.0.0', 24],
  ['192.0.2.0', 24],
  ['192.88.99.0', 24],
  ['192.168.0.0', 16],
  ['198.18.0.0', 15],
  ['198.51.100.0', 24],
  ['203.0.113.0', 24],
  ['224.0.0.0', 4],
  ['240.0.0.0', 4],
] as const) {
  blockList.addSubnet(network, prefix, 'ipv4');
}
for (const [network, prefix] of [
  ['::', 96],
  ['::ffff:0:0:0', 96],
  ['64:ff9b::', 96],
  ['64:ff9b:1::', 48],
  ['100::', 64],
  ['2001::', 23],
  ['2001:db8::', 32],
  ['2002::', 16],
  ['fc00::', 7],
  ['fe80::', 10],
  ['fec0::', 10],
  ['ff00::', 8],
] as const) {
  blockList.addSubnet(network, prefix, 'ipv6');
}

export function isPublicAddress(address: string): boolean {
  const family = isIP(address);
  if (!family) {
    return false;
  }
  return !blockList.check(address, family === 4 ? 'ipv4' : 'ipv6');
}

export function assertPublicHttpsUrl(url: URL): void {
  const host = url.hostname.replace(/^\[|\]$/g, '');
  if (
    url.protocol !== 'https:' ||
    !host ||
    (url.port && url.port !== '443') ||
    url.username ||
    url.password ||
    (isIP(host) && !isPublicAddress(host))
  ) {
    throw new ConnectorError(
      'invalid_arguments',
      'Expected a public HTTPS URL on port 443 without credentials or a private address',
    );
  }
}

// Validate every resolved address at connect time, so DNS rebinding cannot reach internal hosts.
export const publicLookup: LookupFunction = (hostname, options, callback) => {
  dnsLookup(hostname, { ...options, all: true }, (error, addresses) => {
    if (error) {
      callback(error, '');
      return;
    }
    const [first] = addresses;
    if (!first || addresses.some(({ address }) => !isPublicAddress(address))) {
      callback(Object.assign(new Error(`${hostname} resolves to a non-public address`), { code: 'EBLOCKED' }), '');
      return;
    }
    if (options.all) {
      callback(null, addresses);
    } else {
      callback(null, first.address, first.family);
    }
  });
};

function get(url: URL, signal: AbortSignal): Promise<IncomingMessage> {
  return new Promise((resolve, reject) => {
    const req = request(url, {
      method: 'GET',
      headers: { Accept: '*/*', 'User-Agent': USER_AGENT },
      lookup: publicLookup,
      agent,
      signal,
    });
    req.on('response', resolve);
    req.on('error', reject);
    req.end();
  });
}

async function readBody(response: IncomingMessage, maxBytes: number): Promise<Buffer> {
  const declared = Number(response.headers['content-length']);
  if (Number.isFinite(declared) && declared > maxBytes) {
    response.destroy();
    throw new ConnectorError('too_large', `The source file exceeds ${maxBytes} bytes`);
  }
  const chunks: Buffer[] = [];
  let total = 0;
  for await (const chunk of response) {
    total += (chunk as Buffer).length;
    if (total > maxBytes) {
      response.destroy();
      throw new ConnectorError('too_large', `The source file exceeds ${maxBytes} bytes`);
    }
    chunks.push(chunk as Buffer);
  }
  return Buffer.concat(chunks);
}

function filenameFromUrl(url: URL): string | undefined {
  const segment = url.pathname.split('/').filter(Boolean).at(-1);
  if (!segment) {
    return undefined;
  }
  try {
    return decodeURIComponent(segment);
  } catch {
    return segment;
  }
}

export const fetchRemoteFile: RemoteFetcher = async (source, maxBytes) => {
  const signal = AbortSignal.timeout(FETCH_TIMEOUT_MS);
  let url = source;
  for (let redirects = 0; ; redirects += 1) {
    assertPublicHttpsUrl(url);
    let response: IncomingMessage;
    try {
      response = await get(url, signal);
    } catch (error) {
      if (signal.aborted) {
        throw new ConnectorError('source_error', 'The source URL did not respond within the time limit');
      }
      if ((error as NodeJS.ErrnoException).code === 'EBLOCKED') {
        throw new ConnectorError('invalid_arguments', 'The source host resolves to a non-public address');
      }
      throw new ConnectorError('source_error', 'The source URL is unreachable');
    }
    const status = response.statusCode ?? 0;
    const location = response.headers.location;
    if (REDIRECT_STATUSES.has(status) && location) {
      response.resume();
      if (redirects >= MAX_REDIRECTS) {
        throw new ConnectorError('source_error', 'The source URL redirects too many times');
      }
      try {
        url = new URL(location, url);
      } catch {
        throw new ConnectorError('source_error', 'The source URL redirects to an invalid location');
      }
      continue;
    }
    if (status !== 200) {
      response.resume();
      throw new ConnectorError('source_error', `The source URL returned HTTP ${status}`);
    }
    let data: Buffer;
    try {
      data = await readBody(response, maxBytes);
    } catch (error) {
      if (signal.aborted) {
        throw new ConnectorError('source_error', 'The source URL did not respond within the time limit');
      }
      throw error instanceof ConnectorError
        ? error
        : new ConnectorError('source_error', 'The source download was interrupted');
    }
    return {
      data,
      contentType: mediaType(response.headers['content-type']),
      filename: filenameFromDisposition(response.headers['content-disposition']) ?? filenameFromUrl(url),
    };
  }
};
