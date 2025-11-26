import produce from 'immer';
import { IGroupsStore } from '../../types/redux';
import { EGroupsListSorting, EUserListSorting } from '../../types/user';
import { EGroupsActions, TGroupsActions } from './actions';

const INIT_STATE: IGroupsStore = {
  isLoading: true,
  list: [],
  groupsListSorting: EGroupsListSorting.NameAsc,
  currentGroup: {
    data: null,
    userListSorting: EUserListSorting.NameAsc,
  },
  createModal: false,
  editModal: {
    isOpen: false,
    editGroup: null,
  },
};

export const reducer = (state = INIT_STATE, action: TGroupsActions): IGroupsStore => {
  switch (action.type) {
    case EGroupsActions.LoadGroups:
      return { ...state, isLoading: true };

    case EGroupsActions.UserListSortingChanged:
      return produce(state, (draftState) => {
        draftState.currentGroup.userListSorting = action.payload;
      });

    case EGroupsActions.LoadGroupsSuccess:
      return { ...state, list: action.payload, isLoading: false };

    case EGroupsActions.GroupsListSortingChanged:
      return { ...state, isLoading: true, groupsListSorting: action.payload };

    case EGroupsActions.CreateGroup:
      return { ...state, isLoading: true };

    case EGroupsActions.CreateGroupFailed:
      return { ...state, isLoading: false };

    case EGroupsActions.UpdateGroupFailed:
      return { ...state, isLoading: false };

    case EGroupsActions.UpdateGroup:
      return { ...state, isLoading: true };

    case EGroupsActions.UpdateGroupSuccess:
    case EGroupsActions.UpdateUsersGroup:
      return produce(state, (draftState) => {
        const { id } = action.payload;
        const currentList = draftState.list.map((group) => {
          if (group.id === id) return action.payload;
          return group;
        });

        if (draftState.currentGroup) draftState.currentGroup.data = action.payload;
        draftState.list = currentList;
        draftState.isLoading = false;
      });

    case EGroupsActions.DeleteGroup:
      return { ...state, isLoading: true };
    case EGroupsActions.ResetGroup:
      return produce(state, (draftState) => {
        draftState.currentGroup = {
          data: null,
          userListSorting: EUserListSorting.NameAsc,
        };
      });
    case EGroupsActions.LoadGroupSuccess:
      return produce(state, (draftState) => {
        draftState.currentGroup.data = action.payload;
        draftState.isLoading = false;
      });
    case EGroupsActions.LoadGroup:
      return { ...state, isLoading: true };
    case EGroupsActions.CreateModalOpen:
      return { ...state, createModal: true };
    case EGroupsActions.CreateModalClose:
      return { ...state, createModal: false };
    case EGroupsActions.EditModalOpen:
      return {
        ...state,
        editModal: {
          isOpen: true,
          editGroup: action.payload,
        },
      };
    case EGroupsActions.EditModalClose:
      return {
        ...state,
        editModal: {
          isOpen: false,
          editGroup: null,
        },
      };
    default:
      return { ...state };
  }
};
