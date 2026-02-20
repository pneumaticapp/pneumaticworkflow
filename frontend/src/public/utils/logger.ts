/* eslint-disable */
/* prettier-ignore */
import * as Sentry from '@sentry/react';

export const DETAIL_NO_PERMISSION =
  'You do not have permission to perform this action.';

function isExpectedPermissionDenied(args: any[]): boolean {
  return args.some(
    (a) =>
      a && typeof a === 'object' && a.detail === DETAIL_NO_PERMISSION,
  );
}

class BaseLogger {
  /* tslint:disable-next-line:no-any */
  public error(...args: any[]) {
    console.error(...args);

    this.handleSentryLogging(args);
  }

  /* tslint:disable-next-line:no-any */
  public info(...args: any[]) {
    console.info(...args);

    this.handleSentryLogging(args);
  }

  /* tslint:disable-next-line:no-any */
  public handleSentryLogging(args: any[]) {
    const error = args.find(arg => arg instanceof Error);

    const sentryError = error || new Error(JSON.stringify(args));
    if (isExpectedPermissionDenied(args)) {
      Sentry.withScope((scope) => {
        scope.setLevel('info');
        Sentry.captureException(sentryError);
      });
      return;
    }
    Sentry.captureException(sentryError);
  }
}

export const logger = new BaseLogger();
