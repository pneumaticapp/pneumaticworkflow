export const GUEST_URLS = ['/guest-task/'];
export const FORMS_PATH_PREFIX = '/forms';

/**
 * Checks whether the current request targets the public forms app.
 * Combines both detection strategies:
 * - Path-based: domain.com/forms/*
 * - Subdomain: form.domain.com/*
 */
export function isFormPath(
  hostname: string,
  pathname: string,
  formSubdomain: string | undefined,
): boolean {
  const isPathBased = pathname.startsWith(`${FORMS_PATH_PREFIX}/`)
    || pathname === FORMS_PATH_PREFIX;

  const isSubdomain = !!formSubdomain && hostname === formSubdomain;

  return isPathBased || isSubdomain;
}

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
