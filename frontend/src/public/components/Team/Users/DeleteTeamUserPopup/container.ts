import { connect } from 'react-redux';

import type { IApplicationState } from '../../../../redux/store';
import { closeDeleteUserModal, declineInvite, deleteUser } from '../../../../redux/accounts/slice';
import { IDeleteTeamUserPopupProps, DeleteTeamUserPopup } from './DeleteTeamUserPopup';
import { EUserStatus } from '../../../../types/user';

type TStoreProps = Pick<
  IDeleteTeamUserPopupProps,
  'user' | 'usersList' | 'modalState' | 'isUserActive' | 'userWorkflowsCount'
>;
type TDispatchProps = Pick<IDeleteTeamUserPopupProps, 'declineInvite' | 'deleteUser' | 'closeModal'>;

export function mapStateToProps({
  accounts: {
    users,
    deleteUserModal: { user, state: modalState, userWorkflowsCount },
  },
}: IApplicationState): TStoreProps {
  return {
    user,
    usersList: users.filter((currentUser) => currentUser.status && currentUser.status === EUserStatus.Active),
    isUserActive: user?.status === EUserStatus.Active,
    modalState,
    userWorkflowsCount,
  };
}

export const mapDispatchToProps: TDispatchProps = {
  declineInvite,
  deleteUser,
  closeModal: closeDeleteUserModal,
};

export const DeleteTeamUserPopupContainer = connect<TStoreProps, TDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(DeleteTeamUserPopup);
