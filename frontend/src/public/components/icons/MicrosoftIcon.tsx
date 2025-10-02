import * as React from 'react';

interface IMicrosoftIconProps {
  fill?: string;
  className?: string;
}

export const MicrosoftIcon = ({ fill = 'currentColor', ...rest }: IMicrosoftIconProps) => (
  <svg width="19" height="18" viewBox="0 0 19 18" fill={fill} {...rest}>
    <path d="M8.5 0H0.5V8H8.5V0Z" />
    <path d="M8.5 10H0.5V18H8.5V10Z" />
    <path d="M10.5 0H18.5V8H10.5V0Z" />
    <path d="M18.5 10H10.5V18H18.5V10Z" />
  </svg>
);
