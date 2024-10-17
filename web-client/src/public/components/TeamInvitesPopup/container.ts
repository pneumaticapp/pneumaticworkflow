import { connect } from 'react-redux';
import { IApplicationState } from '../../types/redux';
import { ITeamInvitesPopupProps, TeamInvitesPopup } from './TeamInvitesPopup';

import {
  closeTeamInvitesPopup,
  changeGoogleInvites,
} from '../../redux/actions';

type TStoreProps = Pick<ITeamInvitesPopupProps,
| 'isTeamInvitesOpened'
| 'currentUserEmail'
| 'googleUsers'
| 'microsoftUsers'
| 'teamUsers'
>;
type TDispatchProps = Pick<ITeamInvitesPopupProps,
| 'closeTeamInvitesPopup'
| 'changeGoogleInvites'
>;

export function mapStateToProps({
  teamInvites: { isInvitesPopupOpen: isTeamInvitesOpened, googleUsers, microsoftUsers },
  authUser: { email },
  accounts,
}: IApplicationState): TStoreProps {

  return {
    isTeamInvitesOpened,
    currentUserEmail: email,
    googleUsers,
    microsoftUsers,
    teamUsers: accounts.users,
  };
}

export const mapDispatchToProps: TDispatchProps = {
  closeTeamInvitesPopup,
  changeGoogleInvites,
};

export const TeamInvitesPopupContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(TeamInvitesPopup);
