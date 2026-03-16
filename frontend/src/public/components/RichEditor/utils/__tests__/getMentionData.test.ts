import { EUserStatus, TUserListItem } from '../../../../types/user';
import { getMentionData } from '../getMentionData';

jest.mock('../../../../utils/users', () => ({
  getUserFullName: jest.fn((user: TUserListItem) =>
    user ? `${user.firstName} ${user.lastName}`.trim() : '',
  ),
}));

const { getUserFullName } = require('../../../../utils/users') as {
  getUserFullName: jest.Mock;
};

describe('getMentionData', () => {
  const baseUser: TUserListItem = {
    id: 1,
    firstName: 'John',
    lastName: 'Doe',
    status: EUserStatus.Active,
    email: 'john@example.com',
    photo: '',
    phone: '',
    type: 'user',
  };

  beforeEach(() => {
    getUserFullName.mockImplementation((user: TUserListItem) =>
      user ? `${user.firstName} ${user.lastName}`.trim() : '',
    );
  });

  describe('status filtering', () => {
    it('returns only users with Active status', () => {
      const users: TUserListItem[] = [
        { ...baseUser, id: 1, status: EUserStatus.Active },
        { ...baseUser, id: 2, status: EUserStatus.Invited },
        { ...baseUser, id: 3, status: EUserStatus.Deleted },
        { ...baseUser, id: 4, status: EUserStatus.Active },
      ];
      const result = getMentionData(users);
      expect(result).toHaveLength(2);
      expect(result.map((m) => m.id)).toEqual([1, 4]);
    });

    it('returns empty array when no active users', () => {
      const users: TUserListItem[] = [
        { ...baseUser, id: 1, status: EUserStatus.Invited },
        { ...baseUser, id: 2, status: EUserStatus.Deleted },
      ];
      expect(getMentionData(users)).toEqual([]);
    });

    it('returns all users when all are Active', () => {
      const users: TUserListItem[] = [
        { ...baseUser, id: 1 },
        { ...baseUser, id: 2, firstName: 'Jane', lastName: 'Smith' },
      ];
      const result = getMentionData(users);
      expect(result).toHaveLength(2);
      expect(result[0].name).toBe('John Doe');
      expect(result[1].name).toBe('Jane Smith');
    });
  });

  describe('result format', () => {
    it('maps user to object with id and name', () => {
      const users: TUserListItem[] = [{ ...baseUser, id: 42 }];
      const result = getMentionData(users);
      expect(result[0]).toEqual({ id: 42, name: 'John Doe' });
    });

    it('calls getUserFullName for each active user', () => {
      const users: TUserListItem[] = [{ ...baseUser }];
      getMentionData(users);
      expect(getUserFullName).toHaveBeenCalledWith(baseUser);
    });

    it('uses empty string for name when getUserFullName returns empty', () => {
      getUserFullName.mockReturnValue('');
      const users: TUserListItem[] = [{ ...baseUser }];
      const result = getMentionData(users);
      expect(result[0].name).toBe('');
    });
  });

  describe('edge cases', () => {
    it('returns empty array for empty input', () => {
      expect(getMentionData([])).toEqual([]);
    });

    it('ignores users without status', () => {
      const users = [{ ...baseUser, status: undefined }] as unknown as TUserListItem[];
      const result = getMentionData(users);
      expect(result).toHaveLength(0);
    });

    it('treats External status as non-Active', () => {
      const users: TUserListItem[] = [
        { ...baseUser, id: 1, status: EUserStatus.External },
      ];
      expect(getMentionData(users)).toEqual([]);
    });
  });
});
