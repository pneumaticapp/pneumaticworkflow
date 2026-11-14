import React from 'react';
import classnames from 'classnames';

import type { IPlaceholderProps } from './types';

import { Header } from '../Typeography/Header';

import styles from './Placeholder.css';

export function Placeholder({
  mood = 'neutral',
  Icon,
  title,
  description,
  footer,
  containerClassName,
}: IPlaceholderProps) {
  return (
    <div className={classnames(styles['container'], containerClassName)}>
      <div className={styles['icon']}>
        <Icon mood={mood} />
      </div>
      <Header tag="p" size="6" className={styles['title']}>
        {title}
      </Header>
      {description && <p className={styles['description']}>{description}</p>}
      {footer && <div className={styles['footer']}>{footer}</div>}
    </div>
  );
}
