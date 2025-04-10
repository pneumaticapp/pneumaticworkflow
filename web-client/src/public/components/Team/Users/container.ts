import { connect } from 'react-redux';
import { IUsersProps, Users } from './Users';
import { IApplicationState } from '../../../types/redux';
import { getIsUserSubsribed } from '../../../redux/selectors/user';
import {
  teamFetchStarted,
  loadChangeUserAdmin,
  openDeleteUserModal,
  openTeamInvitesPopup,
  setGeneralLoaderVisibility,
  loadMicrosoftInvites,
  changeUserListSorting,
} from '../../../redux/actions';
import { EUserListSorting } from '../../../types/user';
import { withSyncedQueryString } from '../../../HOCs/withSyncedQueryString';

export type TTeamProps = Pick<
  IUsersProps,
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
  IUsersProps,
  | 'fetchUsers'
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
  openModal: openDeleteUserModal,
  openTeamInvitesPopup,
  setGeneralLoaderVisibility,
  loadMicrosoftInvites,
};

const SyncedUsers = withSyncedQueryString<TTeamProps>([
  {
    propName: 'userListSorting',
    queryParamName: 'sorting',
    defaultAction: changeUserListSorting(EUserListSorting.NameAsc),
    createAction: changeUserListSorting,
    getQueryParamByProp: (value) => value,
  }
])(Users);

export const UsersContainer = connect<TTeamProps, TTeamDispatchProps>(mapStateToProps, mapDispatchToProps)(SyncedUsers);
