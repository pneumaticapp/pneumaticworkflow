import { createAction, createSlice, PayloadAction } from "@reduxjs/toolkit";

import { checkSomeRouteIsActive } from '../../utils/history';
import { ERoutes } from '../../constants/routes';
import { ITeamStore } from '../../types/redux';
import { TeamPages, TInviteUsersPayload, UserInvite } from "./types";
import { TUserListItem } from '../../types/user';

const initialTabTeam =
  checkSomeRouteIsActive(ERoutes.Groups) || checkSomeRouteIsActive(ERoutes.GroupDetails)
    ? TeamPages.Groups
    : TeamPages.Users;

const initialState: ITeamStore = {
  page: initialTabTeam,
  isInvitesPopupOpen: false,
  recentInvitedUsers: [],
  invitesUsersList: [],
};

const teamSlice = createSlice({
  name: "team",
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
      state.isInvitesPopupOpen =true;
    },
    closeTeamInvitesPopup: (state) => {
      state.isInvitesPopupOpen = false;
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
  setRecentInvitedUsers,
  loadInvitesUsersSuccess,
} = teamSlice.actions;

export default teamSlice.reducer;
