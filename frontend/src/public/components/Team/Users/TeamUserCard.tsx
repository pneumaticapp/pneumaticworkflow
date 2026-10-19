import * as React from 'react';
import { useDispatch } from 'react-redux';

import {
  loadChangeUserAdmin,
  loadChangeUserManager,
  loadChangeUserReports,
  openDeleteUserModal,
  resendUserInvite,
} from '../../../redux/accounts/slice';
import { TeamUser } from './TeamUser';
import type { ITeamUserCardProps } from './types';

export function TeamUserCard({ user, currentUserId, isSubscribed, onOpenVacationModal }: ITeamUserCardProps) {
  const dispatch = useDispatch();

  const resendInviteHandler = () => {
    if (user.id) dispatch(resendUserInvite(user.id));
  };

  const handleToggleUserAdmin = (targetUser: ITeamUserCardProps['user']) => async () => {
    const { id, isAdmin, email } = targetUser;
    if (id && email) dispatch(loadChangeUserAdmin({ id, isAdmin: !isAdmin, email }));
  };

  return (
    <TeamUser
      resendInvite={resendInviteHandler}
      isCurrentUser={currentUserId === user.id}
      isSubscribed={isSubscribed}
      handleToggleAdmin={handleToggleUserAdmin}
      handleChangeUserManager={(userId, managerId, callbacks) =>
        dispatch(loadChangeUserManager({ id: userId, managerId, ...callbacks }))
      }
      handleChangeUserReports={(userId, reportIds, callbacks) =>
        dispatch(loadChangeUserReports({ id: userId, reportIds, ...callbacks }))
      }
      openModal={() => dispatch(openDeleteUserModal({ user }))}
      openVacationModal={() => onOpenVacationModal(user)}
      user={{ ...user, isAccountOwner: user.isAccountOwner && !user.invite }}
    />
  );
}
