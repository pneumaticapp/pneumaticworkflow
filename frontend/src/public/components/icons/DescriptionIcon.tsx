/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TDescriptionIconProps = React.SVGAttributes<SVGElement>;

export function DescriptionIcon({fill= 'currentColor', ...rest}: TDescriptionIconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="28" viewBox="0 0 22 28" fill={fill} {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M13.6673 0.666656H3.00065C1.53398 0.666656 0.333984 1.86666 0.333984 3.33332V24.6667C0.333984 26.1333 1.52065 27.3333 2.98732 27.3333H19.0007C20.4673 27.3333 21.6673 26.1333 21.6673 24.6667V8.66666L13.6673 0.666656ZM16.334 14H5.66732V16.6667H16.334V14ZM16.334 19.3333H5.66732V22H16.334V19.3333ZM3.00065 24.6667H19.0007V9.99999H12.334V3.33332H3.00065V24.6667Z"/>
    </svg>
  );
}
