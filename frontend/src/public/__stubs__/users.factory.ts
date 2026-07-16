import { TUserListItem, EUserStatus } from '../types/user';

export const makeUser = (overrides: Partial<TUserListItem> = {}): TUserListItem => ({
  id: 1,
  email: '',
  firstName: '',
  lastName: '',
  phone: '',
  photo: '',
  status: EUserStatus.Active,
  type: 'user',
  ...overrides,
});
