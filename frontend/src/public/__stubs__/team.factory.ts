import { EUserGroupType } from '../types/team';
import type { IGroup } from '../types/team';

export const makeGroup = (overrides: Partial<IGroup> = {}): IGroup => ({
  id: 1,
  name: 'Group',
  photo: null,
  users: [],
  type: EUserGroupType.Regular,
  ...overrides,
});
