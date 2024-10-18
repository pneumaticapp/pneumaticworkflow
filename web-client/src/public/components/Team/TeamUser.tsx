import * as React from 'react';
import * as classnames from 'classnames';
import Switch from 'rc-switch';
import { debounce } from 'throttle-debounce';
import { useIntl } from 'react-intl';

import { EUserStatus, TUserListItem } from '../../types/user';
import { IntlMessages } from '../IntlMessages';
import { Avatar } from '../UI/Avatar';
import { getUserFullName } from '../../utils/users';
import { DateFormat } from '../UI/DateFormat';
import { Dropdown, Header, TDropdownOption } from '../UI';
import { AddUserIcon, MoreIcon, RemoveUserIcon, TrashIcon } from '../icons';

import styles from './Team.css';

export interface ITeamUserProps {
  user: TUserListItem;
  isCurrentUser?: boolean;
  isSubscribed?: boolean;
  resendInvite(): Promise<void>;
  handleToggleAdmin(user: TUserListItem): () => Promise<void>;
  openModal(): void;
}

export function TeamUser(props: ITeamUserProps) {
  const {
    user,
    user: { isAdmin, isAccountOwner, status, email, invite },
    handleToggleAdmin,
    resendInvite,
    isCurrentUser,
    isSubscribed,
    openModal,
  } = props;

  const { formatMessage } = useIntl();
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
                date: <DateFormat date={invite?.dateCreated} />,
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
                onChange={handleToggleAdmin(user)}
                checked={isSubscribed ? isAdmin : true}
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
    <div className={styles['card-wrapper']}>
      <div className={classnames(styles['card'])}>
        <Avatar user={user} containerClassName={styles['card-avatar']} size="lg" />
        {renderDetails()}
        {renderControllers()}
      </div>
    </div>
  );
}
