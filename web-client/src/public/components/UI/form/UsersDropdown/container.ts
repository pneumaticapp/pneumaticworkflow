import { connect } from 'react-redux';

import { IApplicationState } from '../../../../types/redux';
import { openTeamInvitesPopup } from '../../../../redux/actions';
import { TUsersDropdownOption, IUsersDropdownProps, UsersDropdownComponent } from './UsersDropdown';

type TStoreProps = Pick<IUsersDropdownProps<TUsersDropdownOption>, 'isTeamInvitesModalOpen' | 'recentInvitedUsers' | 'isAdmin' | 'users'>;
type TDispatchProps = Pick<IUsersDropdownProps<TUsersDropdownOption>, 'openTeamInvitesPopup'>;

function mapStateToProps({
  teamInvites: { isInvitesPopupOpen: isTeamInvitesModalOpen, recentInvitedUsers },
  authUser: { isAdmin },
  accounts: { users }
}: IApplicationState): TStoreProps {
  return {
    users,
    isTeamInvitesModalOpen,
    recentInvitedUsers,
    isAdmin: Boolean(isAdmin),
  };
}

const mapDispatchToProps: TDispatchProps = { openTeamInvitesPopup };

export const UsersDropdown = connect(mapStateToProps, mapDispatchToProps)(UsersDropdownComponent);
