import React from 'react';
import classnames from 'classnames';
import { Skeleton } from '../../UI/Skeleton';

import styles from '../Templates.css';

export function TemplateSystemSkeleton() {
  return (
    <div className={classnames(styles['card'], styles['is-system'])}>
      <div className={styles['card__content']}>
        <div className={styles['card__header']}>
          <Skeleton height="16px" />
        </div>
        <p className={styles['card__description']}>
          <Skeleton height="48px" margin="8px 0" />
        </p>
        <div className={styles['card__footer']}>
          <div className={styles['card__icon']}>
            <Skeleton height="40px" />
          </div>
        </div>
      </div>
    </div>
  );
}
