/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type DropdownCloseIconProps = React.SVGAttributes<SVGElement>;

export function DropdownCloseIcon({ fill = 'currentColor', ...rest }: DropdownCloseIconProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path d="M6.6281 14.7207C6.25565 15.0931 5.65179 15.0931 5.27934 14.7207C4.90689 14.3482 4.90689 13.7444 5.27934 13.3719L13.3719 5.27934C13.7444 4.90689 14.3482 4.90689 14.7207 5.27934C15.0931 5.65179 15.0931 6.25565 14.7207 6.6281L6.6281 14.7207Z" fill="white" />
      <path d="M6.6281 5.27934C6.25565 4.90689 5.65179 4.90689 5.27934 5.27934C4.90689 5.65179 4.90689 6.25565 5.27934 6.6281L13.3719 14.7207C13.7444 15.0931 14.3482 15.0931 14.7207 14.7207C15.0931 14.3482 15.0931 13.7444 14.7207 13.3719L6.6281 5.27934Z" fill="white" />
    </svg>
  );
}
