/* prettier-ignore */
import * as React from 'react';

export const PlusCircleIcon = ({
  fill = 'currentColor',
  // tslint:disable-next-line: trailing-comma
  ...restProps
}: React.SVGProps<SVGSVGElement>) => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" {...restProps}>
    <circle cx="10" cy="10" r="9" fill="var(--pneumatic-color-white)" />
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M10 19C14.9706 19 19 14.9706 19 10C19 5.02944 14.9706 1 10 1C5.02944 1 1 5.02944 1 10C1 14.9706 5.02944 19 10 19ZM10 17C13.866 17 17 13.866 17 10C17 6.13401 13.866 3 10 3C6.13401 3 3 6.13401 3 10C3 13.866 6.13401 17 10 17Z"
      fill={fill}
    />
    <path
      d="M7 11C6.47915 11 6 10.5208 6 10C6 9.47915 6.47915 9 7 9H13C13.5208 9 14 9.47915 14 10C14 10.5208 13.5208 11 13 11H7Z"
      fill={fill}
    />
    <path
      d="M11 7C11 6.47915 10.5208 6 10 6C9.47915 6 9 6.47915 9 7V13C9 13.5208 9.47915 14 10 14C10.5208 14 11 13.5208 11 13V7Z"
      fill={fill}
    />
  </svg>
);
