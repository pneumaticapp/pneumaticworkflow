/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TAttachmentIconProps = React.SVGAttributes<SVGElement>;

export function AttachmentIcon({ fill = 'currentColor', ...rest }: TAttachmentIconProps) {
  return (
    <svg width="22" height="10" viewBox="0 0 22 10" fill={fill} xmlns="http://www.w3.org/2000/svg" { ...rest }>
      <path d="M17 8.63636H5.5C3.29 8.63636 1.5 7.00909 1.5 5C1.5 2.99091 3.29 1.36364 5.5 1.36364H18C19.38 1.36364 20.5 2.38182 20.5 3.63636C20.5 4.89091 19.38 5.90909 18 5.90909H7.5C6.95 5.90909 6.5 5.5 6.5 5C6.5 4.5 6.95 4.09091 7.5 4.09091H17V2.72727H7.5C6.12 2.72727 5 3.74545 5 5C5 6.25455 6.12 7.27273 7.5 7.27273H18C20.21 7.27273 22 5.64545 22 3.63636C22 1.62727 20.21 0 18 0H5.5C2.46 0 0 2.23636 0 5C0 7.76364 2.46 10 5.5 10H17V8.63636Z" />
    </svg>
  );
}
