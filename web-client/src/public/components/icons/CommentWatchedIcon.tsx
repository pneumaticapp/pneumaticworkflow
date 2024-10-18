/* eslint-disable max-len */
import * as React from 'react';

export type TCommentWatchedIconProps = React.SVGAttributes<SVGElement>;

export function CommentWatchedIcon({ fill = 'currentColor', ...restProps }: TCommentWatchedIconProps) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" {...restProps}>
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M10 4C13.1993 4 15.7551 5.78386 17.5962 9.21474L17.7668 9.54121L18 10L17.7668 10.4588C15.9142 14.1029 13.2993 16 10 16C6.80071 16 4.24492 14.2161 2.40375 10.7853L2.23324 10.4588L2 10L2.23324 9.54121C4.08581 5.89709 6.70074 4 10 4ZM10 6C7.73671 6 5.89057 7.1877 4.4104 9.72318L4.25321 10L4.4104 10.2768C5.89057 12.8123 7.73671 14 10 14C12.3441 14 14.2408 12.7259 15.7468 10C14.2408 7.27405 12.3441 6 10 6ZM10 8C11.1046 8 12 8.89543 12 10C12 11.1046 11.1046 12 10 12C8.89543 12 8 11.1046 8 10C8 8.89543 8.89543 8 10 8Z"
        fill={fill}
      />
    </svg>
  );
}
