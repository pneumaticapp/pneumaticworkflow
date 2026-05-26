import { captureException as sentryCaptureException } from './sentryCapture';

function findError(args: unknown[]): Error | undefined {
  const err = args.find((arg): arg is Error => arg instanceof Error);
  return err;
}

function logError(...args: unknown[]): void {
  console.error(...args);
  const err = findError(args);
  if (err) {
    sentryCaptureException(err);
  } else if (args.length > 0) {
    const message =
      args.length === 1 && typeof args[0] === 'string'
        ? args[0]
        : args
          .map((a) => (typeof a === 'object' && a !== null ? JSON.stringify(a) : String(a)))
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
