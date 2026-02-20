import imageCompression from 'browser-image-compression';
import { logger } from './logger';

import { NotificationManager } from '../components/UI/Notifications';
import { getErrorMessage } from './getErrorMessage';
import { uploadFileToFileService } from '../api/fileServiceUpload';
import { createUniqueId } from './createId';
import { isEnvStorage } from '../constants/enviroment';

export type TUploadedFile = {
  id: string;
  name: string;
  url: string;
  thumbnailUrl?: string;
  size: number;
  isRemoved?: boolean;
};

export const MAX_FILE_SIZE = 100 * 1024 * 1024;
const MAX_THUMBNAIL_WIDTH_OR_HEIGHT = 160;

export const uploadUserAvatar = async (file: Blob | File) => {
  const thumbnail = await getThumbnail(file);

  return uploadFiles([thumbnail || file]);
};

export const uploadFiles = async (
  files: Blob[] | FileList,
  validators?: ((file: Blob | File) => Promise<string>)[],
) => {
  const uploadFile = async (file: Blob | File): Promise<TUploadedFile | undefined> => {
    if (!isEnvStorage) {
      NotificationManager.warning({ message: 'file-upload.error-storage' });

      return undefined;
    }

    const filename = file instanceof File ? file.name : createUniqueId('file-xxxyxx');

    if (file.size > MAX_FILE_SIZE) {
      NotificationManager.warning({ message: 'file-upload.max-file-size-error' });

      return undefined;
    }

    const errorMessages = await Promise.all(validators?.map((validate) => validate(file)) || []);

    if (errorMessages.some(Boolean)) {
      errorMessages.forEach((message) => NotificationManager.warning({ message }));

      return undefined;
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
      NotificationManager.notifyApiError(error, {
        message: getErrorMessage(error),
      });
      return undefined;
    }
  };

  const uploadedFiles = await Promise.all(Array.from(files).map(uploadFile));

  return uploadedFiles.filter(Boolean) as TUploadedFile[];
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
