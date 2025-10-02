/* eslint-disable max-len */
import * as React from 'react';

export function ReturnIcon({ fill = 'currentColor', ...rest }: React.SVGAttributes<SVGElement>) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path d="M5.47 12.848C5.77827 13.0407 6.16681 13.0509 6.48477 12.8746C6.80272 12.6984 7 12.3635 7 12V11.0001H17C17.5523 11.0001 18 10.5524 18 10.0001C18 9.44784 17.5523 9.00012 17 9.00012H7V8C7 7.63647 6.80272 7.30158 6.48477 7.12536C6.16681 6.94913 5.77827 6.95933 5.47 7.152L2.47 9.152C2.17762 9.33474 2 9.65521 2 10C2 10.3448 2.17762 10.6653 2.47 10.848L5.47 12.848Z" />
    </svg>
  );
}
