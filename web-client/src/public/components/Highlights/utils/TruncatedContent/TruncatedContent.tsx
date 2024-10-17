import * as React from 'react';

import styles from './TruncatedContent.css';

interface ITruncatedContentProps {
  children: React.ReactNode;
  maxHeight: number;
  isTruncated: boolean;
}

export function TruncatedContent({ children, maxHeight, isTruncated }: ITruncatedContentProps) {
  const maxHeightStyle = isTruncated ? `${maxHeight}px` : '100%';

  return (
    <div
      style={{
        maxHeight: `${maxHeightStyle}`,
      }}
      className={styles['container']}
    >
      {children}
    </div>
  );
}
