/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export interface ISearchIconProps extends React.SVGAttributes<SVGElement> {}

export function SearchIcon({ fill= '#fec336', ...rest }: ISearchIconProps) {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M12.0515 11.3208H12.8645L18 16.4666L16.4666 18L11.3208 12.8645V12.0515L11.0429 11.7633C9.86964 12.7719 8.34648 13.3791 6.68954 13.3791C2.99485 13.3791 0 10.3842 0 6.68954C0 2.99485 2.99485 0 6.68954 0C10.3842 0 13.3791 2.99485 13.3791 6.68954C13.3791 8.34648 12.7719 9.86964 11.7633 11.0429L12.0515 11.3208ZM2.05832 6.68954C2.05832 9.25214 4.12693 11.3208 6.68954 11.3208C9.25214 11.3208 11.3208 9.25214 11.3208 6.68954C11.3208 4.12693 9.25214 2.05832 6.68954 2.05832C4.12693 2.05832 2.05832 4.12693 2.05832 6.68954Z" fill={fill} />
    </svg>
  );
}
