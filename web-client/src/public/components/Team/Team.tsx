import * as React from 'react';
import { useIntl } from 'react-intl';

import { TeamUserSkeleton } from './TeamUserSkeleton';
import { TeamUser } from './TeamUser';
import { DeleteTeamUserPopupContainer } from './DeleteTeamUserPopup';
import { AddGuestsBanner } from './AddGuestsBanner';

import { resendInvite } from '../../api/resendInvite';
import { TITLES } from '../../constants/titles';
import { EUserListSorting, TUserListItem } from '../../types/user';
import { getErrorMessage } from '../../utils/getErrorMessage';
import {
  IChangeUserAdminProps,
  TOpenDeleteUserModalPayload,
  ITeamFetchStartedProps,
} from '../../redux/accounts/actions';
import { IntlMessages } from '../IntlMessages';
import { NotificationManager } from '../UI/Notifications';
import { trackInviteTeamInPage } from '../../utils/analytics';
import { RoundPlusIcon, SearchLargeIcon } from '../icons';
import { Header, InputField } from '../UI';

import styles from './Team.css';

export const STATUS_TITLE_MAP: { [key: string]: string } = {
  active: 'team.title-group-active',
  invited: 'team.title-group-invited',
};

export function Team({
  currentUserId,
  isLoading,
  users,
  isSubscribed,
  fetchUsers,
  resetUsers,
  loadChangeUserAdmin,
  openModal,
  openTeamInvitesPopup,
  setGeneralLoaderVisibility,
  loadMicrosoftInvites
}: ITeamProps) {
  const { formatMessage } = useIntl();

  const [searchQuery, setSearchQuery] = React.useState('');

  const renderSkeleton = () => Array.from([1, 2, 3], (key) => <TeamUserSkeleton key={key} />);

  React.useEffect(() => {
    document.title = TITLES.Team;

    fetchUsers({});
    loadMicrosoftInvites();

    return () => {
      resetUsers();
    };
  }, []);

  const handleClickInviteButton = () => {
    openTeamInvitesPopup();
    trackInviteTeamInPage('Team Page');
  };

  const renderInviteButton = () => {
    return (
      <button type="button" onClick={handleClickInviteButton} className={styles['invite-button']}>
        <RoundPlusIcon className={styles['invite-button__icon']} />
        <IntlMessages id="team.invite-team-large-btn">
          {(text) => (
            <Header tag="span" size="6">
              {text}
            </Header>
          )}
        </IntlMessages>
      </button>
    );
  };

  const renderUsers = () => {
    if (isLoading) {
      return renderSkeleton();
    }

    return getFilteredUsers().map((user) => {
      return (
        <TeamUser
          key={user.id}
          resendInvite={resendInviteHandler(user.id)}
          isCurrentUser={currentUserId === user.id}
          isSubscribed={isSubscribed}
          handleToggleAdmin={handleToggleUserAdmin}
          openModal={() => openModal({ user })}
          user={{ ...user, isAccountOwner: user.isAccountOwner && !user.invite }}
        />
      );
    });
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

  return (
    <div className={styles['container']}>
      <DeleteTeamUserPopupContainer />
      <AddGuestsBanner />

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

      {renderInviteButton()}

      <div className={styles['cards']}>{renderUsers()}</div>
    </div>
  );
}

export interface ITeamProps {
  currentUserId: number;
  isLoading?: boolean;
  sorting?: EUserListSorting;
  users: TUserListItem[];
  isTeamInvitesOpened?: boolean;
  isSubscribed?: boolean;
  trialEnded: boolean | null;
  userListSorting: EUserListSorting;
  fetchUsers(payload: ITeamFetchStartedProps): void;
  resetUsers(): void;
  loadChangeUserAdmin(payload: IChangeUserAdminProps): void;
  openModal(params: TOpenDeleteUserModalPayload): void;
  openTeamInvitesPopup(): void;
  loadMicrosoftInvites(): void;
  setGeneralLoaderVisibility(isVisible: boolean): void;
}
