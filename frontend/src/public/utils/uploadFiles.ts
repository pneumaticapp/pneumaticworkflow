import imageCompression from 'browser-image-compression';
import { logger } from './logger';

import { NotificationManager } from '../components/UI/Notifications';
import { getErrorMessage } from './getErrorMessage';
import { uploadFileToFileService } from '../api/fileServiceUpload';
import { createUniqueId } from './createId';

export type TUploadedFile = {
  id: string;
  name: string;
  url: string;
  thumbnailUrl?: string;
  size: number;
  isRemoved?: boolean;
  error?: string;
};

export const MAX_FILE_SIZE = 100 * 1024 * 1024;
const UPLOAD_BATCH_LIMIT = 3;
const MAX_THUMBNAIL_WIDTH_OR_HEIGHT = 160;

// Internal error markers (not displayed to users — NotificationManager shows localized messages)
const UPLOAD_ERROR_FILE_TOO_LARGE = 'Max file size exceeded';
const UPLOAD_ERROR_VALIDATION = 'Validation failed';

export const uploadUserAvatar = async (file: Blob | File) => {
  const thumbnail = await getThumbnail(file);

  return uploadFiles([thumbnail || file]);
};

export const uploadFiles = async (
  files: Blob[] | FileList,
  validators?: ((file: Blob | File) => Promise<string>)[],
) => {
  const uploadFile = async (file: Blob | File): Promise<TUploadedFile> => {
    const filename = file instanceof File ? file.name : createUniqueId('file-xxxyxx');



    if (file.size > MAX_FILE_SIZE) {
      NotificationManager.warning({ message: 'file-upload.max-file-size-error' });
      return { id: createUniqueId('error-'), name: filename, url: '', size: file.size, error: UPLOAD_ERROR_FILE_TOO_LARGE };
    }

    const errorMessages = await Promise.all(validators?.map((validate) => validate(file)) || []);

    if (errorMessages.some(Boolean)) {
      errorMessages.forEach((message) => NotificationManager.warning({ message }));
      return {
        id: createUniqueId('error-'),
        name: filename,
        url: '',
        size: file.size,
        error: errorMessages.find(Boolean) || UPLOAD_ERROR_VALIDATION,
      };
    }

    try {
      const { publicUrl, fileId } = await uploadFileToFileService({ file, filename });

      return {
        id: fileId,
        name: filename,
        url: publicUrl,
        size: file.size,
      };
    } catch (error) {
      logger.error('failed to upload file:', error);
      const message = getErrorMessage(error);
      NotificationManager.notifyApiError(error, { message });
      return { id: createUniqueId('error-'), name: filename, url: '', size: file.size, error: message };
    }
  };

  const uploadedFiles: TUploadedFile[] = [];
  const filesArray = Array.from(files);
  const limit = UPLOAD_BATCH_LIMIT;
  const chunks = Array.from(
    { length: Math.ceil(filesArray.length / limit) },
    (_, i) => filesArray.slice(i * limit, (i + 1) * limit),
  );

  await chunks.reduce(async (prev, chunk) => {
    await prev;
    const results = await Promise.all(chunk.map(uploadFile));
    uploadedFiles.push(...results);
  }, Promise.resolve());

  return uploadedFiles;
};

export const getThumbnail = async (file: Blob) => {
  const thumbnailMimeTypes = ['image/jpeg', 'image/png', 'image/svg+xml'];

  if (!thumbnailMimeTypes.includes(file.type)) {
    return null;
  }

  if (file.type === 'image/svg+xml') {
    return file;
  }

  const compressOptions = {
    useWebWorker: true,
    maxWidthOrHeight: MAX_THUMBNAIL_WIDTH_OR_HEIGHT,
  };

  return imageCompression(file, compressOptions);
};
