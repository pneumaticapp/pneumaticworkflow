/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TClockIcon = React.SVGAttributes<SVGElement>;

export function ClockIcon({ fill = 'currentColor', ...rest }: TClockIcon) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path d="M9 6C9 5.44772 9.44771 5 10 5C10.5523 5 11 5.44772 11 6V9.46048L13.4998 11.0692C13.9781 11.3549 14.142 11.9877 13.8659 12.4825C13.5897 12.9774 12.9782 13.1469 12.4999 12.8612L9.50015 10.9308C9.17424 10.7361 8.99432 10.3803 9.00014 10.0167C9.00005 10.0112 9 10.0056 9 10V6Z" />
      <path fillRule="evenodd" clipRule="evenodd" d="M10 1C5.02944 1 1 5.02944 1 10C1 14.9706 5.02944 19 10 19C14.9706 19 19 14.9706 19 10C19 5.02944 14.9706 1 10 1ZM10 17C13.866 17 17 13.866 17 10C17 6.13401 13.866 3 10 3C6.13401 3 3 6.13401 3 10C3 13.866 6.13401 17 10 17Z" />
    </svg>
  );
}
