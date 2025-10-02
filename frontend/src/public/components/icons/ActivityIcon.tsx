/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TActivityIconProps = React.SVGAttributes<SVGElement>;

export function ActivityIcon({ fill = 'currentColor', ...rest }: TActivityIconProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest} >
      <path fillRule="evenodd" clipRule="evenodd" d="M15 11C16.6569 11 18 12.3431 18 14V15C18 16.6569 16.6569 18 15 18H5C3.34315 18 2 16.6569 2 15V14C2 12.3431 3.34315 11 5 11H15ZM15 13H5C4.44772 13 4 13.4477 4 14V15C4 15.5523 4.44772 16 5 16H15C15.5523 16 16 15.5523 16 15V14C16 13.4477 15.5523 13 15 13ZM15 2C16.6569 2 18 3.34315 18 5V6C18 7.65685 16.6569 9 15 9H5C3.34315 9 2 7.65685 2 6V5C2 3.34315 3.34315 2 5 2H15ZM15 4H5C4.44772 4 4 4.44772 4 5V6C4 6.55228 4.44772 7 5 7H15C15.5523 7 16 6.55228 16 6V5C16 4.44772 15.5523 4 15 4Z" />
    </svg>
  );
}
