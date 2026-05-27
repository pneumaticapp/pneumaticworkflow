/* eslint-disable */
/* prettier-ignore */
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

jest.mock('../getErrorMessage', () => ({
  getErrorMessage: jest.fn((err: Error) => err.message),
}));

jest.mock('../createId', () => ({
  createUniqueId: jest.fn(() => 'generated-id'),
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

    it('uploads multiple files in parallel', async () => {
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

  describe('validation', () => {
    it('rejects files over MAX_FILE_SIZE', async () => {
      const bigContent = new ArrayBuffer(MAX_FILE_SIZE + 1);
      const bigFile = new File([bigContent], 'huge.zip', { type: 'application/zip' });

      const result = await uploadFiles([bigFile]);

      expect(mockUploadFileToFileService).not.toHaveBeenCalled();
      expect(mockNotificationManager.warning).toHaveBeenCalledWith({
        message: 'file-upload.max-file-size-error',
      });
      expect(result).toEqual([]);
    });

    it('runs custom validators and rejects on failure', async () => {
      const validator = jest.fn().mockResolvedValue('Custom error');
      const file = new File(['data'], 'bad.exe', { type: 'application/octet-stream' });

      const result = await uploadFiles([file], [validator]);

      expect(validator).toHaveBeenCalledWith(file);
      expect(mockUploadFileToFileService).not.toHaveBeenCalled();
      expect(mockNotificationManager.warning).toHaveBeenCalledWith({
        message: 'Custom error',
      });
      expect(result).toEqual([]);
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
    });
  });

  describe('storage disabled', () => {
    it('shows warning and returns empty when isEnvStorage is false', async () => {
      mockIsEnvStorage = false;

      const file = new File(['data'], 'file.pdf', { type: 'application/pdf' });
      const result = await uploadFiles([file]);

      expect(mockUploadFileToFileService).not.toHaveBeenCalled();
      expect(mockNotificationManager.warning).toHaveBeenCalledWith({
        message: 'file-upload.error-storage',
      });
      expect(result).toEqual([]);
    });
  });

  describe('error handling', () => {
    it('catches upload error and shows notification', async () => {
      const error = new Error('Network error');
      mockUploadFileToFileService.mockRejectedValue(error);

      const file = new File(['data'], 'fail.pdf', { type: 'application/pdf' });
      const result = await uploadFiles([file]);

      expect(mockNotificationManager.notifyApiError).toHaveBeenCalledWith(
        error,
        { message: 'Network error' },
      );
      expect(result).toEqual([]);
    });

    it('filters out failed uploads from results', async () => {
      mockUploadFileToFileService
        .mockResolvedValueOnce({ publicUrl: 'https://cdn/ok.pdf', fileId: 'ok-id' })
        .mockRejectedValueOnce(new Error('fail'));

      const files = [
        new File(['a'], 'ok.pdf', { type: 'application/pdf' }),
        new File(['b'], 'fail.pdf', { type: 'application/pdf' }),
      ];
      const result = await uploadFiles(files);

      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('ok-id');
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
        filename: 'generated-id',
      });
      expect(result[0].name).toBe('generated-id');
    });
  });
});
