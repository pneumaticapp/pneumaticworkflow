import * as React from 'react';

export type TBoldPlusIconProps = React.SVGAttributes<SVGElement>;

export function BoldPlusIcon({ fill = 'currentColor', ...rest }: TBoldPlusIconProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path d="M5 11C4.47915 11 4 10.5208 4 10C4 9.47915 4.47915 9 5 9H15C15.5208 9 16 9.47915 16 10C16 10.5208 15.5208 11 15 11H5Z" />
      <path d="M11 5C11 4.47915 10.5208 4 10 4C9.47915 4 9 4.47915 9 5V15C9 15.5208 9.47915 16 10 16C10.5208 16 11 15.5208 11 15V5Z" />
    </svg>
  );
}
