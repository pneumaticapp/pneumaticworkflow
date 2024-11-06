import * as React from 'react';
import * as PerfectScrollbar from 'react-perfect-scrollbar';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';

import { TeamPlaceholderIcon } from '../../TeamPlaceholderIcon';

import { getNotDeletedUsers, getUserFullName } from '../../../../utils/users';
import { connectGoogle, isArrayWithItems, omit } from '../../../../utils/helpers';
import { TUserListItem } from '../../../../types/user';
import { Avatar, Button, InputField, Placeholder } from '../../../UI';
import { inviteUsers } from '../../../../redux/actions';
import { isMatchingSearchQuery } from '../../../../utils/strings';
import { GoogleButton } from '../../../OAuthButtons';
import { IOAuthInviteView } from '../../../../types/team';

import styles from './OAuthInvitesTab.css';
import popupStyles from '../../TeamInvitesPopup.css';

interface IOAuthInvitesTabProps {
  users: IOAuthInviteView[];
  teamUsers: TUserListItem[];
  type: 'google';
}

const ScrollBar = PerfectScrollbar as unknown as Function;

export function OAuthInvitesTab({ type, users, teamUsers }: IOAuthInvitesTabProps) {
  const { formatMessage } = useIntl();
  const { useState, useCallback, useMemo } = React;
  const dispatch = useDispatch();
  const [pendingInvites, setPendingsInvites] = useState<string[]>([]);
  const [searchText, setSearchText] = useState('');
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

  const renderConnectButton = () => {
    const buttonsMap = {
      google: <GoogleButton onClick={connectGoogle} />,
    };

    return buttonsMap[type];
  };

  const renderList = () => {
    if (!isArrayWithItems(filteredUsers)) {
      return (
        <Placeholder
          title={formatMessage({ id: 'team.empty-placeholder-title' })}
          description={formatMessage({ id: 'team.empty-placeholder-description' })}
          Icon={TeamPlaceholderIcon}
          mood="bad"
          containerClassName={styles['empty-list-placeholder']}
        />
      );
    }

    return (
      <ScrollBar options={{ suppressScrollX: true, wheelPropagation: false }} className={styles['scrollbar']}>
        <div className={styles['users']}>
          {filteredUsers.map((user) => {
            const { avatar, email } = user;
            const avatarUser = { ...omit(user, ['type', 'avatar']), photo: avatar };
            const isInvited = getNotDeletedUsers(teamUsers).some((invitedUser) => invitedUser.email === user.email);

            return (
              <div key={user.email} className={styles['user']}>
                <Avatar containerClassName={styles['user__avatar']} user={avatarUser} size="lg" />

                <div className={styles['user-info']}>
                  <p className={styles['user-info__name']}>{getUserFullName(user)}</p>
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

  const isConnected = isArrayWithItems(users);
  if (!isConnected) {
    return renderConnectButton();
  }

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
