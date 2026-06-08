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

import { getResponseErrorMessage } from '../commonRequest';

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

describe('response interceptor: Error.message for Sentry', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('rejected Error contains detail from DRF response in .message', async () => {
    const error = makeAxiosError({ detail: 'Not found.' }, 404);

    await expect(responseErrorHandler(error)).rejects.toMatchObject({
      message: 'Not found.',
      status: 404,
    });
  });

  it('rejected Error contains message field when detail is absent', async () => {
    const error = makeAxiosError({ message: 'Validation failed' }, 400);

    await expect(responseErrorHandler(error)).rejects.toMatchObject({
      message: 'Validation failed',
      status: 400,
    });
  });

  it('rejected Error contains plain text from response.data in .message', async () => {
    const error = makeAxiosError('Internal Server Error', 500);

    await expect(responseErrorHandler(error)).rejects.toMatchObject({
      message: 'Internal Server Error',
      status: 500,
    });
  });

  it('rejected Error contains non-empty fallback when data has no detail/message', async () => {
    const error = makeAxiosError({ code: 'ERR_001' }, 422);

    await expect(responseErrorHandler(error)).rejects.toHaveProperty('message');
    await expect(responseErrorHandler(error)).rejects.not.toHaveProperty('message', '');
  });
});

const FALLBACK = 'No error details provided by server';

describe('getResponseErrorMessage', () => {
  it('returns string as-is when data is a string', () => {
    expect(getResponseErrorMessage('Server error')).toBe('Server error');
  });

  it('returns detail from object (DRF standard)', () => {
    expect(getResponseErrorMessage({ detail: 'Not found.' })).toBe('Not found.');
  });

  it('returns message when detail is absent', () => {
    expect(getResponseErrorMessage({ message: 'Validation error' })).toBe('Validation error');
  });

  it('prioritizes detail over message', () => {
    expect(getResponseErrorMessage({ detail: 'Detail text', message: 'Message text' })).toBe('Detail text');
  });

  it.each([
    ['empty object', {}],
    ['undefined', undefined],
    ['null', null],
  ])('returns fallback when data is %s', (_label, data) => {
    expect(getResponseErrorMessage(data)).toBe(FALLBACK);
  });
});
