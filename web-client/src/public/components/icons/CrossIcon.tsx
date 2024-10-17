/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export interface ICrossIconProps extends React.SVGAttributes<SVGElement> {
  background?: string;
  size?: number;
}

const DEFAULT_SIZE = 32;

export function CrossIcon({fill = 'currentColor', size = 32, background = '#FEC336', ...rest}: ICrossIconProps) {
  const shouldAddStyle = size !== DEFAULT_SIZE;
  const pathProps = Object.assign(
    {fill},
    shouldAddStyle && {style: {transform: `scale(calc(${size} / ${DEFAULT_SIZE}))`}},
  );

  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox={`0 0 ${size} ${size}`} {...rest}>
      <circle cx={size / 2} cy={size / 2} r={size / 2} fill={background} />
      <path d="M9.66634 1.27331L8.72634 0.333313L4.99967 4.05998L1.27301 0.333313L0.333008 1.27331L4.05967 4.99998L0.333008 8.72665L1.27301 9.66665L4.99967 5.93998L8.72634 9.66665L9.66634 8.72665L5.93967 4.99998L9.66634 1.27331Z" {...pathProps} />
    </svg>
  );
}
