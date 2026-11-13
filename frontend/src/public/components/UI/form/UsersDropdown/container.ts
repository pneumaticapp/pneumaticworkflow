import { connect } from 'react-redux';

import type { RootState } from '../../../../redux/store';
import { openTeamInvitesPopup } from '../../../../redux/team/slice';
import type { TUsersDropdownOption, IUsersDropdownProps } from './types';
import { UsersDropdownComponent } from './UsersDropdown';

type TStoreProps = Pick<
  IUsersDropdownProps<TUsersDropdownOption>,
  'isTeamInvitesModalOpen' | 'recentInvitedUsers' | 'isAdmin' | 'users'
>;
type TDispatchProps = Pick<IUsersDropdownProps<TUsersDropdownOption>, 'openTeamInvitesPopup'>;

function mapStateToProps({
  team: { isInvitesPopupOpen: isTeamInvitesModalOpen, recentInvitedUsers },
  authUser: { isAdmin },
  accounts: { users },
}: RootState): TStoreProps {
  return {
    users,
    isTeamInvitesModalOpen,
    recentInvitedUsers,
    isAdmin: Boolean(isAdmin),
  };
}

const mapDispatchToProps: TDispatchProps = { openTeamInvitesPopup };

export const UsersDropdown = connect(mapStateToProps, mapDispatchToProps)(UsersDropdownComponent);
