import { AxiosHeaders, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';

import { commonRequest, TRequestType } from '../commonRequest';

jest.mock('../../utils/auth', () => ({
  getCurrentToken: () => 'test-token',
}));

jest.mock('../../utils/identifyAppPart/identifyAppPartOnClient', () => ({
  identifyAppPartOnClient: () => 'main-app',
}));

jest.mock('../../utils/getConfig', () => ({
  getBrowserConfigEnv: () => ({
    api: {
      publicUrl: 'https://api.example.com',
      fileServiceUrl: 'https://files.example.com',
      urls: { probe: '/probe' },
    },
  }),
}));

async function requestConfig(params: Partial<AxiosRequestConfig> = {}, type: TRequestType = 'public') {
  const adapter = jest.fn(async (config: InternalAxiosRequestConfig) => ({
    data: {},
    status: 200,
    statusText: 'OK',
    headers: new AxiosHeaders(),
    config,
  }));

  await commonRequest('probe', { ...params, adapter }, { type, shouldThrow: true });

  expect(adapter).toHaveBeenCalledTimes(1);
  return adapter.mock.calls[0][0];
}

describe('commonRequest locale headers', () => {
  const originalLang = document.documentElement.lang;

  beforeEach(() => {
    document.documentElement.lang = 'en-US';
  });

  afterEach(() => {
    document.documentElement.lang = originalLang;
  });

  it.each(['ar', 'ar_SY', 'ar-SY', 'ar-sy'])('normalizes document language %s to Syrian Arabic', async (locale) => {
    document.documentElement.lang = locale;

    const config = await requestConfig();

    expect(config.headers.get('Accept-Language')).toBe('ar-SY');
    expect(config.headers.get('Authorization')).toBe('Bearer test-token');
    expect(config.headers.get('Content-Type')).toBe('application/json');
  });

  it.each([
    ['en', 'en-US'],
    ['ru_RU', 'ru-RU'],
  ])('uses normalized document language %s for other supported locales', async (locale, expected) => {
    document.documentElement.lang = locale;

    const config = await requestConfig();

    expect(config.headers.get('Accept-Language')).toBe(expected);
  });

  it('reads the current document language again after the interface language changes', async () => {
    const english = await requestConfig();
    document.documentElement.lang = 'ar-SY';
    const arabic = await requestConfig();

    expect(english.headers.get('Accept-Language')).toBe('en-US');
    expect(arabic.headers.get('Accept-Language')).toBe('ar-SY');
  });

  it('preserves explicit caller language, authorization, content type, and other headers', async () => {
    document.documentElement.lang = 'ar-SY';

    const config = await requestConfig({
      headers: {
        'accept-language': 'fr-FR',
        Authorization: 'Bearer caller-token',
        'Content-Type': 'application/custom+json',
        'X-Request-Id': 'request-id',
      },
    });

    expect(config.headers.get('Accept-Language')).toBe('fr-FR');
    expect(config.headers.get('Authorization')).toBe('Bearer caller-token');
    expect(config.headers.get('Content-Type')).toBe('application/custom+json');
    expect(config.headers.get('X-Request-Id')).toBe('request-id');
    expect(config.withCredentials).toBe(true);
  });

  it.each([false, null])('respects an explicitly disabled language header (%s)', async (value) => {
    document.documentElement.lang = 'ar-SY';

    const config = await requestConfig({ headers: { 'Accept-Language': value } });

    expect(config.headers.has('Accept-Language')).toBe(false);
  });

  it('keeps file upload data and credential behavior while adding the language', async () => {
    document.documentElement.lang = 'ar-SY';
    const data = new FormData();
    data.append('file', new File(['contents'], 'document.txt'));

    const config = await requestConfig({ method: 'POST', data }, 'fileService');

    expect(config.headers.get('Accept-Language')).toBe('ar-SY');
    expect(config.data).toBe(data);
    expect(config.withCredentials).toBe(false);
    expect(config.headers.get('Content-Type')).not.toBe('application/json');
  });
});
