import * as React from 'react';
import { useDispatch } from 'react-redux';

import { resendInvite } from '../../../api/resendInvite';
import { getErrorMessage } from '../../../utils/getErrorMessage';
import { setGeneralLoaderVisibility } from '../../../redux/actions';
import {
  loadChangeUserAdmin,
  loadChangeUserManager,
  loadChangeUserReports,
  openDeleteUserModal,
} from '../../../redux/accounts/slice';
import { NotificationManager } from '../../UI/Notifications';
import { TeamUser } from './TeamUser';
import type { ITeamUserCardProps } from './types';

export function TeamUserCard({ user, currentUserId, isSubscribed, onOpenVacationModal }: ITeamUserCardProps) {
  const dispatch = useDispatch();

  const resendInviteHandler = async () => {
    if (user.id) {
      try {
        dispatch(setGeneralLoaderVisibility(true));
        await resendInvite(user.id);
        NotificationManager.success({ message: 'team.resend-invite-success-msg' });
      } catch (err) {
        NotificationManager.warning({ message: getErrorMessage(err) });
      } finally {
        dispatch(setGeneralLoaderVisibility(false));
      }
    }
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
