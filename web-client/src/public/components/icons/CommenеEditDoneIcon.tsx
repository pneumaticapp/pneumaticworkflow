/* eslint-disable max-len */
import * as React from 'react';

export type TCommenеEditDoneIconProps = React.SVGAttributes<SVGElement>;

export function CommenеEditDoneIcon({ fill = 'currentColor', ...restProps }: TCommenеEditDoneIconProps) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...restProps}>
      <path
        d="M8.72727 16.0746L4.43182 11.6866L3 13.1493L8.72727 19L21 6.46269L19.5682 5L8.72727 16.0746Z"
        fill={fill}
      />
    </svg>
  );
}
