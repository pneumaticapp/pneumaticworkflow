import * as React from 'react';

import styles from './FieldsetDetails.css';

export function FieldsetDetailsSkeleton() {
  return (
    <div className={styles['container']}>
      <header className={styles['header']}>
        <div className={styles['header-skeleton']} style={{ width: '30rem', height: '3.2rem', borderRadius: '0.8rem' }} />
      </header>
      <div className={styles['list']}>
        <div className={styles['header-skeleton']} style={{ width: '20rem', height: '2.4rem', borderRadius: '0.8rem', marginBottom: '1.6rem' }} />
        <div className={styles['header-skeleton']} style={{ width: '100%', height: '8rem', borderRadius: '0.8rem' }} />
      </div>
    </div>
  );
}
