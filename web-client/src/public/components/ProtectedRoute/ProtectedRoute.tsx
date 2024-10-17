import * as React from 'react';
import { Redirect, Route, RouteProps } from 'react-router-dom';

import { ERoutes } from '../../constants/routes';

export interface IProtectedRouteProps extends RouteProps {
  hasAccessAuth?: boolean;
  hasAccess?: boolean;
  onAccessDenied?(): void;
}

export function ProtectedRoute({ children, hasAccess, hasAccessAuth, onAccessDenied, ...rest }: IProtectedRouteProps) {
  return (
    <Route
      {...rest}
      render={({ location }) => {

        if (typeof hasAccessAuth === 'boolean' && !hasAccessAuth) {
          return (<Redirect exact from="/" to="/auth/" />)
        }

        if (onAccessDenied) {
          onAccessDenied();
        }


        if (typeof hasAccess === 'boolean' && !hasAccess) {
          return <Redirect
          to={{
            pathname: ERoutes.Tasks,
            state: { from: location },
          }}
        />
        }

        return children;
      }}
    />
  );
}
