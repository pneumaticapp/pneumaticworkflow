/* eslint-disable @typescript-eslint/no-shadow */
import { EUserStatus, TUserListItem } from '../types/user';
import { IInviteResponse } from '../api/sendInvites';
import { capitalize } from './strings';
import { NotificationManager } from '../components/UI/Notifications';
import { getPluralNoun } from './helpers';
import { IUserInvite } from '../types/team';
import { TDropdownOptionBase } from '../components/UI';

export const EXTERNAL_USER_ID = -1;

export const EXTERNAL_USER: TUserListItem = {
  id: EXTERNAL_USER_ID,
  firstName: 'External',
  lastName: 'User',
  status: EUserStatus.External,
  email: '',
  photo: '',
  phone: '',
  type: 'user',
};

type TUserNameParts = {
  firstName?: string;
  lastName?: string;
  status?: EUserStatus;
  email?: string;
};
type TUserNameOptions = {
  withAtSign?: boolean;
};
export const getUserFullName = (user?: TUserNameParts | null, options: TUserNameOptions = {}): string => {
  if (!user) {
    return '';
  }

  const includedStatuses = [EUserStatus.Inactive];
  const { withAtSign } = options;
  const { firstName = '', lastName = '', email = '', status } = user;

  const fullName = `${firstName} ${lastName}`.trim();
  const formattedFullName = fullName ? `${withAtSign ? '@' : ''}${fullName}` : '';
  const userName = formattedFullName || email;
  if (!userName) {
    return '';
  }

  const statusLabel = status && includedStatuses.includes(status) ? `(${capitalize(status)})` : '';

  return `${userName} ${statusLabel}`.trim();
};

export const getActiveUsers = (users: TUserListItem[]) => {
  return users.filter((user) => user.status === EUserStatus.Active && user.type === 'user');
};

export const getInvitedUsers = (users: TUserListItem[]) => {
  return users.filter((user) => user.status === EUserStatus.Invited && user.type === 'user');
};

export const getNotDeletedUsers = (users: TUserListItem[]) => {
  const activeUsers = users.filter((user) =>
    [user.status !== EUserStatus.Deleted, user.status !== EUserStatus.Inactive, user.type === 'user'].every(Boolean),
  );

  return activeUsers;
};

export const sortUsersByStatus = (users: TUserListItem[]) => {
  return users.slice().sort((a, b) => {
    if ([a.status, b.status].every((status) => status !== EUserStatus.Invited)) {
      return 0;
    }

    return a.status === EUserStatus.Invited ? 1 : -1;
  });
};

const getUserNameForSorting = (user: TUserListItem) => {
  const name = user.firstName || user.email;

  return name.toLowerCase();
};

export const sortUsersByNameAsc = (users: TUserListItem[]) => {
  return users.slice().sort((user1, user2) => {
    return getUserNameForSorting(user1) > getUserNameForSorting(user2) ? 1 : -1;
  });
};

export const sortUsersByNameDesc = (users: TUserListItem[]) => {
  return users.slice().sort((user1, user2) => {
    return getUserNameForSorting(user1) < getUserNameForSorting(user2) ? 1 : -1;
  });
};

export interface IShowNotification {
  (type: 'success' | 'warning', invites: IUserInvite[], title?: string): void;
}

export interface IShowInvitesNotification {
  invites: IUserInvite[];
  sendInvitesResult: IInviteResponse;
}

export const showInvitesNotification = ({ invites, sendInvitesResult }: IShowInvitesNotification) => {
  const showNotification: IShowNotification = (type, invites, title) => {
    if (!invites.length) {
      return;
    }
    const notification = type === 'success' ? NotificationManager.success : NotificationManager.warning;
    const preNotificationTitle = type === 'success' ? 'Successfully invited' : 'Failed to invite';
    notification({
      title:
        title ||
        `${preNotificationTitle} ${getPluralNoun({
          counter: invites.length,
          single: 'user',
          plural: 'users',
          includeCounter: true,
        })}`,
      message: invites.map(({ email }) => email).join('\n'),
    });
  };

  const { alreadyAccepted } = sendInvitesResult;
  const alreadyAcceptedEmails = alreadyAccepted.map(({ email }) => email);
  const alreadyAcceptedUsers = invites.filter(({ email }) => alreadyAcceptedEmails.includes(email));
  const successfullyInvitedUsers = invites.filter(({ email }) => !alreadyAcceptedEmails.includes(email));

  showNotification('warning', alreadyAcceptedUsers, 'users.error-already-accepted');
  showNotification('success', successfullyInvitedUsers);
};

export type TUserDropdownOption = TUserListItem & TDropdownOptionBase;

export const getDropdownUsersList = (users: TUserListItem[]) => {
  const activeUsers = getNotDeletedUsers(users);

  const dropdownSelections: TUserDropdownOption[] = activeUsers.map((user) => ({
    ...user,
    value: String(user.id),
    label: getUserFullName(user)!,
  }));

  return dropdownSelections;
};
