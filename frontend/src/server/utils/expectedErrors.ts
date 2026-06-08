import { logger } from '../../public/utils/logger';
import { TLoggerArgs } from './types';

/**
 * Known non-critical error patterns from backend API responses.
 * Errors matching these patterns are logged at info level (not sent to Sentry).
 * All other errors remain at error level to preserve visibility.
 */
const EXPECTED_ERROR_PATTERNS = [
  'token_not_valid',
  'Token is invalid',
  'Token is expired',
  'Request was throttled',
];

const EXPECTED_ERROR_REGEX = new RegExp(EXPECTED_ERROR_PATTERNS.join('|'));

export function isExpectedError(error: TLoggerArgs[number]): boolean {
  return EXPECTED_ERROR_REGEX.test(String(error));
}

/**
 * Logs expected errors at info level (no Sentry event) and unexpected errors at error level.
 */
export function logServerError(...args: TLoggerArgs) {
  if (args.some(isExpectedError)) {
    logger.info(...args);
  } else {
    logger.error(...args);
  }
}
