import * as Sentry from '@sentry/react';

import { setSentryCapture } from './sentryCapture';
import { DEV_SENTRY_DSN, PROD_SENTRY_DSN } from '../constants/defaultValues';
import { TEnvironment } from './getConfig';

export type TSentryApp = 'main' | 'forms';

const sentryDsnMap: { [key in TEnvironment]: string | null } = {
  local: null,
  staging: DEV_SENTRY_DSN,
  prod: PROD_SENTRY_DSN,
};

export const initSentry = (
  getConfig: () => { env?: TEnvironment },
  app: TSentryApp,
) => {
  const { env = 'local' } = getConfig();
  const dsn = sentryDsnMap[env];
  if (!dsn) return;

  const release = typeof process.env.SENTRY_RELEASE === 'string'
    ? process.env.SENTRY_RELEASE
    : undefined;

  Sentry.init({
    dsn,
    environment: env,
    release,
    initialScope: {
      tags: { app },
    },
    beforeSend(event) {
      if (!dsn) return null;
      return event;
    },
    ignoreErrors: [
      /^Loading chunk \d+ failed\./,
      /^Loading CSS chunk \d+ failed\./,
      /ChunkLoadError/,
      /Non-Error promise rejection captured/,
      /AbortError/,
      /canceled/,
      /Network request failed/,
    ],
  });

  setSentryCapture((error: Error) => {
    Sentry.captureException(error);
  });
};
