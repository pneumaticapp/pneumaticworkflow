/**
 * Expected client-side error patterns — not application bugs.
 * Errors matching these patterns are logged at info level (no Sentry event).
 *
 * Separate from server-side expectedErrors.ts (server/utils/) because:
 * - Different contexts: SSR middleware vs Axios interceptor in browser
 * - "Authentication credentials were not provided" is always expected on client
 *   (redirectToLogin handles it), but context-dependent on server
 * - Changes for client should not accidentally mask server errors
 */

// Auth/permission — session/permission issues, not application bugs
const EXPECTED_AUTH_PATTERNS = [
  'token_not_valid',
  'Token is invalid',
  'Token is expired',
  'Authentication credentials were not provided',
  'You do not have permission',
  'Request was throttled',
];

// Validation — user input errors, not code bugs
const EXPECTED_VALIDATION_PATTERNS = [
  'validation_error',
];

const ALL_EXPECTED_PATTERNS = [...EXPECTED_AUTH_PATTERNS, ...EXPECTED_VALIDATION_PATTERNS];
const EXPECTED_CLIENT_ERROR_REGEX = new RegExp(ALL_EXPECTED_PATTERNS.join('|'));

/**
 * Checks if an API response error is expected (not an application bug).
 * Used in the Axios interceptor to downgrade expected errors from error to info level.
 */
export function isExpectedClientError(responseData: string | object): boolean {
  if (typeof responseData === 'string') {
    return EXPECTED_CLIENT_ERROR_REGEX.test(responseData);
  }

  if (typeof responseData === 'object' && responseData !== null) {
    return EXPECTED_CLIENT_ERROR_REGEX.test(JSON.stringify(responseData));
  }

  return false;
}
