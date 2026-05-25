/* eslint-disable react/no-children-prop */
import * as React from 'react';
import { Route, Link, LinkProps } from 'react-router-dom';
import * as H from 'history';

import { history } from '../../utils/history';

export interface ICustomNavLinkOwnProps {
  to: H.Pathname;
}

export type TCustomNavLinkProps = ICustomNavLinkOwnProps & LinkProps;

const EXCLUDED_PATHNAMES = ['#'];

export function NavLink({ to, children, ...rest }: TCustomNavLinkProps) {
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
