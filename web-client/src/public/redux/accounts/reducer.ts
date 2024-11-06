/* eslint-disable @typescript-eslint/default-param-last */
/* eslint-disable no-param-reassign */
import produce from 'immer';

import { EAccountsActions, TAccountsActions } from './actions';
import { EDeleteUserModalState, IAccounts } from '../../types/redux';
import { EUserListSorting, TUserListItem } from '../../types/user';
import { ESubscriptionPlan } from '../../types/account';

const INIT_DELETE_MODAL: IAccounts['deleteUserModal'] = {
  state: EDeleteUserModalState.Closed,
  userWorkflowsCount: 0,
  user: null,
};

const INIT_STATE: IAccounts = {
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
  deleteUserModal: INIT_DELETE_MODAL,
};

export const reducer = (state = INIT_STATE, action: TAccountsActions): IAccounts => {
  switch (action.type) {
    case EAccountsActions.ResetUsers:
      return { ...state, team: { list: [], isLoading: false } };
    case EAccountsActions.TeamFetchStarted:
      return produce(state, draftState => {
        draftState.team.isLoading = true;
      });
    case EAccountsActions.TeamFetchFailed:
      return produce(state, draftState => {
        draftState.team.isLoading = false;
      });
    case EAccountsActions.TeamFetchFinished:
      return produce(state, draftState => {
        draftState.team.isLoading = false;
        draftState.team.list = action.payload;
      });
    case EAccountsActions.UsersFetchFailed:
      return { ...state, isLoading: false, users: [] };
    case EAccountsActions.UsersFetchFinished:
      return { ...state, isLoading: false, users: action.payload };
    case EAccountsActions.ActiveUsersCountFetchFinished:
      return produce(state, draftState => {
        draftState.planInfo.activeUsers = action.payload.activeUsers;
      });
    case EAccountsActions.SetCurrentPlan:
      return { ...state, isLoading: false, planInfo: action.payload };
    case EAccountsActions.UserListSortingChanged:
      return { ...state, isLoading: false, userListSorting: action.payload };
    case EAccountsActions.ChangeUserAdmin:
      return produce(state, draftState => {
        const { id: userId, isAdmin } = action.payload;

        draftState.team.list = setUserProperties(state.team.list, userId, {
          isAdmin,
        });
        draftState.users = setUserProperties(state.users, action.payload.id, {
          isAdmin,
        });
      });
    case EAccountsActions.OpenDeleteUserModal:
      return produce(state, draftState => {
        draftState.deleteUserModal.user = action.payload.user;
      });
    case EAccountsActions.CloseDeleteUserModal:
      return produce(state, draftState => {
        draftState.deleteUserModal = INIT_DELETE_MODAL;
      });
    case EAccountsActions.SetDeleteUserModalState:
      return produce(state, draftState => {
        draftState.deleteUserModal.state = action.payload;
      });
    case EAccountsActions.SetWorkflowsCount:
      return produce(state, draftState => {
        draftState.deleteUserModal.userWorkflowsCount = action.payload;
      });
    case EAccountsActions.SetIsLoading:
      return produce(state, draftState => {
        draftState.isLoading = true;
      });
    default: return { ...state };
  }
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
