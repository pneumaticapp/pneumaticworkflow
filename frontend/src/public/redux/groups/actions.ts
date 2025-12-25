import { actionGenerator } from '../../utils/redux';
import { ITypedReduxAction } from '../../types/redux';
import { IGroup } from '../team/types';
import { EGroupsListSorting, EUserListSorting } from '../../types/user';

export const enum EGroupsActions {
  LoadGroups = 'LOAD_GROUPS',
  LoadGroupsSuccess = 'LOAD_GROUPS_SUCCESS',
  GroupsListSortingChanged = 'GROUPS_LIST_SORTING_CHANGED',
  CreateGroup = 'CREATE_GROUP',
  CreateModalOpen = 'CREATE_MODAL_OPEN',
  CreateModalClose = 'CREATE_MODAL_CLOSE',
  EditModalOpen = 'EDIT_MODAL_OPEN',
  EditModalClose = 'EDIT_MODAL_CLOSE',
  UpdateGroup = 'UPDATE_GROUP',
  UpdateGroupSuccess = 'UPDATE_GROUP_SUCCESS',
  DeleteGroup = 'DELETE_GROUP',
  UpdateUsersGroup = 'UPDATE_USERS_GROUP',
  UpdateUsersGroupSuccess = 'UPDATE_USERS_GROUP_SUCCESS',
  UserListSortingChanged = 'USER_LIST_SORTING_CHANGED',
  LoadGroup = 'LOAD_GROUP',
  LoadGroupSuccess = 'LOAD_GROUP_SUCCESS',
  ResetGroup = 'RESET_GROUP',
  CreateGroupFailed = 'CREATE_GROUP_FAILED',
  UpdateGroupFailed = 'UPDATE_GROUP_FAILED',
}

export type TLoadGroups = ITypedReduxAction<EGroupsActions.LoadGroups, void>;
export const loadGroups: (payload: void) => TLoadGroups = actionGenerator<EGroupsActions.LoadGroups, void>(
  EGroupsActions.LoadGroups,
);

export type TLoadGroupsSuccess = ITypedReduxAction<EGroupsActions.LoadGroupsSuccess, IGroup[]>;
export const loadGroupsSuccess: (payload: IGroup[]) => TLoadGroupsSuccess = actionGenerator<
  EGroupsActions.LoadGroupsSuccess,
  IGroup[]
>(EGroupsActions.LoadGroupsSuccess);

export type TCreateGroup = ITypedReduxAction<EGroupsActions.CreateGroup, IGroup>;
export const createGroup: (payload: IGroup) => TCreateGroup = actionGenerator<EGroupsActions.CreateGroup, IGroup>(
  EGroupsActions.CreateGroup,
);

export type TCreateGroupFailed = ITypedReduxAction<EGroupsActions.CreateGroupFailed, void>;
export const createGroupFailed: () => TCreateGroupFailed = actionGenerator<EGroupsActions.CreateGroupFailed>(
  EGroupsActions.CreateGroupFailed,
);

export type TUpdateGroupFailed = ITypedReduxAction<EGroupsActions.UpdateGroupFailed, void>;
export const updateGroupFailed: () => TUpdateGroupFailed = actionGenerator<EGroupsActions.UpdateGroupFailed>(
  EGroupsActions.UpdateGroupFailed,
);

export type TUpdateGroup = ITypedReduxAction<EGroupsActions.UpdateGroup, IGroup>;
export const updateGroup: (payload: IGroup) => TUpdateGroup = actionGenerator<EGroupsActions.UpdateGroup, IGroup>(
  EGroupsActions.UpdateGroup,
);

export type TUpdateGroupSuccess = ITypedReduxAction<EGroupsActions.UpdateGroupSuccess, IGroup>;
export const updateGroupSuccess: (payload: IGroup) => TUpdateGroupSuccess = actionGenerator<
  EGroupsActions.UpdateGroupSuccess,
  IGroup
>(EGroupsActions.UpdateGroupSuccess);

export type TDeleteGroup = ITypedReduxAction<EGroupsActions.DeleteGroup, Pick<IGroup, 'id'>>;
export const deleteGroup: (payload: Pick<IGroup, 'id'>) => TDeleteGroup = actionGenerator<
  EGroupsActions.DeleteGroup,
  Pick<IGroup, 'id'>
>(EGroupsActions.DeleteGroup);

export type TCreateModalOpen = ITypedReduxAction<EGroupsActions.CreateModalOpen, void>;
export const createModalOpen: (payload: void) => TCreateModalOpen = actionGenerator<
  EGroupsActions.CreateModalOpen,
  void
>(EGroupsActions.CreateModalOpen);

export type TCreateModalClose = ITypedReduxAction<EGroupsActions.CreateModalClose, void>;
export const createModalClose: (payload: void) => TCreateModalClose = actionGenerator<
  EGroupsActions.CreateModalClose,
  void
>(EGroupsActions.CreateModalClose);

export type TEditModalOpen = ITypedReduxAction<EGroupsActions.EditModalOpen, IGroup>;
export const editModalOpen: (payload: IGroup) => TEditModalOpen = actionGenerator<EGroupsActions.EditModalOpen, IGroup>(
  EGroupsActions.EditModalOpen,
);

export type TEditModalClose = ITypedReduxAction<EGroupsActions.EditModalClose, void>;
export const editModalClose: (payload: void) => TEditModalClose = actionGenerator<EGroupsActions.EditModalClose, void>(
  EGroupsActions.EditModalClose,
);

export type TGroupsListSortingChanged = ITypedReduxAction<EGroupsActions.GroupsListSortingChanged, EGroupsListSorting>;
export const changeGroupsListSorting: (payload: EGroupsListSorting) => TGroupsListSortingChanged = actionGenerator<
  EGroupsActions.GroupsListSortingChanged,
  EGroupsListSorting
>(EGroupsActions.GroupsListSortingChanged);

export type TUserListSortingChange = ITypedReduxAction<EGroupsActions.UserListSortingChanged, EUserListSorting>;
export const userListSortingChanged: (payload: EUserListSorting) => TUserListSortingChange = actionGenerator<
  EGroupsActions.UserListSortingChanged,
  EUserListSorting
>(EGroupsActions.UserListSortingChanged);

export type TResetGroup = ITypedReduxAction<EGroupsActions.ResetGroup, void>;
export const resetGroup: (payload?: void) => TResetGroup = actionGenerator<EGroupsActions.ResetGroup, void>(
  EGroupsActions.ResetGroup,
);

export type TLoadGroup = ITypedReduxAction<EGroupsActions.LoadGroup, number>;
export const loadGroup: (payload: number) => TLoadGroup = actionGenerator<EGroupsActions.LoadGroup, number>(
  EGroupsActions.LoadGroup,
);

export type TLoadGroupSuccess = ITypedReduxAction<EGroupsActions.LoadGroupSuccess, IGroup>;
export const loadGroupSuccess: (payload: IGroup) => TLoadGroupSuccess = actionGenerator<
  EGroupsActions.LoadGroupSuccess,
  IGroup
>(EGroupsActions.LoadGroupSuccess);

export type TUpdateUsersGroup = ITypedReduxAction<EGroupsActions.UpdateUsersGroup, IGroup>;
export const updateUsersGroup: (payload: IGroup) => TUpdateUsersGroup = actionGenerator<
  EGroupsActions.UpdateUsersGroup,
  IGroup
>(EGroupsActions.UpdateUsersGroup);

export type TUpdateUsersGroupSuccess = ITypedReduxAction<EGroupsActions.UpdateGroupSuccess, IGroup>;
export const updateUsersGroupSuccess: (payload: IGroup) => TUpdateUsersGroupSuccess = actionGenerator<
  EGroupsActions.UpdateGroupSuccess,
  IGroup
>(EGroupsActions.UpdateGroupSuccess);

export type TGroupsActions =
  | TLoadGroups
  | TLoadGroup
  | TLoadGroupSuccess
  | TLoadGroupsSuccess
  | TCreateModalOpen
  | TCreateGroup
  | TUpdateGroup
  | TUpdateUsersGroup
  | TUserListSortingChange
  | TCreateModalClose
  | TEditModalOpen
  | TUpdateGroupSuccess
  | TDeleteGroup
  | TGroupsListSortingChanged
  | TResetGroup
  | TUpdateUsersGroupSuccess
  | TEditModalClose
  | TCreateGroupFailed
  | TUpdateGroupFailed;
