import { IApplicationState } from '../../types/redux';
import { EUserListSorting } from '../../types/user';
import { IGroup } from '../team/types';

export const getGroupsList = (state: IApplicationState): IGroup[] => state.groups.list;

export const getGroupsIsLoading = (state: IApplicationState): boolean => state.groups.isLoading;

export const getCurrentGroupData = (state: IApplicationState): IGroup | null => state.groups.currentGroup.data;

export const getCurrentGroupUserListSorting = (state: IApplicationState): EUserListSorting => state.groups.currentGroup.userListSorting;