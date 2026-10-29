import React from 'react';
import classnames from 'classnames';

import { ConfirmableDropdownItem } from './ConfirmableDropdownItem';
import { getDropdownItemColorClass } from './utils/getDropdownItemColorClass';
import type { IDropdownMenuItemProps } from './types';
import { Tooltip } from '../Tooltip';

import styles from './DropdownMenu.css';

export function DropdownMenuItem({ option, isSpaced, closeDropdown }: IDropdownMenuItemProps) {
  const { label, color, withUpperline, disabledTooltip, isDisabled, className, Icon, onClick } = option;

  const handleClick =
    !isDisabled && onClick
      ? () => {
          onClick(closeDropdown);
          closeDropdown();
        }
      : undefined;

  const content = (
    <div>
      {withUpperline && <hr className={styles['line']} />}
      <ConfirmableDropdownItem
        className={classnames(
          styles['dropdown-item'],
          getDropdownItemColorClass(color),
          isSpaced && styles['dropdown-item-mobile'],
          isDisabled && styles['dropdown-item_disabled'],
          className,
        )}
        withConfirmation={option.withConfirmation}
        initialConfirmationState={option.initialConfirmationState}
        closeDropdown={closeDropdown}
        onClick={handleClick}
      >
        {typeof label === 'string' ? (
          <>
            <span className={styles['label']}>{label}</span>
            {Icon && <Icon className={styles['dropdown-item-icon']} />}
          </>
        ) : (
          label
        )}
      </ConfirmableDropdownItem>
    </div>
  );

  if (!isDisabled || !disabledTooltip) return content;

  return (
    <Tooltip
      content={disabledTooltip}
      placement="top"
      interactive={false}
      contentClassName={styles['dropdown-item-tooltip']}
    >
      {content}
    </Tooltip>
  );
}
