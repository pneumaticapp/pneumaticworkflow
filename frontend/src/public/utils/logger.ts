/* eslint-disable */
/* prettier-ignore */
import * as Sentry from '@sentry/react';

export const MSG_FAILED_FETCH_PUBLIC_FORM = 'Failed to fetch public form.';

function isExpectedPublicFormNotFound(sentryError: Error, args: unknown[]): boolean {
  if (sentryError.message.includes('Failed to fetch public form')) {
    return true;
  }
  return args.some(
    (a) => typeof a === 'string' && a.includes('Failed to fetch public form'),
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
    const error = args.find((arg) => arg instanceof Error);
    const sentryError = error || new Error(JSON.stringify(args));

    if (isExpectedPublicFormNotFound(sentryError, args)) {
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
