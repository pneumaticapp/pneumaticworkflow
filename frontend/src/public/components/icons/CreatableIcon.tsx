/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TCreatableIconProps = React.SVGAttributes<SVGElement>;

export function CreatableIcon({ fill = 'currentColor', ...rest }: TCreatableIconProps) {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        fill={fill}
        d="M18 15V13H29V15H18ZM18 27H29V25H18V27ZM29 21H18V19H29V21Z"
      />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        fill={fill}
        d="M17 14H15V26H17L14 29L11 26H13V14H11L14 11L17 14Z"
      />
    </svg>
  );
}
