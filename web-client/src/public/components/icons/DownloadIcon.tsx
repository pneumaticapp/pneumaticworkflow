/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TDownloadIconProps = React.SVGAttributes<SVGElement>;

export function DownloadIcon({ fill = 'currentColor', ...rest }: TDownloadIconProps) {
  return (
    <svg width="14" height="16" viewBox="0 0 14 16" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M14 5.64706H10V0H4V5.64706H0L7 12.2353L14 5.64706ZM6.00008 7.52963V1.88258H8.00008V7.52963H9.17008L7.00008 9.57199L4.83008 7.52963H6.00008ZM14 15.9998V14.1174H0V15.9998H14Z"
      />
    </svg>
  );
}
