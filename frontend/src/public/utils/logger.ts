import { captureException as sentryCaptureException } from './sentryCapture';
import { isExpectedClientError } from './expectedClientErrors';
import { InterceptorError } from '../api/InterceptorError';

function findError(args: unknown[]): Error | undefined {
  return args.find((arg): arg is Error => arg instanceof Error);
}

function logError(...args: unknown[]): void {
  // Temporary: redirect expected API errors to info level (PR #14 will remove this
  // by eliminating duplicate logger.error calls in sagas)
  if (
    args.some(
      (arg) => (typeof arg === 'string' || typeof arg === 'object') && arg !== null && isExpectedClientError(arg),
    )
  ) {
    logInfo(...args);
    return;
  }

  console.error(...args);
  const err = findError(args);
  if (err) {
    if (err instanceof InterceptorError) {
      return;
    }
    sentryCaptureException(err);
  } else if (args.length > 0) {
    const message =
      args.length === 1 && typeof args[0] === 'string'
        ? args[0]
        : args
            .map((a) => {
              if (typeof a === 'object' && a !== null) {
                try {
                  return JSON.stringify(a);
                } catch {
                  return '[non-serializable object]';
                }
              }
              return String(a);
            })
            .join(' ');
    sentryCaptureException(new Error(message));
  }
}

function logInfo(...args: unknown[]): void {
  console.info(...args);
}

export const logger = {
  error: logError,
  info: logInfo,
};
