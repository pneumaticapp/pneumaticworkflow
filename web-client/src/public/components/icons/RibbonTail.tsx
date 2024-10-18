/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export interface IRibbonProps extends React.SVGAttributes<SVGElement> { }

export function RibbonTail({ fill = 'currentColor', ...rest }: IRibbonProps) {
  return (
    <svg width="40" height="24" viewBox="0 0 40 24" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path d="M38.0093 0H0V24H38.0093C39.5329 24 40.4664 22.3596 39.7601 21.0525C39.7004 20.9422 39.6385 20.8324 39.5899 20.7167L36.4729 13.2833C36.4244 13.1676 36.3625 13.0581 36.3033 12.9475C35.9872 12.3564 35.9872 11.6436 36.3033 11.0525C36.3625 10.9419 36.4244 10.8324 36.4729 10.7167L39.5899 3.28332C39.6385 3.16763 39.7004 3.05782 39.7601 2.94746C40.4664 1.64036 39.5329 0 38.0093 0Z" />
    </svg>
  );
}
