/* eslint-disable */
import React from 'react';

export function ImageFileIcon({ fill = '#FEC336', ...rest }: React.SVGAttributes<SVGElement>) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M13 0C14.6569 0 16 1.34315 16 3V13C16 14.6569 14.6569 16 13 16H3C1.34315 16 0 14.6569 0 13V3C0 1.34315 1.34315 0 3 0H13ZM13 2H3C2.44772 2 2 2.44772 2 3V10.697L4.18627 7.41876C4.50017 6.9793 5.09949 6.87371 5.54124 7.15898L5.64018 7.23178L10.7853 11.5193L14 5.745V3C14 2.44772 13.5523 2 13 2ZM4.5 6C5.32843 6 6 5.32843 6 4.5C6 3.67157 5.32843 3 4.5 3C3.67157 3 3 3.67157 3 4.5C3 5.32843 3.67157 6 4.5 6Z"
        fill={fill}
      />
    </svg>
  );
}
