/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { TIconSize } from '../../../types/common';

export interface IProcessFinishIconProps extends React.SVGAttributes<SVGElement> {
  size?: TIconSize;
}

export function ProcessFinishIcon({ fill = '#5fad56', size = 'lg', ...rest }: IProcessFinishIconProps) {
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
        fill="#9046cf"
      />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12.5858 12.5858C13.3668 11.8047 14.6332 11.8047 15.4142 12.5858L23.4142 20.5858C24.1953 21.3668 24.1953 22.6332 23.4142 23.4142C22.6332 24.1953 21.3668 24.1953 20.5858 23.4142L12.5858 15.4142C11.8047 14.6332 11.8047 13.3668 12.5858 12.5858Z"
        fill="#9046cf"
      />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M23.4142 12.5858C22.6332 11.8047 21.3668 11.8047 20.5858 12.5858L12.5858 20.5858C11.8047 21.3668 11.8047 22.6332 12.5858 23.4142C13.3668 24.1953 14.6332 24.1953 15.4142 23.4142L23.4142 15.4142C24.1953 14.6332 24.1953 13.3668 23.4142 12.5858Z"
        fill="#9046cf"
      />
    </svg>
  );

  const smallIcon = (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M10 1C5.02944 1 1 5.02944 1 10C1 14.9706 5.02944 19 10 19C14.9706 19 19 14.9706 19 10C19 5.02944 14.9706 1 10 1ZM8.70711 7.29289C8.31658 6.90237 7.68342 6.90237 7.29289 7.29289C6.90237 7.68342 6.90237 8.31658 7.29289 8.70711L8.58579 10L7.29289 11.2929C6.90237 11.6834 6.90237 12.3166 7.29289 12.7071C7.68342 13.0976 8.31658 13.0976 8.70711 12.7071L10 11.4142L11.2929 12.7071C11.6834 13.0976 12.3166 13.0976 12.7071 12.7071C13.0976 12.3166 13.0976 11.6834 12.7071 11.2929L11.4142 10L12.7071 8.70711C13.0976 8.31658 13.0976 7.68342 12.7071 7.29289C12.3166 6.90237 11.6834 6.90237 11.2929 7.29289L10 8.58579L8.70711 7.29289Z"/>
    </svg>
  );

  const ICON_SIZE_MAP = {
    ['lg']: largeIcon,
    ['sm']: smallIcon,
  };

  return ICON_SIZE_MAP[size];
}
