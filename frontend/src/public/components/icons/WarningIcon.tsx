/* eslint-disable max-len */
import * as React from 'react';

export function WarningIcon({ fill = 'currentColor', ...rest }: React.SVGAttributes<SVGElement>) {
  return (
    <svg width="100%" height="100%" viewBox="0 0 40 40" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M23.0475 5.75343C21.6931 3.41553 18.3069 3.41552 16.9525 5.75342L2.4767 30.7397C1.12225 33.0776 2.81532 36 5.52423 36H34.4758C37.1847 36 38.8778 33.0776 37.5233 30.7397L23.0475 5.75343ZM17 29C17 27.3431 18.3431 26 20 26C21.6569 26 23 27.3431 23 29C23 30.6569 21.6569 32 20 32C18.3431 32 17 30.6569 17 29ZM20 14C18.8954 14 18 14.8954 18 16V22C18 23.1046 18.8954 24 20 24C21.1046 24 22 23.1046 22 22V16C22 14.8954 21.1046 14 20 14Z" />
    </svg>
  );
}
