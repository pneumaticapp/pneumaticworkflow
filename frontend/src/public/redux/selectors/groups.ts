import type { RootState } from '../store';
import { EUserListSorting } from '../../types/user';
import { EUserGroupType, IGroup } from '../team/types';

export const getGroupsList = (state: RootState): IGroup[] => state.groups.list;

export const getRegularGroupsList = (state: RootState): IGroup[] =>
  state.groups.list.filter((group) => group.type !== EUserGroupType.Personal);

export const getGroupsIsLoading = (state: RootState): boolean => state.groups.isLoading;

export const getCurrentGroupData = (state: RootState): IGroup | null => state.groups.currentGroup.data;

export const getCurrentGroupUserListSorting = (state: RootState): EUserListSorting =>
  state.groups.currentGroup.userListSorting;
