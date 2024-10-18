/* eslint-disable max-len */
import * as React from 'react';

export type TNotificationInfoIconProps = React.SVGAttributes<SVGElement>;

export function CommentInfoIcon({ fill = 'currentColor', ...restProps }: TNotificationInfoIconProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill={fill} xmlns="http://www.w3.org/2000/svg" {...restProps}>
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M5 2C3.34315 2 2 3.34276 2 4.99913V11.9971C2 13.6535 3.34315 14.9962 5 14.9962H5.89766C6.24078 14.9962 6.55993 15.1721 6.74315 15.4621L7.46353 16.6024C8.64082 18.4659 11.3592 18.4659 12.5365 16.6024L13.2568 15.4621C13.4401 15.1721 13.7592 14.9962 14.1023 14.9962H15C16.6569 14.9962 18 13.6535 18 11.9971V4.99913C18 3.34276 16.6569 2 15 2H5ZM7 6C6.44772 6 6 6.44759 6 6.99971C6 7.55184 6.44772 7.99942 7 7.99942H13C13.5523 7.99942 14 7.55184 14 6.99971C14 6.44759 13.5523 6 13 6H7ZM7 8.99913C6.44772 8.99913 6 9.44672 6 9.99884C6 10.551 6.44772 10.9986 7 10.9986H13C13.5523 10.9986 14 10.551 14 9.99884C14 9.44672 13.5523 8.99913 13 8.99913H7Z"
      />
    </svg>
  );
}
