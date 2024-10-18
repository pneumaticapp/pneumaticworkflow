/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { TIconSize } from '../../../types/common';

export interface ITaskReturnIconProps extends React.SVGAttributes<SVGElement> {
  size?: TIconSize;
}

export function TaskReturnIcon({ fill = '#e53d00', size = 'lg', ...rest }: ITaskReturnIconProps) {
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
        fill="#e53d00"
      />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M17.1413 12.2507C16.6114 11.8983 15.9638 11.9187 15.45 12.304L10.7833 16.304C10.296 16.6695 10 17.3104 10 18C10 18.6896 10.296 19.3305 10.7833 19.696L15.45 23.696C15.9638 24.0813 16.6114 24.1017 17.1413 23.7493C17.6712 23.3968 18 22.7271 18 22V14C18 13.273 17.6712 12.6032 17.1413 12.2507Z"
        fill="#e53d00"
      />
      <path
        d="M20 14C20 12.8954 20.8954 12 22 12C23.1046 12 24 12.8954 24 14V22C24 23.1046 23.1046 24 22 24C20.8954 24 20 23.1046 20 22V14Z"
        fill="#e53d00"
      />
    </svg>
  );

  const smallIcon = (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M10 1C5.02944 1 1 5.02944 1 10C1 14.9706 5.02944 19 10 19C14.9706 19 19 14.9706 19 10C19 5.02944 14.9706 1 10 1ZM8.725 7.152C8.98189 6.95933 9.30568 6.94913 9.57064 7.12536C9.8356 7.30158 10 7.63648 10 8V12C10 12.3635 9.8356 12.6984 9.57064 12.8746C9.30568 13.0509 8.98189 13.0407 8.725 12.848L6.39167 10.848C6.14802 10.6653 6 10.3448 6 10C6 9.65521 6.14802 9.33474 6.39167 9.152L8.725 7.152ZM12 7C11.4477 7 11 7.44772 11 8V12C11 12.5523 11.4477 13 12 13C12.5523 13 13 12.5523 13 12V8C13 7.44772 12.5523 7 12 7Z"/>
    </svg>

  );

  const ICON_SIZE_MAP = {
    ['lg']: largeIcon,
    ['sm']: smallIcon,
  };

  return ICON_SIZE_MAP[size];
}
