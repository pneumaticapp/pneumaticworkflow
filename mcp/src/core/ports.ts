export interface RemoteFile {
  data: Buffer;
  contentType?: string;
  filename?: string;
}

export type RemoteFetcher = (url: URL, maxBytes: number) => Promise<RemoteFile>;

export interface UploadedFile {
  fileId: string;
  name: string;
  contentType: string;
  size: number;
  url: string;
}

export interface UploadStatus {
  uploadId: string;
  status: 'pending' | 'ready' | 'expired';
  filename: string | null;
  expiresAt: number;
  file: UploadedFile | null;
}

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

// Sliding one-minute window per key; `scope` separates independent limits sharing one backend.
export interface RateLimiter {
  acquire(key: string): Promise<boolean>;
  exhausted(key: string): Promise<boolean>;
}

export type RateLimiterFactory = (scope: string, limitPerMinute: number) => RateLimiter;

export interface UploadRecord {
  uploadId: string;
  keyHash: string;
  filename: string | null;
  expiresAt: number;
  file: UploadedFile | null;
}

// Rules every implementation keeps:
// - create fails with ConnectorError('rate_limited') when the key already has 20 pending, unexpired links;
// - get returns pending records until UPLOAD_RETENTION_SECONDS after expiresAt (so status can say "expired")
//   and ready records for the same retention;
// - claim is one atomic step that succeeds only for a pending, unexpired, unclaimed record (or one whose lease
//   ran out) and returns a lease ID; a lease expires on its own, so a crashed process cannot block the link;
// - complete and release act only for the current lease holder.
export interface UploadStore {
  create(keyHash: string, filename: string | null, ttlSeconds: number): Promise<UploadRecord>;
  get(uploadId: string): Promise<UploadRecord | undefined>;
  claim(uploadId: string, leaseSeconds: number): Promise<string | null>;
  complete(uploadId: string, leaseId: string, file: UploadedFile): Promise<boolean>;
  release(uploadId: string, leaseId: string): Promise<void>;
}

export const UPLOAD_TTL_SECONDS = 60 * 60;
export const UPLOAD_RETENTION_SECONDS = 24 * 60 * 60;

export interface PeopleDirectory {
  users: ReadonlyMap<number, string>;
  groups: ReadonlyMap<number, string>;
}
