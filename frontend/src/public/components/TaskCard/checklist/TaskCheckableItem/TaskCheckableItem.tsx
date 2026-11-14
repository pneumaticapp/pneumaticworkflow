import React from 'react';
import ReactDOM from 'react-dom';

import { createCheckPlaceholderId } from '../createCheckPlaceholderId';

import { Checkbox } from '../../../UI';
import type { TTaskCheckableItemProps } from './types';

import styles from '../../../RichText/RichText.css';

export function TaskCheckableItem({
  listApiName,
  itemApiName,
  isChecked,
  disabled,
  markChecklistItem,
  unmarkChecklistItem,
}: TTaskCheckableItemProps) {
  const element = document.getElementById(createCheckPlaceholderId(listApiName, itemApiName));
  if (!element) {
    return null;
  }

  const handleChange = (event: React.FormEvent<HTMLInputElement>) => {
    const newChecked = event.currentTarget.checked;

    if (newChecked) {
      markChecklistItem({ listApiName, itemApiName });
    } else {
      unmarkChecklistItem({ listApiName, itemApiName });
    }
  };

  return ReactDOM.createPortal(
    <Checkbox
      checked={isChecked}
      containerClassName={styles['checkbox']}
      onChange={handleChange}
      disabled={disabled}
    />,
    element,
  );
}
