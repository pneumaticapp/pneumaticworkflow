/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TNotesIconProps = React.SVGAttributes<SVGElement>;

export function NotesIcon({ fill = 'currentColor', ...rest }: TNotesIconProps) {
  return (
    <svg width="18" height="2" viewBox="0 0 18 2" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M18 0.0100002L0 0V2H18V0.0100002Z" />
    </svg>
  );
}
