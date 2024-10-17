import { configMock } from '../../__stubs__/configMock';
jest.mock('../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue(configMock),
}));
import { commonRequest } from '../commonRequest';
import { registerUser } from '../registerUser';
import { mapRequestBody } from '../../utils/mappers';

jest.mock('../commonRequest');

describe('registerUser', () => {
  it('вызывает commonRequest с нужными параметрами', async () => {
    const userData = {
      companyName: 'My Company',
      email: 'example@gmail.com',
      firstName: 'User',
      lastName: 'Test',
      photo: '/url/to/photo.jpg',
      fromEmail: true,
      timezone: ''
    };
    (commonRequest as jest.Mock).mockResolvedValueOnce('OK');

    const result = await registerUser(userData);

    expect(result).toEqual('OK');
    expect(commonRequest).toHaveBeenCalledWith('registerUrl', {
      method: 'POST',
      body: mapRequestBody(userData),
      headers: {
        'Content-Type': 'application/json',
      },
    }, {
      type: 'local',
      shouldThrow: true,
    });
  });
});
