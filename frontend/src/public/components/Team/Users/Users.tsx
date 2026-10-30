import React, { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { TeamUserCard } from './TeamUserCard';
import { DeleteTeamUserPopupContainer } from './DeleteTeamUserPopup';
import { AddGuestsBanner } from './AddGuestsBanner';
import { CreatePerformerModal } from '../CreatePerformerModal';
import { VacationSettingsModal } from './VacationSettingsModal';

import { EUserListSorting } from '../../../types/user';
import type { TUserListItem } from '../../../types/user';
import { trackInviteTeamInPage } from '../../../utils/analytics';
import { withSyncedQueryString } from '../../../HOCs/withSyncedQueryString';
import { SearchLargeIcon } from '../../icons';
import { InputField } from '../../UI';
import { AddButton } from '../../UI/Buttons/AddButton';
import { TeamUserSkeleton } from '../TeamUserSkeleton';
import { TITLES } from '../../../constants/titles';
import { PageTitle } from '../../PageTitle';
import { EPageTitle } from '../../../constants/defaultValues';
import { getIsUserSubsribed, getSubscriptionPlan } from '../../../redux/selectors/user';
import {
  getAccountsTeamList,
  getAccountsTeamIsLoading,
  getAccountsUserListSorting,
} from '../../../redux/selectors/accounts';
import { getAuthUserId } from '../../../redux/selectors/authUser';
import { ESubscriptionPlan } from '../../../types/account';
import type { IUsersProps } from './types';
import { teamFetchStarted, userListSortingChanged } from '../../../redux/accounts/slice';
import { loadInvitesUsers, openCreatePerformerModal, openTeamInvitesPopup } from '../../../redux/team/slice';

import styles from './Users.css';

export function Users({ userListSorting }: IUsersProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const users = useSelector(getAccountsTeamList);
  const isUsersLoading = useSelector(getAccountsTeamIsLoading);
  const currentUserId = useSelector(getAuthUserId);
  const isSubscribed = useSelector(getIsUserSubsribed);
  const billingPlan = useSelector(getSubscriptionPlan);

  const isFreePlan = billingPlan === ESubscriptionPlan.Free;
  const accessConditions = isSubscribed || isFreePlan;

  const [searchQuery, setSearchQuery] = useState('');
  const [vacationModalUser, setVacationModalUser] = useState<TUserListItem | null>(null);

  useEffect(() => {
    dispatch(teamFetchStarted({}));
    dispatch(loadInvitesUsers());
    document.title = TITLES.Team;
  }, [dispatch]);

  const getVisibleUsers = () => {
    if (!searchQuery) {
      return users;
    }

    const queryWords = searchQuery.split(' ').map((str) => str.toLowerCase());
    const checkQueryWord = (queryWord: string, user: TUserListItem) =>
      [user.firstName, user.lastName, user.email]
        .map((str) => str.toLowerCase())
        .some((property) => property.includes(queryWord));

    return users.filter((user) => queryWords.every((queryWord) => checkQueryWord(queryWord, user)));
  };

  const handleClickInviteButton = () => {
    dispatch(openTeamInvitesPopup());
    trackInviteTeamInPage('Team Page');
  };

  const handleOpenCreateUserModal = () => {
    dispatch(openCreatePerformerModal());
  };

  const handleCloseVacationModal = () => {
    setVacationModalUser(null);
  };

  const handleChangeSearchQuery = (e: React.FormEvent<HTMLInputElement>) => {
    setSearchQuery(e.currentTarget.value);
  };

  const handleClearSearchQuery = () => {
    setSearchQuery('');
  };

  const renderSearch = () => {
    return (
      <div className={styles['search']}>
        <SearchLargeIcon className={styles['search__icon']} />
        <InputField
          value={searchQuery}
          onChange={handleChangeSearchQuery}
          containerClassName={styles['search-field']}
          className={styles['search-field__input']}
          placeholder={formatMessage({ id: 'team.search' })}
          fieldSize="md"
          onClear={handleClearSearchQuery}
        />
      </div>
    );
  };

  const renderCards = () => {
    if (isUsersLoading) {
      return Array.from([1, 2, 3], (key) => <TeamUserSkeleton key={key} />);
    }

    return (
      <ul className={styles['cards__list']}>
        {getVisibleUsers().map((user) => (
          <li key={user.id}>
            <TeamUserCard
              user={user}
              currentUserId={currentUserId}
              isSubscribed={accessConditions}
              onOpenVacationModal={setVacationModalUser}
            />
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className={styles['container']}>
      <DeleteTeamUserPopupContainer />
      <AddGuestsBanner />
      <CreatePerformerModal />
      <VacationSettingsModal isOpen={!!vacationModalUser} onClose={handleCloseVacationModal} user={vacationModalUser} />

      <PageTitle titleId={EPageTitle.Team} withUnderline={false} />
      {renderSearch()}

      <div className={styles['buttons-row']}>
        <AddButton
          title={formatMessage({ id: 'team.invite-team-large-btn' })}
          caption={formatMessage({ id: 'team.invite-team-large-btn-caption' })}
          onClick={handleClickInviteButton}
        />
        <AddButton
          title={formatMessage({ id: 'team.create-user-button' })}
          caption={formatMessage({ id: 'team.create-user-button-caption' })}
          onClick={handleOpenCreateUserModal}
        />
      </div>

      <div className={styles['cards']}>{renderCards()}</div>
    </div>
  );
}

const SyncedUsers = withSyncedQueryString<IUsersProps>([
  {
    propName: 'userListSorting',
    queryParamName: 'sorting',
    defaultAction: userListSortingChanged(EUserListSorting.NameAsc),
    createAction: userListSortingChanged,
    getQueryParamByProp: (value) => value,
  },
])(Users) as React.ComponentType<IUsersProps>;

export function UsersContainer() {
  const userListSorting = useSelector(getAccountsUserListSorting);

  return <SyncedUsers userListSorting={userListSorting} />;
}
