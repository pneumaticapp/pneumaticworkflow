import * as Sentry from '@sentry/react';

import { DEV_SENTRY_DSN, PROD_SENTRY_DSN } from '../constants/defaultValues';
import { TEnvironment } from './getConfig';

export const initSentry = (getConfig: () => { env?: TEnvironment } ) => {
  const { env = 'local' } = getConfig();

  const sentryDevMap: { [key in TEnvironment]: string | null } = {
    local: null,
    staging: DEV_SENTRY_DSN,
    prod: PROD_SENTRY_DSN,
  };

  const dsn = sentryDevMap[env];
  if (!dsn) {
    return;
  }

  Sentry.init({ dsn });
};
