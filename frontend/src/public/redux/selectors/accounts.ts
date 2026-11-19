import type { IAccountPlan } from '../../types/account';
import type { EUserListSorting, TUserListItem } from '../../types/user';
import type { RootState } from '../store';

export const getAccountPlan = (state: RootState): IAccountPlan => state.accounts.planInfo;

export const getAccountsUsers = (state: RootState): TUserListItem[] => state.accounts.users;

export const getAccountsTeamList = (state: RootState): TUserListItem[] => state.accounts.team.list;

export const getAccountsTeamIsLoading = (state: RootState): boolean => state.accounts.team.isLoading;

export const getAccountsUserListSorting = (state: RootState): EUserListSorting => state.accounts.userListSorting;
