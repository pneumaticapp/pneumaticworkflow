import { getUserPublic } from '../utils/getUserPublic';
import { logServerError, LOG_PREFIX_ACCOUNT_CONTEXT } from '../../utils/expectedErrors';
import { logger } from '../../../public/utils/logger';
import { serverApi } from '../../utils';

type GetUserPublicRequest = Parameters<typeof getUserPublic>[0];

jest.mock('../../utils/expectedErrors', () => ({
  ...jest.requireActual('../../utils/expectedErrors'),
  logServerError: jest.fn(),
}));
jest.mock('../../../public/utils/logger', () => ({
  logger: { info: jest.fn(), error: jest.fn() },
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

  it('uses logger.info for expected auth error (401 credentials not provided)', async () => {
    const authError = { detail: 'Authentication credentials were not provided.' };
    (serverApi.get as jest.Mock).mockRejectedValue(authError);

    await expect(getUserPublic(req as GetUserPublicRequest, 'invalid-token')).rejects.toBe(authError);

    expect(logger.info).toHaveBeenCalledTimes(1);
    expect(logger.info).toHaveBeenCalledWith(LOG_PREFIX_ACCOUNT_CONTEXT, authError);
    expect(logServerError).not.toHaveBeenCalled();
  });

  it('uses logServerError for unexpected errors', async () => {
    const unexpectedError = new Error('Internal Server Error');
    (serverApi.get as jest.Mock).mockRejectedValue(unexpectedError);

    await expect(getUserPublic(req as GetUserPublicRequest, 'bad-token')).rejects.toBe(unexpectedError);

    expect(logServerError).toHaveBeenCalledTimes(1);
    expect(logServerError).toHaveBeenCalledWith(LOG_PREFIX_ACCOUNT_CONTEXT, unexpectedError);
    expect(logger.info).not.toHaveBeenCalled();
  });

  it('re-throws the original error after logging', async () => {
    const apiError = new Error('Server Error');
    (serverApi.get as jest.Mock).mockRejectedValue(apiError);

    await expect(getUserPublic(req as GetUserPublicRequest, 'bad-token')).rejects.toBe(apiError);
  });
});
