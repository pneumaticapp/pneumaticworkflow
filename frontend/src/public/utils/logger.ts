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
    const isValidationError =
      args[0] === 'Response Error:' &&
      args[1] &&
      typeof args[1] === 'object' &&
      (args[1].code === 'validation_error' || args[1].code === 'validationError');

    if (isValidationError) {
      Sentry.captureMessage(JSON.stringify(args), 'info');
      return;
    }

    const error = args.find(arg => arg instanceof Error);

    const sentryError = error || new Error(JSON.stringify(args));
    Sentry.captureException(sentryError);
  }
}

export const logger = new BaseLogger();
