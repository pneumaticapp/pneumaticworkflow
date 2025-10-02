export const PROXY_URL_PREFIX = '/api/';
/*
  Used to add a private API path,
  any regular expression can be added without a prefix.
 */
export const PROXY_ALLOWED_ROUTES = [
  '/auth/token/obtain',
  '/auth/signout',
  '/auth/superuser/token',
  '/accounts/users/\\d+/delete',
  '/auth/signup',
  '/auth/reset-password.*',
  '/auth/change-password',
  '/accounts/invites.*',
  '/accounts/api-key',
  '/auth/resend-verification',
  '/auth/verification.*',
  '/workflows/attachments.*',
];
