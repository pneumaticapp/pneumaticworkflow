import type { PeopleDirectory } from '../core/ports.js';
import type { PneumaticClient } from './client.js';

const TTL_MS = 5 * 60 * 1000;
const FAILURE_TTL_MS = 60 * 1000;
const MAX_ACCOUNTS = 1000;

const cache = new Map<string, { expiresAt: number; directory: Promise<PeopleDirectory> }>();

interface Person {
  id?: unknown;
  first_name?: unknown;
  last_name?: unknown;
  email?: unknown;
  name?: unknown;
}

function personName({ first_name: first, last_name: last, email }: Person): string {
  const full = [first, last].filter((part) => typeof part === 'string' && part.trim()).join(' ');
  return full || (typeof email === 'string' ? email : '');
}

function byId(values: unknown, name: (item: Person) => string): Map<number, string> {
  const map = new Map<number, string>();
  for (const item of Array.isArray(values) ? (values as Person[]) : []) {
    if (typeof item?.id === 'number' && name(item)) {
      map.set(item.id, name(item));
    }
  }
  return map;
}

async function fetchDirectory(client: PneumaticClient): Promise<PeopleDirectory> {
  const [users, groups] = await Promise.all([client.get('/accounts/users'), client.get('/accounts/groups')]);
  return {
    users: byId(users, personName),
    groups: byId(groups, (group) => (typeof group.name === 'string' ? group.name : '')),
  };
}

// Cached per account key across requests; a failed load is not cached and callers fall back to bare IDs.
export function loadPeople(client: PneumaticClient): Promise<PeopleDirectory> {
  const cached = cache.get(client.identity);
  if (cached && cached.expiresAt > Date.now()) {
    return cached.directory;
  }
  cache.delete(client.identity);
  if (cache.size >= MAX_ACCOUNTS) {
    cache.delete(cache.keys().next().value as string);
  }
  const entry = { expiresAt: Date.now() + TTL_MS, directory: fetchDirectory(client) };
  cache.set(client.identity, entry);
  // A failure is remembered briefly so a missing permission does not cost two requests per call.
  entry.directory.catch(() => {
    entry.expiresAt = Math.min(entry.expiresAt, Date.now() + FAILURE_TTL_MS);
  });
  return entry.directory;
}

export function forgetPeople(client: PneumaticClient) {
  cache.delete(client.identity);
}
