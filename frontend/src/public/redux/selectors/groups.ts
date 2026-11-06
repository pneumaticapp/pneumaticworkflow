import type { RootState } from '../store';
import type { EUserListSorting } from '../../types/user';
import { EUserGroupType } from '../../types/team';
import type { IGroup } from '../../types/team';

export const getGroupsList = (state: RootState): IGroup[] => state.groups.list;

export const getRegularGroupsList = (state: RootState): IGroup[] =>
  state.groups.list.filter((group) => group.type !== EUserGroupType.Personal);

export const getGroupsIsLoading = (state: RootState): boolean => state.groups.isLoading;

export const getCurrentGroupData = (state: RootState): IGroup | null => state.groups.currentGroup.data;

export const getCurrentGroupUserListSorting = (state: RootState): EUserListSorting =>
  state.groups.currentGroup.userListSorting;
