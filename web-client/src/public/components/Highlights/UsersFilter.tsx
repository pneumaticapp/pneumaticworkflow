/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';
import { useIntl } from 'react-intl';

import { Checkbox } from '../UI/Fields/Checkbox';
import { getUserFullName } from '../../utils/users';
import { IntlMessages } from '../IntlMessages';
import { TUserListItem } from '../../types/user';
import { isArrayWithItems } from '../../utils/helpers';
import { ShowMore } from '../UI/ShowMore';

import styles from './Filters.css';

export interface IUsersFilterProps {
  searchText: string;
  selectedUsers: number[];
  users: TUserListItem[];
  changeUsersFilter(userId: number): (e: React.ChangeEvent<HTMLInputElement>) => void;
  changeUsersSearchText(e: React.ChangeEvent<HTMLInputElement>): void;
}

const MAX_SHOW_USERS = 10;

export function UsersFilter({
  searchText,
  selectedUsers,
  users,
  changeUsersFilter,
  changeUsersSearchText,
}: IUsersFilterProps) {
  const { useCallback, useEffect, useMemo, useState } = React;
  const { formatMessage } = useIntl();

  const isUsersNumberExceeded = useMemo(
    () => users.length > MAX_SHOW_USERS,
    [users],
  );

  const isSearchFilled = useMemo(
    () => searchText.length > 1,
    [searchText],
  );

  const [isShowAllVisibleState, setShowAllVisibleState] = useState(isSearchFilled ? false : isUsersNumberExceeded);

  useEffect(
    () => setShowAllVisibleState(isUsersNumberExceeded),
    [isUsersNumberExceeded],
  );

  const handleShowAll = useCallback(
    () => setShowAllVisibleState(!isShowAllVisibleState),
    [isShowAllVisibleState, isUsersNumberExceeded],
  );

  const truncatedUsers = useMemo(() => {
    if (!isShowAllVisibleState && !isSearchFilled) {
      return users;
    }

    if (isSearchFilled) {
      return users.filter(({ firstName, lastName }) => (
        [firstName, lastName].join(' ').toLowerCase().includes(searchText.toLowerCase())
      ));
    }

    const usersToShow = users.slice(0, MAX_SHOW_USERS);
    const isSelectedWorkflowsHidden = selectedUsers.some(id => !usersToShow.map(({ id }) => id).includes(id));

    if (isSelectedWorkflowsHidden) {
      handleShowAll();
    }

    return usersToShow;
  }, [isShowAllVisibleState, searchText, selectedUsers, users]);

  const isPanelExpanded = isArrayWithItems(selectedUsers) ? true : undefined;
  const lastCheckboxClassname = isShowAllVisibleState ? styles['mb-1'] : styles['mb-4'];

  return (
    <ShowMore
      containerClassName={styles['filter-container']}
      label="process-highlights.date-picker-by-users-label"
      isInitiallyVisible={isPanelExpanded}
    >
      {isUsersNumberExceeded &&
        <input
          autoFocus
          className={styles['filter__input']}
          placeholder={formatMessage({ id: 'process-highlights.search-users-placeholder'})}
          value={searchText}
          onChange={changeUsersSearchText}
        />
      }
      <div className={styles['filter__checkboxes']}>
        {truncatedUsers.map((user, idx) => (
          <Checkbox
            containerClassName={idx === truncatedUsers.length - 1 ? lastCheckboxClassname : styles['mb-1']}
            id={`users-filter__checkbox_${user.id}`}
            title={getUserFullName(user)}
            onChange={changeUsersFilter(user.id)}
            checked={selectedUsers.includes(user.id)}
            key={`users-filter-checkbox-${user.id}`}
          />
        ))}
      </div>
      {isShowAllVisibleState &&
        <button className={classnames('mb-4', styles['filter__button-show-all'])} onClick={handleShowAll}>
          <IntlMessages id ="process-highlights.show-all-users" />
        </button>
      }
    </ShowMore>
  );
}
