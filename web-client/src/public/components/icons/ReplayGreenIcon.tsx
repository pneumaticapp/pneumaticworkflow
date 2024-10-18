/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export interface IReplayGreenIconProps extends React.SVGAttributes<SVGElement> {}

export function ReplayIconGreen({ ...rest }: IReplayGreenIconProps) {
  return (
    <svg width="22" height="27" viewBox="0 0 22 27" fill="#24d5a1" xmlns="http://www.w3.org/2000/svg">
      <path d="M10.9998 5.33333V0L17.6665 6.66667L10.9998 13.3333V8C6.5865 8 2.99984 11.5867 2.99984 16C2.99984 20.4133 6.5865 24 10.9998 24C15.4132 24 18.9998 20.4133 18.9998 16H21.6665C21.6665 21.8933 16.8932 26.6667 10.9998 26.6667C5.1065 26.6667 0.333172 21.8933 0.333172 16C0.333172 10.1067 5.1065 5.33333 10.9998 5.33333Z" fill="#24d5a1" {...rest} />
    </svg>
  );
}
