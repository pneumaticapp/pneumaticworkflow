import * as React from 'react';
import { memo, useState, useEffect, useRef, KeyboardEvent } from 'react';
import { useIntl } from 'react-intl';

import { CommentEditCancelIcon } from '../../icons/CommentEditCancelIcon';
import { CommentEditDoneIcon } from '../../icons/CommentEditDoneIcon';
import { ModifyDropdown } from '../../UI/ModifyDropdown/ModifyDropdown';
import { EDIT_ICON_COLOR } from './constants';
import { EModifyDropdownToggle } from '../../UI/ModifyDropdown/types';

import { IDatasetRowProps } from './types';

import styles from './DatasetRow.css';

export const DatasetRow = memo(({
  value: initialValue = '',
  isEditing: isEditingProp = false,
  onSave,
  onDelete,
  onCancel,
}: IDatasetRowProps) => {
  const { formatMessage } = useIntl();
  const [isEditing, setIsEditing] = useState(isEditingProp);
  const [currentValue, setCurrentValue] = useState(initialValue);
  const [hasError, setHasError] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setIsEditing(isEditingProp);
  }, [isEditingProp]);

  useEffect(() => {
    setCurrentValue(initialValue);
  }, [initialValue]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  const handleSave = () => {
    const trimmedValue = currentValue.trim();
    if (!trimmedValue) {
      setHasError(true);
      inputRef.current?.focus();

      return;
    }

    onSave(trimmedValue);
    setIsEditing(false);
    setHasError(false);
  };


  const handleCancel = () => {
    setCurrentValue(initialValue);
    setIsEditing(false);
    setHasError(false);
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
            if (hasError) setHasError(false);
          }}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
        />
        <div className={styles['actions']}>
          <button
            type="button"
            className={styles['action-button']}
            aria-label={formatMessage({ id: 'general.cancel' })}
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
            aria-label={formatMessage({ id: 'general.save' })}
            onMouseDown={(e) => {
              e.preventDefault();
              handleSave();
            }}
          >
            <CommentEditDoneIcon fill={EDIT_ICON_COLOR} />
          </button>
        </div>
        {hasError && (
          <p className={styles['error-text']}>
            {formatMessage({ id: 'validation.dataset-row-empty' })}
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
          onEdit={() => {
            setIsEditing(true);
          }}
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
