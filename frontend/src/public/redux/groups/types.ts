import type { EGroupsListSorting, EUserListSorting } from '../../types/user';
import type { IGroup } from '../../types/team';

export interface IGroupsStore {
  isLoading: boolean;
  list: IGroup[];
  groupsListSorting: EGroupsListSorting;
  currentGroup: {
    data: IGroup | null;
    userListSorting: EUserListSorting;
  };
  createModal: boolean;
  editModal: {
    isOpen: boolean;
    editGroup: IGroup | null;
  };
}
