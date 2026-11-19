export type TAttachmentType = 'file' | 'image' | 'video';

export type TUploadedFile = {
  id: string;
  name: string;
  url: string;
  thumbnailUrl?: string;
  size: number;
  isRemoved?: boolean;
  error?: string;
};
