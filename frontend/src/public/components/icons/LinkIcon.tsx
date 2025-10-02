/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TLinkIconProps = React.SVGAttributes<SVGElement>;

export const LinkIcon = ({ fill = 'currentColor', ...rest }: TLinkIconProps) => (
  <svg width="20" height="10" viewBox="0 0 20 10" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
    <path fillRule="evenodd" clipRule="evenodd" d="M9 8H5C3.35 8 2 6.65 2 5C2 3.35 3.35 2 5 2H9V0H5C2.24 0 0 2.24 0 5C0 7.76 2.24 10 5 10H9V8ZM15 0H11V2H15C16.65 2 18 3.35 18 5C18 6.65 16.65 8 15 8H11V10H15C17.76 10 20 7.76 20 5C20 2.24 17.76 0 15 0ZM14 4H6V6H14V4Z" />
  </svg>
);
