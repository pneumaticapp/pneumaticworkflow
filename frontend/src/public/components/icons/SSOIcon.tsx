/* eslint-disable max-len */
import * as React from 'react';

interface ISSOIconProps {
  fill?: string;
  className?: string;
}

export const SSOIcon = ({ fill = 'currentColor', ...rest }: ISSOIconProps) => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...rest}>
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M17 8H18C19.1 8 20 8.9 20 10V20C20 21.1 19.1 22 18 22H6C4.9 22 4 21.1 4 20V10C4 8.9 4.9 8 6 8H7V7C7 4.24 9.24 2 12 2C14.76 2 17 4.24 17 7V8ZM12 4C10.34 4 9 5.34 9 7V8H15V7C15 5.34 13.66 4 12 4ZM6 20V10H18V20H6ZM14 15C14 16.1 13.1 17 12 17C10.9 17 10 16.1 10 15C10 13.9 10.9 13 12 13C13.1 13 14 13.9 14 15Z"
      fill={fill}
    />
  </svg>
);
