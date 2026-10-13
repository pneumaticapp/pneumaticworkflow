import * as Sentry from '@sentry/node';

import { setSentryCapture } from '../../public/utils/sentryCapture';

type TEnvironment = 'local' | 'staging' | 'prod';

export const initSentryServer = (): void => {
  const dsn = process.env.SENTRY_DSN;
  const env = (process.env.MCS_RUN_ENV || 'local') as TEnvironment;

  if (!dsn || env === 'local') return;

  const release = typeof process.env.SENTRY_RELEASE === 'string' ? process.env.SENTRY_RELEASE : undefined;

  Sentry.init({
    dsn,
    environment: env,
    release,
    initialScope: {
      tags: { app: 'server' },
    },
    beforeSend(event) {
      const url = event.request?.url;
      if (url && /\/mcp(?:\/|\?|$)/.test(url)) return null;
      return event;
    },
  });

  setSentryCapture((error: Error) => {
    Sentry.captureException(error);
  });
};
