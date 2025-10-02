import React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import { NavLink } from 'react-router-dom';
import { useDispatch } from 'react-redux';

import { Dropdown, TDropdownOption } from '../../../UI';
import { GroupIcon, IntegrateIcon, MoreIcon, PencilIcon, TrashIcon, UnionIcon } from '../../../icons';
import { WorkflowCardUsers } from '../../../WorkflowCardUsers';
import { IGroup } from '../../../../types/team';
import { ERoutes } from '../../../../constants/routes';
import { createGroup, deleteGroup, editModalOpen, updateUsersGroup } from '../../../../redux/actions';
import { UserSelection } from '../../UserSelection';

import styles from './Group.css';
import { useCheckDevice } from '../../../../hooks/useCheckDevice';
import { ETemplateOwnerType, RawPerformer } from '../../../../types/template';

export interface IGroupProps {
  group: IGroup;
}

export function Group({ group }: IGroupProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const { isDesktop } = useCheckDevice();

  const mapUsers = group.users.map((id) => {
    return {
      sourceId: id,
      type: ETemplateOwnerType.User,
    } as RawPerformer;
  });

  const renderDropdownMore = () => {
    const dropdownOptions: TDropdownOption[] = [
      {
        label: formatMessage({ id: 'group.edit-name' }),
        onClick: () => dispatch(editModalOpen(group)),
        Icon: PencilIcon,
        size: 'sm',
      },
      {
        label: formatMessage({ id: 'group.clone' }),
        onClick: () =>
          dispatch(
            createGroup({
              ...group,
              name: `${group.name} (${formatMessage({ id: 'group.clone' })})`,
            }),
          ),
        Icon: UnionIcon,
        size: 'sm',
      },
      {
        label: formatMessage({ id: 'group.add-user' }),
        customSubOption: (
          <UserSelection
            uniqKey={group.id}
            selectedUsers={group.users}
            onChange={(user) => {
              dispatch(
                updateUsersGroup({
                  ...group,
                  users: [...group.users, user.id],
                }),
              );
            }}
            onChangeSelected={(user) => {
              dispatch(
                updateUsersGroup({
                  ...group,
                  users: group.users.filter((id: number) => id !== user.id),
                }),
              );
            }}
            onClickAllUsers={(isSelectAll, users) => {
              dispatch(
                updateUsersGroup({
                  ...group,
                  users,
                }),
              );
            }}
          />
        ),
        Icon: IntegrateIcon,
      },
      {
        label: formatMessage({ id: 'group.delete' }),
        onClick: () => dispatch(deleteGroup(group.id as unknown as Pick<IGroup, 'id'>)),
        Icon: TrashIcon,
        color: 'red',
        withUpperline: true,
        withConfirmation: true,
        size: 'sm',
      },
    ];

    return (
      <Dropdown
        renderToggle={(isOpen: boolean) => (
          <MoreIcon className={classnames(styles['group__more'], isOpen && styles['is-active'])} />
        )}
        options={dropdownOptions}
      />
    );
  };

  return (
    <article className={styles['group']}>
      <figure>
        {group.photo ? <img src={group.photo} alt={group.name} /> : <GroupIcon />}
        {!isDesktop && renderDropdownMore()}
      </figure>
      <div className={styles['group__info']}>
        <div className={styles['group__name']}>
          <h2 title={group.name}>
            <NavLink to={ERoutes.GroupDetails.replace(':id', String(group.id))} className={styles['link']}>
              {group.name}
            </NavLink>
          </h2>
          <p className={styles['group__users']}>
            <span>{group.users.length}</span>{' '}
            {group.users.length === 1 ? formatMessage({ id: 'group.user' }) : formatMessage({ id: 'group.users' })}
          </p>
        </div>
        <div className={styles['group__stat']}>
          <WorkflowCardUsers users={mapUsers} maxUsers={5} />
        </div>
      </div>
      <div className={styles['group__setting']}>{isDesktop && renderDropdownMore()}</div>
    </article>
  );
}
