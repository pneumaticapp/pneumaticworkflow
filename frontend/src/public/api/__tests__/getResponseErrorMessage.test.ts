import { AxiosError, AxiosResponse } from 'axios';

jest.mock('../../utils/logger', () => ({ logger: { error: jest.fn() } }));
jest.mock('../../../server/utils/getAuthHeader', () => ({ getAuthHeader: jest.fn() }));
jest.mock('../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue({
    api: { publicUrl: 'http://test', urls: {} },
  }),
}));
jest.mock('../../utils/mappers', () => ({ mapToCamelCase: jest.fn((d: unknown) => d) }));
jest.mock('../../utils/urls', () => ({ mergePaths: jest.fn((_b: string, u: string) => u) }));
jest.mock('../../utils/identifyAppPart/identifyAppPartOnClient', () => ({
  identifyAppPartOnClient: jest.fn().mockReturnValue('public'),
}));
jest.mock('../../utils/auth', () => ({ getCurrentToken: jest.fn() }));
jest.mock('../../constants/enviroment', () => ({ envBackendURL: '' }));
jest.mock('../../utils/isRequestCanceled', () => ({ isRequestCanceled: jest.fn().mockReturnValue(false) }));

jest.mock('axios', () => {
  const mockRequest = jest.fn().mockRejectedValue(new Error('not configured'));
  const mockInstance = Object.assign(mockRequest, {
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  });

  return {
    __esModule: true,
    default: {
      create: jest.fn().mockReturnValue(mockInstance),
    },
  };
});

import '../commonRequest';
import axios from 'axios';

const mockedAxios = axios as jest.Mocked<typeof axios>;
const mockInstance = mockedAxios.create.mock.results[0].value;
const responseErrorHandler = mockInstance.interceptors.response.use.mock.calls[0][1] as
  (error: AxiosError) => Promise<never>;

function makeAxiosError(data: unknown, status: number): AxiosError {
  return {
    response: {
      data,
      status,
    } as AxiosResponse,
    isAxiosError: true,
    name: 'AxiosError',
    message: `Request failed with status code ${status}`,
    toJSON: () => ({}),
  } as AxiosError;
}

function makeNetworkError(message: string): AxiosError {
  return {
    message,
    isAxiosError: true,
    name: 'AxiosError',
    toJSON: () => ({}),
  } as AxiosError;
}

describe('response interceptor: Error.message for Sentry', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('uses message from payload when present', async () => {
    const error = makeAxiosError({ message: 'Validation failed', code: 'ERR_001' }, 400);

    await expect(responseErrorHandler(error)).rejects.toMatchObject({
      message: 'Validation failed',
      code: 'ERR_001',
      status: 400,
    });
  });

  it('falls back to JSON.stringify with status when payload has no message field', async () => {
    const error = makeAxiosError({ detail: 'Not found.' }, 404);

    await expect(responseErrorHandler(error)).rejects.toMatchObject({
      message: JSON.stringify({ detail: 'Not found.', status: 404 }),
      detail: 'Not found.',
      status: 404,
    });
  });

  it('uses plain text from response.data as Error.error property', async () => {
    const error = makeAxiosError('Internal Server Error', 500);

    await expect(responseErrorHandler(error)).rejects.toMatchObject({
      error: 'Internal Server Error',
      status: 500,
    });
  });

  it('falls back to JSON.stringify with status when payload has no message or detail', async () => {
    const error = makeAxiosError({ code: 'ERR_001' }, 422);

    const rejected = responseErrorHandler(error);
    await expect(rejected).rejects.toHaveProperty('message', JSON.stringify({ code: 'ERR_001', status: 422 }));
  });

  it('never produces empty Error.message', async () => {
    const error = makeAxiosError({}, 500);

    await expect(responseErrorHandler(error)).rejects.toHaveProperty('message');
    await expect(responseErrorHandler(error)).rejects.not.toHaveProperty('message', '');
  });

  it('preserves all payload properties on the rejected Error', async () => {
    const error = makeAxiosError({ code: 'ERR_002', details: { name: 'url', reason: 'invalid' } }, 400);

    await expect(responseErrorHandler(error)).rejects.toMatchObject({
      code: 'ERR_002',
      details: { name: 'url', reason: 'invalid' },
      status: 400,
    });
  });

  it('uses Axios error.message when response is absent (network error)', async () => {
    const error = makeNetworkError('Network Error');

    await expect(responseErrorHandler(error)).rejects.toHaveProperty('message', 'Network Error');
  });

  it('uses Axios error.message on timeout (no response)', async () => {
    const error = makeNetworkError('timeout of 10000ms exceeded');

    await expect(responseErrorHandler(error)).rejects.toHaveProperty('message', 'timeout of 10000ms exceeded');
  });

  it('never produces empty message for network errors without response', async () => {
    const error = makeNetworkError('');

    const rejected = responseErrorHandler(error);
    await expect(rejected).rejects.toHaveProperty('message');
    await expect(responseErrorHandler(error)).rejects.not.toHaveProperty('message', '');
    await expect(responseErrorHandler(error)).rejects.not.toHaveProperty('message', '{}');
  });
});
