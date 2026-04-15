import * as React from 'react';
import { memo } from 'react';
import { Link } from 'react-router-dom';
import { Header } from '../../index';
import { IAddCardButtonProps } from './types';

import styles from './AddCardButton.css';


function AddCardButtonComponent({ title, caption, icon, onClick, to, className, testId }: IAddCardButtonProps) {
  const content = (
    <div className={styles['custom-card']}>
      <div>
        <Header size="6" tag="span" className={styles['custom-card__title']}>
          {title}
        </Header>
        <span className={styles['custom-card__caption']}>{caption}</span>
      </div>
      <div className={styles['custom-card__icon']}>
        {icon}
      </div>
    </div>
  );

  if (to) {
    return (
      <Link className={className} to={to} onClick={onClick} data-test-id={testId}>
        {content}
      </Link>
    );
  }

  return (
    <div className={className}>
      <button type="button" className={styles['card-action']} onClick={onClick} data-test-id={testId}>
        {content}
      </button>
    </div>
  );
}

export const AddCardButton = memo(AddCardButtonComponent);
