import { getUser } from '../utils/getUser';
import { logServerError } from '../../utils/expectedErrors';
import { serverApi } from '../../utils';

jest.mock('../../utils/expectedErrors', () => ({
  logServerError: jest.fn(),
}));
jest.mock('../../utils', () => ({ serverApi: { get: jest.fn() } }));
jest.mock('../../utils/getAuthHeader', () => ({
  getAuthHeader: jest.fn(() => ({ Authorization: 'Bearer test-token' })),
}));
jest.mock('../../../public/utils/identifyAppPart/identifyAppPartOnServer', () => ({
  identifyAppPartOnServer: jest.fn(() => 'main'),
}));

type MockRequest = {
  headers: { 'user-agent': string };
};

type GetUserRequest = Parameters<typeof getUser>[0];

const req: MockRequest = {
  headers: { 'user-agent': 'test-agent' },
};

describe('getUser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns user data on successful API call', async () => {
    const mockUser = { id: 1, email: 'test@test.com', account: {} };
    (serverApi.get as jest.Mock).mockResolvedValue(mockUser);

    const result = await getUser(req as GetUserRequest, 'valid-token', 'test-agent');

    expect(result).toBe(mockUser);
    expect(serverApi.get).toHaveBeenCalledTimes(1);
    expect(serverApi.get).toHaveBeenCalledWith(
      'getUser',
      { headers: { Authorization: 'Bearer test-token' }, json: true },
      true,
    );
  });

  it('uses logServerError (not logger.error) when API call fails', async () => {
    const apiError = new Error('token_not_valid');
    (serverApi.get as jest.Mock).mockRejectedValue(apiError);

    await expect(getUser(req as GetUserRequest, 'invalid-token')).rejects.toThrow('token_not_valid');

    expect(logServerError).toHaveBeenCalledTimes(1);
    expect(logServerError).toHaveBeenCalledWith('failed to get user context: ', apiError);
  });

  it('re-throws the original error after logging', async () => {
    const apiError = new Error('Unauthorized');
    (serverApi.get as jest.Mock).mockRejectedValue(apiError);

    await expect(getUser(req as GetUserRequest, 'bad-token')).rejects.toBe(apiError);
  });
});
