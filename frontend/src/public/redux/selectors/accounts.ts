import { IAccountPlan, IApplicationState } from '../../types/redux';
import { TUserListItem } from '../../types/user';

export const getAccountPlan = (state: IApplicationState): IAccountPlan => state.accounts.planInfo;

export const getAccountsUsers = (state: IApplicationState): TUserListItem[] => state.accounts.users;
