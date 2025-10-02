import React, { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { AddGuestsBanner } from './AddGuestsBanner';
import { TeamUserSkeleton } from '../TeamUserSkeleton';
import { TITLES } from '../../../constants/titles';
import { PageTitle } from '../../PageTitle';
import { EPageTitle } from '../../../constants/defaultValues';
import { EGroupsListSorting } from '../../../types/user';
import { SearchLargeIcon } from '../../icons';
import { InputField, Placeholder } from '../../UI';
import { AddButton } from '../../UI/Buttons/AddButton';
import { IGroup } from '../../../types/team';
import { CreateGroupModal } from './CreateGroupModal';
import { EditGroupModal } from './EditGroupModal';
import { Group } from './Group';
import { createModalOpen, teamFetchStarted } from '../../../redux/actions';
import { IApplicationState } from '../../../types/redux';
import { TasksPlaceholderIcon } from '../../Tasks/TasksPlaceholderIcon';

import styles from './Groups.css';

export const STATUS_TITLE_MAP: { [key: string]: string } = {
  active: 'team.title-group-active',
  invited: 'team.title-group-invited',
};

export interface IGroupsProps {
  groupsListSorting: EGroupsListSorting;
  updateGroup(payload: Partial<IGroup>): void;
  editModalClose(): void;
}

export function Groups() {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  const { list: groups, isLoading } = useSelector((state: IApplicationState) => state.groups);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    dispatch(teamFetchStarted({}));
    document.title = TITLES.Groups;
  }, []);

  const renderSearch = () => {
    return (
      <>
        <SearchLargeIcon className={styles['search__icon']} />
        <InputField
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.currentTarget.value)}
          containerClassName={styles['search-field']}
          className={styles['search-field__input']}
          placeholder={formatMessage({ id: 'team.groups.search' })}
          fieldSize="md"
          onClear={() => setSearchQuery('')}
        />
      </>
    );
  };

  const renderGroups = () => {
    if (isLoading) return Array.from([1, 2, 3], (key) => <TeamUserSkeleton key={key} />);

    const getFilteredGroups = () => {
      if (!searchQuery) return groups;

      const queryWords = searchQuery.split(' ').map((str) => str.toLowerCase());
      const checkQueryWord = (queryWord: string, user: IGroup) => {
        return [user.name].map((str) => str.toLowerCase()).some((property) => property.includes(queryWord));
      };

      return groups.filter((group) => {
        return queryWords.every((queryWord) => checkQueryWord(queryWord, group));
      });
    };

    const filteredGroups = getFilteredGroups();

    if (!filteredGroups.length) {
      return (
        <Placeholder
          title={formatMessage({ id: 'team.groups.empty-result-title' })}
          description={formatMessage({ id: 'team.groups.empty-result-description' })}
          Icon={TasksPlaceholderIcon}
          mood="neutral"
          containerClassName={styles['placeholder']}
        />
      );
    }

    return filteredGroups.map((group) => {
      return (
        <div key={group.id} className={styles['groups__item']}>
          <Group group={group} />
        </div>
      );
    });
  };

  return (
    <div className={styles['container']}>
      <PageTitle titleId={EPageTitle.Team} withUnderline={false} />
      <AddGuestsBanner />
      <section className={styles['search']}>{renderSearch()}</section>
      <AddButton
        title={formatMessage({ id: 'team.groups.add-group.title' })}
        caption={formatMessage({ id: 'team.groups.add-group.caption' })}
        onClick={() => dispatch(createModalOpen())}
      />
      <div className={styles['groups']}>{renderGroups()}</div>
      <CreateGroupModal />
      <EditGroupModal />
    </div>
  );
}
