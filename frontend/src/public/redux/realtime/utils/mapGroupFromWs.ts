import { IGroup } from '../../team/types';
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
