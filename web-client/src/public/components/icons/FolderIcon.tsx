/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export function FolderIcon({ fill = 'currentColor', ...rest }: React.SVGAttributes<SVGElement>) {
  return (
    <svg width="20" height="16" viewBox="0 0 20 16" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M2 0H8L10 2H18C19.1 2 20 2.9 20 4V14C20 15.1 19.1 16 18 16H2C0.9 16 0 15.1 0 14L0.01 2C0.01 0.9 0.9 0 2 0ZM9.17 4L7.17 2H2V14H18V4H9.17Z"
      />
    </svg>
  );
}
