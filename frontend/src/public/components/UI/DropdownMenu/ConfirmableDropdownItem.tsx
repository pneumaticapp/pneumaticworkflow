import * as React from 'react';
import { useState } from 'react';
import { useIntl } from 'react-intl';
import OutsideClickHandler from 'react-outside-click-handler';

import type { IConfirmableDropdownItemProps, TDropdownItemState } from './types';

import styles from './DropdownMenu.css';

export function ConfirmableDropdownItem({
  children,
  className,
  withConfirmation,
  initialConfirmationState = 'option',
  closeDropdown,
  onClick,
}: IConfirmableDropdownItemProps) {
  const { formatMessage } = useIntl();
  const [dropdownItemState, setDropdownItemState] = useState<TDropdownItemState>(initialConfirmationState);

  if (!withConfirmation) {
    if (!onClick) {
      return (
        <span role="menuitem" tabIndex={0} className={className}>
          {children}
        </span>
      );
    }

    return (
      <button type="button" role="menuitem" className={className} onClick={onClick}>
        {children}
      </button>
    );
  }

  const handleConfirm = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    onClick?.(event);
  };

  const handleReject = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    setDropdownItemState('option');
    if (initialConfirmationState === 'confirmation') {
      closeDropdown();
    }
  };

  const handleShowConfirmation = () => {
    setDropdownItemState('confirmation');
  };

  const handleOutsideClick = () => {
    if (initialConfirmationState === 'option') {
      setDropdownItemState('option');
    }
  };

  return (
    <OutsideClickHandler onOutsideClick={handleOutsideClick}>
      {dropdownItemState === 'confirmation' ? (
        <div role="menuitem" tabIndex={0} className={className}>
          <div className={styles['dropdown-confirm']}>
            <span>{formatMessage({ id: 'dropdown.are-you-sure' })}</span>{' '}
            <button type="button" onClick={handleConfirm} className={styles['dropdown-confirm-option']}>
              {formatMessage({ id: 'dropdown.yes' })}
            </button>
            {' / '}
            <button type="button" onClick={handleReject} className={styles['dropdown-confirm-option']}>
              {formatMessage({ id: 'dropdown.no' })}
            </button>
          </div>
        </div>
      ) : (
        <button type="button" role="menuitem" className={className} onClick={handleShowConfirmation}>
          {children}
        </button>
      )}
    </OutsideClickHandler>
  );
}
