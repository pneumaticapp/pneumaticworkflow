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

/**
 * Documented 401 response from /accounts/public/account for invalid/inactive shareKey.
 * Handled locally in getUserPublic (not added to global filter to avoid masking
 * real auth failures in getUser, getPages, oauthHandler).
 */
export const EXPECTED_AUTH_ERROR = 'Authentication credentials were not provided';
export const LOG_PREFIX_ACCOUNT_CONTEXT = 'failed to get account context: ';

const EXPECTED_ERROR_REGEX = new RegExp(EXPECTED_ERROR_PATTERNS.join('|'));

export function errorToString(error: TLoggerArgs[number]): string {
  if (error instanceof Error) {
    return error.message;
  } if (typeof error === 'object' && error !== null) {
    return JSON.stringify(error);
  }

  return String(error);
}

export function isExpectedError(error: TLoggerArgs[number]): boolean {
  return EXPECTED_ERROR_REGEX.test(errorToString(error));
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
