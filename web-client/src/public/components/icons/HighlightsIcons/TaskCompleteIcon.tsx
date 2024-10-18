/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { TIconSize } from '../../../types/common';

export interface ITaskCompleteIconProps extends React.SVGAttributes<SVGElement> {
  size?: TIconSize;
}

export function TaskCompleteIcon({ fill = '#5fad56', size = 'lg', ...rest }: ITaskCompleteIconProps) {
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
        fill="#5fad56"
      />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M25.3379 12.5134C26.1589 13.2523 26.2255 14.5169 25.4866 15.3379L17.4866 25.3379C17.1195 25.7458 16.6011 25.9849 16.0526 25.9993C15.5041 26.0137 14.9738 25.8022 14.5858 25.4142L10.5858 21.4142C9.80474 20.6332 9.80474 19.3669 10.5858 18.5858C11.3668 17.8048 12.6332 17.8048 13.4142 18.5858L15.9236 21.0952L22.5134 12.6621C23.2523 11.8411 24.5169 11.7745 25.3379 12.5134Z"
        fill="#5fad56"
      />
    </svg>
  );

  const smallIcon = (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10ZM13.7433 8.66897C14.1127 8.25846 14.0795 7.62617 13.669 7.25671C13.2584 6.88726 12.6262 6.92053 12.2567 7.33104L8.9618 11.5476L7.7071 10.2929C7.31658 9.90237 6.68342 9.90237 6.29289 10.2929C5.90237 10.6834 5.90237 11.3166 6.29289 11.7071L8.29289 13.7071C8.48688 13.9011 8.75204 14.0069 9.02629 13.9997C9.30053 13.9924 9.55977 13.8729 9.74329 13.669L13.7433 8.66897Z"/>
    </svg>
  );

  const ICON_SIZE_MAP = {
    ['lg']: largeIcon,
    ['sm']: smallIcon,
  };

  return ICON_SIZE_MAP[size];
}
