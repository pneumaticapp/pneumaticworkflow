import * as React from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { TeamUser } from './TeamUser';
import { DeleteTeamUserPopupContainer } from './DeleteTeamUserPopup';
import { AddGuestsBanner } from './AddGuestsBanner';

import { resendInvite } from '../../../api/resendInvite';
import { EUserListSorting, TUserListItem } from '../../../types/user';
import { getErrorMessage } from '../../../utils/getErrorMessage';
import {
  IChangeUserAdminProps,
  TOpenDeleteUserModalPayload,
  ITeamFetchStartedProps,
} from '../../../redux/accounts/actions';
import { trackInviteTeamInPage } from '../../../utils/analytics';
import { SearchLargeIcon } from '../../icons';
import { InputField } from '../../UI';
import { AddButton } from '../../UI/Buttons/AddButton';
import { NotificationManager } from '../../UI/Notifications';
import { TeamUserSkeleton } from '../TeamUserSkeleton';
import { TITLES } from '../../../constants/titles';
import { PageTitle } from '../../PageTitle';
import { EPageTitle } from '../../../constants/defaultValues';

import styles from './Users.css';
import { getSubscriptionPlan } from '../../../redux/selectors/user';
import { ESubscriptionPlan } from '../../../types/account';

export const STATUS_TITLE_MAP: { [key: string]: string } = {
  active: 'team.title-group-active',
  invited: 'team.title-group-invited',
};

export interface IUsersProps {
  currentUserId: number;
  isLoading?: boolean;
  sorting?: EUserListSorting;
  users: TUserListItem[];
  isTeamInvitesOpened?: boolean;
  isSubscribed?: boolean;
  trialEnded: boolean | null;
  userListSorting: EUserListSorting;
  fetchUsers(payload: ITeamFetchStartedProps): void;
  loadChangeUserAdmin(payload: IChangeUserAdminProps): void;
  openModal(params: TOpenDeleteUserModalPayload): void;
  openTeamInvitesPopup(): void;
  loadMicrosoftInvites(): void;
  setGeneralLoaderVisibility(isVisible: boolean): void;
}

export function Users({
  currentUserId,
  isLoading,
  users,
  isSubscribed,
  fetchUsers,
  loadChangeUserAdmin,
  openModal,
  openTeamInvitesPopup,
  setGeneralLoaderVisibility,
  loadMicrosoftInvites,
}: IUsersProps) {
  const { formatMessage } = useIntl();

  const billingPlan = useSelector(getSubscriptionPlan);
  const isFreePlan = billingPlan === ESubscriptionPlan.Free;
  const accessConditions = isSubscribed || isFreePlan;

  const [searchQuery, setSearchQuery] = React.useState('');

  React.useEffect(() => {
    fetchUsers({});
    loadMicrosoftInvites();
    document.title = TITLES.Team;
  }, []);

  const handleClickInviteButton = () => {
    openTeamInvitesPopup();
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

  const renderUsers = () => {
    if (isLoading) {
      return Array.from([1, 2, 3], (key) => <TeamUserSkeleton key={key} />);
    }

    const getFilteredUsers = () => {
      if (!searchQuery) {
        return users;
      }

      const queryWords = searchQuery.split(' ').map((str) => str.toLowerCase());
      const checkQueryWord = (queryWord: string, user: TUserListItem) => {
        return [user.firstName, user.lastName, user.email]
          .map((str) => str.toLowerCase())
          .some((property) => property.includes(queryWord));
      };

      const filteredUsers = users.filter((user) => {
        return queryWords.every((queryWord) => checkQueryWord(queryWord, user));
      });

      return filteredUsers;
    };

    const resendInviteHandler = (userId?: number) => async () => {
      if (userId) {
        try {
          setGeneralLoaderVisibility(true);
          await resendInvite(userId);
          NotificationManager.success({ message: 'team.resend-invite-success-msg' });
        } catch (err) {
          NotificationManager.warning({ message: getErrorMessage(err) });
        } finally {
          setGeneralLoaderVisibility(false);
        }
      }
    };

    const handleToggleUserAdmin = (user: TUserListItem) => async () => {
      const { id, isAdmin, email } = user;

      if (id && email) {
        loadChangeUserAdmin({ id, isAdmin: !isAdmin, email });
      }
    };

    return getFilteredUsers().map((user) => {
      return (
        <TeamUser
          key={user.id}
          resendInvite={resendInviteHandler(user.id)}
          isCurrentUser={currentUserId === user.id}
          isSubscribed={accessConditions}
          handleToggleAdmin={handleToggleUserAdmin}
          openModal={() => openModal({ user })}
          user={{ ...user, isAccountOwner: user.isAccountOwner && !user.invite }}
        />
      );
    });
  };

  return (
    <div className={styles['container']}>
      <DeleteTeamUserPopupContainer />
      <AddGuestsBanner />

      <PageTitle titleId={EPageTitle.Team} withUnderline={false} />
      {renderSearch()}

      <AddButton
        title={formatMessage({ id: 'team.invite-team-large-btn' })}
        caption={formatMessage({ id: 'team.invite-team-large-btn-caption' })}
        onClick={handleClickInviteButton}
      />

      <div className={styles['cards']}>{renderUsers()}</div>
    </div>
  );
}
