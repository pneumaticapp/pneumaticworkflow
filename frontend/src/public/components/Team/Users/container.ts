import { connect } from 'react-redux';
import { Users } from './Users';
import { IUsersProps } from './types';
import { IApplicationState } from '../../../types/redux';
import { getIsUserSubsribed } from '../../../redux/selectors/user';
import {setGeneralLoaderVisibility} from '../../../redux/actions';
import {  
  teamFetchStarted,
  loadChangeUserAdmin,
  openDeleteUserModal,
  userListSortingChanged as changeUserListSorting
} from '../../../redux/accounts/slice';
import { openTeamInvitesPopup, loadInvitesUsers } from '../../../redux/team/slice';
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
  | 'loadInvitesUsers'
>;

export function mapStateToProps(state: IApplicationState): TTeamProps {
  const {
    accounts,
    authUser,
    accounts: {
      planInfo: { trialEnded },
    },
    team: { isInvitesPopupOpen: isTeamInvitesOpened },
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
  loadInvitesUsers,
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
