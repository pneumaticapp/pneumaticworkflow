/* eslint-disable */
/* prettier-ignore */
import * as Sentry from '@sentry/react';

const AUTH_CREDENTIALS_NOT_PROVIDED =
  'Authentication credentials were not provided.';

function isExpectedAuthNotProvided(args: any[]): boolean {
  return args.some(
    (arg) =>
      arg &&
      typeof arg === 'object' &&
      arg.detail === AUTH_CREDENTIALS_NOT_PROVIDED,
  );
}

function isUninformativeError(message: string): boolean {
  const trimmed = (message || '').trim();
  if (
    !trimmed ||
    trimmed === 'No error message' ||
    trimmed === 'Error' ||
    trimmed === '{}' ||
    trimmed === '[]'
  ) {
    return true;
  }
  if (trimmed.includes('Request Error') && trimmed.endsWith(',{}]')) {
    return true;
  }
  return false;
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
    const msg = sentryError.message || '';

    const sendAsInfo =
      isExpectedAuthNotProvided(args) || isUninformativeError(msg);

    if (sendAsInfo) {
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
