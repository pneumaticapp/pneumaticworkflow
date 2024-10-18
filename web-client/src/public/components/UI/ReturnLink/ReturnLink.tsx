import * as React from 'react';

import { ERoutes } from '../../../constants/routes';
import { ReturnIcon } from '../../icons';
import { NavLink } from '../../NavLink';

import styles from './ReturnLink.css';

interface IReturnLinkProps {
  label: string;
  route: ERoutes;
}

export function ReturnLink({ label, route }: IReturnLinkProps) {
  return (
    <NavLink to={route} className={styles['back-link']}>
      <ReturnIcon className={styles['icon']} />
      {label}
    </NavLink>
  );
}
