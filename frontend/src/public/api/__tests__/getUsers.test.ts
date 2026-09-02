import { getUsersQueryString } from '../getUsers';
import { EUserStatus } from '../../types/user';

jest.mock('../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue({
    api: { urls: { getUsers: '/accounts/users', getUsersPublic: '/accounts/users/public' } },
  }),
}));

describe('getUsersQueryString', () => {
  it('sends is_ai=false so AI agents are excluded from the team list', () => {
    const query = getUsersQueryString({
      type: 'user',
      status: [EUserStatus.Active, EUserStatus.Invited],
      isAi: false,
    });

    expect(query).toBe('?type=user&status=active,invited&is_ai=false');
  });

  it('omits is_ai entirely when the caller does not care', () => {
    const query = getUsersQueryString({ type: 'user' });

    expect(query).toBe('?type=user');
  });

  it('sends is_ai=true when only agents are wanted', () => {
    expect(getUsersQueryString({ isAi: true })).toBe('?is_ai=true');
  });

  it('returns an empty string without a config', () => {
    expect(getUsersQueryString()).toBe('');
  });
});
