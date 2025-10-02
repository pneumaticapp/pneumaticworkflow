import * as React from 'react';

export type TArrowDropdownIcon = React.SVGAttributes<SVGElement>;

export function ArrowDropdownIcon({ fill = 'currentColor', ...rest }: TArrowDropdownIcon) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={fill} {...rest} xmlns="http://www.w3.org/2000/svg">
      <path d="M7 10L12 15L17 10H7Z" fill="#62625F" />
    </svg>
  );
}
