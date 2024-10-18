/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TBellIconProps = React.SVGAttributes<SVGElement>;

export function BellIcon({fill= 'currentColor'}: TBellIconProps) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={fill} xmlns="http://www.w3.org/2000/svg">
      <path fillRule="evenodd" clipRule="evenodd" d="M10.5 3.53488C10.5 2.68558 11.17 2 12 2C12.83 2 13.5 2.68558 13.5 3.53488V4.73209C16.64 5.42791 19 8.29302 19 11.7209V15.8605L21 17.907V18.9302H3V17.907L5 15.8605V11.7209C5 8.29302 7.36 5.42791 10.5 4.73209V3.53488ZM12 6.60465C14.76 6.60465 17 8.89674 17 11.7209V16.8837H7V11.7209C7 8.89674 9.24 6.60465 12 6.60465ZM10.01 19.9637C10.01 21.0893 10.9 22 12 22C13.1 22 13.99 21.0893 13.99 19.9637H10.01Z"/>
    </svg>

  );
}
