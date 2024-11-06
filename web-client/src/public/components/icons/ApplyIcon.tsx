/* eslint-disable max-len */
import * as React from 'react';

export function ApplyIcon({ fill = 'currentColor', ...rest }: React.SVGAttributes<SVGElement>) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M10 19C14.9706 19 19 14.9706 19 10C19 5.02944 14.9706 1 10 1C5.02944 1 1 5.02944 1 10C1 14.9706 5.02944 19 10 19ZM10 17C13.866 17 17 13.866 17 10C17 6.13401 13.866 3 10 3C6.13401 3 3 6.13401 3 10C3 13.866 6.13401 17 10 17Z" />
      <path fillRule="evenodd" clipRule="evenodd" d="M13.7072 7.29289C14.0977 7.68342 14.0977 8.31658 13.7072 8.70711L9.70717 13.7071C9.50218 13.9121 9.21833 14.018 8.92917 13.9975C8.64001 13.9769 8.37399 13.8319 8.20006 13.6L6.20006 11.6C5.86869 11.1582 5.95823 10.5314 6.40006 10.2C6.84189 9.86863 7.46869 9.95817 7.80006 10.4L9.10825 11.4776L12.293 7.29289C12.6835 6.90237 13.3166 6.90237 13.7072 7.29289Z" />
    </svg>
  );
}
