/* eslint-disable */
/* prettier-ignore */
import * as Sentry from '@sentry/react';

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
    Sentry.captureException(sentryError);
  }
}

export const logger = new BaseLogger();
