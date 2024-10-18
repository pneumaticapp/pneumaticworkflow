/* eslint-disable max-len */
import * as React from 'react';

export type TArrowUpIcon = React.SVGAttributes<SVGElement>;

export function ArrowUpIcon({ fill = 'currentColor', ...rest }: TArrowUpIcon) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M7.12536 6.48477C6.94913 6.16681 6.95933 5.77827 7.152 5.47L9.152 2.47C9.33474 2.17762 9.65521 2 10 2C10.3448 2 10.6653 2.17762 10.848 2.47L12.848 5.47C13.0407 5.77827 13.0509 6.16681 12.8746 6.48477C12.6984 6.80272 12.3635 7 12 7H8C7.63648 7 7.30158 6.80272 7.12536 6.48477Z" />
      <path d="M9 5C9 4.44772 9.44772 4 10 4C10.5523 4 11 4.44771 11 5V17C11 17.5523 10.5523 18 10 18C9.44772 18 9 17.5523 9 17V5Z" />
    </svg>
  );
}
