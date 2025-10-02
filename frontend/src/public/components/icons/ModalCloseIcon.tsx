/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

interface IThinCloseIconProps extends Pick<React.SVGProps<SVGSVGElement>, 'className' | 'fill' | 'onClick'> {
  size?: number;
}

export function ModalCloseIcon({
  fill = 'currentColor',
  size = 10,
  // tslint:disable-next-line: trailing-comma
  ...restProps
}: IThinCloseIconProps) {

  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill={fill}
      {...restProps}
    >
      <path d="M5.27934 6.6281C4.90689 6.25565 4.90689 5.65179 5.27934 5.27934C5.65179 4.90689 6.25565 4.90689 6.6281 5.27934L14.7207 13.3719C15.0931 13.7444 15.0931 14.3482 14.7207 14.7207C14.3482 15.0931 13.7444 15.0931 13.3719 14.7207L5.27934 6.6281Z"/>
      <path d="M14.7207 6.6281C15.0931 6.25565 15.0931 5.65179 14.7207 5.27934C14.3482 4.90689 13.7444 4.90689 13.3719 5.27934L5.27934 13.3719C4.90689 13.7444 4.90689 14.3482 5.27934 14.7207C5.65179 15.0931 6.25565 15.0931 6.6281 14.7207L14.7207 6.6281Z"/>
    </svg>
  );
}
