import React, { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { TeamUser } from './TeamUser';
import { DeleteTeamUserPopupContainer } from './DeleteTeamUserPopup';
import { AddGuestsBanner } from './AddGuestsBanner';
import { CreateUserModal } from './CreateUserModal';

import { resendInvite } from '../../../api/resendInvite';
import { TUserListItem } from '../../../types/user';
import { getErrorMessage } from '../../../utils/getErrorMessage';
import { trackInviteTeamInPage } from '../../../utils/analytics';
import { SearchLargeIcon } from '../../icons';
import { InputField } from '../../UI';
import { AddButton } from '../../UI/Buttons/AddButton';
import { NotificationManager } from '../../UI/Notifications';
import { TeamUserSkeleton } from '../TeamUserSkeleton';
import { TITLES } from '../../../constants/titles';
import { PageTitle } from '../../PageTitle';
import { EPageTitle } from '../../../constants/defaultValues';
import { getSubscriptionPlan } from '../../../redux/selectors/user';
import { getIsCreateUserModalOpen } from '../../../redux/selectors/accounts';
import { ESubscriptionPlan } from '../../../types/account';
import { IUsersProps } from './types';
import { openCreateUserModal, closeCreateUserModal } from '../../../redux/accounts/actions';

import styles from './Users.css';



export const STATUS_TITLE_MAP: { [key: string]: string } = {
  active: 'team.title-group-active',
  invited: 'team.title-group-invited',
};

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
  loadInvitesUsers,
}: IUsersProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const billingPlan = useSelector(getSubscriptionPlan);
  const isCreateUserModalOpen = useSelector(getIsCreateUserModalOpen);
  const isFreePlan = billingPlan === ESubscriptionPlan.Free;
  const accessConditions = isSubscribed || isFreePlan;

  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchUsers({});
    loadInvitesUsers();
    document.title = TITLES.Team;
  }, []);

  const handleClickInviteButton = () => {
    openTeamInvitesPopup();
    trackInviteTeamInPage('Team Page');
  };

  const handleOpenCreateUserModal = () => {
    dispatch(openCreateUserModal());
  };

  const handleCloseCreateUserModal = () => {
    dispatch(closeCreateUserModal());
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
      <CreateUserModal isOpen={isCreateUserModalOpen} onClose={handleCloseCreateUserModal} />

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

      <div className={styles['cards']}>{renderUsers()}</div>
    </div>
  );
}
