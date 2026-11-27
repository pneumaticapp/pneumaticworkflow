import { getRegularGroupsList } from '../groups';
import type { RootState } from '../../store';
import type { IGroupsStore } from '../../groups/types';
import { EUserGroupType } from '../../../types/team';
import type { IGroup } from '../../../types/team';
import { EGroupsListSorting, EUserListSorting } from '../../../types/user';
import { makeGroup } from '../../../__stubs__/team.factory';

const createMockState = (list: IGroup[]): RootState => {
  const groupsStore: IGroupsStore = {
    isLoading: false,
    list,
    groupsListSorting: EGroupsListSorting.NameAsc,
    currentGroup: {
      data: null,
      userListSorting: EUserListSorting.NameAsc,
    },
    createModal: false,
    editModal: {
      isOpen: false,
      editGroup: null,
    },
  };

  const partialState: Partial<RootState> = {
    groups: groupsStore,
  };

  return partialState as RootState;
};

describe('getRegularGroupsList selector', () => {
  it('returns only regular groups and filters out personal groups', () => {
    const regularGroupFirst = makeGroup({ id: 1, name: 'Sales', type: EUserGroupType.Regular });
    const personalGroup = makeGroup({ id: 2, name: 'My Personal', type: EUserGroupType.Personal });
    const regularGroupSecond = makeGroup({ id: 3, name: 'Support', type: EUserGroupType.Regular });
    const state = createMockState([regularGroupFirst, personalGroup, regularGroupSecond]);

    const result = getRegularGroupsList(state);

    expect(result).toEqual([regularGroupFirst, regularGroupSecond]);
  });

  it('returns an empty array when groups list is empty', () => {
    const state = createMockState([]);

    const result = getRegularGroupsList(state);

    expect(result).toEqual([]);
  });

  it('returns the same array reference when state.groups.list has not changed', () => {
    const sharedList = [
      makeGroup({ id: 1, name: 'Sales', type: EUserGroupType.Regular }),
      makeGroup({ id: 2, name: 'My Personal', type: EUserGroupType.Personal }),
    ];
    const firstState = createMockState(sharedList);
    const secondState = createMockState(sharedList);

    const firstResult = getRegularGroupsList(firstState);
    const secondResult = getRegularGroupsList(secondState);

    expect(secondResult).toBe(firstResult);
  });

  it('recomputes result when state.groups.list reference changes', () => {
    const initialGroup = makeGroup({ id: 1, name: 'Sales', type: EUserGroupType.Regular });
    const addedGroup = makeGroup({ id: 3, name: 'Marketing', type: EUserGroupType.Regular });

    const firstResult = getRegularGroupsList(createMockState([initialGroup]));
    const secondResult = getRegularGroupsList(createMockState([initialGroup, addedGroup]));

    expect(secondResult).not.toBe(firstResult);
    expect(secondResult).toEqual([initialGroup, addedGroup]);
  });
});
