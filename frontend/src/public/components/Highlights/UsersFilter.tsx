import * as React from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useIntl } from 'react-intl';

import { Checkbox } from '../UI/Fields/Checkbox';
import { getUserFullName } from '../../utils/users';
import { IntlMessages } from '../IntlMessages';
import { isArrayWithItems } from '../../utils/helpers';
import { ShowMore } from '../UI/ShowMore';
import { IUsersFilterProps } from './types';

import styles from './Filters.css';

const MAX_SHOW_USERS = 10;

export function UsersFilter({
  searchText,
  selectedUsers,
  users,
  changeUsersFilter,
  changeUsersSearchText,
}: IUsersFilterProps) {
  const { formatMessage } = useIntl();
  const searchInputRef = useRef<HTMLInputElement>(null);

  const isUsersNumberExceeded = useMemo(() => users.length > MAX_SHOW_USERS, [users]);

  const isSearchFilled = useMemo(() => searchText.length > 1, [searchText]);

  const [isShowAllVisibleState, setShowAllVisibleState] = useState(
    isSearchFilled ? false : isUsersNumberExceeded,
  );

  useEffect(() => {
    setShowAllVisibleState(isUsersNumberExceeded);
  }, [isUsersNumberExceeded]);

  useEffect(() => {
    if (isUsersNumberExceeded) {
      searchInputRef.current?.focus();
    }
  }, [isUsersNumberExceeded]);

  const handleShowAll = useCallback(() => {
    setShowAllVisibleState((isVisible) => !isVisible);
  }, []);

  const truncatedUsers = useMemo(() => {
    if (!isShowAllVisibleState && !isSearchFilled) {
      return users;
    }

    if (isSearchFilled) {
      return users.filter(({ firstName, lastName }) =>
        [firstName, lastName].join(' ').toLowerCase().includes(searchText.toLowerCase()),
      );
    }

    const usersToShow = users.slice(0, MAX_SHOW_USERS);
    const isSelectedUsersHidden = selectedUsers.some(
      (id) => !usersToShow.map(({ id: userId }) => userId).includes(id),
    );

    if (isSelectedUsersHidden) {
      handleShowAll();
    }

    return usersToShow;
  }, [handleShowAll, isSearchFilled, isShowAllVisibleState, searchText, selectedUsers, users]);

  const isPanelExpanded = isArrayWithItems(selectedUsers) ? true : undefined;

  return (
    <ShowMore
      containerClassName={styles['filter']}
      label="process-highlights.date-picker-by-users-label"
      isInitiallyVisible={isPanelExpanded}
    >
      {isUsersNumberExceeded && (
        <input
          ref={searchInputRef}
          className={styles['filter__input']}
          placeholder={formatMessage({ id: 'process-highlights.search-users-placeholder' })}
          value={searchText}
          onChange={changeUsersSearchText}
        />
      )}
      <div className={styles['filter__options']}>
        {truncatedUsers.map((user) => (
          <Checkbox
            id={`users-filter__checkbox_${user.id}`}
            title={getUserFullName(user)}
            titleClassName={styles['filter__option-label']}
            labelClassName={styles['filter__option-row']}
            onChange={changeUsersFilter(user.id)}
            checked={selectedUsers.includes(user.id)}
            key={`users-filter-checkbox-${user.id}`}
          />
        ))}
      </div>
      {isShowAllVisibleState && (
        <button
          type="button"
          className={styles['filter__show-all']}
          onClick={handleShowAll}
          aria-label={formatMessage({ id: 'process-highlights.show-all-users' })}
        >
          <IntlMessages id="process-highlights.show-all-users" />
        </button>
      )}
    </ShowMore>
  );
}
