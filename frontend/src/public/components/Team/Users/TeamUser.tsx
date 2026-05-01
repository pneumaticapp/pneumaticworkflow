import * as React from 'react';
import classnames from 'classnames';
import Switch from 'rc-switch';
import { debounce } from 'throttle-debounce';
import { useIntl } from 'react-intl';

import { EUserStatus, TUserListItem, isUserAbsent } from '../../../types/user';
import { IntlMessages } from '../../IntlMessages';
import { Avatar } from '../../UI/Avatar';
import { getUserFullName } from '../../../utils/users';
import { getDate } from '../../../utils/strings';
import { Dropdown, Header, TDropdownOption } from '../../UI';
import { AddUserIcon, MoreIcon, RemoveUserIcon, TrashIcon } from '../../icons';
import { SelectManagerModal } from '../SelectManagerModal';
import { SelectReportsModal } from '../SelectReportsModal';

import styles from './Users.css';

export interface ITeamUserProps {
  user: TUserListItem;
  isCurrentUser?: boolean;
  isSubscribed?: boolean;
  resendInvite(): Promise<void>;
  handleToggleAdmin(user: TUserListItem): () => Promise<void>;
  handleChangeUserManager(userId: number, managerId: number | null, callbacks?: { onSuccess?: () => void; onError?: () => void }): void;
  handleChangeUserReports(userId: number, reportIds: number[], callbacks?: { onSuccess?: () => void; onError?: () => void }): void;
  openModal(): void;
  openVacationModal(): void;
}

export function TeamUser(props: ITeamUserProps) {
  const {
    user,
    user: { isAdmin, isAccountOwner, status, email, invite },
    handleToggleAdmin,
    resendInvite,
    isCurrentUser,
    isSubscribed,
    handleChangeUserManager,
    handleChangeUserReports,
    openModal,
    openVacationModal,
  } = props;

  const { formatMessage } = useIntl();
  const [isManagerModalOpen, setIsManagerModalOpen] = React.useState(false);
  const [isReportsModalOpen, setIsReportsModalOpen] = React.useState(false);
  const [isManagerSaving, setIsManagerSaving] = React.useState(false);
  const [isReportsSaving, setIsReportsSaving] = React.useState(false);
  const isUserActive = status === EUserStatus.Active;

  const resendInviteDebounced = React.useCallback(debounce(700, resendInvite), [resendInvite]);

  const dropdownOptions: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'team.card-resend-invite' }),
      onClick: resendInviteDebounced,
      isHidden: isUserActive,
      Icon: AddUserIcon,
    },
    {
      label: formatMessage({ id: 'team.card-vacation-settings' }),
      onClick: openVacationModal,
      isHidden: !isUserActive,
      Icon: undefined, // Or a suitable icon from standard library
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
      label: isUserActive
        ? formatMessage({ id: 'team.card-delete' })
        : formatMessage({ id: 'team.card-revoke-invite' }),
      onClick: openModal,
      Icon: isUserActive ? TrashIcon : RemoveUserIcon,
      color: 'red',
      withUpperline: !isUserActive,
    },
  ];

  const renderDetails = () => {
    const detailsMap: { [key in string]: JSX.Element } = {
      [EUserStatus.Active]: (
        <>
          <Header size="6" tag="p" className={styles['card-header']}>
            {getUserFullName(user)}
            {isUserAbsent(user) && (
              <span className={styles['card-absent-badge']} data-testid="absent-badge">
                {formatMessage({ id: 'team.card-absent-badge' })}
              </span>
            )}
          </Header>
          <p className={styles['card-subheader']}>
            <strong>{formatMessage({ id: 'team.user-id' }, { id: user.id })}</strong>{' '}
            {formatMessage({ id: 'team.user-email' }, { email: user.email })}
          </p>
        </>
      ),
      [EUserStatus.Invited]: (
        <>
          <Header size="6" tag="p" className={styles['card-header']}>
            {email}
          </Header>
          <p className={styles['card-subheader']}>
            {formatMessage(
              {
                id: 'team.user-invited',
              },
              {
                date: getDate(invite?.dateCreated),
                username: invite?.byUsername,
              },
            )}
          </p>
        </>
      ),
    };

    const details = detailsMap[status];

    if (!details) {
      return null;
    }

    return <div>{details}</div>;
  };

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
      <div className={styles['card-wrapper']}>
        <div className={classnames(styles['card'])}>
          <Avatar user={user} containerClassName={styles['card-avatar']} size="lg" />
          {renderDetails()}
          {renderControllers()}
        </div>
      </div>
      {isManagerModalOpen && (
        <SelectManagerModal
          isOpen={isManagerModalOpen}
          onClose={() => {
            if (!isManagerSaving) {
              setIsManagerModalOpen(false);
            }
          }}
          onConfirm={(managerId) => {
            setIsManagerSaving(true);
            handleChangeUserManager(user.id, managerId, {
              onSuccess: () => {
                setIsManagerSaving(false);
                setIsManagerModalOpen(false);
              },
              onError: () => {
                setIsManagerSaving(false);
              },
            });
          }}
          currentUserId={user.id}
          currentManagerId={user.managerId || null}
          isLoading={isManagerSaving}
        />
      )}
      {isReportsModalOpen && (
        <SelectReportsModal
          isOpen={isReportsModalOpen}
          onClose={() => {
            if (!isReportsSaving) {
              setIsReportsModalOpen(false);
            }
          }}
          onConfirm={(reportIds) => {
            setIsReportsSaving(true);
            handleChangeUserReports(user.id, reportIds, {
              onSuccess: () => {
                setIsReportsSaving(false);
                setIsReportsModalOpen(false);
              },
              onError: () => {
                setIsReportsSaving(false);
              },
            });
          }}
          currentUserId={user.id}
          currentReportIds={user.reportIds || []}
          isLoading={isReportsSaving}
        />
      )}
    </>
  );
}
