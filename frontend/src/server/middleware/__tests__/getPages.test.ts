import { getPages } from '../utils/getPages';
import { logServerError } from '../../utils/expectedErrors';
import { serverApi } from '../../utils';

jest.mock('../../utils/expectedErrors', () => ({
  logServerError: jest.fn(),
}));
jest.mock('../../utils', () => ({ serverApi: { get: jest.fn() } }));
jest.mock('../../../public/utils/getConfig', () => ({
  getConfig: () => ({ api: { urls: { getPages: '/pages' } } }),
}));

describe('getPages', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns pages data on successful API call', async () => {
    const mockPages = { logo: 'logo.png', title: 'My App' };
    (serverApi.get as jest.Mock).mockResolvedValue(mockPages);

    const result = await getPages();

    expect(result).toBe(mockPages);
    expect(serverApi.get).toHaveBeenCalledTimes(1);
    expect(serverApi.get).toHaveBeenCalledWith('/pages');
  });

  it('uses logServerError (not logger.error) when API call fails', async () => {
    const apiError = new Error('Not Found');
    (serverApi.get as jest.Mock).mockRejectedValue(apiError);

    await getPages();

    expect(logServerError).toHaveBeenCalledTimes(1);
    expect(logServerError).toHaveBeenCalledWith('failed to get pages: ', apiError);
  });

  it('returns null when API call fails', async () => {
    (serverApi.get as jest.Mock).mockRejectedValue(new Error('Not Found'));

    const result = await getPages();

    expect(result).toBeNull();
  });
});
