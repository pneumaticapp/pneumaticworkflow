import imageCompression from 'browser-image-compression';
import { logger } from './logger';

import { NotificationManager } from '../components/UI/Notifications';
import { generateAttachmentUploadUrl, IAttachmentUploadUrlResponse } from '../api/generateAttachmentUploadUrl';
import { publishAttachmentLink, IPublishAttachmentLinkResponse } from '../api/publishAttachmentLink';
import { createUniqueId } from './createId';
import { isEnvStorage } from '../constants/enviroment';

export type TUploadedFile = {
  id: number;
  name: string;
  url: string;
  thumbnailUrl?: string;
  size: number;
  isRemoved?: boolean;
};

export const MAX_FILE_SIZE = 100 * 1024 * 1024;
const MAX_THUMBNAIL_WIDTH_OR_HEIGHT = 160;

export const uploadUserAvatar = async (file: Blob | File, accountId: number,) => {
  const thumbnail = await getThumbnail(file);

  return uploadFiles([thumbnail || file], accountId!);
}

export const uploadFiles = async (files: Blob[] | FileList, accountId: number, validators?: ((file: Blob | File) => Promise<string>)[]) => {
  const uploadFile = async (file: Blob | File): Promise<TUploadedFile | undefined> => {
    if (!isEnvStorage) {
      NotificationManager.warning({ message: 'file-upload.error-storage' });

      return undefined;
    }

    const filename =  file instanceof File ? file.name : createUniqueId('file-xxxyxx');

    if (file.size > MAX_FILE_SIZE) {
      NotificationManager.warning({ message: 'file-upload.max-file-size-error' });

      return undefined;
    }

    const errorMessages = await Promise.all(validators?.map(validate => validate(file)) || []);

    if (errorMessages.some(Boolean)) {
      errorMessages.forEach(message => NotificationManager.warning({ message }));

      return undefined;
    }

    try {
      const { id, fileUploadUrl } = await generateAttachmentUploadUrl({
        accountId,
        filename,
        thumbnail: false,
        contentType: file.type,
        size: file.size,
      }) as IAttachmentUploadUrlResponse;

      const sendToGoogleCloudRequests = [
        sendFileToGoogleCloud(fileUploadUrl, file),
      ].filter(Boolean) as Promise<string>[];

      await Promise.all(sendToGoogleCloudRequests);

      const { url } = await publishAttachmentLink(id) as IPublishAttachmentLinkResponse;

      return {
        id,
        name: filename,
        url,
        size: file.size,
      };
    } catch (error) {
      logger.error('failed to upload file:', error);
      NotificationManager.warning({ message: 'file-upload.error' });

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

const sendFileToGoogleCloud = (signedUrl: string, file: File | Blob) => {
  return fetch(signedUrl,
    {
      method: 'PUT',
      headers: {
        'Content-Type': file.type,
      },
      body: file,
    },
  ).then(response => {
    if (!response.ok) {
      throw Error(response.statusText);
    }

    return response.statusText;
  });
};
