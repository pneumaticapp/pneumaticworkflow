/* eslint-disable max-len */
import * as React from 'react';

export function SearchMediumIcon({ fill = 'currentColor', ...rest }: React.SVGAttributes<SVGElement>) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M9.5 17C13.6421 17 17 13.6421 17 9.5C17 5.35786 13.6421 2 9.5 2C5.35786 2 2 5.35786 2 9.5C2 13.6421 5.35786 17 9.5 17ZM9.5 15C12.5376 15 15 12.5376 15 9.5C15 6.46243 12.5376 4 9.5 4C6.46243 4 4 6.46243 4 9.5C4 12.5376 6.46243 15 9.5 15Z" />
      <path d="M13.4153 13.4152C13.7906 13.0398 14.3992 13.0398 14.7745 13.4152L17.7182 16.3589C18.0935 16.7343 18.0935 17.3428 17.7182 17.7181C17.3428 18.0935 16.7343 18.0935 16.3589 17.7181L13.4153 14.7744C13.04 14.3991 13.04 13.7905 13.4153 13.4152Z" />
    </svg>
  );
}
