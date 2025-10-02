import React, { SVGAttributes } from 'react';

export type TNotesIconProps = SVGAttributes<SVGElement>;

export function NotesIcon({ fill = 'currentColor', ...rest }: TNotesIconProps) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path d="M8 7V9L11 9V17H13V9L16 9V7H8Z" fill={fill} />
      <path d="M3 11L9 11.01V13H3V11Z" fill={fill} />
      <path d="M15 11L21 11.01V13H15V11Z" fill={fill} />
    </svg>
  );
}
