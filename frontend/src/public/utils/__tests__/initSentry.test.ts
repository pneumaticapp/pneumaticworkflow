// <reference types="jest" />

jest.mock('@sentry/react', () => ({
  init: jest.fn(),
  captureException: jest.fn(),
}));

jest.mock('../sentryCapture', () => ({
  setSentryCapture: jest.fn(),
}));

jest.mock('../../constants/defaultValues', () => ({
  DEV_SENTRY_DSN: 'https://staging-dsn@sentry.io/123',
  PROD_SENTRY_DSN: 'https://prod-dsn@sentry.io/456',
}));

describe('initSentry', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('release from envSentryRelease', () => {
    it('passes envSentryRelease as release to Sentry.init when available', () => {
      jest.doMock('../../constants/enviroment', () => ({
        envSentryRelease: 'v3.5.0',
      }));
      jest.resetModules();

      const { initSentry } = require('../initSentry');

      const getConfig = () => ({ env: 'prod' as const });
      initSentry(getConfig, 'main');

      const sentryMock = require('@sentry/react');
      expect(sentryMock.init).toHaveBeenCalledWith(
        expect.objectContaining({
          release: 'v3.5.0',
        }),
      );
    });

    it('passes undefined release when envSentryRelease is undefined', () => {
      jest.doMock('../../constants/enviroment', () => ({
        envSentryRelease: undefined,
      }));
      jest.resetModules();

      const { initSentry } = require('../initSentry');

      const getConfig = () => ({ env: 'staging' as const });
      initSentry(getConfig, 'forms');

      const sentryMock = require('@sentry/react');
      expect(sentryMock.init).toHaveBeenCalledWith(
        expect.objectContaining({
          release: undefined,
        }),
      );
    });
  });

  describe('environment routing', () => {
    beforeEach(() => {
      jest.doMock('../../constants/enviroment', () => ({
        envSentryRelease: undefined,
      }));
      jest.resetModules();
    });

    it('does not init Sentry for local environment', () => {
      const { initSentry } = require('../initSentry');

      const getConfig = () => ({ env: 'local' as const });
      initSentry(getConfig, 'main');

      const sentryMock = require('@sentry/react');
      expect(sentryMock.init).not.toHaveBeenCalled();
    });

    it('inits Sentry with staging DSN for staging environment', () => {
      const { initSentry } = require('../initSentry');

      const getConfig = () => ({ env: 'staging' as const });
      initSentry(getConfig, 'main');

      const sentryMock = require('@sentry/react');
      expect(sentryMock.init).toHaveBeenCalledWith(
        expect.objectContaining({
          dsn: 'https://staging-dsn@sentry.io/123',
          environment: 'staging',
        }),
      );
    });

    it('inits Sentry with prod DSN for prod environment', () => {
      const { initSentry } = require('../initSentry');

      const getConfig = () => ({ env: 'prod' as const });
      initSentry(getConfig, 'forms');

      const sentryMock = require('@sentry/react');
      expect(sentryMock.init).toHaveBeenCalledWith(
        expect.objectContaining({
          dsn: 'https://prod-dsn@sentry.io/456',
          environment: 'prod',
        }),
      );
    });

    it('defaults to local when env is not provided', () => {
      const { initSentry } = require('../initSentry');

      const getConfig = () => ({});
      initSentry(getConfig, 'main');

      const sentryMock = require('@sentry/react');
      expect(sentryMock.init).not.toHaveBeenCalled();
    });
  });

  describe('app tag', () => {
    beforeEach(() => {
      jest.doMock('../../constants/enviroment', () => ({
        envSentryRelease: undefined,
      }));
      jest.resetModules();
    });

    it('sets app tag to main', () => {
      const { initSentry } = require('../initSentry');

      const getConfig = () => ({ env: 'prod' as const });
      initSentry(getConfig, 'main');

      const sentryMock = require('@sentry/react');
      expect(sentryMock.init).toHaveBeenCalledWith(
        expect.objectContaining({
          initialScope: {
            tags: { app: 'main' },
          },
        }),
      );
    });

    it('sets app tag to forms', () => {
      const { initSentry } = require('../initSentry');

      const getConfig = () => ({ env: 'staging' as const });
      initSentry(getConfig, 'forms');

      const sentryMock = require('@sentry/react');
      expect(sentryMock.init).toHaveBeenCalledWith(
        expect.objectContaining({
          initialScope: {
            tags: { app: 'forms' },
          },
        }),
      );
    });
  });

  describe('setSentryCapture', () => {
    beforeEach(() => {
      jest.doMock('../../constants/enviroment', () => ({
        envSentryRelease: undefined,
      }));
      jest.resetModules();
    });

    it('calls setSentryCapture on successful init', () => {
      const { initSentry } = require('../initSentry');
      const { setSentryCapture } = require('../sentryCapture');

      const getConfig = () => ({ env: 'prod' as const });
      initSentry(getConfig, 'main');

      expect(setSentryCapture).toHaveBeenCalledWith(expect.any(Function));
    });

    it('does not call setSentryCapture when dsn is null (local)', () => {
      const { initSentry } = require('../initSentry');
      const { setSentryCapture } = require('../sentryCapture');

      const getConfig = () => ({ env: 'local' as const });
      initSentry(getConfig, 'main');

      expect(setSentryCapture).not.toHaveBeenCalled();
    });
  });

  it.each(['/mcp/connections', '/auth/signin/?redirectUrl=%2Fmcp%2Fconnections'])(
    'test_initSentry__MCP_path_%s__drops_events_and_breadcrumbs',
    (path) => {
      // arrange
      jest.resetModules();
      const { initSentry } = require('../initSentry');
      const sentry = require('@sentry/react');
      const { setSentryCapture } = require('../sentryCapture');
      const originalUrl = window.location.pathname + window.location.search;
      window.history.replaceState({}, '', path);
      const event = { message: 'private request' };
      const breadcrumb = { message: 'private capability' };
      let callbacks!: {
        beforeSend(value: typeof event): unknown;
        beforeBreadcrumb(value: typeof breadcrumb): unknown;
      };
      const initMock = sentry.init as jest.Mock;
      initMock.mockImplementationOnce((options: typeof callbacks) => {
        callbacks = options;
      });
      initSentry(() => ({ env: 'prod' as const }), 'main');

      // act
      const sentEvent = callbacks.beforeSend(event);
      const sentBreadcrumb = callbacks.beforeBreadcrumb(breadcrumb);
      window.history.replaceState({}, '', originalUrl);

      // assert
      expect(sentEvent).toBeNull();
      expect(sentBreadcrumb).toBeNull();
      expect(initMock).toHaveBeenCalledTimes(1);
      expect(initMock).toHaveBeenCalledWith(
        expect.objectContaining({
          beforeSend: expect.any(Function),
          beforeBreadcrumb: expect.any(Function),
        }),
      );
      expect(setSentryCapture).toHaveBeenCalledTimes(1);
      expect(setSentryCapture).toHaveBeenCalledWith(expect.any(Function));
    },
  );
});
