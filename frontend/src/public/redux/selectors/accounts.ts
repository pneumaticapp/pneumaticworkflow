import { createSelector } from 'reselect';

import { IAccountPlan, IApplicationState } from '../../types/redux';
import { TUserListItem } from '../../types/user';
import { getNotDeletedUsers } from '../../utils/users';

export const getAccountPlan = (state: IApplicationState): IAccountPlan => state.accounts.planInfo;

export const getAccountsUsers = (state: IApplicationState): TUserListItem[] => state.accounts.users;

export const getNotDeletedAccountsUsers = createSelector(getAccountsUsers, getNotDeletedUsers);

export const getIsCreateUserModalOpen = (state: IApplicationState): boolean => state.accounts.isCreateUserModalOpen;

export const getAccountsTeamList = (state: IApplicationState): TUserListItem[] => state.accounts.team.list;
