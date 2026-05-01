import { ESubscriptionPlan } from './account';

export type TUserType = 'user' | 'guest' | 'group';
export interface IUnsavedUser {
  id?: number;
  isAccountOwner?: boolean;
  account: IAccount;
  email: string;
  token: string;
  firstName: string;
  lastName: string;
  phone: string;
  photo: string;
  status?: EUserStatus;
  invite?: UserInvite;
  isAdmin?: boolean;
  hasWorkflowViewerAccess?: boolean;
  hasWorkflowStarterAccess?: boolean;
  type: TUserType;
  language: string;
  timezone: string;
  dateFmt: string;
  dateFdw: string;
}

export enum EUserDropdownOptionType {
  User = 'user',
  UserGroup = 'group',
}

export type TUserListItem = Pick<
  IUnsavedUser,
  | 'email'
  | 'isAdmin'
  | 'isAccountOwner'
  | 'firstName'
  | 'lastName'
  | 'phone'
  | 'photo'
  | 'invite'
  | 'type'
> & {
  id: number;
  status: EUserStatus;
  vacation?: IUserVacation | null;
};

export type TAccountLeaseLevel = 'standard' | 'partner' | 'tenant';

export interface IAccount {
  id?: number;
  dateJoined?: string;
  name: string;
  isSubscribed: boolean;
  billingSync: boolean;
  isBlocked?: boolean;
  isVerified?: boolean;
  tenantName: string;
  billingPlan: ESubscriptionPlan;
  plan: ESubscriptionPlan;
  planExpiration: string | null;
  leaseLevel: TAccountLeaseLevel;
  logoSm: string | null;
  logoLg: string | null;
  trialEnded: boolean;
  trialIsActive: boolean;
}

interface UserInvite {
  id: string;
  byUsername: string;
  dateCreated: string;
  invitedBy: number | null;
  invitedFrom: string;
}

export type TUserInvited = Pick<IUnsavedUser, 'firstName' | 'lastName' | 'timezone'> & {
  password: string;
};

export enum EUserStatus {
  Invited = 'invited',
  Active = 'active',
  Deleted = 'deleted',
  Registration = 'registration',
  Inactive = 'inactive',
  External = 'external',
}

export const enum EAbsenceStatus {
  Active = 'active',
  Vacation = 'vacation',
  SickLeave = 'sick_leave',
}

export interface IUserVacation {
  startDate: string | null;
  endDate: string | null;
  absenceStatus: string;
  substituteUserIds: number[];
}

export function isUserAbsent(user: { vacation?: IUserVacation | null }): boolean {
  if (!user.vacation) return false;
  return user.vacation.absenceStatus !== EAbsenceStatus.Active;
}

export type TUserId = {
  id: number;
};

export enum EUserListSorting {
  NameAsc = 'team-name-asc',
  NameDesc = 'team-name-desc',
  Status = 'team-group-status',
}

export enum EGroupsListSorting {
  NameAsc = 'group-name-asc',
  NameDesc = 'group-name-desc',
}

export interface ICreateUserRequest {
  email: string;
  password?: string;
  phone?: string;
  photo?: string;
  firstName?: string;
  lastName?: string;
  isAdmin?: boolean;
  isTasksDigestSubscriber?: boolean;
  isDigestSubscriber?: boolean;
  isNewslettersSubscriber?: boolean;
  isSpecialOffersSubscriber?: boolean;
  isNewTasksSubscriber?: boolean;
  isCompleteTasksSubscriber?: boolean;
  isCommentsMentionsSubscriber?: boolean;
  language?: string;
  timezone?: string;
  dateFmt?: string;
  dateFdw?: number;
  groups?: number[];
}

export interface IUserResponse {
  id: number;
  email: string;
  phone: string;
  photo: string;
  firstName: string;
  lastName: string;
  type: TUserType;
  dateJoined: string;
  dateJoinedTsp: number;
  isAdmin: boolean;
  isAccountOwner: boolean;
  isTasksDigestSubscriber: boolean;
  isDigestSubscriber: boolean;
  isNewslettersSubscriber: boolean;
  isSpecialOffersSubscriber: boolean;
  isNewTasksSubscriber: boolean;
  isCompleteTasksSubscriber: boolean;
  isCommentsMentionsSubscriber: boolean;
  language: string;
  timezone: string;
  dateFmt: string;
  dateFdw: number;
  groups: number[];
  invite: UserInvite | null;
  vacation?: IUserVacation | null;
}