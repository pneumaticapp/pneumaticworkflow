/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export function SmallArrow({ fill = 'currentColor', ...rest }: React.SVGAttributes<SVGElement>) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M13.8329 7.61828C14.0678 7.99982 14.0542 8.46608 13.7973 8.836L11.1307 12.436C10.887 12.7869 10.4597 13 10 13C9.54028 13 9.11299 12.7869 8.86934 12.436L6.20267 8.836C5.94578 8.46608 5.93218 7.99982 6.16714 7.61828C6.40211 7.23673 6.84863 7 7.33333 7H12.6667C13.1514 7 13.5979 7.23673 13.8329 7.61828Z" />
    </svg>
  );
}
