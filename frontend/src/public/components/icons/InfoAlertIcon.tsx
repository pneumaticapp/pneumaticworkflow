/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TInfoAlertIconProps = React.SVGAttributes<SVGElement>;

export function InfoAlertIcon({ fill = 'currentColor', ...rest }: TInfoAlertIconProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M10 1C5.02944 1 1 5.02944 1 10C1 14.9706 5.02944 19 10 19C14.9706 19 19 14.9706 19 10C19 5.02944 14.9706 1 10 1ZM10 8C10.8284 8 11.5 7.32843 11.5 6.5C11.5 5.67157 10.8284 5 10 5C9.17157 5 8.5 5.67157 8.5 6.5C8.5 7.32843 9.17157 8 10 8ZM11 10C11 9.44772 10.5523 9 10 9H9C8.44772 9 8 9.44772 8 10C8 10.5523 8.44772 11 9 11V13C8.44772 13 8 13.4477 8 14C8 14.5523 8.44772 15 9 15H11C11.5523 15 12 14.5523 12 14C12 13.4477 11.5523 13 11 13V10Z" />
    </svg>
  );
}
