/* eslint-disable max-len */
import React, { SVGAttributes } from 'react';

export function CircleWithArrowRightIcon({ fill = 'currentColor', ...rest }: SVGAttributes<SVGElement>) {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" {...rest}>
      <circle cx="16" cy="16" r="15.5" stroke={fill} />
      <path
        fill={fill}
        d="M19.53 18.848C19.2217 19.0407 18.8332 19.0509 18.5152 18.8746C18.1973 18.6984 18 18.3635 18 18V17.0001H10C9.44772 17.0001 9 16.5524 9 16.0001C9 15.4478 9.44772 15.0001 10 15.0001H18V14C18 13.6365 18.1973 13.3016 18.5152 13.1254C18.8332 12.9491 19.2217 12.9593 19.53 13.152L22.53 15.152C22.8224 15.3347 23 15.6552 23 16C23 16.3448 22.8224 16.6653 22.53 16.848L19.53 18.848Z"
      />
    </svg>
  );
}
