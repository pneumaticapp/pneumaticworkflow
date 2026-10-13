import * as Sentry from '@sentry/react';

import { setSentryCapture } from './sentryCapture';
import { DEV_SENTRY_DSN, PROD_SENTRY_DSN } from '../constants/defaultValues';
import { TEnvironment } from './getConfig';
import { envSentryRelease } from '../constants/enviroment';
import { mcpContinuation } from './safeRedirect';

export type TSentryApp = 'main' | 'forms';

const sentryDsnMap: { [key in TEnvironment]: string | null } = {
  local: null,
  staging: DEV_SENTRY_DSN,
  prod: PROD_SENTRY_DSN,
};

export const initSentry = (getConfig: () => { env?: TEnvironment }, app: TSentryApp) => {
  const { env = 'local' } = getConfig();
  const dsn = sentryDsnMap[env];
  if (!dsn) return;

  const release = typeof envSentryRelease === 'string' ? envSentryRelease : undefined;

  Sentry.init({
    dsn,
    environment: env,
    release,
    initialScope: {
      tags: { app },
    },
    beforeSend(event) {
      if (!dsn) return null;
      if (
        window.location.pathname.startsWith('/mcp/') ||
        mcpContinuation(new URLSearchParams(window.location.search).get('redirectUrl'))
      )
        return null;
      return event;
    },
    beforeBreadcrumb(breadcrumb) {
      return window.location.pathname.startsWith('/mcp/') ||
        mcpContinuation(new URLSearchParams(window.location.search).get('redirectUrl'))
        ? null
        : breadcrumb;
    },
    ignoreErrors: [
      /ResizeObserver loop/,
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
