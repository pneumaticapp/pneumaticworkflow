import type { RemoteFile } from './files.js';
import type { UploadedFile, UploadRecord, UploadStatus } from './uploads.js';

export type RemoteFetcher = (url: URL, maxBytes: number) => Promise<RemoteFile>;

export interface UploadLinks {
  create(filename?: string): Promise<{ uploadId: string; uploadUrl: string; expiresAt: number }>;
  get(uploadId: string): Promise<UploadStatus | undefined>;
}

// State shared by every request; a deployment with several replicas needs implementations backed by one store.

export type ReplayKind = 'code' | 'refresh' | 'family' | 'rotation';

export interface ReplayStore {
  isHealthy(): Promise<boolean>;
  isUsed(kind: ReplayKind, id: string): Promise<boolean>;
  // Records the first use atomically; false when the ID was already used or has expired.
  markUsed(kind: ReplayKind, id: string, exp: number): Promise<boolean>;
}

// Sliding one-minute window per key.
export interface RateLimiter {
  acquire(key: string): Promise<boolean>;
  isExhausted(key: string): Promise<boolean>;
}

// `scope` separates independent limits that share one backend.
export type RateLimiterFactory = (scope: string, limitPerMinute: number) => RateLimiter;

// Records outlive expiresAt by UPLOAD_RETENTION_SECONDS; claim is an atomic lease that lapses on its own.
export interface UploadStore {
  create(keyHash: string, filename: string | null, ttlSeconds: number): Promise<UploadRecord>;
  get(uploadId: string): Promise<UploadRecord | undefined>;
  claim(uploadId: string, leaseSeconds: number): Promise<string | null>;
  complete(uploadId: string, leaseId: string, file: UploadedFile): Promise<boolean>;
  release(uploadId: string, leaseId: string): Promise<void>;
}
