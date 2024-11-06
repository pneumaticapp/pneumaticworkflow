/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

interface IFilledHelpIconProps extends Pick<React.SVGProps<SVGSVGElement>, 'className' | 'fill'> {
  size?: number;
}

export function FilledHelpIcon({
  fill = '#fec336',
  // tslint:disable-next-line: trailing-comma
  ...restProps
}: IFilledHelpIconProps) {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill={fill} xmlns="http://www.w3.org/2000/svg">
      <path fillRule="evenodd" clipRule="evenodd" d="M9 0C4.02944 0 0 4.02944 0 9C0 13.9706 4.02944 18 9 18C13.9706 18 18 13.9706 18 9C18 4.02944 13.9706 0 9 0ZM9 7C9.82843 7 10.5 6.32843 10.5 5.5C10.5 4.67157 9.82843 4 9 4C8.17157 4 7.5 4.67157 7.5 5.5C7.5 6.32843 8.17157 7 9 7ZM10 9C10 8.44772 9.55228 8 9 8H8C7.44772 8 7 8.44772 7 9C7 9.55228 7.44772 10 8 10V12C7.44772 12 7 12.4477 7 13C7 13.5523 7.44772 14 8 14H10C10.5523 14 11 13.5523 11 13C11 12.4477 10.5523 12 10 12V9Z" />
    </svg>
  );
}
