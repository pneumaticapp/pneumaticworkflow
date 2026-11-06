import type { IGroup } from '../../../types/team';
import type { IWsGroupData } from '../types';

export function mapWsGroupToGroup(group: IWsGroupData): IGroup {
  return {
    id: group.id,
    name: group.name,
    photo: group.photo,
    type: group.type,
    users: group.users,
  };
}
