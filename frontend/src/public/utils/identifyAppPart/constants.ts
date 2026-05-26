export const GUEST_URLS = ['/guest-task/'];
export const FORMS_PATH_PREFIX = '/forms';

/**
 * Returns the basename for React Router in the forms app.
 * - Path-based mode (/forms/{token}): returns '/forms' so Router strips the prefix
 * - Subdomain mode (forms.domain.com/{token}): returns undefined (no prefix to strip)
 */
export function getFormsBasename(pathname: string): string | undefined {
  const isPathBased = pathname.startsWith(`${FORMS_PATH_PREFIX}/`)
    || pathname === FORMS_PATH_PREFIX;

  return isPathBased ? FORMS_PATH_PREFIX : undefined;
}
