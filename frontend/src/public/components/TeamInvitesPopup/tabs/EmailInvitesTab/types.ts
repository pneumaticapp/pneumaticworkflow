export type TUploadingInviteStatus = 'initial' | 'uploading' | 'success' | 'error';
export type TUploadingInvite = {
  id: string;
  email: string;
  status: TUploadingInviteStatus;
};