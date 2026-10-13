import { IGroup, EUserGroupType } from '../redux/team/types';

export const makeGroup = (overrides: Partial<IGroup> = {}): IGroup => ({
  id: 1,
  name: 'Group',
  photo: null,
  users: [],
  type: EUserGroupType.Regular,
  ...overrides,
});
