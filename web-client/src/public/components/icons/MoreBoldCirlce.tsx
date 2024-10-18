/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export function MoreBoldCirlce({ fill = 'currentColor', ...rest }: React.SVGAttributes<SVGElement>) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <circle cx="10" cy="10" r="9" />
      <path fillRule="evenodd" clipRule="evenodd" d="M6.29289 8.29289C6.68342 7.90237 7.31658 7.90237 7.70711 8.29289L10 10.5858L12.2929 8.29289C12.6834 7.90237 13.3166 7.90237 13.7071 8.29289C14.0976 8.68342 14.0976 9.31658 13.7071 9.70711L10.7071 12.7071C10.3166 13.0976 9.68342 13.0976 9.29289 12.7071L6.29289 9.70711C5.90237 9.31658 5.90237 8.68342 6.29289 8.29289Z" fill="white" />
    </svg>
  );
}
