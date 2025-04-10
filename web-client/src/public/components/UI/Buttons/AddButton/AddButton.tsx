import * as React from 'react';

import { PlusWithCircleIcon } from '../../../icons';

import styles from './AddButton.css';

export interface IAddButtonProps {
  title: string;
  caption: string;
  onClick(e: React.MouseEvent): void;
}

export function AddButton({ title, caption, onClick }: IAddButtonProps) {
  return (
    <button type="button" className={styles['add-button']} onClick={onClick}>
      <div className={styles['add-button__icon']}>
        <PlusWithCircleIcon />
      </div>
      <div>
        <h2>{title}</h2>
        <p>{caption}</p>
      </div>
    </button>
  );
}
