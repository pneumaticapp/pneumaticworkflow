import React, { useState } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import OutsideClickHandler from 'react-outside-click-handler';

import { IConfirmableDropdownItemProps, TDropdownItemState } from './types';

import styles from './Dropdown.css';

export function ConfirmableDropdownItem({
  children,
  className,
  cssModule,
  withConfirmation,
  initialConfirmationState = 'option',
  closeDropdown,
  onClick,
}: IConfirmableDropdownItemProps) {
  const { formatMessage } = useIntl();
  const [state, setState] = useState<TDropdownItemState>(initialConfirmationState);
  const itemClassName = classnames(cssModule?.['dropdown-item'], className);

  if (!withConfirmation) {
    if (!onClick) return <span className={itemClassName}>{children}</span>;

    return (
      <button type="button" className={itemClassName} onClick={onClick}>
        {children}
      </button>
    );
  }

  const rejectConfirmation = () => {
    setState('option');
    if (initialConfirmationState === 'confirmation') closeDropdown();
  };

  return (
    <OutsideClickHandler onOutsideClick={() => setState(initialConfirmationState)}>
      {state === 'option' ? (
        <button type="button" className={itemClassName} onClick={() => setState('confirmation')}>
          {children}
        </button>
      ) : (
        <div className={itemClassName}>
          <span className={styles['dropdown-confirm']}>
            {formatMessage({ id: 'dropdown.are-you-sure' })}{' '}
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                onClick?.();
              }}
              className={styles['dropdown-confirm-option']}
            >
              {formatMessage({ id: 'dropdown.yes' })}
            </button>{' / '}
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                rejectConfirmation();
              }}
              className={styles['dropdown-confirm-option']}
            >
              {formatMessage({ id: 'dropdown.no' })}
            </button>
          </span>
        </div>
      )}
    </OutsideClickHandler>
  );
}
