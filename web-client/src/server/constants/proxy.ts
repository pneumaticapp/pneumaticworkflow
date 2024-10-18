export const PROXY_URL_PREFIX = '/api/';
/*
  Используется для добавления приватного пути API,
  добавить можно любое регулярное выражение без префикса
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
