import * as React from 'react';

import type { ITokenListProps } from './types';

import styles from './TokenList.css';

export function TokenList({ children, 'data-testid': testId }: ITokenListProps) {
  return (
    <ul className={styles['token-list']} data-testid={testId}>
      {children}
    </ul>
  );
}
