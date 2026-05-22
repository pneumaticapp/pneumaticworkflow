// <reference types="jest" />

describe('enviroment constants', () => {
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

  const loadModule = () => require('../enviroment');

  describe('getEnv (via exported constants)', () => {
    describe('when window.__pneumaticConfig has featureFlags', () => {
      it('reads value from featureFlags over process.env', () => {
        process.env.LANGUAGE_CODE = 'en';
        (window as any).__pneumaticConfig = {
          config: {
            featureFlags: {
              LANGUAGE_CODE: 'ru',
            },
          },
        };

        const mod = loadModule();

        expect(mod.envLanguageCode).toBe('ru');
      });

      it('returns undefined from featureFlags when key is missing and process.env also missing', () => {
        delete process.env.HOST;
        (window as any).__pneumaticConfig = {
          config: {
            featureFlags: {},
          },
        };

        const mod = loadModule();

        expect(mod.envHost).toBeUndefined();
      });

      it('falls back to process.env when key is not in featureFlags', () => {
        process.env.SENTRY_DSN = 'https://sentry.example.com';
        (window as any).__pneumaticConfig = {
          config: {
            featureFlags: {},
          },
        };

        const mod = loadModule();

        expect(mod.envSentry).toBe('https://sentry.example.com');
      });
    });

    describe('when __pneumaticConfig is absent on window', () => {
      it('falls back to process.env', () => {
        process.env.BACKEND_URL = 'http://api.local';
        delete (window as any).__pneumaticConfig;

        const mod = loadModule();

        expect(mod.envBackendURL).toBe('http://api.local');
      });
    });

    describe('when __pneumaticConfig.config has no featureFlags', () => {
      it('falls back to process.env', () => {
        process.env.WSS_URL = 'wss://ws.local';
        (window as any).__pneumaticConfig = { config: {} };

        const mod = loadModule();

        expect(mod.envWssURL).toBe('wss://ws.local');
      });
    });
  });

  describe('boolean feature flags', () => {
    describe('isEnvCaptcha', () => {
      it('returns true when CAPTCHA is undefined (default enabled)', () => {
        delete process.env.CAPTCHA;

        const mod = loadModule();

        expect(mod.isEnvCaptcha).toBe(true);
      });

      it('returns false when CAPTCHA is "no"', () => {
        process.env.CAPTCHA = 'no';

        const mod = loadModule();

        expect(mod.isEnvCaptcha).toBe(false);
      });

      it('returns true when CAPTCHA is "yes"', () => {
        process.env.CAPTCHA = 'yes';

        const mod = loadModule();

        expect(mod.isEnvCaptcha).toBe(true);
      });
    });

    describe('isEnvGoogleAuth', () => {
      it('returns false when GOOGLE_AUTH is "no"', () => {
        process.env.GOOGLE_AUTH = 'no';

        const mod = loadModule();

        expect(mod.isEnvGoogleAuth).toBe(false);
      });

      it('returns true when GOOGLE_AUTH is undefined', () => {
        delete process.env.GOOGLE_AUTH;

        const mod = loadModule();

        expect(mod.isEnvGoogleAuth).toBe(true);
      });
    });

    describe('isEnvBilling', () => {
      it('returns false when BILLING is "no"', () => {
        process.env.BILLING = 'no';

        const mod = loadModule();

        expect(mod.isEnvBilling).toBe(false);
      });

      it('returns true when BILLING is undefined', () => {
        delete process.env.BILLING;

        const mod = loadModule();

        expect(mod.isEnvBilling).toBe(true);
      });
    });

    describe('isEnvSignup', () => {
      it('returns false when SIGNUP is "no"', () => {
        process.env.SIGNUP = 'no';

        const mod = loadModule();

        expect(mod.isEnvSignup).toBe(false);
      });

      it('returns true when SIGNUP is undefined', () => {
        delete process.env.SIGNUP;

        const mod = loadModule();

        expect(mod.isEnvSignup).toBe(true);
      });
    });

    describe('isEnvAi', () => {
      it('returns false when AI is "no"', () => {
        process.env.AI = 'no';

        const mod = loadModule();

        expect(mod.isEnvAi).toBe(false);
      });

      it('returns true when AI is undefined', () => {
        delete process.env.AI;

        const mod = loadModule();

        expect(mod.isEnvAi).toBe(true);
      });
    });

    describe('isEnvPush', () => {
      it('returns false when PUSH is "no"', () => {
        process.env.PUSH = 'no';

        const mod = loadModule();

        expect(mod.isEnvPush).toBe(false);
      });

      it('returns true when PUSH is undefined', () => {
        delete process.env.PUSH;

        const mod = loadModule();

        expect(mod.isEnvPush).toBe(true);
      });
    });

    describe('isEnvStorage', () => {
      it('returns false when STORAGE is "no"', () => {
        process.env.STORAGE = 'no';

        const mod = loadModule();

        expect(mod.isEnvStorage).toBe(false);
      });

      it('returns true when STORAGE is undefined', () => {
        delete process.env.STORAGE;

        const mod = loadModule();

        expect(mod.isEnvStorage).toBe(true);
      });
    });

    describe('isEnvAnalytics', () => {
      it('returns false when ANALYTICS is "no"', () => {
        process.env.ANALYTICS = 'no';

        const mod = loadModule();

        expect(mod.isEnvAnalytics).toBe(false);
      });

      it('returns true when ANALYTICS is undefined', () => {
        delete process.env.ANALYTICS;

        const mod = loadModule();

        expect(mod.isEnvAnalytics).toBe(true);
      });
    });

    describe('isEnvMsAuth', () => {
      it('returns false when MS_AUTH is "no"', () => {
        process.env.MS_AUTH = 'no';

        const mod = loadModule();

        expect(mod.isEnvMsAuth).toBe(false);
      });

      it('returns true when MS_AUTH is undefined', () => {
        delete process.env.MS_AUTH;

        const mod = loadModule();

        expect(mod.isEnvMsAuth).toBe(true);
      });
    });

    describe('isEnvSSOAuth', () => {
      it('returns false when SSO_AUTH is "no"', () => {
        process.env.SSO_AUTH = 'no';

        const mod = loadModule();

        expect(mod.isEnvSSOAuth).toBe(false);
      });

      it('returns true when SSO_AUTH is undefined', () => {
        delete process.env.SSO_AUTH;

        const mod = loadModule();

        expect(mod.isEnvSSOAuth).toBe(true);
      });
    });

    it('reads boolean flag from featureFlags when available', () => {
      process.env.AI = 'yes';
      (window as any).__pneumaticConfig = {
        config: {
          featureFlags: {
            AI: 'no',
          },
        },
      };

      const mod = loadModule();

      expect(mod.isEnvAi).toBe(false);
    });
  });

  describe('string environment variables', () => {
    it('exports envSSOProvider from env', () => {
      process.env.SSO_PROVIDER = 'okta';

      const mod = loadModule();

      expect(mod.envSSOProvider).toBe('okta');
    });

    it('exports envHost from env', () => {
      process.env.HOST = 'https://app.pneumatic.app';

      const mod = loadModule();

      expect(mod.envHost).toBe('https://app.pneumatic.app');
    });

    it('exports envAnalyticsId from env', () => {
      process.env.ANALYTICS_ID = 'UA-12345';

      const mod = loadModule();

      expect(mod.envAnalyticsId).toBe('UA-12345');
    });

    it('exports envRecaptchaSiteKey from RECAPTCHA_SITE_KEY', () => {
      process.env.RECAPTCHA_SITE_KEY = 'site-key-123';

      const mod = loadModule();

      expect(mod.envRecaptchaSiteKey).toBe('site-key-123');
    });

    it('exports envGoogleClientId from env', () => {
      process.env.GOOGLE_CLIENT_ID = 'google-id-123';

      const mod = loadModule();

      expect(mod.envGoogleClientId).toBe('google-id-123');
    });

    it('exports envSentryRelease from env', () => {
      process.env.SENTRY_RELEASE = 'v1.2.3';

      const mod = loadModule();

      expect(mod.envSentryRelease).toBe('v1.2.3');
    });
  });

  describe('envDevMode', () => {
    it('returns true when NODE_ENV is development', () => {
      process.env.NODE_ENV = 'development';

      const mod = loadModule();

      expect(mod.envDevMode).toBe(true);
    });

    it('returns false when NODE_ENV is production', () => {
      process.env.NODE_ENV = 'production';

      const mod = loadModule();

      expect(mod.envDevMode).toBe(false);
    });
  });

  describe('envFirebase', () => {
    it('builds firebase config from env vars', () => {
      process.env.FIREBASE_VAPID_KEY = 'vapid-key';
      process.env.FIREBASE_API_KEY = 'api-key';
      process.env.FIREBASE_AUTH_DOMAIN = 'auth.domain';
      process.env.FIREBASE_PROJECT_ID = 'project-id';
      process.env.FIREBASE_STORAGE_BUCKET = 'bucket';
      process.env.FIREBASE_SENDER_ID = 'sender-id';
      process.env.FIREBASE_APP_ID = 'app-id';
      process.env.FIREBASE_MEASUREMENT_ID = 'G-12345';

      const mod = loadModule();

      expect(mod.envFirebase).toEqual({
        vapidKey: 'vapid-key',
        config: {
          apiKey: 'api-key',
          authDomain: 'auth.domain',
          projectId: 'project-id',
          storageBucket: 'bucket',
          messagingSenderId: 'sender-id',
          appId: 'app-id',
          measurementId: 'G-12345',
        },
      });
    });

    it('reads firebase config from featureFlags when available', () => {
      (window as any).__pneumaticConfig = {
        config: {
          featureFlags: {
            FIREBASE_VAPID_KEY: 'browser-vapid',
            FIREBASE_API_KEY: 'browser-api-key',
            FIREBASE_AUTH_DOMAIN: 'browser-auth',
            FIREBASE_PROJECT_ID: 'browser-project',
            FIREBASE_STORAGE_BUCKET: 'browser-bucket',
            FIREBASE_SENDER_ID: 'browser-sender',
            FIREBASE_APP_ID: 'browser-app',
            FIREBASE_MEASUREMENT_ID: 'browser-G-99',
          },
        },
      };

      const mod = loadModule();

      expect(mod.envFirebase.vapidKey).toBe('browser-vapid');
      expect(mod.envFirebase.config.apiKey).toBe('browser-api-key');
    });
  });
});
