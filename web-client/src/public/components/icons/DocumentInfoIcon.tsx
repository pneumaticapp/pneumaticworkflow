/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TDocumentInfoIconProps = React.SVGAttributes<SVGElement>;

export function DocumentInfoIcon({ fill = '#FEC336', ...restProps }: TDocumentInfoIconProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...restProps} >
      <path fillRule="evenodd" clipRule="evenodd" d="M6 1C3.79086 1 2 2.79086 2 5V15C2 17.2091 3.79086 19 6 19H14C16.2091 19 18 17.2091 18 15V9L10 1H6ZM6 3L9 3V8C9 9.10457 9.89543 10 11 10H16V15C16 16.1046 15.1046 17 14 17H6C4.89543 17 4 16.1046 4 15V5C4 3.89543 4.89543 3 6 3Z" />
    </svg>
  );
}
