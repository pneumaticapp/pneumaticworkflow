import type { MouseEventHandler, KeyboardEventHandler } from 'react';
import React, { useState } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { TrashIcon } from '../../../icons';
import type { IDeletableDropdownOptionProps } from './types';
import dropdownStyles from '../../../UI/Dropdown/Dropdown.css';
import styles from './DeletableDropdownOption.css';

export function DeletableDropdownOption({ label, onDelete, onClick, closeDropdown }: IDeletableDropdownOptionProps) {
  const { formatMessage } = useIntl();
  const [isConfirming, setIsConfirming] = useState(false);

  const handleLabelClick: MouseEventHandler<HTMLSpanElement> = (event) => {
    event.stopPropagation();
    closeDropdown?.();
    onClick?.();
  };

  const handleLabelKeyDown: KeyboardEventHandler<HTMLSpanElement> = (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      event.stopPropagation();
      closeDropdown?.();
      onClick?.();
    }
  };

  const handleConfirm: MouseEventHandler<HTMLButtonElement> = (event) => {
    event.stopPropagation();
    closeDropdown?.();
    onDelete();
  };

  const handleReject: MouseEventHandler<HTMLButtonElement> = (event) => {
    event.stopPropagation();
    setIsConfirming(false);
  };

  const handleDeleteClick: MouseEventHandler<HTMLSpanElement> = (event) => {
    event.stopPropagation();
    setIsConfirming(true);
  };

  const handleContainerClick: MouseEventHandler<HTMLSpanElement> = (event) => {
    event.stopPropagation();
  };

  const handleDeleteKeyDown: KeyboardEventHandler<SVGSVGElement> = (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      event.stopPropagation();
      setIsConfirming(true);
    }
  };

  if (isConfirming) {
    return (
      <span
        className={classnames(dropdownStyles['dropdown-confirm'], styles['confirmation-container'])}
        role="presentation"
        onClick={handleContainerClick}
      >
        <span>{formatMessage({ id: 'dropdown.are-you-sure' })}</span>
        <span>
          <button type="button" onClick={handleConfirm} className={dropdownStyles['dropdown-confirm-option']}>
            {formatMessage({ id: 'dropdown.yes' })}
          </button>
          {' / '}
          <button type="button" onClick={handleReject} className={dropdownStyles['dropdown-confirm-option']}>
            {formatMessage({ id: 'dropdown.no' })}
          </button>
        </span>
      </span>
    );
  }

  return (
    <span className={styles['container']}>
      <span
        className={styles['label']}
        {...(onClick && {
          role: 'button',
          tabIndex: 0,
          onClick: handleLabelClick,
          onKeyDown: handleLabelKeyDown,
        })}
      >
        {label}
      </span>
      <span className={styles['divider']} aria-hidden="true" />
      <span className={styles['delete-button']} role="presentation" onClick={handleDeleteClick}>
        <TrashIcon
          className={styles['delete-icon']}
          role="button"
          tabIndex={0}
          aria-label={formatMessage({ id: 'fieldsets.rule-delete' })}
          onKeyDown={handleDeleteKeyDown}
        />
      </span>
    </span>
  );
}
