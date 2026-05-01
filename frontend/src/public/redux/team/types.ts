import { EOptionTypes } from '../../components/UI/form/UsersDropdown';
import { ETaskPerformerType } from '../../types/template';

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

export enum TeamPages {
  Users = 'users',
  Groups = 'groups',
}

export interface UserInvitePayload {
  email: string;
  type: InvitesType;
  groups?: number[];
}

export type TInviteUsersPayload = {
  invites: UserInvitePayload[];
  withGeneralLoader?: boolean;
  withSuccessNotification?: boolean;
  onStartUploading?(): void;
  onEndUploading?(): void;
  onError?(): void;
};

export interface IGroupDropdownOption extends Omit<IGroup, 'type'> {
  optionType: EOptionTypes.Group;
  label: string;
  value: string;
  type: ETaskPerformerType.UserGroup;
}