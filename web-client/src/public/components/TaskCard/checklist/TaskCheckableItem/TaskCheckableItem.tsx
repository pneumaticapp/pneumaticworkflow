import * as React from 'react';
import ReactDOM from 'react-dom';

import { createCheckPlaceholderId } from '..';

import { Checkbox } from '../../../UI';
import { TMarkChecklistItemPayload, TUnmarkChecklistItemPayload } from '../../../../redux/actions';

import styles from '../../../RichText/RichText.css';

export type TTaskCheckableItemOwnProps = {
  listApiName: string;
  itemApiName: string;
  disabled?: boolean;
}

export type TTaskCheckableItemReduxProps = {
  isChecked: boolean;
  markChecklistItem(payload: TMarkChecklistItemPayload): void;
  unmarkChecklistItem(payload: TUnmarkChecklistItemPayload): void;
};

type ITaskCheckableItemProps = TTaskCheckableItemOwnProps & TTaskCheckableItemReduxProps;

export function TaskCheckableItem({
  listApiName,
  itemApiName,
  isChecked,
  disabled,
  markChecklistItem,
  unmarkChecklistItem,
}: ITaskCheckableItemProps) {
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
  }

  return ReactDOM.createPortal(
    <Checkbox
      checked={isChecked}
      containerClassName={styles['checkbox']}
      labelClassName={styles['checkbox-label']}
      onChange={handleChange}
      disabled={disabled}
    />,
    element
  );
}
