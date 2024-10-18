/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TCreditCardIcon = React.SVGAttributes<SVGElement>;

export function CreditCardIcon({ fill = 'currentColor', ...rest }: TCreditCardIcon) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M16 3C17.6569 3 19 4.34315 19 6V14C19 15.6569 17.6569 17 16 17H4C2.34315 17 1 15.6569 1 14V6C1 4.34315 2.34315 3 4 3H16ZM3 9V14C3 14.5523 3.44772 15 4 15H16C16.5523 15 17 14.5523 17 14V9H3ZM3 7H17V6C17 5.44772 16.5523 5 16 5H4C3.44772 5 3 5.44772 3 6V7Z"/>
    </svg>
  );
}
