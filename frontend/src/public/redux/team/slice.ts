import { createAction, createSlice, PayloadAction } from '@reduxjs/toolkit';

import { getTeamPageByRoute } from '../../utils/team/getTeamPageByRoute';
import { ITeamStore } from '../../types/redux';
import { TeamPages, TInviteUsersPayload, UserInvite } from './types';
import { TUserListItem } from '../../types/user';

const initialState: ITeamStore = {
  page: getTeamPageByRoute(),
  isInvitesPopupOpen: false,
  recentInvitedUsers: [],
  invitesUsersList: [],
  createPerformerModal: {
    isOpen: false,
    isSubmitting: false,
  },
};

const teamSlice = createSlice({
  name: 'team',
  initialState,
  reducers: {
    changeTeamActiveTab: (state, action: PayloadAction<TeamPages>) => {
      state.page = action.payload;
    },
    updateTeamActiveTab: (state, action: PayloadAction<TeamPages>) => {
      state.page = action.payload;
    },
    setRecentInvitedUsers: (state, action: PayloadAction<TUserListItem[]>) => {
      state.recentInvitedUsers = action.payload;
    },
    loadInvitesUsersSuccess: (state, action: PayloadAction<UserInvite[]>) => {
      state.invitesUsersList = action.payload;
    },
    openTeamInvitesPopup: (state) => {
      state.isInvitesPopupOpen = true;
    },
    closeTeamInvitesPopup: (state) => {
      state.isInvitesPopupOpen = false;
    },
    openCreatePerformerModal: (state) => {
      state.createPerformerModal.isOpen = true;
    },
    closeCreatePerformerModal: (state) => {
      state.createPerformerModal = { isOpen: false, isSubmitting: false };
    },
    createPerformerStarted: (state) => {
      state.createPerformerModal.isSubmitting = true;
    },
    createPerformerFailed: (state) => {
      state.createPerformerModal.isSubmitting = false;
    },
  },
});

export const setTeamActivePage = createAction<TeamPages>('team/setTeamActivePage');
export const inviteUsers = createAction<TInviteUsersPayload>('team/inviteUsers');
export const loadInvitesUsers = createAction<void>('team/loadInvitesUsers');
export const loadInvitesUsersFailed = createAction<void>('team/loadInvitesUsersFailed');

export const {
  changeTeamActiveTab,
  updateTeamActiveTab,
  openTeamInvitesPopup,
  closeTeamInvitesPopup,
  openCreatePerformerModal,
  closeCreatePerformerModal,
  createPerformerStarted,
  createPerformerFailed,
  setRecentInvitedUsers,
  loadInvitesUsersSuccess,
} = teamSlice.actions;

export default teamSlice.reducer;
