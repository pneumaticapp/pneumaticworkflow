import React, { forwardRef, useImperativeHandle, useRef } from 'react';

import type { ITableViewContainerProps, ITableViewContainerRef } from './types';

import styles from './WorkflowsTable.css';

export const TableViewContainer = forwardRef<ITableViewContainerRef, ITableViewContainerProps>(({ children }, ref) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useImperativeHandle(ref, () => ({
    get element() {
      return containerRef.current;
    },
  }));

  return (
    <div className={styles['table-view-container']} ref={containerRef}>
      {children}
    </div>
  );
});
