import { createBrowserHistory } from 'history';

import { ERoutes } from '../constants/routes';

export const history = createBrowserHistory({});

const getRoutesRegExps = (...routes: ERoutes[]) => {
  const getRegExpFromRoute = (route: ERoutes) => new RegExp(`^${route.replace(':id', '[0-9]+')}$`);
  const routesRegExp = routes.map(getRegExpFromRoute);

  return routesRegExp;
}

export const checkSomeRouteIsActive = (...routes: ERoutes[]) => {
  return getRoutesRegExps(...routes).some(route => route.test(history.location.pathname));
};

export const checkSomeRouteMatchesLocation = (location: string, routes: ERoutes[]) => {
  return getRoutesRegExps(...routes).some(route => route.test(location));
};

export const isGoogleAuth = () => history.location.pathname.includes(ERoutes.SignUpGoogle);
export const isCreateTemplate = () => history.location.pathname.includes(ERoutes.TemplatesCreate);
export const isAccountProfile = () => history.location.pathname.includes(ERoutes.Profile);
export const isAccountSettings = () => history.location.pathname.includes(ERoutes.AccountSettings);

export const getQueryStringParams = (query: string): { [key: string]: string } => {
  return query
    ? (/^[?#]/.test(query) ? query.slice(1) : query)
      .split('&')
      .reduce((params: { [key: string]: string }, param) => {
        const [key, value] = param.split('=');
        params[key] = value ? decodeURIComponent(value.replace(/\+/g, ' ')) : '';

        return params;
      }, {},
      )
    : {};
};

export const getQueryStringByParams = (params: { [key: string]: string }) => {
  const paramKeys = Object.keys(params);
  if (paramKeys.length === 0) {
    return '';
  }

  const stringifiedParams = paramKeys
    .map(paramName => `${paramName}=${params[paramName]}`)
    .join('&');

  return `?${stringifiedParams}`;
};
