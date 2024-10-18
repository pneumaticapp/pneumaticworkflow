/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TFilterIconProps = React.SVGAttributes<SVGElement>;

export function FilterIcon(props: TFilterIconProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" {...props} >
      <path fillRule="evenodd" clipRule="evenodd" d="M6.99999 10.3205L2.18626 3.58124C1.7135 2.91937 2.18662 2 2.99999 2H17C17.8134 2 18.2865 2.91937 17.8137 3.58124L13 10.3205V15C13 15.3788 12.786 15.725 12.4472 15.8944L8.44721 17.8944C7.78231 18.2269 6.99999 17.7434 6.99999 17V10.3205ZM4.94318 4L8.81373 9.41876C8.93487 9.58836 8.99999 9.79158 8.99999 10V15.382L11 14.382V10C11 9.79158 11.0651 9.58836 11.1863 9.41876L15.0568 4H4.94318Z" fill="#262522" />
    </svg>
  );
}
