/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { TIconSize } from '../../../types/common';

export interface IProcessStartIconProps extends React.SVGAttributes<SVGElement> {
  size?: TIconSize;
}

export function ProcessStartIcon({ fill = '#39a0ed', size = 'lg', ...rest }: IProcessStartIconProps) {
  const largeIcon = (
    <svg
      width="36"
      height="36"
      viewBox="0 0 36 36"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      {...rest}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M18 4C10.268 4 4 10.268 4 18C4 25.732 10.268 32 18 32C25.732 32 32 25.732 32 18C32 10.268 25.732 4 18 4ZM0 18C0 8.05887 8.05887 0 18 0C27.9411 0 36 8.05887 36 18C36 27.9411 27.9411 36 18 36C8.05887 36 0 27.9411 0 18Z"
        fill="#39a0ed"
      />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M15.0305 12.2507C15.6664 11.8983 16.4435 11.9187 17.06 12.304L23.06 16.304C23.6448 16.6695 24 17.3104 24 18C24 18.6896 23.6448 19.3305 23.06 19.696L17.06 23.696C16.4435 24.0813 15.6664 24.1017 15.0305 23.7493C14.3946 23.3968 14 22.7271 14 22V14C14 13.2729 14.3946 12.6032 15.0305 12.2507Z"
        fill="#39a0ed"
      />
    </svg>
  );

  const smallIcon = (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10ZM9.53 7.152C9.22173 6.95933 8.83319 6.94913 8.51523 7.12536C8.19728 7.30158 8 7.63648 8 8V12C8 12.3635 8.19728 12.6984 8.51523 12.8746C8.83319 13.0509 9.22173 13.0407 9.53 12.848L12.53 10.848C12.8224 10.6653 13 10.3448 13 10C13 9.65521 12.8224 9.33474 12.53 9.152L9.53 7.152Z"/>
    </svg>
  );

  const ICON_SIZE_MAP = {
    ['lg']: largeIcon,
    ['sm']: smallIcon,
  };

  return ICON_SIZE_MAP[size];
}
