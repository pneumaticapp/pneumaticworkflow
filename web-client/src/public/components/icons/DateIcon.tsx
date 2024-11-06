/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TDateIconProps = React.SVGAttributes<SVGElement>;

export function DateIcon({ fill = 'currentColor', ...rest }: TDateIconProps) {
  return (
    <svg width="18" height="20" viewBox="0 0 18 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M16 20C17.1 20 18 19.1 18 18V4C18 2.9 17.1 2 16 2H15V0H13V2H5V0H3V2H2C0.89 2 0.01 2.9 0.01 4L0 18C0 19.1 0.89 20 2 20H16ZM6 11V9H4V11H6ZM2 6H16V4H2V6ZM16 8V18H2V8H16ZM14 11V9H12V11H14ZM10 11H8V9H10V11Z" />
    </svg>
  );
}
