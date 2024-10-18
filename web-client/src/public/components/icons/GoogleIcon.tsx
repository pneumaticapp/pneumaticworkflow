/* eslint-disable max-len */
import * as React from 'react';

interface IGoogleIconProps {
  fill?: string;
  className?: string;
}

export const GoogleIcon = ({ fill = 'currentColor', ...rest }: IGoogleIconProps) => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill={fill} {...rest}>
    <path d="M9.11932 10.8281C9.11932 10.8281 12.6103 10.8281 14.0352 10.8281C13.2515 13.1484 12.0404 14.4141 9.11932 14.4141C6.12705 14.4141 3.77597 12.0234 3.77597 9.07031C3.77597 6.11719 6.12705 3.72656 9.11932 3.72656C10.6867 3.72656 11.7554 4.28906 12.6816 5.0625C13.4653 4.28906 13.394 4.21875 15.2464 2.46094C13.679 0.914062 11.4704 0 9.11932 0C4.06095 0 0 4.00781 0 9C0 13.9922 4.06095 18 9.11932 18C16.6713 18 18.5236 11.5312 17.8824 7.17188H9.11932V10.8281Z" />
  </svg>
);
