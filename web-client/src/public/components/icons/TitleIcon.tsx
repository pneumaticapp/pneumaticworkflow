/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TTitleIconProps = React.SVGAttributes<SVGElement>;

export function TitleIcon({ fill = 'currentColor', ...rest }: TTitleIconProps) {
  return (
    <svg width="18" height="14" viewBox="0 0 18 14" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M0 0H18V2L0 2.01V0ZM18 6.01L0 6V8H18V6.01ZM0 12H12V14H0V12Z"
      />
    </svg>
  );
}
