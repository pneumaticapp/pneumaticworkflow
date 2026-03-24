export const USER_ERROR_STATUSES = [401, 403, 404];

export function isUserError(status: number): boolean {
  return USER_ERROR_STATUSES.includes(status);
}
