export enum InvitesType {
  Google = 'google',
  Microsoft = 'microsoft',
  Email = 'email',
}

export interface UserInvite {
  email: string;
  firstName?: string;
  id: number;
  jobTitle?: string;
  lastName?: string;
  photo?: string;
  source: InvitesType;
}

export interface IGroup {
  id: number;
  name: string;
  photo: string | null;
  users: number[];
}

export enum ETeamPages {
  Users = 'users',
  Groups = 'groups',
}

export interface UserInvitePayload {
  email: string;
  type: InvitesType;
  groups?: number[];
}