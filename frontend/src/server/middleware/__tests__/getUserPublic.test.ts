import { getUserPublic } from '../utils/getUserPublic';
import { logServerError } from '../../utils/expectedErrors';
import { serverApi } from '../../utils';

type GetUserPublicRequest = Parameters<typeof getUserPublic>[0];

jest.mock('../../utils/expectedErrors', () => ({
  logServerError: jest.fn(),
}));
jest.mock('../../utils', () => ({ serverApi: { get: jest.fn() } }));
jest.mock('../../utils/getAuthHeader', () => ({
  getAuthHeader: jest.fn(() => ({ Authorization: 'Bearer test-token' })),
}));

type MockRequest = {
  headers: { 'user-agent': string };
};

const req: MockRequest = {
  headers: { 'user-agent': 'test-agent' },
};

describe('getUserPublic', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns user data on successful API call', async () => {
    const mockUser = { id: 1, email: 'test@test.com' };
    (serverApi.get as jest.Mock).mockResolvedValue(mockUser);

    const result = await getUserPublic(req as GetUserPublicRequest, 'valid-token', 'test-agent');

    expect(result).toBe(mockUser);
    expect(serverApi.get).toHaveBeenCalledTimes(1);
    expect(serverApi.get).toHaveBeenCalledWith(
      'getPublicAccount',
      { headers: { Authorization: 'Bearer test-token' }, json: true },
      true,
    );
  });

  it('uses logServerError (not logger.error) when API call fails', async () => {
    const apiError = new Error('Not Found');
    (serverApi.get as jest.Mock).mockRejectedValue(apiError);

    await expect(getUserPublic(req as GetUserPublicRequest, 'invalid-token')).rejects.toThrow('Not Found');

    expect(logServerError).toHaveBeenCalledTimes(1);
    expect(logServerError).toHaveBeenCalledWith('failed to get account context: ', apiError);
  });

  it('re-throws the original error after logging', async () => {
    const apiError = new Error('Server Error');
    (serverApi.get as jest.Mock).mockRejectedValue(apiError);

    await expect(getUserPublic(req as GetUserPublicRequest, 'bad-token')).rejects.toBe(apiError);
  });
});
