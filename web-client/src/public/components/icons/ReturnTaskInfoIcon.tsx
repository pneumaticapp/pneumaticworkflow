/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TReturnTaskInfoIconProps = React.SVGAttributes<SVGElement>;

export function ReturnTaskInfoIcon({ fill = '#E53D00', ...rest }: TReturnTaskInfoIconProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M10 1C5.02944 1 1 5.02944 1 10C1 14.9706 5.02944 19 10 19C14.9706 19 19 14.9706 19 10C19 5.02944 14.9706 1 10 1ZM8.725 7.152C8.98189 6.95933 9.30568 6.94913 9.57064 7.12536C9.8356 7.30158 10 7.63648 10 8V12C10 12.3635 9.8356 12.6984 9.57064 12.8746C9.30568 13.0509 8.98189 13.0407 8.725 12.848L6.39167 10.848C6.14802 10.6653 6 10.3448 6 10C6 9.65521 6.14802 9.33474 6.39167 9.152L8.725 7.152ZM12 7C11.4477 7 11 7.44772 11 8V12C11 12.5523 11.4477 13 12 13C12.5523 13 13 12.5523 13 12V8C13 7.44772 12.5523 7 12 7Z" />
    </svg>
  );
}
