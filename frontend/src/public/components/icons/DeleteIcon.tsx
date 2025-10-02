/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TDeleteIconProps = React.SVGAttributes<SVGElement>;

export function DeleteIcon({ fill = 'currentColor', ...rest }: TDeleteIconProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest} >
      <path fillRule="evenodd" clipRule="evenodd" d="M10 1C5.02944 1 1 5.02944 1 10C1 14.9706 5.02944 19 10 19C14.9706 19 19 14.9706 19 10C19 5.02944 14.9706 1 10 1ZM10 17C13.866 17 17 13.866 17 10C17 6.13401 13.866 3 10 3C6.13401 3 3 6.13401 3 10C3 13.866 6.13401 17 10 17Z" />
      <path d="M13.694 12.2164C14.102 12.6244 14.102 13.286 13.694 13.694C13.286 14.102 12.6244 14.102 12.2164 13.694L6.30602 7.78361C5.89799 7.37559 5.89799 6.71405 6.30602 6.30602C6.71405 5.89799 7.37559 5.89799 7.78361 6.30602L13.694 12.2164Z" />
      <path d="M12.2164 6.30602C12.6244 5.89799 13.286 5.89799 13.694 6.30602C14.102 6.71405 14.102 7.37559 13.694 7.78361L7.78361 13.694C7.37559 14.102 6.71405 14.102 6.30602 13.694C5.89799 13.286 5.89799 12.6244 6.30602 12.2164L12.2164 6.30602Z" />
    </svg>
  );
}
