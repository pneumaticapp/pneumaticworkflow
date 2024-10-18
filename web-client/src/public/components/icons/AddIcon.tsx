/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TAddIconProps = React.SVGAttributes<SVGElement>;

export function AddIcon({fill= 'currentColor', width= 16, height= 16, ...rest }: TAddIconProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={width} height={height}
      viewBox={`0 0 ${width} ${height}`}
      fill={fill}
      {...rest}
    >
      <path
        d="M12.6663 8.66667H8.66634V12.6667H7.33301V8.66667H3.33301V7.33333H7.33301V3.33333H8.66634V7.33333H12.6663V8.66667Z"
      />
    </svg>
  );
}
