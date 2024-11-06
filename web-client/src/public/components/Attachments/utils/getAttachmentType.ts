/* eslint-disable */
/* prettier-ignore */
import { TAttachmentType } from '../../../types/attachments';

export function getAttachmentTypeByFilename(filename: string): TAttachmentType | null {
  const fileExtension = getFileExtension(filename).toUpperCase();
  if (!fileExtension) {
    return null;
  }

  return getAttachemntTypeMap.find(({ check }) => check(fileExtension))?.type || 'file';
}

export function getAttachmentTypeByUrl(url: string): TAttachmentType | null {
  const fileExtension = getUrlFileExtension(url).toUpperCase();
  if (!fileExtension) {
    return null;
  }

  return getAttachemntTypeMap.find(({ check }) => check(fileExtension))?.type || 'file';
}

function getFileExtension(filename: string) {
  const executedSubstring = /^.+\.([^.\/]+)$/.exec(filename);

  return executedSubstring == null ? '' : executedSubstring[1];
}

function getUrlFileExtension(url: string) {
  const regEx = /(?:(?:https?|ftp):\/\/)?[a-z0-9.-]+\.[a-z]{2,}\/\S*?\.*\.([a-zA-Z0-9]+)(?=\s|,|$)/;

  return regEx.exec(url)?.[1] || '';
}

const VIDEO_FILE_EXTENSIONS = [
  'MP4',
  'MOV',
  'WMV',
  'AVI',
  'FLV',
  'F4V',
  'SWF',
  'MKV',
  'WEBM',
];

const IMAGE_FILE_EXTENSIONS = [
  'JPG',
  'JPEG',
  'PNG',
  'GIF',
];

const getAttachemntTypeMap: { check(fileExtension: string): boolean; type: TAttachmentType }[] = [
  {
    check: (fileExtension: string) => IMAGE_FILE_EXTENSIONS.some(extension => extension === fileExtension),
    type: 'image',
  },
  {
    check: (fileExtension: string) => VIDEO_FILE_EXTENSIONS.some(extension => extension === fileExtension),
    type: 'video',
  },
  {
    check: () => true,
    type: 'file',
  },
];
