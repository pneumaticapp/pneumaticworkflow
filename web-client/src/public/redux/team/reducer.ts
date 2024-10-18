/* eslint-disable @typescript-eslint/default-param-last */
/* eslint-disable no-param-reassign */
import produce from 'immer';
import { ITeamInvitesStore } from '../../types/redux';
import { ETeamActions, TTeamModalActions } from './actions';

const INIT_STATE: ITeamInvitesStore = {
  isInvitesPopupOpen: false,
  recentInvitedUsers: [],
  googleUsers: [],
  microsoftUsers: [],
};

export const reducer = (state = INIT_STATE, action: TTeamModalActions): ITeamInvitesStore => {
  switch (action.type) {
    case ETeamActions.OpenPopup:
      return { ...state, isInvitesPopupOpen: true };
    case ETeamActions.ClosePopup:
      return { ...state, isInvitesPopupOpen: false };
    case ETeamActions.SetRecentInvitedUsers:
      return { ...state, recentInvitedUsers: action.payload };
    case ETeamActions.ChangeGoogleInvites:
      return { ...state, googleUsers: action.payload };

    case ETeamActions.LoadMicrosoftInvitesSuccess:
      return produce(state, (draftState) => {
        draftState.microsoftUsers = action.payload;
      });

    default:
      return { ...state };
  }
};
