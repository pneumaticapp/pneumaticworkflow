// <reference types="jest" />

jest.mock('../../../../config/common.json', () => ({
  api: {
    urls: {
      getUser: '/auth/context',
      getToken: '/auth/signin',
    },
  },
  exposedToBrowser: [
    'host',
    'api.publicUrl',
    'api.wsPublicUrl',
    'api.urls',
    'analyticsId',
    'mainPage',
    'formSubdomain',
    'recaptchaSecret',
    'firebase',
    'featureFlags',
  ],
}));

jest.mock('lodash.merge', () => {
  const deepMerge = (target: any, ...sources: any[]): any => {
    const result = { ...target };
    for (const source of sources) {
      if (!source) continue;
      for (const key of Object.keys(source)) {
        if (
          typeof source[key] === 'object' &&
          source[key] !== null &&
          !Array.isArray(source[key]) &&
          typeof result[key] === 'object' &&
          result[key] !== null
        ) {
          result[key] = deepMerge(result[key], source[key]);
        } else {
          result[key] = source[key];
        }
      }
    }
    return result;
  };
  return deepMerge;
});

jest.mock('../../../server/utils/helpers', () => ({
  get: (obj: any, path: string) => {
    return path.split('.').reduce((acc: any, part: string) => acc && acc[part], obj);
  },
  set: (obj: any, path: string, value: any) => {
    const parts = path.split('.');
    let current = obj;
    for (let i = 0; i < parts.length - 1; i++) {
      if (!(parts[i] in current)) current[parts[i]] = {};
      current = current[parts[i]];
    }
    current[parts[parts.length - 1]] = value;
  },
}));

jest.mock('../../types/user', () => ({}));
jest.mock('../../types/redux', () => ({}));
jest.mock('../../redux/pages/types', () => ({}));

describe('getConfig', () => {
  const ORIGINAL_ENV = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...ORIGINAL_ENV };
    delete (window as any).__pneumaticConfig;
  });

  afterEach(() => {
    process.env = ORIGINAL_ENV;
    delete (window as any).__pneumaticConfig;
  });

  const loadModule = () => require('../getConfig');

  describe('getConfig()', () => {
    it('includes featureFlags in the returned config', () => {
      process.env.CAPTCHA = 'yes';
      process.env.AI = 'no';
      process.env.BILLING = 'yes';
      process.env.SENTRY_RELEASE = 'v2.0.0';

      const { getConfig } = loadModule();
      const config = getConfig();

      expect(config.featureFlags).toBeDefined();
      expect(config.featureFlags.CAPTCHA).toBe('yes');
      expect(config.featureFlags.AI).toBe('no');
      expect(config.featureFlags.BILLING).toBe('yes');
      expect(config.featureFlags.SENTRY_RELEASE).toBe('v2.0.0');
    });

    it('maps RECAPTCHA_SITE_KEY env to featureFlags', () => {
      process.env.RECAPTCHA_SITE_KEY = 'recaptcha-key-abc';

      const { getConfig } = loadModule();
      const config = getConfig();

      expect(config.featureFlags.RECAPTCHA_SITE_KEY).toBe('recaptcha-key-abc');
    });

    it('maps all boolean feature flags to featureFlags object', () => {
      process.env.GOOGLE_AUTH = 'no';
      process.env.MS_AUTH = 'yes';
      process.env.SSO_AUTH = 'no';
      process.env.SIGNUP = 'yes';
      process.env.PUSH = 'no';
      process.env.ANALYTICS = 'no';
      process.env.SSO_PROVIDER = 'okta';

      const { getConfig } = loadModule();
      const config = getConfig();

      expect(config.featureFlags.GOOGLE_AUTH).toBe('no');
      expect(config.featureFlags.MS_AUTH).toBe('yes');
      expect(config.featureFlags.SSO_AUTH).toBe('no');
      expect(config.featureFlags.SIGNUP).toBe('yes');
      expect(config.featureFlags.PUSH).toBe('no');
      expect(config.featureFlags.ANALYTICS).toBe('no');
      expect(config.featureFlags.SSO_PROVIDER).toBe('okta');
    });

    it('maps connection env vars to featureFlags', () => {
      process.env.LANGUAGE_CODE = 'ru';
      process.env.BACKEND_URL = 'http://api.local';
      process.env.SENTRY_DSN = 'https://sentry.example.com';
      process.env.WSS_URL = 'wss://ws.local';
      process.env.HOST = 'https://app.local';
      process.env.ANALYTICS_ID = 'UA-999';
      process.env.GOOGLE_CLIENT_ID = 'google-id';

      const { getConfig } = loadModule();
      const config = getConfig();

      expect(config.featureFlags.LANGUAGE_CODE).toBe('ru');
      expect(config.featureFlags.BACKEND_URL).toBe('http://api.local');
      expect(config.featureFlags.SENTRY_DSN).toBe('https://sentry.example.com');
      expect(config.featureFlags.WSS_URL).toBe('wss://ws.local');
      expect(config.featureFlags.HOST).toBe('https://app.local');
      expect(config.featureFlags.ANALYTICS_ID).toBe('UA-999');
      expect(config.featureFlags.GOOGLE_CLIENT_ID).toBe('google-id');
    });

    it('maps Firebase env vars to featureFlags', () => {
      process.env.FIREBASE_VAPID_KEY = 'vapid';
      process.env.FIREBASE_API_KEY = 'api-key';
      process.env.FIREBASE_AUTH_DOMAIN = 'auth-domain';
      process.env.FIREBASE_PROJECT_ID = 'proj';
      process.env.FIREBASE_STORAGE_BUCKET = 'bucket';
      process.env.FIREBASE_SENDER_ID = 'sender';
      process.env.FIREBASE_APP_ID = 'app';
      process.env.FIREBASE_MEASUREMENT_ID = 'G-1';

      const { getConfig } = loadModule();
      const config = getConfig();

      expect(config.featureFlags.FIREBASE_VAPID_KEY).toBe('vapid');
      expect(config.featureFlags.FIREBASE_API_KEY).toBe('api-key');
      expect(config.featureFlags.FIREBASE_AUTH_DOMAIN).toBe('auth-domain');
      expect(config.featureFlags.FIREBASE_PROJECT_ID).toBe('proj');
      expect(config.featureFlags.FIREBASE_STORAGE_BUCKET).toBe('bucket');
      expect(config.featureFlags.FIREBASE_SENDER_ID).toBe('sender');
      expect(config.featureFlags.FIREBASE_APP_ID).toBe('app');
      expect(config.featureFlags.FIREBASE_MEASUREMENT_ID).toBe('G-1');
    });

    it('returns undefined for unset featureFlags keys', () => {
      delete process.env.SENTRY_RELEASE;
      delete process.env.SSO_PROVIDER;

      const { getConfig } = loadModule();
      const config = getConfig();

      expect(config.featureFlags.SENTRY_RELEASE).toBeUndefined();
      expect(config.featureFlags.SSO_PROVIDER).toBeUndefined();
    });

    it('still includes RECAPTCHA_SITE_KEY in recaptchaSecret field', () => {
      process.env.RECAPTCHA_SITE_KEY = 'recaptcha-xyz';

      const { getConfig } = loadModule();
      const config = getConfig();

      expect(config.recaptchaSecret).toBe('recaptcha-xyz');
    });
  });

  describe('serverConfigToBrowser()', () => {
    it('includes featureFlags in browser config', () => {
      process.env.CAPTCHA = 'no';
      process.env.AI = 'yes';

      const { serverConfigToBrowser } = loadModule();
      const browserConfig = serverConfigToBrowser();

      expect(browserConfig.featureFlags).toBeDefined();
      expect(browserConfig.featureFlags.CAPTCHA).toBe('no');
      expect(browserConfig.featureFlags.AI).toBe('yes');
    });
  });

  describe('getBrowserConfig()', () => {
    it('returns window.__pneumaticConfig', () => {
      const mockConfig = {
        config: { host: 'test', featureFlags: { AI: 'yes' } },
        user: {},
        invitedUser: {},
        pages: {},
      };
      (window as any).__pneumaticConfig = mockConfig;

      const { getBrowserConfig } = loadModule();

      expect(getBrowserConfig()).toBe(mockConfig);
    });
  });

  describe('getBrowserConfigEnv()', () => {
    it('returns config from window.__pneumaticConfig', () => {
      const innerConfig = { host: 'localhost', featureFlags: { PUSH: 'no' } };
      (window as any).__pneumaticConfig = { config: innerConfig };

      const { getBrowserConfigEnv } = loadModule();

      expect(getBrowserConfigEnv()).toBe(innerConfig);
    });

    it('returns empty object when no browser config', () => {
      delete (window as any).__pneumaticConfig;

      const { getBrowserConfigEnv } = loadModule();

      expect(getBrowserConfigEnv()).toEqual({});
    });
  });
});
