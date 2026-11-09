import { isRouteAllowed, serverApi } from '../request';

jest.mock('axios', () => {
  const mockRequest = jest.fn();
  const mockIsAxiosError = jest.fn();

  return {
    __esModule: true,
    default: {
      request: mockRequest,
      isAxiosError: mockIsAxiosError,
    },
    request: mockRequest,
    isAxiosError: mockIsAxiosError,
  };
});

interface IMockAxios {
  default: {
    request: jest.Mock;
    isAxiosError: jest.Mock;
  };
}

const { default: mockAxios }: IMockAxios = require('axios');

describe('utils', () => {
  describe('request', () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });

    it('returns a successfully completed promise with the data if there is no error.', async () => {
      const body = { body: 'test' };
      mockAxios.request.mockResolvedValue({ data: body });

      const result = await serverApi.get('/some/url', {});

      expect(result).toEqual(body);
      expect(mockAxios.request).toHaveBeenCalledTimes(1);
      expect(mockAxios.request).toHaveBeenCalledWith(
        expect.objectContaining({
          method: 'get',
          url: expect.stringContaining('/some/url'),
        }),
      );
    });

    it('returns a failed promise with the response data if the response failed with 4xx or 5xx.', async () => {
      const errorData = { detail: 'bad request' };
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 400,
          data: errorData,
        },
      };
      mockAxios.isAxiosError.mockReturnValue(true);
      mockAxios.request.mockRejectedValue(axiosError);

      await expect(serverApi.get('/api/some/url', {}, true, true)).rejects.toEqual(errorData);
      expect(mockAxios.request).toHaveBeenCalledTimes(1);
    });

    it('returns a failed promise with fallback Error when err.response.data is empty.', async () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 500,
          data: undefined,
        },
      };
      mockAxios.isAxiosError.mockReturnValue(true);
      mockAxios.request.mockRejectedValue(axiosError);

      await expect(serverApi.get('/some/url', {})).rejects.toEqual(new Error('Request failed with status 500'));
      expect(mockAxios.request).toHaveBeenCalledTimes(1);
    });

    it('returns a failed promise with the error object when network error occurred.', async () => {
      const networkError = new Error('connect ECONNREFUSED 127.0.0.1:8001');
      mockAxios.isAxiosError.mockReturnValue(false);
      mockAxios.request.mockRejectedValue(networkError);

      await expect(serverApi.get('/some/url', {})).rejects.toEqual(networkError);
      expect(mockAxios.request).toHaveBeenCalledTimes(1);
    });
  });

  describe('isRouteAllowed', () => {
    it('returns true if a permitted link is provided.', () => {
      expect(isRouteAllowed('/api/auth/token/obtain')).toEqual(true);
    });
  });
});
