/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { TIconSize } from '../../../types/common';

export interface IProcessCompleteIconProps extends React.SVGAttributes<SVGElement> {
  size?: TIconSize;
}

export function ProcessCompleteIcon({ fill = '#5fad56', size = 'lg', ...rest }: IProcessCompleteIconProps) {
  const largeIcon = (
    <svg
      width="32"
      height="32"
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      {...rest}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M0 4C0 1.79086 1.79086 0 4 0H14C17.3137 0 20 2.68629 20 6V18C20 20.2091 18.2091 22 16 22H4C1.79086 22 0 20.2091 0 18V4ZM14 4H4V18H16V6C16 4.89543 15.1046 4 14 4Z"
        fill="#5fad56"
      />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M16 8C16 5.79086 17.7909 4 20 4H26C29.3137 4 32 6.68629 32 10V20C32 23.3137 29.3137 26 26 26H22C18.6863 26 16 23.3137 16 20V8ZM26 8H20V20C20 21.1046 20.8954 22 22 22H26C27.1046 22 28 21.1046 28 20V10C28 8.89543 27.1046 8 26 8Z"
        fill="#5fad56"
      />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M2 16C3.10457 16 4 16.8954 4 18V30C4 31.1046 3.10457 32 2 32C0.89543 32 0 31.1046 0 30V18C0 16.8954 0.89543 16 2 16Z"
        fill="#5fad56"
      />
    </svg>
  );

  const smallIcon = (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M2 4C2 2.89543 2.89543 2 4 2H9C10.6569 2 12 3.34315 12 5V11C12 12.1046 11.1046 13 10 13H4C2.89543 13 2 12.1046 2 11V4Z"/>
      <path fillRule="evenodd" clipRule="evenodd" d="M10 6C10 4.89543 10.8954 4 12 4H15C16.6569 4 18 5.34315 18 7V12C18 13.6569 16.6569 15 15 15H13C11.3431 15 10 13.6569 10 12V6Z"/>
      <path fillRule="evenodd" clipRule="evenodd" d="M3 10C3.55228 10 4 10.4477 4 11V17C4 17.5523 3.55228 18 3 18C2.44772 18 2 17.5523 2 17V11C2 10.4477 2.44772 10 3 10Z"/>
    </svg>

  );

  const ICON_SIZE_MAP = {
    ['lg']: largeIcon,
    ['sm']: smallIcon,
  };

  return ICON_SIZE_MAP[size];
}
