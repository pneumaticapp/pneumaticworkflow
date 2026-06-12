import { createAction, createSlice, PayloadAction } from '@reduxjs/toolkit';

import { IGroupsStore } from '../../types/redux';
import { EGroupsListSorting, EUserListSorting } from '../../types/user';
import { IGroup } from '../team/types';

const initialState: IGroupsStore = {
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

export const loadGroups = createAction<void>('groups/loadGroups');
export const createGroup = createAction<IGroup>('groups/createGroup');
export const updateGroup = createAction<IGroup>('groups/updateGroup');
export const updateUsersGroup = createAction<IGroup>('groups/updateUsersGroup');
export const deleteGroup = createAction<Pick<IGroup, 'id'>>('groups/deleteGroup');
export const loadGroup = createAction<number>('groups/loadGroup');

const groupsSlice = createSlice({
  name: 'groups',
  initialState,
  reducers: {
    loadGroupsSuccess: (state, action: PayloadAction<IGroup[]>) => {
      state.list = action.payload;
      state.isLoading = false;
    },

    groupsListSortingChanged: (state, action: PayloadAction<EGroupsListSorting>) => {
      state.isLoading = true;
      state.groupsListSorting = action.payload;
    },

    userListSortingChanged: (state, action: PayloadAction<EUserListSorting>) => {
      state.currentGroup.userListSorting = action.payload;
    },

    createGroupFailed: (state) => {
      state.isLoading = false;
    },

    updateGroupFailed: (state) => {
      state.isLoading = false;
    },

    updateGroupSuccess: (state, action: PayloadAction<IGroup>) => {
      const { id } = action.payload;
      state.list = state.list.map((group) => (group.id === id ? action.payload : group));
      state.currentGroup.data = action.payload;
      state.isLoading = false;
    },

    loadGroupSuccess: (state, action: PayloadAction<IGroup>) => {
      state.currentGroup.data = action.payload;
      state.isLoading = false;
    },

    resetGroup: (state) => {
      state.currentGroup = {
        data: null,
        userListSorting: EUserListSorting.NameAsc,
      };
    },

    createModalOpen: (state) => {
      state.createModal = true;
    },

    createModalClose: (state) => {
      state.createModal = false;
    },

    editModalOpen: (state, action: PayloadAction<IGroup>) => {
      state.editModal = {
        isOpen: true,
        editGroup: action.payload,
      };
    },

    editModalClose: (state) => {
      state.editModal = {
        isOpen: false,
        editGroup: null,
      };
    },

    upsertGroupFromWs: (state, action: PayloadAction<IGroup>) => {
      const group = action.payload;
      const index = state.list.findIndex((item) => item.id === group.id);

      if (index === -1) {
        state.list.push(group);
      } else {
        state.list[index] = group;
      }

      if (state.currentGroup.data?.id === group.id) {
        state.currentGroup.data = group;
      }
    },

    removeGroupFromWs: (state, action: PayloadAction<number>) => {
      state.list = state.list.filter((group) => group.id !== action.payload);

      if (state.currentGroup.data?.id === action.payload) {
        state.currentGroup.data = null;
      }

      if (state.editModal.editGroup?.id === action.payload) {
        state.editModal.editGroup = null;
        state.editModal.isOpen = false;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadGroups, (state) => {
        state.isLoading = true;
      })
      .addCase(createGroup, (state) => {
        state.isLoading = true;
      })
      .addCase(updateGroup, (state) => {
        state.isLoading = true;
      })
      .addCase(updateUsersGroup, (state) => {
        state.isLoading = true;
      })
      .addCase(deleteGroup, (state) => {
        state.isLoading = true;
      })
      .addCase(loadGroup, (state) => {
        state.isLoading = true;
      });
  },
});

export const {
  loadGroupsSuccess,
  groupsListSortingChanged,
  userListSortingChanged,
  createGroupFailed,
  updateGroupFailed,
  updateGroupSuccess,
  loadGroupSuccess,
  resetGroup,
  createModalOpen,
  createModalClose,
  editModalOpen,
  editModalClose,
  upsertGroupFromWs,
  removeGroupFromWs,
} = groupsSlice.actions;

export const changeGroupsListSorting = groupsListSortingChanged;

export default groupsSlice.reducer;
