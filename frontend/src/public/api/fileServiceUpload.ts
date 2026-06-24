import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export interface IFileServiceUploadRequest {
  file: File | Blob;
  filename: string;
}

export interface IFileServiceUploadResponse {
  publicUrl: string;
  fileId: string;
}

export async function uploadFileToFileService({
  file,
  filename,
}: IFileServiceUploadRequest): Promise<IFileServiceUploadResponse> {
  const {
    api: {
      urls: { fileServiceUpload },
    },
  } = getBrowserConfigEnv();

  const formData = new FormData();
  formData.append('file', file, filename);

  const data = await commonRequest<IFileServiceUploadResponse>(
    fileServiceUpload,
    {
      method: 'POST',
      data: formData,
    },
    {
      type: 'fileService',
      shouldThrow: true,
    },
  );

  return {
    publicUrl: data.publicUrl,
    fileId: data.fileId,
  };
}
