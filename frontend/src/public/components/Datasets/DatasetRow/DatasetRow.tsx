import * as React from 'react';
import { memo, useState, useEffect, useRef, KeyboardEvent } from 'react';
import { useIntl } from 'react-intl';

import { CommentEditCancelIcon } from '../../icons/CommentEditCancelIcon';
import { CommentEditDoneIcon } from '../../icons/CommentEditDoneIcon';
import { ModifyDropdown } from '../../UI/ModifyDropdown/ModifyDropdown';
import { EDIT_ICON_COLOR } from './constants';
import { EModifyDropdownToggle } from '../../UI/ModifyDropdown/types';
import { validateDatasetRow } from '../../../utils/validators';

import { IDatasetRowProps } from './types';

import styles from './DatasetRow.css';

export const DatasetRow = memo(({
  value: initialValue = '',
  isEditing = false,
  existingItems = [],
  onEdit,
  onSave,
  onDelete,
  onCancel,
}: IDatasetRowProps) => {
  const { formatMessage } = useIntl();
  const [currentValue, setCurrentValue] = useState(initialValue);
  const [errorText, setErrorText] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setCurrentValue(initialValue);
  }, [initialValue]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  const handleSave = () => {
    const error = validateDatasetRow(currentValue, existingItems, initialValue || undefined);
    if (error) {
      setErrorText(error);
      inputRef.current?.focus();
      return;
    }

    const trimmedValue = currentValue.trim();
    onSave(trimmedValue);
    setErrorText('');
  };


  const handleCancel = () => {
    setCurrentValue(initialValue);
    setErrorText('');
    onCancel?.();
  };

  const handleBlur = () => {
    const trimmedValue = currentValue.trim();
    if (!trimmedValue || trimmedValue === initialValue) {
      handleCancel();
    } else {
      handleSave();
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      handleSave();
    }

    if (event.key === 'Escape') {
      handleCancel();
    }
  };

  if (isEditing) {
    return (
      <div className={styles['container']}>
        <input
          ref={inputRef}
          className={styles['input']}
          value={currentValue}
          onChange={(e) => {
            setCurrentValue(e.target.value);
            if (errorText) setErrorText('');
          }}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
        />
        <div className={styles['actions']}>
          <button
            type="button"
            className={styles['action-button']}
            aria-label={formatMessage({ id: 'datasets.row.cancel' })}
            onMouseDown={(e) => {
              e.preventDefault();
              handleCancel();
            }}
          >
            <CommentEditCancelIcon fill={EDIT_ICON_COLOR} />
          </button>
          <button
            type="button"
            className={styles['action-button']}
            aria-label={formatMessage({ id: 'datasets.row.save' })}
            onMouseDown={(e) => {
              e.preventDefault();
              handleSave();
            }}
          >
            <CommentEditDoneIcon fill={EDIT_ICON_COLOR} />
          </button>
        </div>
        {errorText && (
          <p className={styles['error-text']}>
            {formatMessage({ id: errorText })}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className={styles['container']}>
      <span className={styles['value']}>{initialValue}</span>
      <div className={styles['actions']}>
        <ModifyDropdown
          onEdit={() => onEdit?.()}
          onDelete={onDelete}
          editLabel={formatMessage({ id: 'datasets.row.edit' })}
          deleteLabel={formatMessage({ id: 'datasets.row.delete' })}
          toggleType={EModifyDropdownToggle.More}
          className={styles['more-icon']}
        />
      </div>
    </div>
  );
});

DatasetRow.displayName = 'DatasetRow';
