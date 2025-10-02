/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TErrorBlockIconProps = React.SVGAttributes<SVGElement>;

export function ErrorBlockIcon(props: TErrorBlockIconProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path fillRule="evenodd" clipRule="evenodd" d="M10 2C14.4183 2 18 5.58172 18 10C18 14.4183 14.4183 18 10 18C5.58172 18 2 14.4183 2 10C2 5.58172 5.58172 2 10 2ZM14.8906 6.52332L6.52332 14.8906C7.50417 15.5892 8.70411 16 10 16C13.3137 16 16 13.3137 16 10C16 8.70411 15.5892 7.50417 14.8906 6.52332ZM10 4C6.68629 4 4 6.68629 4 10C4 11.2959 4.41083 12.4958 5.10935 13.4767L13.4767 5.10935C12.4958 4.41083 11.2959 4 10 4Z" fill="#F44336" />
    </svg>
  );
}
