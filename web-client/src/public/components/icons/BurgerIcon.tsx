/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TBurgerIconIcon = React.SVGAttributes<SVGElement>;

export function BurgerIcon({ fill = 'currentColor', ...rest }: TBurgerIconIcon) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest} >
      <path d="M2.85714 11C2.38376 11 2 10.5523 2 10C2 9.44772 2.38376 9 2.85714 9L17.1429 9C17.6162 9 18 9.44771 18 10C18 10.5523 17.6162 11 17.1429 11L2.85714 11Z" />
      <path d="M2.85714 6C2.38376 6 2 5.55228 2 5C2 4.44772 2.38376 4 2.85714 4L17.1429 4C17.6162 4 18 4.44772 18 5C18 5.55228 17.6162 6 17.1429 6L2.85714 6Z" />
      <path d="M2.85714 16C2.38376 16 2 15.5523 2 15C2 14.4477 2.38376 14 2.85714 14L17.1429 14C17.6162 14 18 14.4477 18 15C18 15.5523 17.6162 16 17.1429 16L2.85714 16Z" />
    </svg>
  );
}
