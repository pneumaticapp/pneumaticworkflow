import { ESubscriptionPlan } from './account';
import { IUserInviteItem } from './team';

export type TUserType = 'user' | 'guest';
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
  invite?: IUserInviteItem;
  isAdmin?: boolean;
  type: TUserType;
  language: string,
  timezone: string,
  dateFmt: string,
  dateFdw: string,
}

export type TGoogleAuthUserInfo = Partial<
  Pick<IUnsavedUser, 'email' | 'firstName' | 'lastName' | 'phone' | 'photo'>
> & {
  companyName?: string;
};

export type TUserListItem = Pick<
  IUnsavedUser,
  'email' | 'isAdmin' | 'isAccountOwner' | 'firstName' | 'lastName' | 'phone' | 'photo' | 'invite' | 'isAdmin' | 'type'
> & {
  id: number;
  status: EUserStatus;
};

export type TAccountLeaseLevel = 'standard' | 'partner' | 'tenant';

export interface IAccount {
  id?: number;
  dateJoined?: string;
  name: string;
  isSubscribed: boolean;
  isBlocked?: boolean;
  isVerified?: boolean;
  tenantName: string;
  billingPlan: ESubscriptionPlan;
  plan: ESubscriptionPlan;
  planExpiration: string | null;
  leaseLevel: TAccountLeaseLevel;
  logoSm: string | null;
  logoLg: string | null;
  paymentCardProvided: boolean;
  trialEnded: boolean;
  trialIsActive: boolean;
}

export type TUserInvited = Pick<IUnsavedUser, 'firstName' | 'lastName' | 'timezone'> & {
  password: string;
};

export const enum EUserStatus {
  Invited = 'invited',
  Active = 'active',
  Deleted = 'deleted',
  Registration = 'registration',
  Inactive = 'inactive',
  External = 'external',
}

export type TUserId = {
  id: number;
};

export enum EUserListSorting {
  NameAsc = 'team-name-asc',
  NameDesc = 'team-name-desc',
  Status = 'team-group-status',
}
