import * as React from 'react';
import { useState, MouseEventHandler, KeyboardEventHandler } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { TrashIcon } from '../../../icons';
import { IDeletableDropdownOptionProps } from './types';
import dropdownStyles from '../../../UI/Dropdown/Dropdown.css';
import styles from './DeletableDropdownOption.css';

export function DeletableDropdownOption({ label, onDelete }: IDeletableDropdownOptionProps) {
  const { formatMessage } = useIntl();
  const [isConfirming, setIsConfirming] = useState(false);

  const handleConfirm: MouseEventHandler<HTMLButtonElement> = (event) => {
    event.stopPropagation();
    onDelete();
  };

  const handleReject: MouseEventHandler<HTMLButtonElement> = (event) => {
    event.stopPropagation();
    setIsConfirming(false);
  };

  const handleDeleteClick: MouseEventHandler<SVGSVGElement> = (event) => {
    event.stopPropagation();
    setIsConfirming(true);
  };

  const handleContainerClick: MouseEventHandler<HTMLDivElement> = (event) => {
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
      <div
        className={classnames(dropdownStyles['dropdown-confirm'], styles['confirmation-container'])}
        onClick={handleContainerClick}
      >
        <span>{formatMessage({ id: 'dropdown.are-you-sure' })}</span>
        <span>
          <button
            type="button"
            onClick={handleConfirm}
            className={dropdownStyles['dropdown-confirm-option']}
          >
            {formatMessage({ id: 'dropdown.yes' })}
          </button>
          {' / '}
          <button
            type="button"
            onClick={handleReject}
            className={dropdownStyles['dropdown-confirm-option']}
          >
            {formatMessage({ id: 'dropdown.no' })}
          </button>
        </span>
      </div>
    );
  }

  return (
    <div className={styles['container']}>
      <span>{label}</span>
      <TrashIcon
        className={styles['delete-icon']}
        role="button"
        tabIndex={0}
        onClick={handleDeleteClick}
        onKeyDown={handleDeleteKeyDown}
      />
    </div>
  );
}
