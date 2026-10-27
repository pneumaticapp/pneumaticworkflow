import * as React from 'react';
import { useCallback } from 'react';
import { useDispatch } from 'react-redux';

import {
  loadChangeUserAdmin,
  loadChangeUserManager,
  loadChangeUserReports,
  openDeleteUserModal,
  resendUserInvite,
} from '../../../redux/accounts/slice';
import { TeamUser } from './TeamUser';
import type { ITeamUserCardProps, ITeamUserProps } from './types';

export function TeamUserCard({ user, currentUserId, isSubscribed, onOpenVacationModal }: ITeamUserCardProps) {
  const dispatch = useDispatch();

  const resendInviteHandler = useCallback(() => {
    if (user.id) dispatch(resendUserInvite(user.id));
  }, [dispatch, user.id]);

  const handleToggleUserAdmin = (targetUser: ITeamUserCardProps['user']) => async () => {
    const { id, isAdmin, email } = targetUser;
    if (id && email) dispatch(loadChangeUserAdmin({ id, isAdmin: !isAdmin, email }));
  };

  const handleChangeUserManager: ITeamUserProps['handleChangeUserManager'] = (userId, managerId, callbacks) => {
    dispatch(loadChangeUserManager({ id: userId, managerId, ...callbacks }));
  };

  const handleChangeUserReports: ITeamUserProps['handleChangeUserReports'] = (userId, reportIds, callbacks) => {
    dispatch(loadChangeUserReports({ id: userId, reportIds, ...callbacks }));
  };

  const handleOpenDeleteModal = () => {
    dispatch(openDeleteUserModal({ user }));
  };

  const handleOpenVacationModal = () => {
    onOpenVacationModal(user);
  };

  return (
    <TeamUser
      resendInvite={resendInviteHandler}
      isCurrentUser={currentUserId === user.id}
      isSubscribed={isSubscribed}
      handleToggleAdmin={handleToggleUserAdmin}
      handleChangeUserManager={handleChangeUserManager}
      handleChangeUserReports={handleChangeUserReports}
      openModal={handleOpenDeleteModal}
      openVacationModal={handleOpenVacationModal}
      user={{ ...user, isAccountOwner: user.isAccountOwner && !user.invite }}
    />
  );
}
