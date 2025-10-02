/* eslint-disable react/no-children-prop */
import * as React from 'react';
import { Route, Link, NavLinkProps } from 'react-router-dom';
import * as H from 'history';

import { history } from '../../utils/history';

export interface ICustomNavLinkOwnProps {
  to: H.Pathname;
}

export type TCustomNavLinkProps = ICustomNavLinkOwnProps & NavLinkProps;

const EXCLUDED_PATHNAMES = ['#'];

export function NavLink({ location, to, children, ...rest }: TCustomNavLinkProps) {
  return (
    <Route
      path={to}
      children={() => (
        <Link replace={EXCLUDED_PATHNAMES.includes(to) || to === history.location.pathname} to={to} {...rest}>
          {children}
        </Link>
      )}
    />
  );
}
