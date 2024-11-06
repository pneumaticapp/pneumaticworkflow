/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TTrashIconProps = React.SVGAttributes<SVGElement>;

export const TrashIcon = ({ fill = 'currentColor', ...rest }: TTrashIconProps) => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest} >
    <path fillRule="evenodd" clipRule="evenodd" d="M9 2H11C12.1046 2 13 2.89543 13 4H16C17.1046 4 18 4.89543 18 6V7C18 8.10457 17.1046 9 16 9H15.9199L15 16C15 17.1046 14.1046 18 13 18H7C5.89543 18 5 17.1046 5.00345 16.083L4.07987 9H4C2.89543 9 2 8.10457 2 7V6C2 4.89543 2.89543 4 4 4H7C7 2.89543 7.89543 2 9 2ZM4 6H16V7H4V6ZM6.08649 9H13.9132L13.0035 15.917L13 16H7L6.08649 9Z" />
  </svg>
);
