import { TDropdownItemColor } from './types';

import styles from './Dropdown.css';

export const getDropdownItemColorClass = (color: TDropdownItemColor = 'black') => ({
  black: styles['dropdown-item_black'],
  green: styles['dropdown-item_green'],
  red: styles['dropdown-item_red'],
  orange: styles['dropdown-item_orange'],
})[color];
