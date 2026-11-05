export const UPLOAD_TTL_SECONDS = 60 * 60;
export const UPLOAD_RETENTION_SECONDS = 24 * 60 * 60;

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

export interface UploadRecord {
  uploadId: string;
  keyHash: string;
  filename: string | null;
  expiresAt: number;
  file: UploadedFile | null;
}
