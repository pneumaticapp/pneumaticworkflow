/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TFileCopyIconProps = React.SVGAttributes<SVGElement>;

export const FileCopyIcon = ({ ...rest }: TFileCopyIconProps) => (
  <svg width="18" height="22" viewBox="0 0 18 22" fill="none" xmlns="http://www.w3.org/2000/svg" >
    <path fillRule="evenodd" clipRule="evenodd" d="M13 0H2C0.9 0 0 0.9 0 2V16H2V2H13V0ZM12 4H6C4.9 4 4.01 4.9 4.01 6L4 20C4 21.1 4.89 22 5.99 22H16C17.1 22 18 21.1 18 20V10L12 4ZM6 6V20H16V11H11V6H6Z" fill="#62625F" {...rest} />
  </svg>
);
