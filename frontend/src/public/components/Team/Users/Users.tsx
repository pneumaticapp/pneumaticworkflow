import * as React from 'react';
import { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { TeamUserCard } from './TeamUserCard';
import { TeamAgent } from './TeamAgent';
import { DeleteTeamUserPopupContainer } from './DeleteTeamUserPopup';
import { AddGuestsBanner } from './AddGuestsBanner';
import { CreatePerformerModal } from './CreatePerformerModal';
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
  getIsAccountsTeamLoading,
  getIsCreateUserModalOpen,
  getUserListSorting,
} from '../../../redux/selectors/accounts';
import { getAuthUserId } from '../../../redux/selectors/authUser';
import { getAIAgentsState, getAIProviders } from '../../../redux/selectors/ai';
import { ESubscriptionPlan } from '../../../types/account';
import type { IUsersProps, TTeamListItem } from './types';
import {
  closeCreateUserModal,
  openCreateUserModal,
  teamFetchStarted,
  userListSortingChanged,
} from '../../../redux/accounts/slice';
import { loadInvitesUsers, openTeamInvitesPopup } from '../../../redux/team/slice';
import { loadAIAgents, loadAIProviders } from '../../../redux/ai/slice';
import { matchesSearchQuery, sortListItems } from './listUtils';

import styles from './Users.css';

export function Users({ userListSorting }: IUsersProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const users = useSelector(getAccountsTeamList);
  const isUsersLoading = useSelector(getIsAccountsTeamLoading);
  const currentUserId = useSelector(getAuthUserId);
  const isSubscribed = useSelector(getIsUserSubsribed);
  const billingPlan = useSelector(getSubscriptionPlan);
  const isCreateUserModalOpen = useSelector(getIsCreateUserModalOpen);
  const { list: agents, isLoading: areAgentsLoading } = useSelector(getAIAgentsState);
  const providers = useSelector(getAIProviders);

  const isFreePlan = billingPlan === ESubscriptionPlan.Free;
  const accessConditions = isSubscribed || isFreePlan;

  const [searchQuery, setSearchQuery] = useState('');
  const [vacationModalUser, setVacationModalUser] = useState<TUserListItem | null>(null);

  useEffect(() => {
    dispatch(teamFetchStarted({}));
    dispatch(loadInvitesUsers());
    dispatch(loadAIAgents());
    dispatch(loadAIProviders());
    document.title = TITLES.Team;
  }, [dispatch]);

  const providerNameById = new Map(providers.map((provider) => [provider.id, provider.name]));

  const getVisibleItems = (): TTeamListItem[] => {
    const items: TTeamListItem[] = [
      ...users.map((user) => ({ kind: 'user' as const, user })),
      ...agents.map((agent) => ({ kind: 'agent' as const, agent })),
    ];

    const filteredItems = searchQuery
      ? items.filter((item) =>
          matchesSearchQuery(
            item,
            searchQuery.split(' ').map((str) => str.toLowerCase()),
          ),
        )
      : items;

    return sortListItems(filteredItems, userListSorting);
  };

  const handleClickInviteButton = () => {
    dispatch(openTeamInvitesPopup());
    trackInviteTeamInPage('Team Page');
  };

  const renderSearch = () => {
    return (
      <div className={styles['search']}>
        <SearchLargeIcon className={styles['search__icon']} />
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

  const renderCards = () => {
    if (isUsersLoading || areAgentsLoading) {
      return Array.from([1, 2, 3], (key) => <TeamUserSkeleton key={key} />);
    }

    return getVisibleItems().map((item) => {
      if (item.kind === 'user') {
        return (
          <TeamUserCard
            key={`user:${item.user.id}`}
            user={item.user}
            currentUserId={currentUserId}
            isSubscribed={accessConditions}
            onOpenVacationModal={setVacationModalUser}
          />
        );
      }

      return (
        <div key={`agent:${item.agent.id}`} className={styles['card-wrapper']}>
          <TeamAgent agent={item.agent} providerName={providerNameById.get(item.agent.providerId)} />
        </div>
      );
    });
  };

  return (
    <div className={styles['container']}>
      <DeleteTeamUserPopupContainer />
      <AddGuestsBanner />
      <CreatePerformerModal isOpen={isCreateUserModalOpen} onClose={() => dispatch(closeCreateUserModal())} />
      <VacationSettingsModal
        isOpen={!!vacationModalUser}
        onClose={() => setVacationModalUser(null)}
        user={vacationModalUser}
      />

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
          onClick={() => dispatch(openCreateUserModal())}
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
  const userListSorting = useSelector(getUserListSorting);

  return <SyncedUsers userListSorting={userListSorting} />;
}
