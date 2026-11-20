import { EInvitesType, EUserGroupType } from '../types/team';
import type { IGroup, IUserInvite } from '../types/team';

export const makeGroup = (overrides: Partial<IGroup> = {}): IGroup => ({
  id: 1,
  name: 'Group',
  photo: null,
  users: [],
  type: EUserGroupType.Regular,
  ...overrides,
});

export const makeUserInvite = (overrides: Partial<IUserInvite> = {}): IUserInvite => ({
  id: 1,
  email: 'invite@pneumatic.app',
  firstName: 'John',
  lastName: 'Doe',
  jobTitle: 'Developer',
  photo: 'https://pneumatic.app/photo.png',
  source: EInvitesType.Google,
  ...overrides,
});
