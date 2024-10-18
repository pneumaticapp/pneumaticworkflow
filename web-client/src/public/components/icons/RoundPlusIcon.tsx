/* eslint-disable max-len */
import * as React from 'react';

export interface IRoundPlusIconProps extends React.SVGAttributes<SVGElement> { }

export function RoundPlusIcon({ fill = 'currentColor', ...rest }: IRoundPlusIconProps) {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest} >
      <path fillRule="evenodd" clipRule="evenodd" d="M20 6C12.268 6 6 12.268 6 20C6 27.732 12.268 34 20 34C27.732 34 34 27.732 34 20C34 12.268 27.732 6 20 6ZM2 20C2 10.0589 10.0589 2 20 2C29.9411 2 38 10.0589 38 20C38 29.9411 29.9411 38 20 38C10.0589 38 2 29.9411 2 20Z" />
      <path d="M12 20C12 18.8954 12.8954 18 14 18H26C27.1046 18 28 18.8954 28 20C28 21.1046 27.1046 22 26 22H14C12.8954 22 12 21.1046 12 20Z" />
      <path d="M20 12C21.1046 12 22 12.8954 22 14V26C22 27.1046 21.1046 28 20 28C18.8954 28 18 27.1046 18 26L18 14C18 12.8954 18.8954 12 20 12Z" />
    </svg>
  );
}
