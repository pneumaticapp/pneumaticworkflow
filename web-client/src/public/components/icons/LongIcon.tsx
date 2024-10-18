/* eslint-disable max-len */
import * as React from 'react';

export type TLongIconProps = React.SVGAttributes<SVGElement>;

export function LongIcon({ fill = 'currentColor', ...rest }: TLongIconProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M6.48462 12.8746C6.16666 13.0509 5.77812 13.0407 5.46985 12.848L2.46985 10.848C2.17747 10.6653 1.99985 10.3448 1.99985 10C1.99985 9.65521 2.17747 9.33474 2.46985 9.152L5.46985 7.152C5.77812 6.95933 6.16666 6.94913 6.48462 7.12536C6.80257 7.30158 6.99985 7.63647 6.99985 8V12C6.99985 12.3635 6.80257 12.6984 6.48462 12.8746Z"
      />
      <path d="M4.99985 11C4.44756 11 3.99985 10.5523 3.99985 10C3.99985 9.44772 4.44756 9 4.99985 9L16.9998 9C17.5521 9 17.9998 9.44771 17.9998 10C17.9998 10.5523 17.5521 11 16.9998 11L4.99985 11Z" />
    </svg>
  );
}
