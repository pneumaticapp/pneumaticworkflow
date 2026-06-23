import { IGroup } from '../../team/types';
import type { IWsGroupData } from '../types';

export function mapWsGroupToGroup(group: IWsGroupData): IGroup {
  return {
    ...group,
    users: group.users.map((user) => user.id)
  };
}
