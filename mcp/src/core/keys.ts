import { createHash } from 'node:crypto';

// Caches, limiters and stores key API keys by hash so the raw key never sits in a map.
export const hashApiKey = (apiKey: string) => createHash('sha256').update(apiKey).digest('hex');
