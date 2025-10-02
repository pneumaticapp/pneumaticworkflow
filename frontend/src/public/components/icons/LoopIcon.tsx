/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TLoopIconProps = React.SVGAttributes<SVGElement>;

export function LoopIcon({fill= 'currentColor', ...rest}: TLoopIconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="16" viewBox="0 0 12 16" fill={fill} {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M6.00033 0.666687V2.66669C8.94699 2.66669 11.3337 5.05335 11.3337 8.00002C11.3337 9.04669 11.027 10.02 10.507 10.84L9.53366 9.86669C9.83366 9.31335 10.0003 8.67335 10.0003 8.00002C10.0003 5.79335 8.20699 4.00002 6.00033 4.00002V6.00002L3.33366 3.33335L6.00033 0.666687ZM2.00033 8.00002C2.00033 10.2067 3.79366 12 6.00033 12V10L8.66699 12.6667L6.00033 15.3334V13.3334C3.05366 13.3334 0.666992 10.9467 0.666992 8.00002C0.666992 6.95335 0.973659 5.98002 1.49366 5.16002L2.46699 6.13335C2.16699 6.68669 2.00033 7.32669 2.00033 8.00002Z"/>
    </svg>

  );
}
