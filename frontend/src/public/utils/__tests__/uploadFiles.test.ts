// <reference types="jest" />
import { uploadFiles, getThumbnail, MAX_FILE_SIZE } from '../uploadFiles';

const mockUploadFileToFileService = jest.fn();
jest.mock('../../api/fileServiceUpload', () => ({
  uploadFileToFileService: (...args: any[]) => mockUploadFileToFileService(...args),
}));

jest.mock('../../components/UI/Notifications', () => ({
  NotificationManager: { warning: jest.fn(), notifyApiError: jest.fn() },
}));

jest.mock('../logger', () => ({
  logger: { error: jest.fn() },
}));

const FS_ERROR_MAPPER: Record<string, string> = {
  FILE_001: 'file-service.file-not-found',
  FILE_002: 'file-service.access-denied',
  FILE_003: 'file-service.size-exceeded',
  AUTH_001: 'file-service.auth-failed',
  PERM_001: 'file-service.permission-denied',
};

jest.mock('../getErrorMessage', () => ({
  getErrorMessage: jest.fn((err: any) => {
    // Simulate normalizeToCustomError: unwrap ApiError.data
    const code = err?.data?.code || err?.code;
    return FS_ERROR_MAPPER[code] || err?.message || 'Something Went Wrong';
  }),
}));

let idCounter = 0;
jest.mock('../createId', () => ({
  createUniqueId: jest.fn(() => `generated-id-${++idCounter}`),
}));

let mockIsEnvStorage = true;
jest.mock('../../constants/enviroment', () => ({
  get isEnvStorage() { return mockIsEnvStorage; },
}));

import { NotificationManager } from '../../components/UI/Notifications';

const mockNotificationManager = NotificationManager as jest.Mocked<typeof NotificationManager>;

describe('uploadFiles', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsEnvStorage = true;
    idCounter = 0;
  });

  describe('getThumbnail', () => {
    it('returns null if uploaded file is not image', async () => {
      const mockTextFile = new File(['file contents'], 'fileName.txt', { type: 'text/plain' });

      const thumbnail = await getThumbnail(mockTextFile);

      expect(thumbnail).toBe(null);
    });

    it('returns file as-is for SVG', async () => {
      const svg = new File(['<svg></svg>'], 'icon.svg', { type: 'image/svg+xml' });

      const result = await getThumbnail(svg);

      expect(result).toBe(svg);
    });
  });

  describe('successful upload', () => {
    it('calls uploadFileToFileService for each file', async () => {
      mockUploadFileToFileService.mockResolvedValue({
        publicUrl: 'https://cdn.example.com/a.pdf',
        fileId: 'file-abc',
      });
      const file = new File(['content'], 'report.pdf', { type: 'application/pdf' });

      const result = await uploadFiles([file]);

      expect(mockUploadFileToFileService).toHaveBeenCalledTimes(1);
      expect(mockUploadFileToFileService).toHaveBeenCalledWith({
        file,
        filename: 'report.pdf',
      });
      expect(result).toEqual([{
        id: 'file-abc',
        name: 'report.pdf',
        url: 'https://cdn.example.com/a.pdf',
        size: file.size,
      }]);
    });

    it('uploads multiple files', async () => {
      mockUploadFileToFileService
        .mockResolvedValueOnce({ publicUrl: 'https://cdn/1.pdf', fileId: 'id-1' })
        .mockResolvedValueOnce({ publicUrl: 'https://cdn/2.pdf', fileId: 'id-2' });
      const files = [
        new File(['a'], 'file1.pdf', { type: 'application/pdf' }),
        new File(['b'], 'file2.pdf', { type: 'application/pdf' }),
      ];

      const result = await uploadFiles(files);

      expect(mockUploadFileToFileService).toHaveBeenCalledTimes(2);
      expect(result).toHaveLength(2);
    });
  });

  describe('chunked upload', () => {
    it('uploads in chunks of 3', async () => {
      const callOrder: number[] = [];
      mockUploadFileToFileService.mockImplementation(async () => {
        callOrder.push(Date.now());
        return { publicUrl: 'https://cdn/f', fileId: `id-${callOrder.length}` };
      });
      const files = Array.from({ length: 5 }, (_, i) =>
        new File([`content-${i}`], `file${i}.pdf`, { type: 'application/pdf' }),
      );

      const result = await uploadFiles(files);

      expect(mockUploadFileToFileService).toHaveBeenCalledTimes(5);
      expect(result).toHaveLength(5);
    });
  });

  describe('validation', () => {
    it('returns error object for files over MAX_FILE_SIZE', async () => {
      const bigContent = new ArrayBuffer(MAX_FILE_SIZE + 1);
      const bigFile = new File([bigContent], 'huge.zip', { type: 'application/zip' });

      const result = await uploadFiles([bigFile]);

      expect(mockUploadFileToFileService).not.toHaveBeenCalled();
      expect(mockNotificationManager.warning).toHaveBeenCalledWith({
        message: 'file-upload.max-file-size-error',
      });
      expect(result).toHaveLength(1);
      expect(result[0].error).toBe('Max file size exceeded');
      expect(result[0].url).toBe('');
      expect(result[0].name).toBe('huge.zip');
    });

    it('returns error object when custom validator rejects', async () => {
      const validator = jest.fn().mockResolvedValue('Custom error');
      const file = new File(['data'], 'bad.exe', { type: 'application/octet-stream' });

      const result = await uploadFiles([file], [validator]);

      expect(validator).toHaveBeenCalledWith(file);
      expect(mockUploadFileToFileService).not.toHaveBeenCalled();
      expect(mockNotificationManager.warning).toHaveBeenCalledWith({
        message: 'Custom error',
      });
      expect(result).toHaveLength(1);
      expect(result[0].error).toBe('Custom error');
    });

    it('passes files when custom validator returns empty string', async () => {
      const validator = jest.fn().mockResolvedValue('');
      mockUploadFileToFileService.mockResolvedValue({
        publicUrl: 'https://cdn/ok.pdf',
        fileId: 'ok-id',
      });
      const file = new File(['data'], 'ok.pdf', { type: 'application/pdf' });

      const result = await uploadFiles([file], [validator]);

      expect(mockUploadFileToFileService).toHaveBeenCalledTimes(1);
      expect(result).toHaveLength(1);
      expect(result[0].error).toBeUndefined();
    });
  });

  describe('storage disabled', () => {
    it('returns error object when isEnvStorage is false', async () => {
      mockIsEnvStorage = false;
      const file = new File(['data'], 'file.pdf', { type: 'application/pdf' });

      const result = await uploadFiles([file]);

      expect(mockUploadFileToFileService).not.toHaveBeenCalled();
      expect(mockNotificationManager.warning).toHaveBeenCalledWith({
        message: 'file-upload.error-storage',
      });
      expect(result).toHaveLength(1);
      expect(result[0].error).toBe('Storage disabled');
      expect(result[0].url).toBe('');
    });
  });

  describe('error handling', () => {
    it('returns error object on upload failure', async () => {
      const error = new Error('Network error');
      mockUploadFileToFileService.mockRejectedValue(error);
      const file = new File(['data'], 'fail.pdf', { type: 'application/pdf' });

      const result = await uploadFiles([file]);

      expect(mockNotificationManager.notifyApiError).toHaveBeenCalledWith(
        error,
        { message: 'Network error' },
      );
      expect(result).toHaveLength(1);
      expect(result[0].error).toBe('Network error');
      expect(result[0].url).toBe('');
      expect(result[0].name).toBe('fail.pdf');
    });

    it('includes both success and error results', async () => {
      mockUploadFileToFileService
        .mockResolvedValueOnce({ publicUrl: 'https://cdn/ok.pdf', fileId: 'ok-id' })
        .mockRejectedValueOnce(new Error('fail'));
      const files = [
        new File(['a'], 'ok.pdf', { type: 'application/pdf' }),
        new File(['b'], 'fail.pdf', { type: 'application/pdf' }),
      ];

      const result = await uploadFiles(files);

      expect(result).toHaveLength(2);
      expect(result[0].id).toBe('ok-id');
      expect(result[0].error).toBeUndefined();
      expect(result[1].error).toBe('fail');
    });

    it('handles file service error with code FILE_003 (size exceeded) via ApiError', async () => {
      // Simulates real ApiError shape from axios interceptor:
      // ApiError.data = {code, message} (response payload)
      const fsError = Object.assign(new Error('File size exceeds limit'), {
        name: 'ApiError',
        data: { code: 'FILE_003', message: 'File size exceeds limit' },
        status: 413,
      });
      mockUploadFileToFileService.mockRejectedValue(fsError);
      const file = new File(['data'], 'big.zip', { type: 'application/zip' });

      const result = await uploadFiles([file]);

      expect(mockNotificationManager.notifyApiError).toHaveBeenCalledWith(
        fsError,
        { message: 'file-service.size-exceeded' },
      );
      expect(result).toHaveLength(1);
      expect(result[0].error).toBe('file-service.size-exceeded');
      expect(result[0].url).toBe('');
    });

    it('handles file service auth error AUTH_001 via ApiError', async () => {
      const fsError = Object.assign(new Error('Authentication failed'), {
        name: 'ApiError',
        data: { code: 'AUTH_001', message: 'Authentication failed' },
        status: 401,
      });
      mockUploadFileToFileService.mockRejectedValue(fsError);
      const file = new File(['data'], 'secret.pdf', { type: 'application/pdf' });

      const result = await uploadFiles([file]);

      expect(mockNotificationManager.notifyApiError).toHaveBeenCalledWith(
        fsError,
        { message: 'file-service.auth-failed' },
      );
      expect(result).toHaveLength(1);
      expect(result[0].error).toBe('file-service.auth-failed');
    });
  });

  describe('Blob support', () => {
    it('generates filename for Blob using createUniqueId', async () => {
      mockUploadFileToFileService.mockResolvedValue({
        publicUrl: 'https://cdn/blob',
        fileId: 'blob-id',
      });
      const blob = new Blob(['blob-data'], { type: 'image/png' });

      const result = await uploadFiles([blob]);

      expect(mockUploadFileToFileService).toHaveBeenCalledWith({
        file: blob,
        filename: 'generated-id-1',
      });
      expect(result[0].name).toBe('generated-id-1');
    });
  });
});
