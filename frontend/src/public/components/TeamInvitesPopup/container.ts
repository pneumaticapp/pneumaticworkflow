import { connect } from 'react-redux';
import type { RootState } from '../../redux/store';
import { TeamInvitesPopup } from './TeamInvitesPopup';
import type { ITeamInvitesPopupProps } from './types';

import { closeTeamInvitesPopup } from '../../redux/team/slice';

type TStoreProps = Pick<ITeamInvitesPopupProps, 'isTeamInvitesOpened' | 'invitesUsersList' | 'teamUsers'>;
type TDispatchProps = Pick<ITeamInvitesPopupProps, 'closeTeamInvitesPopup'>;

export function mapStateToProps({
  team: { isInvitesPopupOpen: isTeamInvitesOpened, invitesUsersList },
  accounts,
}: RootState): TStoreProps {
  return {
    isTeamInvitesOpened,
    invitesUsersList,
    teamUsers: accounts.users,
  };
}

export const mapDispatchToProps: TDispatchProps = {
  closeTeamInvitesPopup,
};

export const TeamInvitesPopupContainer = connect(mapStateToProps, mapDispatchToProps)(TeamInvitesPopup);
