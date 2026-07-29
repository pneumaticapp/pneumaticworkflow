import * as React from 'react';
import classnames from 'classnames';
import * as H from 'history';

import { ReturnIcon } from '../../icons';
import { NavLink } from '../../NavLink';

import styles from './ReturnLink.css';

interface IReturnLinkProps {
  label: string;
  route: H.Pathname;
  className?: string;
}

export function ReturnLink({ label, route, className }: IReturnLinkProps) {
  return (
    <NavLink to={route} className={classnames(styles['back-link'], className)}>
      <ReturnIcon className={styles['icon']} />
      {label}
    </NavLink>
  );
}
