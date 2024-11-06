/* eslint-disable max-len */
import * as React from 'react';

export type TArrowDownIcon = React.SVGAttributes<SVGElement>;

export function ArrowDownIcon({ fill = 'currentColor', ...rest }: TArrowDownIcon) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M12.8746 13.5152C13.0509 13.8332 13.0407 14.2217 12.848 14.53L10.848 17.53C10.6653 17.8224 10.3448 18 10 18C9.65521 18 9.33474 17.8224 9.152 17.53L7.152 14.53C6.95933 14.2217 6.94913 13.8332 7.12536 13.5152C7.30158 13.1973 7.63647 13 8 13H12C12.3635 13 12.6984 13.1973 12.8746 13.5152Z" />
      <path d="M11 15C11 15.5523 10.5523 16 10 16C9.44771 16 9 15.5523 9 15L9 3C9 2.44772 9.44772 2 10 2C10.5523 2 11 2.44772 11 3L11 15Z" />
    </svg>
  );
}
