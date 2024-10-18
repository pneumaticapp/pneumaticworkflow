/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TAddTemplateIconProps = React.SVGAttributes<SVGElement>;

export function AddTemplateIcon({ fill = 'currentColor', ...rest }: TAddTemplateIconProps) {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M10.6667 2.66797H26.6667C28.1334 2.66797 29.3334 3.86797 29.3334 5.33464V21.3346C29.3334 22.8013 28.1334 24.0013 26.6667 24.0013H10.6667C9.20008 24.0013 8.00008 22.8013 8.00008 21.3346V5.33464C8.00008 3.86797 9.20008 2.66797 10.6667 2.66797ZM2.66675 8.0013H5.33341V26.668H24.0001V29.3346H5.33341C3.86675 29.3346 2.66675 28.1346 2.66675 26.668V8.0013ZM26.6667 21.3346H10.6667V5.33464H26.6667V21.3346ZM16.0001 19.3346V7.33464L24.0001 13.3346L16.0001 19.3346Z" />
    </svg>
  );
}
