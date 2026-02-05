import React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';
import Switch from 'rc-switch';

import { updateUsersGroup } from '../../../redux/actions';
import { loadChangeUserAdmin } from '../../../redux/accounts/slice';
import { IApplicationState } from '../../../types/redux';
import { TUserListItem, EUserStatus } from '../../../types/user';
import { getUserFullName } from '../../../utils/users';
import { TrashIcon } from '../../icons';
import { Header, Avatar } from '../../UI';
import { getDate } from '../../../utils/strings';
import { useCheckDevice } from '../../../hooks/useCheckDevice';
import { IGroup } from '../../../redux/team/types';

import styles from './User.css';

export interface IGroupUserProps {
  user: TUserListItem;
}

export function GroupUser({ user }: IGroupUserProps) {
  const { isDesktop } = useCheckDevice();
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const group: IGroup | null = useSelector((state: IApplicationState) => state.groups.currentGroup.data);
  const id: number = useSelector((state: IApplicationState) => state.authUser.id);

  if (!group) return null;

  const renderDetails = () => {
    const detailsMap: { [key in string]: JSX.Element } = {
      [EUserStatus.Active]: (
        <>
          <Header size="6" tag="h2" className={styles['card-header']}>
            {getUserFullName(user)}
          </Header>
          <p className={styles['user__caption']}>
            <strong>{formatMessage({ id: 'team.user-id' }, { id: user.id })}</strong>{' '}
            {formatMessage({ id: 'team.user-email' }, { email: user.email })}
          </p>
        </>
      ),
      [EUserStatus.Invited]: (
        <>
          <Header size="6" tag="h2" className={styles['card-header']}>
            {user.email}
          </Header>
          <p className={styles['user__caption']}>
            {formatMessage(
              {
                id: 'team.user-invited',
              },
              {
                date: getDate(user.invite?.dateCreated),
                username: user.invite?.byUsername,
              },
            )}
          </p>
        </>
      ),
    };

    const details = detailsMap[user.status];

    if (!details) {
      return null;
    }

    return <div>{details}</div>;
  };

  const renderControllers = () => {
    const controllersMap = [
      {
        check: () => user.id === id,
        render: () => <p className={styles['card-badge']}>{formatMessage({ id: 'team.card-current-user-badge' })}</p>,
      },
      {
        check: () => user?.isAccountOwner,
        render: () => <p className={styles['card-badge']}>{formatMessage({ id: 'team.card-account-owner-badge' })}</p>,
      },
      {
        check: () => true,
        render: () => (
          <div className={styles['user__admin']}>
            <p>Admin</p>
            <Switch
              className={classnames(
                'custom-switch custom-switch-primary custom-switch-small',
                styles['card-admin__switch'],
              )}
              onChange={() =>
                dispatch(
                  loadChangeUserAdmin({
                    id: user.id,
                    email: user.email,
                    isAdmin: !user.isAdmin,
                  }),
                )
              }
              checked={user.isAdmin}
              checkedChildren={null}
              unCheckedChildren={null}
            />
          </div>
        ),
      },
    ];

    return <div className={styles['card-aside']}>{controllersMap.find(({ check }) => check())?.render()}</div>;
  };

  const renderConfig = () => {
    return (
      <div className={styles['user__config']}>
        {renderControllers()}
        <button
          type="button"
          aria-label="Delete user in group"
          className={styles['user__delete']}
          onClick={() => {
            dispatch(
              updateUsersGroup({
                ...group,
                users: group.users.filter((ids: number) => ids !== user.id),
              }),
            );
          }}
        >
          <TrashIcon />
        </button>
      </div>
    );
  };

  return (
    <div className={classnames(styles['user'])}>
      <div className={styles['user__avatar']}>
        <Avatar user={user} size="lg" />
        {!isDesktop && renderConfig()}
      </div>
      <div className={styles['user__info']}>{renderDetails()}</div>
      {isDesktop && renderConfig()}
    </div>
  );
}
