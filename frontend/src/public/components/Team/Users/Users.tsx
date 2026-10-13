import * as React from 'react';
import { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { TeamUser } from './TeamUser';
import { TeamAgent } from './TeamAgent';
import { DeleteTeamUserPopupContainer } from './DeleteTeamUserPopup';
import { AddGuestsBanner } from './AddGuestsBanner';
import { CreatePerformerModal } from './CreatePerformerModal';
import { VacationSettingsModal } from './VacationSettingsModal';

import { resendInvite } from '../../../api/resendInvite';
import { EUserListSorting, EUserStatus } from '../../../types/user';
import type { TUserListItem } from '../../../types/user';
import { getErrorMessage } from '../../../utils/getErrorMessage';
import { getUserNameForSorting } from '../../../utils/users';
import { trackInviteTeamInPage } from '../../../utils/analytics';
import { withSyncedQueryString } from '../../../HOCs/withSyncedQueryString';
import { SearchLargeIcon } from '../../icons';
import { InputField } from '../../UI';
import { AddButton } from '../../UI/Buttons/AddButton';
import { NotificationManager } from '../../UI/Notifications';
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
  loadChangeUserAdmin,
  loadChangeUserManager,
  loadChangeUserReports,
  openCreateUserModal,
  openDeleteUserModal,
  teamFetchStarted,
  userListSortingChanged,
} from '../../../redux/accounts/slice';
import { loadInvitesUsers, openTeamInvitesPopup } from '../../../redux/team/slice';
import { loadAIAgents, loadAIProviders } from '../../../redux/ai/slice';
import { setGeneralLoaderVisibility } from '../../../redux/actions';

import styles from './Users.css';

const getItemName = (item: TTeamListItem): string => {
  return item.kind === 'user' ? getUserNameForSorting(item.user) : item.agent.name.toLowerCase();
};

const sortListItems = (items: TTeamListItem[], sorting: EUserListSorting): TTeamListItem[] => {
  const compareNames = (a: TTeamListItem, b: TTeamListItem) => {
    const [nameA, nameB] = [getItemName(a), getItemName(b)];

    return nameA > nameB ? 1 : nameA < nameB ? -1 : 0;
  };

  if (sorting === EUserListSorting.NameDesc) {
    return items.slice().sort((a, b) => compareNames(b, a));
  }

  if (sorting === EUserListSorting.Status) {
    const isInvitedUser = (item: TTeamListItem) => item.kind === 'user' && item.user.status === EUserStatus.Invited;

    return items
      .slice()
      .sort(compareNames)
      .sort((a, b) => {
        if (!isInvitedUser(a) && !isInvitedUser(b)) {
          return 0;
        }

        return isInvitedUser(a) ? 1 : -1;
      });
  }

  return items.slice().sort(compareNames);
};

const matchesSearchQuery = (item: TTeamListItem, queryWords: string[]): boolean => {
  const fields = item.kind === 'user' ? [item.user.firstName, item.user.lastName, item.user.email] : [item.agent.name];
  const loweredFields = fields.map((str) => str.toLowerCase());

  return queryWords.every((queryWord) => loweredFields.some((field) => field.includes(queryWord)));
};

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

  const renderUserCard = (user: TUserListItem) => {
    const resendInviteHandler = async () => {
      if (user.id) {
        try {
          dispatch(setGeneralLoaderVisibility(true));
          await resendInvite(user.id);
          NotificationManager.success({ message: 'team.resend-invite-success-msg' });
        } catch (err) {
          NotificationManager.warning({ message: getErrorMessage(err) });
        } finally {
          dispatch(setGeneralLoaderVisibility(false));
        }
      }
    };

    const handleToggleUserAdmin = (targetUser: TUserListItem) => async () => {
      const { id, isAdmin, email } = targetUser;

      if (id && email) {
        dispatch(loadChangeUserAdmin({ id, isAdmin: !isAdmin, email }));
      }
    };

    const handleChangeUserManager = (
      userId: number,
      managerId: number | null,
      callbacks?: { onSuccess?: () => void; onError?: () => void },
    ) => {
      dispatch(loadChangeUserManager({ id: userId, managerId, ...callbacks }));
    };

    const handleChangeUserReports = (
      userId: number,
      reportIds: number[],
      callbacks?: { onSuccess?: () => void; onError?: () => void },
    ) => {
      dispatch(loadChangeUserReports({ id: userId, reportIds, ...callbacks }));
    };

    return (
      <TeamUser
        key={user.id}
        resendInvite={resendInviteHandler}
        isCurrentUser={currentUserId === user.id}
        isSubscribed={accessConditions}
        handleToggleAdmin={handleToggleUserAdmin}
        handleChangeUserManager={handleChangeUserManager}
        handleChangeUserReports={handleChangeUserReports}
        openModal={() => dispatch(openDeleteUserModal({ user }))}
        openVacationModal={() => setVacationModalUser(user)}
        user={{ ...user, isAccountOwner: user.isAccountOwner && !user.invite }}
      />
    );
  };

  const renderCards = () => {
    if (isUsersLoading || areAgentsLoading) {
      return Array.from([1, 2, 3], (key) => <TeamUserSkeleton key={key} />);
    }

    return getVisibleItems().map((item) => {
      if (item.kind === 'user') {
        return renderUserCard(item.user);
      }

      return (
        <div key={item.agent.id} className={styles['card-wrapper']}>
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
