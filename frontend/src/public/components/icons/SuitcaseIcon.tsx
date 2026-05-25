/* eslint-disable max-len */
import * as React from 'react';

export type TSuitcaseIconProps = React.SVGAttributes<SVGElement>;

export function SuitcaseIcon({ fill = 'currentColor', ...rest }: TSuitcaseIconProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M9 2H11C12.5977 2 13.9037 3.24892 13.9949 4.82373L14 5V6H15C16.6569 6 18 7.34315 18 9V15C18 16.6569 16.6569 18 15 18H5C3.34315 18 2 16.6569 2 15V9C2 7.34315 3.34315 6 5 6H6V5C6 3.40232 7.24892 2.09634 8.82373 2.00509L9 2ZM16 14H4V15C4 15.5523 4.44772 16 5 16H15C15.5523 16 16 15.5523 16 15V14ZM15 8H5C4.44772 8 4 8.44772 4 9V12H16V9C16 8.44772 15.5523 8 15 8ZM11 4H9C8.48716 4 8.06449 4.38604 8.00673 4.88338L8 5V6H12V5C12 4.48716 11.614 4.06449 11.1166 4.00673L11 4Z"
        fill={fill}
      />
    </svg>
  );
}
