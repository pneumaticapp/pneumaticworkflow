export enum EInvitesType {
  Google = 'google',
  Microsoft = 'microsoft',
  Email = 'email',
}

export interface IUserInviteMicrosoft {
  id: number;
  email: string;
  source: 'microsoft' | 'google' | 'email';
  firstName?: string;
  lastName?: string;
  photo?: string;
  jobTitle?: string;
}

export interface IUserInvite {
  email: string;
  type: TInviteType;
  firstName?: string;
  lastName?: string;
  avatar?: string;
}

export interface IOAuthInviteView extends IUserInvite {
  avatar: string;
  firstName: string;
  lastName: string;
  phone: string;
  type: 'google';
}

export interface IUserInviteItem {
  id: string;
  invitedBy: number | null;
  byUsername: string;
  dateCreated: string;
  invitedFrom: string;
}

export interface IUserInviteResponse {
  id: string;
}

export type TTeamInvitesPopup = boolean;

export type TInviteType = 'google' | 'microsoft' | 'email';
