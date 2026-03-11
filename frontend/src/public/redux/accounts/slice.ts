import { createSlice, PayloadAction, createAction } from '@reduxjs/toolkit';

import { EDeleteUserModalState, IAccounts, IAccountPlan } from '../../types/redux';
import { EUserListSorting, TUserListItem, ICreateUserRequest } from '../../types/user';
import { ESubscriptionPlan } from '../../types/account';

import {
  IChangeUserAdminProps,
  TOpenDeleteUserModalPayload,
  TActiveUsersCountFetchFinishedPayload,
  TUsersFetchPayload,
  ITeamFetchStartedProps,
  TDeleteUserPayload,
  TDeclineInvitePayload,
} from './types';

const initialDeleteModal: IAccounts['deleteUserModal'] = {
  state: EDeleteUserModalState.Closed,
  userWorkflowsCount: 0,
  user: null,
};

const initialState: IAccounts = {
  planInfo: {
    activeUsers: null,
    maxUsers: 10,
    planExpiration: null,
    trialEnded: false,
    maxTemplates: 0,
    activeTemplates: 0,
    ownerName: '',
    billingPlan: ESubscriptionPlan.Unknown,
    trialIsActive: true,
    isSubscribed: false,
    tenantsActiveUsers: null
  },
  isLoading: false,
  users: [],
  team: {
    list: [],
    isLoading: false,
  },
  userListSorting: EUserListSorting.NameAsc,
  deleteUserModal: initialDeleteModal,
  isCreateUserModalOpen: false,
};


function setUserProperties(users: TUserListItem[], userId: number, changedProps: Partial<TUserListItem>) {
  return users.map(user => {
    if (user.id === userId) {
      return {
        ...user,
        ...changedProps,
      };
    }

    return user;
  });
}

const accountsSlice = createSlice({
  name: 'accounts',
  initialState,
  reducers: {
    resetUsers: (state) => {
      state.team.list = [];
      state.team.isLoading = false;
    },

    teamFetchStarted: (state) => {
      state.team.isLoading = true;
    },

    teamFetchFailed: (state) => {
      state.team.isLoading = false;
    },

    teamFetchFinished: (state, action: PayloadAction<TUserListItem[]>) => {
      state.team.isLoading = false;
      state.team.list = action.payload;
    },

    usersFetchFailed: (state) => {
      state.isLoading = false;
      state.users = [];
    },

    usersFetchFinished: (state, action: PayloadAction<TUserListItem[]>) => {
      state.isLoading = false;
      state.users = action.payload;
    },

    activeUsersCountFetchFinished: (state, action: PayloadAction<TActiveUsersCountFetchFinishedPayload>) => {
      state.planInfo.activeUsers = action.payload.activeUsers;
    },

    setCurrentPlan: (state, action: PayloadAction<IAccountPlan>) => {
      state.isLoading = false;
      state.planInfo = action.payload;
    },

    userListSortingChanged: (state, action: PayloadAction<EUserListSorting>) => {
      state.isLoading = false;
      state.userListSorting = action.payload;
    },

    changeUserAdmin: (state, action: PayloadAction<IChangeUserAdminProps>) => {
      const { id: userId, isAdmin } = action.payload;

      state.team.list = setUserProperties(state.team.list, userId, {
        isAdmin,
      });
      state.users = setUserProperties(state.users, action.payload.id, {
        isAdmin,
      });
    },

    openDeleteUserModal: (state, action: PayloadAction<TOpenDeleteUserModalPayload>) => {
      state.deleteUserModal.user = action.payload.user;
    },

    closeDeleteUserModal: (state) => {
      state.deleteUserModal = initialDeleteModal;
    },

    setDeleteUserModalState: (state, action: PayloadAction<EDeleteUserModalState>) => {
      state.deleteUserModal.state = action.payload;
    },

    setWorkflowsCount: (state, action: PayloadAction<number>) => {
      state.deleteUserModal.userWorkflowsCount = action.payload;
    },

    setIsLoading: (state) => {
      state.isLoading = true;
    },

    openCreateUserModal: (state) => {
      state.isCreateUserModalOpen = true;
    },

    closeCreateUserModal: (state) => {
      state.isCreateUserModalOpen = false;
    },
  },
});

export const usersFetchStarted = createAction('accounts/usersFetchStarted', (payload?: TUsersFetchPayload) => ({
  payload
}));
export const teamFetchStarted = createAction<ITeamFetchStartedProps>('accounts/teamFetchStarted');
export const loadChangeUserAdmin = createAction<IChangeUserAdminProps>('accounts/loadChangeUserAdmin');
export const deleteUser = createAction<TDeleteUserPayload>('accounts/deleteUser');
export const declineInvite = createAction<TDeclineInvitePayload>('accounts/declineInvite');
export const loadActiveUsersCount = createAction<void>('accounts/loadActiveUsersCount');
export const fetchCurrentPlanFailed = createAction<void>('accounts/fetchCurrentPlanFailed');
export const loadPlan = createAction<void>('accounts/loadPlan');
export const startTrialSubscriptionAction = createAction<void>('accounts/startTrialSubscriptionAction');
export const startFreeSubscriptionAction = createAction<void>('accounts/startFreeSubscriptionAction');
export const createUser = createAction<ICreateUserRequest>('accounts/createUser');

export const {
  resetUsers,
  teamFetchFailed,
  teamFetchFinished,
  usersFetchFailed,
  usersFetchFinished,
  activeUsersCountFetchFinished,
  setCurrentPlan,
  userListSortingChanged,
  changeUserAdmin,
  openDeleteUserModal,
  closeDeleteUserModal,
  setDeleteUserModalState,
  setWorkflowsCount,
  setIsLoading,
  openCreateUserModal,
  closeCreateUserModal,
} = accountsSlice.actions;

export default accountsSlice.reducer;
