import { mapWsUserToListItem } from '../mapUserFromWs';

describe('mapWsUserToListItem', () => {
  it('renames websocket subordinatesIds to reportIds', () => {
    const result = mapWsUserToListItem({
      id: 1,
      firstName: 'John',
      lastName: 'Smith',
      email: 'john@example.com',
      photo: null,
      isAdmin: false,
      isAccountOwner: false,
      managerId: null,
      subordinatesIds: [2, 3],
    });

    expect(result.reportIds).toEqual([2, 3]);
    expect(result).not.toHaveProperty('subordinatesIds');
  });
});
