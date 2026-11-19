import type { TUserListItem } from '../types/user';
import { EUserStatus } from '../types/user';
import { capitalize } from './strings';

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
