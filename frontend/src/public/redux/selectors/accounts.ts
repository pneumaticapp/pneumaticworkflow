import { IAccountPlan } from '../../types/redux';
import { TUserListItem } from '../../types/user';
import type { RootState } from '../store';

export const getAccountPlan = (state: RootState): IAccountPlan => state.accounts.planInfo;

export const getAccountsUsers = (state: RootState): TUserListItem[] => state.accounts.users;

export const getIsCreateUserModalOpen = (state: RootState): boolean => state.accounts.isCreateUserModalOpen;

export const getAccountsTeamList = (state: RootState): TUserListItem[] => state.accounts.team.list;
