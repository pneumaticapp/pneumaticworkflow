export interface UserInviteResponse {
  id: string;
}

export enum ErrorCode {
  Validation = 'validation_error',
  Accepted = 'invite_already_accepted',
}
