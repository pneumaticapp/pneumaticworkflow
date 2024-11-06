import { connect } from 'react-redux';
import { loadMicrosoftInvites } from "../../redux/team/actions";

import { IApplicationState } from '../../types/redux';
import {
  loadChangeUserAdmin,
  teamFetchStarted,
  resetUsers,
  changeUserListSorting,
  openDeleteUserModal,
  openTeamInvitesPopup,
  setGeneralLoaderVisibility,
} from '../../redux/actions';
import { ITeamProps, Team } from './Team';
import { withSyncedQueryString } from '../../HOCs/withSyncedQueryString';
import { EUserListSorting } from '../../types/user';
import { getIsUserSubsribed } from '../../redux/selectors/user';

export type TTeamProps = Pick<
  ITeamProps,
  | 'currentUserId'
  | 'isLoading'
  | 'sorting'
  | 'users'
  | 'isTeamInvitesOpened'
  | 'isSubscribed'
  | 'trialEnded'
  | 'userListSorting'
>;
type TTeamDispatchProps = Pick<
  ITeamProps,
  | 'fetchUsers'
  | 'resetUsers'
  | 'loadChangeUserAdmin'
  | 'openModal'
  | 'openTeamInvitesPopup'
  | 'setGeneralLoaderVisibility'
  | 'loadMicrosoftInvites'
>;

export function mapStateToProps(state: IApplicationState): TTeamProps {
  const {
    accounts,
    authUser,
    accounts: {
      planInfo: { trialEnded },
    },
    teamInvites: { isInvitesPopupOpen: isTeamInvitesOpened },
  } = state;
  const isSubscribed = getIsUserSubsribed(state);

  return {
    users: accounts.team.list,
    currentUserId: Number(authUser.id),
    isLoading: accounts.team.isLoading,
    sorting: accounts.userListSorting,
    isTeamInvitesOpened,
    isSubscribed,
    userListSorting: accounts.userListSorting,
    trialEnded,
  };
}

export const mapDispatchToProps: TTeamDispatchProps = {
  fetchUsers: teamFetchStarted,
  loadChangeUserAdmin,
  resetUsers,
  openModal: openDeleteUserModal,
  openTeamInvitesPopup,
  setGeneralLoaderVisibility,
  loadMicrosoftInvites,
};

const SyncedTeam = withSyncedQueryString<ITeamProps>([
  {
    propName: 'userListSorting',
    queryParamName: 'sorting',
    defaultAction: changeUserListSorting(EUserListSorting.NameAsc),
    createAction: changeUserListSorting,
    getQueryParamByProp: (value) => value,
  },
])(Team);

export const TeamContainer = connect<TTeamProps, TTeamDispatchProps>(mapStateToProps, mapDispatchToProps)(SyncedTeam);
