import { EUserGroupType, InvitesType } from '../redux/team/types';
import type { IGroup, UserInvite } from '../redux/team/types';

export const makeGroup = (overrides: Partial<IGroup> = {}): IGroup => ({
  id: 1,
  name: 'Group',
  photo: null,
  users: [],
  type: EUserGroupType.Regular,
  ...overrides,
});

export const makeUserInvite = (overrides: Partial<UserInvite> = {}): UserInvite => ({
  id: 1,
  email: 'invite@pneumatic.app',
  firstName: 'John',
  lastName: 'Doe',
  jobTitle: 'Developer',
  photo: 'https://pneumatic.app/photo.png',
  source: InvitesType.Google,
  ...overrides,
});
