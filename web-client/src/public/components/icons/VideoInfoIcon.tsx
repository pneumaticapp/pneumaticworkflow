/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TVideoInfoIconProps = React.SVGAttributes<SVGElement>;

export function VideoInfoIcon({ fill = '#FEC336', ...restProps }: TVideoInfoIconProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...restProps} >
      <path fillRule="evenodd" clipRule="evenodd" d="M9.53 7.152C9.22173 6.95933 8.83319 6.94913 8.51523 7.12536C8.19728 7.30158 8 7.63648 8 8V12C8 12.3635 8.19728 12.6984 8.51523 12.8746C8.83319 13.0509 9.22173 13.0407 9.53 12.848L12.53 10.848C12.8224 10.6653 13 10.3448 13 10C13 9.65521 12.8224 9.33474 12.53 9.152L9.53 7.152Z" />
      <path fillRule="evenodd" clipRule="evenodd" d="M10 19C14.9706 19 19 14.9706 19 10C19 5.02944 14.9706 1 10 1C5.02944 1 1 5.02944 1 10C1 14.9706 5.02944 19 10 19ZM10 17C13.866 17 17 13.866 17 10C17 6.13401 13.866 3 10 3C6.13401 3 3 6.13401 3 10C3 13.866 6.13401 17 10 17Z" />
    </svg>
  );
}
