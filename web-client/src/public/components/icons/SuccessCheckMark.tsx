/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TSuccessCheckMarkProps = React.SVGAttributes<SVGElement>;

export function SuccessCheckMark({ fill = 'currentColor', ...rest }: TSuccessCheckMarkProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" fill={fill}  {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M15.7072 5.29289C16.0977 5.68342 16.0977 6.31658 15.7072 6.70711L8.70717 13.7071C8.50218 13.9121 8.21833 14.018 7.92917 13.9975C7.64001 13.9769 7.37399 13.8319 7.20006 13.6L4.20006 9.6C3.86869 9.15817 3.95823 8.53137 4.40006 8.2C4.84189 7.86863 5.46869 7.95817 5.80006 8.4L8.10825 11.4776L14.293 5.29289C14.6835 4.90237 15.3166 4.90237 15.7072 5.29289Z" />
    </svg>
  );
}
