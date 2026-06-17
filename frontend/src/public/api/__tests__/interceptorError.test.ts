import { AxiosError, AxiosResponse } from 'axios';

const mockLoggerError = jest.fn();
const mockLoggerInfo = jest.fn();

jest.mock('../../utils/logger', () => ({ logger: { error: mockLoggerError, info: mockLoggerInfo } }));
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
jest.mock('../../utils/expectedClientErrors', () => ({
  isExpectedClientError: jest.fn().mockReturnValue(false),
}));

jest.mock('axios', () => {
  const mockRequest = jest.fn();
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

import axios from 'axios';
import { InterceptorError } from '../commonRequest';

const mockedAxios = axios as jest.Mocked<typeof axios>;
const mockInstance = mockedAxios.create.mock.results[0].value;
const responseErrorHandler = mockInstance.interceptors.response.use.mock.calls[0][1] as
  (error: AxiosError) => Promise<never>;

function makeAxiosError(data: Record<string, string>, status: number): AxiosError {
  return {
    response: {
      data,
      status,
    } as AxiosResponse,
    config: {},
    isAxiosError: true,
    name: 'AxiosError',
    message: `Request failed with status code ${status}`,
    toJSON: () => ({}),
  } as AxiosError;
}

describe('response interceptor: InterceptorError', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('rejects with InterceptorError instance', async () => {
    const error = makeAxiosError({ detail: 'Not found' }, 404);

    await expect(responseErrorHandler(error)).rejects.toBeInstanceOf(InterceptorError);
  });

  it('preserves payload properties on InterceptorError', async () => {
    const error = makeAxiosError({ detail: 'Forbidden' }, 403);

    await expect(responseErrorHandler(error)).rejects.toMatchObject({
      detail: 'Forbidden',
      status: 403,
    });
  });
});

describe('commonRequest catch block: deduplication', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('does not call logger.error when interceptor already logged the error (shouldThrow: false)', async () => {
    const interceptorError = Object.assign(new InterceptorError(), {
      detail: 'token_not_valid',
      status: 401,
    });
    mockInstance.mockRejectedValueOnce(interceptorError);

    const { commonRequest } = require('../commonRequest');
    await commonRequest('/test', {}, { shouldThrow: false });

    expect(mockLoggerError).not.toHaveBeenCalled();
  });

  it('calls logger.error for non-InterceptorError in catch (shouldThrow: false)', async () => {
    const genericError = new Error('Network Error');
    mockInstance.mockRejectedValueOnce(genericError);

    const { commonRequest } = require('../commonRequest');
    await commonRequest('/test', {}, { shouldThrow: false });

    expect(mockLoggerError).toHaveBeenCalledTimes(1);
    expect(mockLoggerError).toHaveBeenCalledWith(genericError);
  });
});
