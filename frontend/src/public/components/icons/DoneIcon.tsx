/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { EIconSize } from '../../types/common';

export interface IDoneIconProps extends React.SVGAttributes<SVGElement> {
  iconSize?: EIconSize;
}

export function DoneIcon({
  fill = '#24d5a1',
  width = '24',
  height = '20',
  iconSize = EIconSize.Desktop,
  // tslint:disable-next-line: trailing-comma
  ...rest
}: IDoneIconProps) {
  if (iconSize === EIconSize.Desktop) {
    return (
      <svg width={width} height={height} viewBox="0 0 24 20" fill="none" xmlns="http://www.w3.org/2000/svg" {...rest}>
        <path
          d="M7.63636 15.4329L1.90909 9.58211L0 11.5324L7.63636 19.3334L24 2.61694L22.0909 0.666687L7.63636 15.4329Z"
          fill={fill}
        />
      </svg>
    );
  }

  return (
    <svg width="12" height="10" viewBox="0 0 12 10" fill="none" xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path
        d="M3.81818 7.71646L0.954545 4.79109L0 5.76621L3.81818 9.66671L12 1.3085L11.0455 0.333374L3.81818 7.71646Z"
        fill={fill}
      />
    </svg>
  );
}
