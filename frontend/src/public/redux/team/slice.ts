import { createAction, createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

import { checkSomeRouteIsActive } from '../../utils/history';
import { ERoutes } from '../../constants/routes';
import { ETeamPages } from './types';
import type { ITeamStore, TInviteUsersPayload } from './types';
import type { IUserInvite } from '../../types/team';
import type { TUserListItem } from '../../types/user';

const initialTabTeam =
  checkSomeRouteIsActive(ERoutes.Groups) || checkSomeRouteIsActive(ERoutes.GroupDetails)
    ? ETeamPages.Groups
    : ETeamPages.Users;

const initialState: ITeamStore = {
  page: initialTabTeam,
  isInvitesPopupOpen: false,
  recentInvitedUsers: [],
  invitesUsersList: [],
};

const teamSlice = createSlice({
  name: 'team',
  initialState,
  reducers: {
    changeTeamActiveTab: (state, action: PayloadAction<ETeamPages>) => {
      state.page = action.payload;
    },
    updateTeamActiveTab: (state, action: PayloadAction<ETeamPages>) => {
      state.page = action.payload;
    },
    setRecentInvitedUsers: (state, action: PayloadAction<TUserListItem[]>) => {
      state.recentInvitedUsers = action.payload;
    },
    loadInvitesUsersSuccess: (state, action: PayloadAction<IUserInvite[]>) => {
      state.invitesUsersList = action.payload;
    },
    openTeamInvitesPopup: (state) => {
      state.isInvitesPopupOpen = true;
    },
    closeTeamInvitesPopup: (state) => {
      state.isInvitesPopupOpen = false;
    },
  },
});

export const setTeamActivePage = createAction<ETeamPages>('team/setTeamActivePage');
export const inviteUsers = createAction<TInviteUsersPayload>('team/inviteUsers');
export const loadInvitesUsers = createAction<void>('team/loadInvitesUsers');
export const loadInvitesUsersFailed = createAction<void>('team/loadInvitesUsersFailed');

export const {
  changeTeamActiveTab,
  updateTeamActiveTab,
  openTeamInvitesPopup,
  closeTeamInvitesPopup,
  setRecentInvitedUsers,
  loadInvitesUsersSuccess,
} = teamSlice.actions;

export default teamSlice.reducer;
