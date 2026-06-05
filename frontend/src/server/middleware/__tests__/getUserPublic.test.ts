import { Request } from 'express';

import { getUserPublic } from '../utils/getUserPublic';
import { logger } from '../../../public/utils/logger';
import { serverApi } from '../../utils';

jest.mock('../../../public/utils/logger', () => ({
  logger: { error: jest.fn(), info: jest.fn() },
}));
jest.mock('../../utils', () => ({ serverApi: { get: jest.fn() } }));
jest.mock('../../utils/getAuthHeader', () => ({
  getAuthHeader: jest.fn(() => ({ Authorization: 'Bearer test-token' })),
}));

const req = {
  headers: { 'user-agent': 'test-agent' },
} as Request;

describe('getUserPublic', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns user data on successful API call', async () => {
    const mockUser = { id: 1, email: 'test@test.com' };
    (serverApi.get as jest.Mock).mockResolvedValue(mockUser);

    const result = await getUserPublic(req, 'valid-token', 'test-agent');

    expect(result).toBe(mockUser);
    expect(serverApi.get).toHaveBeenCalledTimes(1);
    expect(serverApi.get).toHaveBeenCalledWith(
      'getPublicAccount',
      { headers: { Authorization: 'Bearer test-token' }, json: true },
      true,
    );
  });

  it('logs with info level (not error) when API call fails', async () => {
    const apiError = new Error('Not Found');
    (serverApi.get as jest.Mock).mockRejectedValue(apiError);

    await expect(getUserPublic(req, 'invalid-token')).rejects.toThrow('Not Found');

    expect(logger.info).toHaveBeenCalledTimes(1);
    expect(logger.info).toHaveBeenCalledWith('failed to get account context: ', apiError);
    expect(logger.error).not.toHaveBeenCalled();
  });

  it('re-throws the original error after logging', async () => {
    const apiError = new Error('Server Error');
    (serverApi.get as jest.Mock).mockRejectedValue(apiError);

    await expect(getUserPublic(req, 'bad-token')).rejects.toBe(apiError);
  });
});
