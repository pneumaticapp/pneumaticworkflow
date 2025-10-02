export const SUPERUSER_TOKEN_STORAGE_KEY = "superuser_token";

export function setSuperuserToken(token: string) {
  sessionStorage.setItem(SUPERUSER_TOKEN_STORAGE_KEY, token);
}

export function getSuperuserToken() {
  return sessionStorage.getItem(SUPERUSER_TOKEN_STORAGE_KEY)
}

export function resetSuperuserToken() {
  sessionStorage.removeItem(SUPERUSER_TOKEN_STORAGE_KEY);
}
