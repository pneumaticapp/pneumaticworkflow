

import { getUser } from '../utils/getUser';
import { logger } from '../../../public/utils/logger';
import { serverApi } from '../../utils';

jest.mock('../../../public/utils/logger', () => ({
  logger: { error: jest.fn(), info: jest.fn() },
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

  it('logs with info level (not error) when API call fails', async () => {
    const apiError = new Error('token_not_valid');
    (serverApi.get as jest.Mock).mockRejectedValue(apiError);

    await expect(getUser(req as GetUserRequest, 'invalid-token')).rejects.toThrow('token_not_valid');

    expect(logger.info).toHaveBeenCalledTimes(1);
    expect(logger.info).toHaveBeenCalledWith('failed to get user context: ', apiError);
    expect(logger.error).not.toHaveBeenCalled();
  });

  it('re-throws the original error after logging', async () => {
    const apiError = new Error('Unauthorized');
    (serverApi.get as jest.Mock).mockRejectedValue(apiError);

    await expect(getUser(req as GetUserRequest, 'bad-token')).rejects.toBe(apiError);
  });
});
