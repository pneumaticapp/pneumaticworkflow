export const SUPERUSER_RETURN_ROUTE_STORAGE_KEY = "superuser_return_route";

export function setSuperuserReturnRoute(route: string) {
  sessionStorage.setItem(SUPERUSER_RETURN_ROUTE_STORAGE_KEY, route);
}

export function getSuperuserReturnRoute() {
  return sessionStorage.getItem(SUPERUSER_RETURN_ROUTE_STORAGE_KEY)
}

export function resetSuperuserReturnRoute() {
  sessionStorage.removeItem(SUPERUSER_RETURN_ROUTE_STORAGE_KEY);
}
