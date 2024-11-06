/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export interface ISendIconProps extends React.SVGAttributes<SVGElement> {
  fill?: string;
  size?: number;
}

export const SendIcon = ({fill = '#B9B9B8', ...rest}: ISendIconProps) => {
  return (
    <svg width="20" height="18" viewBox="0 0 20 18" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M0 7L0.00952381 0L20 9L0.00952381 18L0 11L14.2857 9L0 7ZM1.91429 3.03L9.06667 6.25L1.90476 5.25L1.91429 3.03ZM9.05714 11.75L1.90476 14.97V12.75L9.05714 11.75Z"/>
    </svg>
  );
};
