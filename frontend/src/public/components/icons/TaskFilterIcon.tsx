/* eslint-disable max-len */
import React from 'react';

export function TaskFilterIcon({ className }: React.SVGAttributes<SVGElement>) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M15 2C16.6569 2 18 3.34315 18 5V15C18 16.6569 16.6569 18 15 18H5C3.34315 18 2 16.6569 2 15V5C2 3.34315 3.34315 2 5 2H15ZM4 15C4 15.5523 4.44772 16 5 16H15C15.5523 16 16 15.5523 16 15V11H13.874C13.4464 12.6613 11.9783 13.905 10.2058 13.9948L10 14C8.20519 14 6.68648 12.8179 6.17993 11.1898L6.12602 11H4V15ZM15 4H5C4.44772 4 4 4.44772 4 5V9H7C7.51284 9 7.93551 9.38604 7.99327 9.88338L8 10C8 11.1046 8.89543 12 10 12C11.0544 12 11.9182 11.1841 11.9945 10.1493L12.0067 9.88338C12.0601 9.4243 12.4243 9.06005 12.8834 9.00673L13 9H16V5C16 4.44772 15.5523 4 15 4Z"
        fill="#262522"
      />
    </svg>
  );
}
