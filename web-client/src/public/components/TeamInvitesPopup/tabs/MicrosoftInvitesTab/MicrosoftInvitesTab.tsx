import React, { useCallback, useMemo, useState } from 'react';
import ScrollBar from 'react-perfect-scrollbar';
import { useDispatch } from 'react-redux';
import { useIntl } from 'react-intl';

import { Avatar, Button, InputField } from '../../../UI';
import popupStyles from '../../TeamInvitesPopup.css';
import { IUserInviteMicrosoft } from '../../../../types/team';
import { isMatchingSearchQuery } from '../../../../utils/strings';
import { getNotDeletedUsers, getUserFullName } from '../../../../utils/users';
import { TUserListItem } from '../../../../types/user';
import { inviteUsers } from '../../../../redux/actions';

import styles from '../OAuthInvitesTab/OAuthInvitesTab.css';

export function MicrosoftInvitesTab({ type, users, teamUsers }: IMicrosoftInvitesTabProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const [searchText, setSearchText] = useState('');
  const [pendingInvites, setPendingsInvites] = useState<string[]>([]);

  const addPendingInvite = (email: string) => setPendingsInvites([...pendingInvites, email]);
  const removePendingInvite = (email: string) =>
    setPendingsInvites(pendingInvites.filter((invite) => invite !== email));

  const filteredUsers = useMemo(() => {
    return users.filter((user) => isMatchingSearchQuery(searchText, [user.email, getUserFullName(user)]));
  }, [users, searchText]);

  const sendInvite = useCallback(
    (email: string) => () => {
      dispatch(
        inviteUsers({
          invites: [{ email, type }],
          withSuccessNotification: true,
          onStartUploading: () => {
            addPendingInvite(email);
          },
          onEndUploading: () => {
            removePendingInvite(email);
          },
          onError: () => {
            removePendingInvite(email);
          },
        }),
      );
    },
    [],
  );

  const renderList = () => {
    return (
      <ScrollBar options={{ suppressScrollX: true, wheelPropagation: false }} className={styles['scrollbar']}>
        <div className={styles['users']}>
          {filteredUsers.map((user) => {
            const { email } = user;
            const avatarUser = {
              firstName: user.firstName || '',
              lastName: user.lastName || '',
              email: user.email,
              photo: user.photo || '',
            };

            const isInvited = getNotDeletedUsers(teamUsers).some((invitedUser) => invitedUser.email === user.email);

            return (
              <div key={user.email} className={styles['user']}>
                <Avatar containerClassName={styles['user__avatar']} user={avatarUser} size="lg" />

                <div className={styles['user-info']}>
                  <p className={styles['user-info__name']}>{getUserFullName(avatarUser)}</p>
                  <p className={styles['user-info__email']}>{email}</p>
                </div>

                <Button
                  buttonStyle="yellow"
                  className={styles['user__add']}
                  onClick={sendInvite(email)}
                  label={formatMessage({ id: 'team.add-button' })}
                  size="md"
                  disabled={isInvited}
                  isLoading={pendingInvites.includes(email)}
                />
              </div>
            );
          })}
        </div>
      </ScrollBar>
    );
  };

  return (
    <>
      <InputField
        autoFocus
        value={searchText}
        onChange={(e) => setSearchText(e.currentTarget.value)}
        placeholder={formatMessage({ id: 'team.search-field' })}
        fieldSize="md"
        className={popupStyles['input-field']}
      />

      {renderList()}
    </>
  );
}

interface IMicrosoftInvitesTabProps {
  users: IUserInviteMicrosoft[];
  teamUsers: TUserListItem[];
  type: 'microsoft';
}
