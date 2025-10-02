/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TCheckboxIconProps = React.SVGAttributes<SVGElement>;

export const CheckboxIcon = ({ fill = 'currentColor', ...rest }: TCheckboxIconProps) => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg"  {...rest}>
    <path fillRule="evenodd" clipRule="evenodd" d="M2 0H18C19.1 0 20 0.9 20 2V18C20 19.1 19.1 20 18 20H2C0.9 20 0 19.1 0 18L0.00999999 2C0.00999999 0.9 0.9 0 2 0ZM2 18H18V2H2V18Z" />
    <path fillRule="evenodd" clipRule="evenodd" d="M9 11.17L13.59 6.57999L15 7.99999L9 14L5 9.99999L6.41 8.58999L9 11.17Z" />
  </svg>
);
