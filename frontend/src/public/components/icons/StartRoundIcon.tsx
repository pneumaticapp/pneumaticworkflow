/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export type TStartRoundIconProps = React.SVGAttributes<SVGElement>;

export const StartRoundIcon = ({ fill = 'currentColor', ...rest }: TStartRoundIconProps) => (
  <svg width="40" height="40" viewBox="0 0 40 40" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest} >
    <path fillRule="evenodd" clipRule="evenodd" d="M20 6C12.268 6 6 12.268 6 20C6 27.732 12.268 34 20 34C27.732 34 34 27.732 34 20C34 12.268 27.732 6 20 6ZM2 20C2 10.0589 10.0589 2 20 2C29.9411 2 38 10.0589 38 20C38 29.9411 29.9411 38 20 38C10.0589 38 2 29.9411 2 20Z" />
    <path fillRule="evenodd" clipRule="evenodd" d="M17.0305 14.2507C17.6664 13.8983 18.4435 13.9187 19.06 14.304L25.06 18.304C25.6448 18.6695 26 19.3104 26 20C26 20.6896 25.6448 21.3305 25.06 21.696L19.06 25.696C18.4435 26.0813 17.6664 26.1017 17.0305 25.7493C16.3946 25.3968 16 24.7271 16 24V16C16 15.2729 16.3946 14.6032 17.0305 14.2507Z" />
  </svg>
);
