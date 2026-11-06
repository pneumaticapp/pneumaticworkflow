export enum EInvitesType {
  Google = 'google',
  Microsoft = 'microsoft',
  Email = 'email',
}

export interface IUserInvite {
  email: string;
  firstName?: string;
  id: number;
  jobTitle?: string;
  lastName?: string;
  photo?: string;
  source: EInvitesType;
}

export interface IUserInvitePayload {
  email: string;
  type: EInvitesType;
  groups?: number[];
}

export enum EUserGroupType {
  Regular = 'regular',
  Personal = 'personal',
}

export interface IGroup {
  id: number;
  name: string;
  photo: string | null;
  users: number[];
  type: EUserGroupType;
}
