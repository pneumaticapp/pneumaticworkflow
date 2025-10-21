import { connect } from 'react-redux';
import { IApplicationState } from '../../types/redux';
import { TeamInvitesPopup } from './TeamInvitesPopup';
import { ITeamInvitesPopupProps } from './types';

import {
  closeTeamInvitesPopup,
} from '../../redux/team/slice';

type TStoreProps = Pick<ITeamInvitesPopupProps,
| 'isTeamInvitesOpened'
| 'invitesUsersList'
| 'teamUsers'
>;
type TDispatchProps = Pick<ITeamInvitesPopupProps,
| 'closeTeamInvitesPopup'
>;

export function mapStateToProps({
  team: { isInvitesPopupOpen: isTeamInvitesOpened, invitesUsersList },
  accounts,
}: IApplicationState): TStoreProps {

  return {
    isTeamInvitesOpened,
    invitesUsersList,
    teamUsers: accounts.users,
  };
}

export const mapDispatchToProps: TDispatchProps = {
  closeTeamInvitesPopup
};

export const TeamInvitesPopupContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(TeamInvitesPopup);
