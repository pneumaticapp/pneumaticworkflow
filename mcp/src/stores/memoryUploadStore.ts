import { randomUUID } from 'node:crypto';

import { ConnectorError } from '../core/errors.js';
import { UPLOAD_RETENTION_SECONDS, type UploadRecord, type UploadStore } from '../core/ports.js';
import { nowSeconds } from '../core/time.js';

const MAX_ENTRIES = 10_000;
const MAX_PENDING_PER_KEY = 20;

// Per process: an upload link opened on another replica would not be found.
export function createMemoryUploadStore(): UploadStore {
  const entries = new Map<string, UploadRecord>();
  const leases = new Map<string, { leaseId: string; until: number }>();

  function prune() {
    const now = nowSeconds();
    for (const [uploadId, entry] of entries) {
      if (entry.expiresAt + UPLOAD_RETENTION_SECONDS < now) {
        entries.delete(uploadId);
        leases.delete(uploadId);
      }
    }
  }

  const holds = (uploadId: string, leaseId: string) => {
    const lease = leases.get(uploadId);
    return lease !== undefined && lease.leaseId === leaseId && lease.until >= nowSeconds();
  };

  return {
    async create(keyHash, filename, ttlSeconds) {
      prune();
      const now = nowSeconds();
      const pending = [...entries.values()].filter(
        (entry) => entry.keyHash === keyHash && !entry.file && entry.expiresAt >= now,
      ).length;
      if (pending >= MAX_PENDING_PER_KEY || entries.size >= MAX_ENTRIES) {
        throw new ConnectorError(
          'rate_limited',
          'Too many open upload links; use or let the existing ones expire first',
        );
      }
      const record: UploadRecord = {
        uploadId: randomUUID(),
        keyHash,
        filename,
        expiresAt: now + ttlSeconds,
        file: null,
      };
      entries.set(record.uploadId, record);
      return { ...record };
    },
    async get(uploadId) {
      prune();
      const entry = entries.get(uploadId);
      return entry && { ...entry };
    },
    async claim(uploadId, leaseSeconds) {
      const entry = entries.get(uploadId);
      const now = nowSeconds();
      const lease = leases.get(uploadId);
      if (!entry || entry.file || entry.expiresAt < now || (lease && lease.until >= now)) {
        return null;
      }
      const leaseId = randomUUID();
      leases.set(uploadId, { leaseId, until: now + leaseSeconds });
      return leaseId;
    },
    async complete(uploadId, leaseId, file) {
      const entry = entries.get(uploadId);
      if (!entry || entry.file || !holds(uploadId, leaseId)) {
        return false;
      }
      entry.file = file;
      leases.delete(uploadId);
      return true;
    },
    async release(uploadId, leaseId) {
      if (leases.get(uploadId)?.leaseId === leaseId) {
        leases.delete(uploadId);
      }
    },
  };
}
