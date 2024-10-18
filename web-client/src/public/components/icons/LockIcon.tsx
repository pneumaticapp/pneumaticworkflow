import * as React from 'react';

export const LockIcon = ({ fill = 'currentColor', ...rest }: React.SVGAttributes<SVGElement>) => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" {...rest}>
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M13.9951 5.80036C13.8911 3.68397 12.1422 2 10 2C7.79086 2 6 3.79086 6 6V8C4 8 3 9.69378 3 11V15C3 16.6569 4.34315
        18 6 18H14C15.6569 18 17 16.6569 17 15V11C17 9.69412 16 8 13.9951 8L14 6L13.9951 5.80036ZM8 8H12V6C12 4.94564 11.1841
        4.08183 10.1493 4.00549L10 4C8.89543 4 8 4.89543 8 6V8ZM5 11C5 10.4477 5.44772 10 6 10H14C14.5523 10 15 10.4477 15 11V15C15
        15.5523 14.5523 16 14 16H6C5.44772 16 5 15.5523 5 15V11Z"
      fill={fill}
    />
    <path
      d="M11 13C11 13.5523 10.5523 14 10 14C9.44772 14 9 13.5523 9 13C9 12.4477 9.44772 12 10 12C10.5523 12 11 12.4477 11 13Z"
      fill={fill}
    />
  </svg>
);
