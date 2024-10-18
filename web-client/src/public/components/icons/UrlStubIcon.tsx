/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export function UrlStubIcon({ fill = 'currentColor', ...rest }: React.SVGAttributes<SVGElement>) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M2.16667 2.16667V13.8333H13.8333V8H15.5V13.8333C15.5 14.75 14.75 15.5 13.8333 15.5H2.16667C1.24167 15.5 0.5 14.75 0.5 13.8333V2.16667C0.5 1.25 1.24167 0.5 2.16667 0.5H8V2.16667H2.16667ZM9.66667 2.16667V0.5H15.5V6.33333H13.8333V3.34167L5.64167 11.5333L4.46667 10.3583L12.6583 2.16667H9.66667Z"
        fill={fill}
      />
    </svg>
  );
}
