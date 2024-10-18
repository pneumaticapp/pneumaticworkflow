import { acceptInvite } from '../acceptInvite';
import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';

jest.mock('../commonRequest');
jest.mock('../../utils/getConfig');

describe('acceptInvite', () => {
  it('вызывает commonRequest с нужным урлом и параметрами', async () => {
    const token = 'some-token';
    const id = '123';
    const user = { firstName: 'Test', lastName: 'User', password: 'test_pwd', timezone: '' };

    (commonRequest as jest.Mock).mockResolvedValueOnce({ token });
    (getBrowserConfigEnv as jest.Mock).mockReturnValueOnce({
      api: {
        urls: {
          acceptInvite: '/accounts/invites/:id/accept/',
        },
      },
    });

    const result = await acceptInvite(id, user);

    expect(result).toEqual({ token });
    expect(commonRequest).toHaveBeenCalledWith(
      '/accounts/invites/123/accept/',
      {
        method: 'POST',
        body: JSON.stringify({ first_name: 'Test', last_name: 'User', password: 'test_pwd', timezone: '' }),
      },
      {
        type: 'local',
        shouldThrow: true,
      },
    );
  });
});
