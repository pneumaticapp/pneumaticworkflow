/* eslint-disable @typescript-eslint/default-param-last */
/* eslint-disable no-param-reassign */
import produce from 'immer';
import { ITeamStore } from '../../types/redux';
import { ETeamActions, TTeamModalActions } from './actions';
import { ETeamPages } from '../../types/team';
import { checkSomeRouteIsActive } from '../../utils/history';
import { ERoutes } from '../../constants/routes';

const initialTabTeam =
  checkSomeRouteIsActive(ERoutes.Groups) || checkSomeRouteIsActive(ERoutes.GroupDetails)
    ? ETeamPages.Groups
    : ETeamPages.Users;

const INIT_STATE: ITeamStore = {
  page: initialTabTeam,
  isInvitesPopupOpen: false,
  recentInvitedUsers: [],
  googleUsers: [],
  microsoftUsers: [],
};

export const reducer = (state = INIT_STATE, action: TTeamModalActions): ITeamStore => {
  switch (action.type) {
    case ETeamActions.ChangeTeamActiveTab:
      return { ...state, page: action.payload };
    case ETeamActions.UpdateTeamActiveTab:
      return { ...state, page: action.payload };
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
