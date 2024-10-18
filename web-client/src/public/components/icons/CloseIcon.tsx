/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export interface ICloseIconProps extends React.SVGAttributes<SVGElement> {
  fill?: string;
  size?: number;
}

export const CloseIcon = ({fill = '#62625F', size = 20, ...rest}: ICloseIconProps) => {
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M10 0C4.47 0 0 4.47 0 10C0 15.53 4.47 20 10 20C15.53 20 20 15.53 20 10C20 4.47 15.53 0 10 0ZM12.59 6L10 8.59L7.41 6L6 7.41L8.59 10L6 12.59L7.41 14L10 11.41L12.59 14L14 12.59L11.41 10L14 7.41L12.59 6ZM2 10C2 14.41 5.59 18 10 18C14.41 18 18 14.41 18 10C18 5.59 14.41 2 10 2C5.59 2 2 5.59 2 10Z" fill={fill}/>
    </svg>

  );
};
