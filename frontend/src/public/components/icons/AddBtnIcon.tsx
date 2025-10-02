/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export interface IAddBtnIconProps extends React.SVGAttributes<SVGElement> {
  background?: string;
  size?: number;
}

const DEFAULT_SIZE = 40;

export function AddBtnIcon({fill = 'currentColor', size = 40, background = '#FEC336', ...rest}: IAddBtnIconProps) {
  const shouldAddStyle = size !== DEFAULT_SIZE;
  const pathProps = Object.assign(
    {fill},
    shouldAddStyle && {style: {transform: `scale(calc(${size} / ${DEFAULT_SIZE}))`}},
  );

  if (size !== 32) {
    return (
      <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox={`0 0 ${size} ${size}`} {...rest}>
        <circle cx={size / 2} cy={size / 2} r={size / 2} fill={background}/>
        <path d="M24.6663 20.6667H20.6663V24.6667H19.333V20.6667H15.333V19.3334H19.333V15.3334H20.6663V19.3334H24.6663V20.6667Z" {...pathProps} />
      </svg>
    );
  }

  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox={`0 0 ${size} ${size}`} {...rest}>
      <circle cx={size / 2} cy={size / 2} r={size / 2} fill={background}/>
      <path d="M20.6663 16.6667H16.6663V20.6667H15.333V16.6667H11.333V15.3334H15.333V11.3334H16.6663V15.3334H20.6663V16.6667Z" fill="#262522" />
    </svg>
  );
}
