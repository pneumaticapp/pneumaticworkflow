/* eslint-disable */
/* prettier-ignore */
import { TDashboardColor } from '../types';

import styles from '../Dashboard.css';

export function getClassNameByColor(color: TDashboardColor) {
  const classesMap: { [key in TDashboardColor]: string } = {
    blue: styles['dashboard-color-blue'],
    yellow: styles['dashboard-color-yellow'],
    green:  styles['dashboard-color-green'],
    red: styles['dashboard-color-red'],
    gray: styles['dashboard-color-gray'],
  };

  return classesMap[color];
}
