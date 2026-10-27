import * as React from 'react';
import { useMemo, useState } from 'react';
import classnames from 'classnames';
import Switch from 'rc-switch';
import { debounce } from 'throttle-debounce';
import { useIntl } from 'react-intl';

import { EUserStatus } from '../../../types/user';
import { IntlMessages } from '../../IntlMessages';
import { Avatar } from '../../UI/Avatar';
import { Dropdown } from '../../UI';
import type { TDropdownOption } from '../../UI';
import { AddUserIcon, MoreIcon, RemoveUserIcon, TrashIcon } from '../../icons';
import { TeamUserDetails } from './TeamUserDetails';
import { TeamUserRelationsModals } from './TeamUserRelationsModals';
import type { ITeamUserProps } from './types';

import styles from './Users.css';

export function TeamUser({
  user,
  handleToggleAdmin,
  resendInvite,
  isCurrentUser,
  isSubscribed,
  handleChangeUserManager,
  handleChangeUserReports,
  openModal,
  openVacationModal,
}: ITeamUserProps) {
  const { isAdmin, isAccountOwner, status } = user;

  const { formatMessage } = useIntl();
  const [isManagerModalOpen, setIsManagerModalOpen] = useState(false);
  const [isReportsModalOpen, setIsReportsModalOpen] = useState(false);
  const isUserActive = status === EUserStatus.Active;

  const resendInviteDebounced = useMemo(() => debounce(700, resendInvite), [resendInvite]);

  const handleCloseManagerModal = () => {
    setIsManagerModalOpen(false);
  };

  const handleCloseReportsModal = () => {
    setIsReportsModalOpen(false);
  };

  const dropdownOptions: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'team.card-resend-invite' }),
      onClick: resendInviteDebounced,
      isHidden: isUserActive,
      Icon: AddUserIcon,
    },
    {
      label: 'Manager',
      onClick: () => setIsManagerModalOpen(true),
      isHidden: !isUserActive,
    },
    {
      label: 'Reports',
      onClick: () => setIsReportsModalOpen(true),
      isHidden: !isUserActive,
    },
    {
      label: formatMessage({ id: 'team.card-vacation-settings' }),
      onClick: openVacationModal,
      isHidden: !isUserActive,
    },
    {
      label: isUserActive
        ? formatMessage({ id: 'team.card-delete' })
        : formatMessage({ id: 'team.card-revoke-invite' }),
      onClick: openModal,
      Icon: isUserActive ? TrashIcon : RemoveUserIcon,
      color: 'red',
      withUpperline: !isUserActive,
    },
  ];

  const renderControllers = () => {
    const controllersMap = [
      {
        check: () => isCurrentUser,
        render: () => <p className={styles['card-badge']}>{formatMessage({ id: 'team.card-current-user-badge' })}</p>,
      },
      {
        check: () => isAccountOwner,
        render: () => <p className={styles['card-badge']}>{formatMessage({ id: 'team.card-account-owner-badge' })}</p>,
      },
      {
        check: () => true,
        render: () => (
          <>
            <div className={styles['card-admin']}>
              <IntlMessages id="team.card-admin-toggle" />
              <Switch
                className={classnames(
                  'custom-switch custom-switch-primary custom-switch-small',
                  styles['card-admin__switch'],
                )}
                disabled={!isSubscribed}
                onChange={handleToggleAdmin(user)}
                checked={isAdmin}
                checkedChildren={null}
                unCheckedChildren={null}
              />
            </div>
            <div className={styles['card-more-container']}>
              <Dropdown
                renderToggle={(isOpen) => (
                  <MoreIcon className={classnames(styles['card-more'], isOpen && styles['card-more_active'])} />
                )}
                options={dropdownOptions}
              />
            </div>
          </>
        ),
      },
    ];

    return <div className={styles['card-aside']}>{controllersMap.find(({ check }) => check())?.render()}</div>;
  };

  return (
    <>
      <div className={classnames(styles['card'])}>
        <Avatar user={user} containerClassName={styles['card-avatar']} size="lg" />
        <TeamUserDetails user={user} />
        {renderControllers()}
      </div>
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
