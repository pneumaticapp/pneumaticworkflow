import type { TDropdownItemColor } from '../types';

import styles from '../DropdownMenu.css';

export const getDropdownItemColorClass = (color: TDropdownItemColor = 'black') => {
  const colorClassMap = {
    black: styles['dropdown-item_black'],
    green: styles['dropdown-item_green'],
    red: styles['dropdown-item_red'],
    orange: styles['dropdown-item_orange'],
  };

  return colorClassMap[color];
};
