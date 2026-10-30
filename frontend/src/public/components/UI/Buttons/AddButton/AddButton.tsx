import * as React from 'react';

import { PlusWithCircleIcon } from '../../../icons';

import styles from './AddButton.css';

export interface IAddButtonProps {
  title: string;
  caption: string;
  disabled?: boolean;
  onClick(e: React.MouseEvent): void;
}

export function AddButton({ title, caption, disabled, onClick }: IAddButtonProps) {
  return (
    <button type="button" className={styles['add-button']} onClick={onClick} disabled={disabled}>
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
