import React, { useState, useEffect } from 'react';
import { useIntl } from 'react-intl';
import classNames from 'classnames';
import { useDispatch, useSelector } from 'react-redux';
import { history } from '../../../utils/history';

import {
  loadGroup,
  editModalOpen,
  createGroup,
  deleteGroup,
  teamFetchStarted,
  resetGroup,
  updateUsersGroup,
  userListSortingChanged,
} from '../../../redux/actions';
import { IApplicationState } from '../../../types/redux';
import { IGroup } from '../../../redux/team/types';
import { EUserListSorting, TUserListItem } from '../../../types/user';
import {
  IntegrateIcon,
  TrashIcon,
  PencilIcon,
  UnionIcon,
  SearchLargeIcon,
  AddUserIcon,
  SettingsIcon,
} from '../../icons';
import {
  TDropdownOption,
  InputField,
  DropdownList,
  Dropdown,
  Button,
  TDropdownOptionBase,
  Placeholder,
} from '../../UI';
import { UserSelection } from '../UserSelection';
import { GroupUser } from './GroupUser';

import styles from './GroupDetails.css';
import { EditGroupModal } from '../Groups/EditGroupModal';
import { ERoutes } from '../../../constants/routes';
import { TaskCarkSkeleton } from '../../TaskCard/TaskCarkSkeleton';
import { TasksPlaceholderIcon } from '../../Tasks/TasksPlaceholderIcon';

export function GroupDetails({ match }: any) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const group: IGroup | null = useSelector((state: IApplicationState) => state.groups.currentGroup.data);
  const sorting: EUserListSorting = useSelector(
    (state: IApplicationState) => state.groups.currentGroup.userListSorting,
  );
  const users: TUserListItem[] = useSelector((state: IApplicationState) => state.accounts.team.list);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    dispatch(teamFetchStarted({}));
    dispatch(loadGroup(match.params.id));

    return () => {
      dispatch(resetGroup());
    };
  }, []);

  if (!group || !users)
    return (
      <div className={styles['container']}>
        <TaskCarkSkeleton />
      </div>
    );

  const getFilteredUsers = () => {
    const sortedUsersGroup = users.filter((user: TUserListItem) => {
      return group.users.find((item: number) => item === user.id);
    });

    if (!searchQuery) {
      return sortedUsersGroup;
    }

    const queryWords = searchQuery.split(' ').map((str) => str.toLowerCase());
    const checkQueryWord = (queryWord: string, user: TUserListItem) => {
      return [user.firstName, user.lastName, user.email]
        .map((str) => str.toLowerCase())
        .some((property) => property.includes(queryWord));
    };

    const filteredUsers = sortedUsersGroup.filter((user: TUserListItem) => {
      return queryWords.every((queryWord) => checkQueryWord(queryWord, user));
    });

    return filteredUsers;
  };

  const renderAddUsers = () => {
    const dropdownOptionsUsers: TDropdownOption = {
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
          onClickAllUsers={(_, selectedUsers) => {
            dispatch(
              updateUsersGroup({
                ...group,
                users: selectedUsers,
              }),
            );
          }}
        />
      ),
      Icon: IntegrateIcon,
    };

    return (
      <Dropdown
        renderToggle={(isOpen: boolean) => (
          <Button
            size="sm"
            icon={AddUserIcon}
            label="Add users"
            buttonStyle="transparent-black"
            className={classNames(styles['header__config-btn'], isOpen && styles['is-active'])}
          />
        )}
        options={dropdownOptionsUsers}
      />
    );
  };

  const renderModify = () => {
    const dropdownOptionsModify: TDropdownOption[] = [
      {
        label: formatMessage({ id: 'group.edit-name' }),
        onClick: () => dispatch(editModalOpen(group)),
        Icon: PencilIcon,
        size: 'sm',
      },
      {
        label: formatMessage({ id: 'group.clone' }),
        onClick: () => {
          dispatch(
            createGroup({
              ...group,
              name: `${group.name} (${formatMessage({ id: 'group.clone' })})`,
            }),
          );
          history.push(ERoutes.Groups);
        },
        Icon: UnionIcon,
        size: 'sm',
      },
      {
        label: formatMessage({ id: 'group.delete' }),
        onClick: () => {
          dispatch(deleteGroup(group.id as unknown as Pick<IGroup, 'id'>));
          history.push(ERoutes.Groups);
        },
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
          <Button
            size="sm"
            icon={SettingsIcon}
            label="Modify"
            buttonStyle="transparent-black"
            className={classNames(styles['header__config-btn'], isOpen && styles['is-active'])}
          />
        )}
        options={dropdownOptionsModify}
      />
    );
  };

  const renderSearch = () => {
    return (
      <div className={styles['search']}>
        <SearchLargeIcon width={20} height={20} className={styles['search__icon']} />
        <InputField
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.currentTarget.value)}
          containerClassName={styles['search-field']}
          className={styles['search-field__input']}
          placeholder={formatMessage({ id: 'team.search' })}
          fieldSize="md"
          onClear={() => setSearchQuery('')}
        />
      </div>
    );
  };

  const renderSorting = () => {
    const dropdownOptions: TDropdownOptionBase[] = [
      {
        label: (
          <p className={styles['dropdown__sorting']}>
            <span>Sort by name</span> (A-Z)
          </p>
        ),
        value: EUserListSorting.NameAsc,
      },
      {
        label: (
          <p className={styles['dropdown__sorting']}>
            <span>Sort by name</span> (Z-A)
          </p>
        ),
        value: EUserListSorting.NameDesc,
      },
      {
        label: (
          <p className={styles['dropdown__sorting']}>
            <span>Group by</span> status
          </p>
        ),
        value: EUserListSorting.Status,
      },
    ];

    return (
      <DropdownList
        placement="left"
        className={styles['test']}
        controlSize="sm"
        isSearchable={false}
        defaultValue={dropdownOptions.find((item) => item.value === sorting)}
        onChange={(val: any) => dispatch(userListSortingChanged(val.value))}
        options={dropdownOptions}
      />
    );
  };

  const renderUserList = () => {
    const list = getFilteredUsers().map((user: TUserListItem) => (
      <div key={user.id} className={styles['list__item']}>
        <GroupUser user={{ ...user, isAccountOwner: user.isAccountOwner && !user.invite }} />
      </div>
    ));

    if (!list.length) {
      return (
        <Placeholder
          title={formatMessage({ id: 'group.list-user.title' })}
          description={formatMessage({ id: 'group.list-user.caption' })}
          Icon={TasksPlaceholderIcon}
          mood="neutral"
          containerClassName={styles['placeholder']}
        />
      );
    }

    return list;
  };

  return (
    <div className={styles['container']}>
      <header className={styles['header']}>
        <h1 title={group.name}>{group.name}</h1>
        <div className={styles['header__config']}>
          <div className={styles['header__config-item']}>{renderAddUsers()}</div>
          <div className={styles['header__config-item']}>{renderModify()}</div>
        </div>
      </header>
      <div className={styles['list']}>
        <div className={styles['list__filter']}>
          {renderSearch()}
          {renderSorting()}
        </div>
        {renderUserList()}
      </div>

      <EditGroupModal />
    </div>
  );
}
