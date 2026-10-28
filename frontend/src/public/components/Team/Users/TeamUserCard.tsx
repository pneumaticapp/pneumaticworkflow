import * as React from 'react';
import { useMemo, useState } from 'react';
import { debounce } from 'throttle-debounce';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';

import { EUserStatus, isUserAbsent } from '../../../types/user';
import { getUserFullName } from '../../../utils/users';
import { getDate } from '../../../utils/strings';
import {
  loadChangeUserAdmin,
  loadChangeUserManager,
  loadChangeUserReports,
  openDeleteUserModal,
  resendUserInvite,
} from '../../../redux/accounts/slice';
import { Avatar } from '../../UI/Avatar';
import type { TDropdownOption } from '../../UI';
import { AddUserIcon, RemoveUserIcon, TrashIcon } from '../../icons';
import { PerformerCard } from '../PerformerCard';
import { TeamUserRelationsModals } from './TeamUserRelationsModals';
import type { ITeamUserCardProps, TChangeUserManager, TChangeUserReports } from './types';

const RESEND_INVITE_DEBOUNCE_MS = 700;

export function TeamUserCard({ user, currentUserId, isSubscribed, onOpenVacationModal }: ITeamUserCardProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const [isManagerModalOpen, setIsManagerModalOpen] = useState(false);
  const [isReportsModalOpen, setIsReportsModalOpen] = useState(false);

  const { id, email, isAdmin, status, invite } = user;
  const isUserActive = status === EUserStatus.Active;
  const isAccountOwner = user.isAccountOwner && !invite;

  const resendInviteDebounced = useMemo(
    () => debounce(RESEND_INVITE_DEBOUNCE_MS, () => dispatch(resendUserInvite(id))),
    [dispatch, id],
  );

  const handleToggleAdmin = () => {
    dispatch(loadChangeUserAdmin({ id, isAdmin: !isAdmin, email }));
  };

  const handleChangeUserManager: TChangeUserManager = (userId, managerId, callbacks) => {
    dispatch(loadChangeUserManager({ id: userId, managerId, ...callbacks }));
  };

  const handleChangeUserReports: TChangeUserReports = (userId, reportIds, callbacks) => {
    dispatch(loadChangeUserReports({ id: userId, reportIds, ...callbacks }));
  };

  const handleOpenManagerModal = () => {
    setIsManagerModalOpen(true);
  };

  const handleCloseManagerModal = () => {
    setIsManagerModalOpen(false);
  };

  const handleOpenReportsModal = () => {
    setIsReportsModalOpen(true);
  };

  const handleCloseReportsModal = () => {
    setIsReportsModalOpen(false);
  };

  const handleOpenVacationModal = () => {
    onOpenVacationModal(user);
  };

  const handleOpenDeleteModal = () => {
    dispatch(openDeleteUserModal({ user }));
  };

  const options: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'team.card-resend-invite' }),
      onClick: resendInviteDebounced,
      isHidden: isUserActive,
      Icon: AddUserIcon,
    },
    { label: 'Manager', onClick: handleOpenManagerModal, isHidden: !isUserActive },
    { label: 'Reports', onClick: handleOpenReportsModal, isHidden: !isUserActive },
    {
      label: formatMessage({ id: 'team.card-vacation-settings' }),
      onClick: handleOpenVacationModal,
      isHidden: !isUserActive,
    },
    {
      label: formatMessage({ id: isUserActive ? 'team.card-delete' : 'team.card-revoke-invite' }),
      onClick: handleOpenDeleteModal,
      Icon: isUserActive ? TrashIcon : RemoveUserIcon,
      color: 'red',
      withUpperline: !isUserActive,
    },
  ];

  const getBadge = () => {
    if (currentUserId === id) return formatMessage({ id: 'team.card-current-user-badge' });
    if (isAccountOwner) return formatMessage({ id: 'team.card-account-owner-badge' });

    return undefined;
  };

  const description = isUserActive ? (
    <>
      <strong>{formatMessage({ id: 'team.user-id' }, { id })}</strong>{' '}
      {formatMessage({ id: 'team.user-email' }, { email })}
    </>
  ) : (
    formatMessage({ id: 'team.user-invited' }, { date: getDate(invite?.dateCreated), username: invite?.byUsername })
  );

  return (
    <>
      <PerformerCard
        avatar={<Avatar user={user} size="lg" />}
        name={isUserActive ? getUserFullName(user) : email}
        nameBadge={isUserActive && isUserAbsent(user) ? formatMessage({ id: 'team.card-absent-badge' }) : undefined}
        description={description}
        badge={getBadge()}
        toggle={{
          label: formatMessage({ id: 'team.card-admin-toggle' }),
          isChecked: Boolean(isAdmin),
          isDisabled: !isSubscribed,
          onChange: handleToggleAdmin,
        }}
        options={options}
        data-testid={`team-user-${id}`}
      />
      <TeamUserRelationsModals
        user={user}
        isManagerModalOpen={isManagerModalOpen}
        isReportsModalOpen={isReportsModalOpen}
        onCloseManagerModal={handleCloseManagerModal}
        onCloseReportsModal={handleCloseReportsModal}
        handleChangeUserManager={handleChangeUserManager}
        handleChangeUserReports={handleChangeUserReports}
      />
    </>
  );
}
