/* eslint-disable max-len */
import * as React from 'react';

export interface IRoundDocIconProps extends React.SVGAttributes<SVGElement> {}

export function RoundDocIcon({ fill = 'currentColor', ...rest }: IRoundDocIconProps) {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" {...rest}>
      <circle cx="20" cy="20" r="19.5" stroke={fill} />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M16 11C13.7909 11 12 12.7909 12 15V25C12 27.2091 13.7909 29 16 29H24C26.2091 29 28 27.2091 28 25V19L20 11H16ZM16 13L19 13V18C19 19.1046 19.8954 20 21 20H26V25C26 26.1046 25.1046 27 24 27H16C14.8954 27 14 26.1046 14 25V15C14 13.8954 14.8954 13 16 13Z"
        fill={fill}
      />
    </svg>
  );
}
