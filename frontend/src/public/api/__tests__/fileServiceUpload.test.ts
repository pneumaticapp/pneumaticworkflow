// <reference types="jest" />
import { uploadFileToFileService } from '../fileServiceUpload';
import { commonRequest } from '../commonRequest';

jest.mock('../commonRequest', () => ({
  commonRequest: jest.fn(),
}));

jest.mock('../../utils/getConfig', () => ({
  getBrowserConfigEnv: () => ({
    api: {
      urls: {
        fileServiceUpload: '/files/upload',
      },
    },
  }),
}));

describe('fileServiceUpload', () => {
  const mockedCommonRequest = commonRequest as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('sends POST with FormData to file service URL', async () => {
    mockedCommonRequest.mockResolvedValue({
      publicUrl: 'https://cdn.example.com/abc.pdf',
      fileId: 'abc-123',
    });

    const file = new File(['content'], 'report.pdf', { type: 'application/pdf' });
    await uploadFileToFileService({ file, filename: 'report.pdf' });

    expect(mockedCommonRequest).toHaveBeenCalledTimes(1);

    const [url, options, extra] = mockedCommonRequest.mock.calls[0];
    expect(url).toBe('/files/upload');
    expect(options.method).toBe('POST');
    expect(options.data).toBeInstanceOf(FormData);
    expect(extra).toEqual({ type: 'fileService', shouldThrow: true });
  });

  it('appends file to FormData with correct filename', async () => {
    mockedCommonRequest.mockResolvedValue({ publicUrl: '', fileId: '' });

    const file = new File(['data'], 'photo.jpg', { type: 'image/jpeg' });
    await uploadFileToFileService({ file, filename: 'my-photo.jpg' });

    const formData: FormData = mockedCommonRequest.mock.calls[0][1].data;
    const sentFile = formData.get('file') as File;
    expect(sentFile).toBeInstanceOf(File);
    expect(sentFile.name).toBe('my-photo.jpg');
  });

  it('returns publicUrl and fileId from response', async () => {
    mockedCommonRequest.mockResolvedValue({
      publicUrl: 'https://cdn.example.com/file-abc',
      fileId: 'file-abc',
    });

    const file = new File([''], 'doc.txt', { type: 'text/plain' });
    const result = await uploadFileToFileService({ file, filename: 'doc.txt' });

    expect(result).toEqual({
      publicUrl: 'https://cdn.example.com/file-abc',
      fileId: 'file-abc',
    });
  });

  it('propagates errors from commonRequest', async () => {
    mockedCommonRequest.mockRejectedValue(new Error('Network error'));

    const file = new File([''], 'fail.txt', { type: 'text/plain' });

    await expect(
      uploadFileToFileService({ file, filename: 'fail.txt' }),
    ).rejects.toThrow('Network error');
  });

  it('works with Blob instead of File', async () => {
    mockedCommonRequest.mockResolvedValue({
      publicUrl: 'https://cdn.example.com/blob',
      fileId: 'blob-id',
    });

    const blob = new Blob(['blob-data'], { type: 'image/png' });
    const result = await uploadFileToFileService({ file: blob, filename: 'avatar.png' });

    expect(result.fileId).toBe('blob-id');
    expect(mockedCommonRequest).toHaveBeenCalledTimes(1);
  });

  it('propagates file service error with code FILE_003 in payload', async () => {
    const apiError = Object.assign(new Error('File size exceeds limit'), {
      name: 'ApiError',
      data: { code: 'FILE_003', message: 'File size exceeds limit' },
      status: 413,
    });
    mockedCommonRequest.mockRejectedValue(apiError);

    const file = new File(['large'], 'big.zip', { type: 'application/zip' });

    await expect(
      uploadFileToFileService({ file, filename: 'big.zip' }),
    ).rejects.toMatchObject({
      message: 'File size exceeds limit',
      data: { code: 'FILE_003' },
    });
  });

  it('propagates permission error PERM_001 from file service', async () => {
    const apiError = Object.assign(new Error('Permission denied'), {
      name: 'ApiError',
      data: { code: 'PERM_001', message: 'Permission denied' },
      status: 403,
    });
    mockedCommonRequest.mockRejectedValue(apiError);

    const file = new File(['data'], 'secret.pdf', { type: 'application/pdf' });

    await expect(
      uploadFileToFileService({ file, filename: 'secret.pdf' }),
    ).rejects.toMatchObject({
      message: 'Permission denied',
      data: { code: 'PERM_001' },
      status: 403,
    });
  });
});
