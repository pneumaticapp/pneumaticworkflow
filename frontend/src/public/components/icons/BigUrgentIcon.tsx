/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TBigUrgentIconProps = React.SVGAttributes<SVGElement>;

export function BigUrgentIcon({ fill = 'currentColor', ...rest }: TBigUrgentIconProps) {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill={fill} xmlns="http://www.w3.org/2000/svg">
      <path d="M25.0652 18.6765C25.0652 18.6765 29.9699 16.7668 28.9249 10.521C28.9249 10.521 36 13.534 36 23.5256C36 31.7556 28.8371 38 20 38C23.3137 38 26 35.4542 26 32.3142C26 30.3053 24.9125 29.0567 23.8882 27.8807C22.8873 26.7316 21.9469 25.6519 22.1404 24C22.1404 24 17.1054 25.5999 18.1006 30.4853C18.1006 30.4853 16.2613 29.7426 16.6531 27.3137C16.6531 27.3137 14 28.4855 14 32.3711C14 35.5716 16.6861 38 20 38C11.1634 38 4 31.4538 4 23.3794C4 18.2137 6.9001 15.003 9.63154 11.979C12.3004 9.0242 14.8083 6.24773 14.2923 2C14.2923 2 27.719 6.11407 25.0652 18.6765Z" />
    </svg>
  );
}
