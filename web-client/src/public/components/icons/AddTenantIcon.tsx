import React from 'react';

export type TAddTenantIconProps = React.SVGAttributes<SVGElement>;

export function AddTenantIcon({ fill = 'currentColor', ...rest }: TAddTenantIconProps) {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" {...rest}>
      <circle cx="20" cy="20" r="19.5" stroke={fill} />
      <path
        d="M15 21C14.4792 21 14 20.5208 14 20C14 19.4792 14.4792 19 15 19H25C25.5208 19 26 19.4792 26 20C26 20.5208 25.5208 21 25 21H15Z"
        fill={fill}
      />
      <path
        d="M21 15C21 14.4792 20.5208 14 20 14C19.4792 14 19 14.4792 19 15V25C19 25.5208 19.4792 26 20 26C20.5208 26 21 25.5208 21 25V15Z"
        fill={fill}
      />
    </svg>
  );
}
