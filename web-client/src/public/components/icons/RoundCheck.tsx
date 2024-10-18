/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

export interface IRoundCheckProps {
  checked: boolean;
}

export const RoundCheck = ({ checked }: IRoundCheckProps) => {
  if (!checked) {
    return (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" clipRule="evenodd" d="M10 19C14.9706 19 19 14.9706 19 10C19 5.02944 14.9706 1 10 1C5.02944 1 1 5.02944 1 10C1 14.9706 5.02944 19 10 19ZM10 17C13.866 17 17 13.866 17 10C17 6.13401 13.866 3 10 3C6.13401 3 3 6.13401 3 10C3 13.866 6.13401 17 10 17Z" fill="#DCDCDB" />
      </svg>
    );
  }

  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path fillRule="evenodd" clipRule="evenodd" d="M1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10ZM13.7433 8.66897C14.1127 8.25846 14.0795 7.62617 13.669 7.25671C13.2584 6.88726 12.6262 6.92053 12.2567 7.33104L8.9618 11.5476L7.7071 10.2929C7.31658 9.90237 6.68342 9.90237 6.29289 10.2929C5.90237 10.6834 5.90237 11.3166 6.29289 11.7071L8.29289 13.7071C8.48688 13.9011 8.75204 14.0069 9.02629 13.9997C9.30053 13.9924 9.55977 13.8729 9.74329 13.669L13.7433 8.66897Z" fill="#4CAF50" />
    </svg>
  );
};
