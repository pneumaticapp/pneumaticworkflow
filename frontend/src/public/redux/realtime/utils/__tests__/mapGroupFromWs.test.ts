import { EUserGroupType } from '../../../team/types';
import { mapWsGroupToGroup } from '../mapGroupFromWs';

describe('mapWsGroupToGroup', () => {
  it('keeps user ids as-is when WS payload sends PrimaryKeyRelatedField list', () => {
    const result = mapWsGroupToGroup({
      id: 10,
      name: 'Engineering',
      photo: null,
      type: EUserGroupType.Regular,
      users: [1, 2, 3],
    });

    expect(result).toEqual({
      id: 10,
      name: 'Engineering',
      photo: null,
      type: EUserGroupType.Regular,
      users: [1, 2, 3],
    });
  });

  it('does not map users through .id (avoids undefined/null after backend serializer change)', () => {
    const result = mapWsGroupToGroup({
      id: 1,
      name: 'Ops',
      photo: 'https://example.com/photo.png',
      type: EUserGroupType.Regular,
      users: [42],
    });

    expect(result.users).toEqual([42]);
    expect(result.users.every((id) => typeof id === 'number')).toBe(true);
  });
});
