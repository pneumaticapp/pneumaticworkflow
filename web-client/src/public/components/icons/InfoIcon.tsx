/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export const InfoIcon = ({
  fill = '#dcdcdb',
  width,
  height,
  // tslint:disable-next-line: trailing-comma
  ...restProps
}: React.SVGProps<SVGSVGElement>) => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...restProps}>
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM9 5V7H11V5H9ZM9 9V15H11V9H9ZM2 10C2 14.41 5.59 18 10 18C14.41 18 18 14.41 18 10C18 5.59 14.41 2 10 2C5.59 2 2 5.59 2 10Z"
    />
  </svg>
);
