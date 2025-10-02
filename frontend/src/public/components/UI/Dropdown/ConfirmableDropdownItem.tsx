import React, { useState } from 'react';
import { DropdownItemProps, DropdownItem } from 'reactstrap';
import { useIntl } from 'react-intl';
import OutsideClickHandler from 'react-outside-click-handler';

import styles from './Dropdown.css';

export type TDropdownItemState = "option" | "confirmation";

export interface IConfirmableDropdownItemProps extends DropdownItemProps {
  withConfirmation?: boolean;
  initialConfirmationState?: TDropdownItemState;
  closeDropdown(): void;
}

export function ConfirmableDropdownItem({
  withConfirmation,
  initialConfirmationState = "option",
  closeDropdown,
  ...dropdownItemProps
}: IConfirmableDropdownItemProps) {
  const { formatMessage } = useIntl()
  const [dropdownItemState, setDropdownItemState] = useState<TDropdownItemState>(initialConfirmationState)

  if (!withConfirmation) {
    return <DropdownItem {...dropdownItemProps} tag={dropdownItemProps.onClick ? "button" : "span"} />
  }

  const handleConfirm: React.AllHTMLAttributes<HTMLButtonElement>['onClick'] = event => {
    event.stopPropagation();
    dropdownItemProps.onClick?.(event);
  }

  const handleReject: React.AllHTMLAttributes<HTMLButtonElement>['onClick'] = event => {
    event.stopPropagation();
    setDropdownItemState("option");
    if (initialConfirmationState === "confirmation") {
      closeDropdown();
    }
  }

  const renderContent = () => {
    const contentMap = {
      option: dropdownItemProps.children,
      confirmation: (
        <div className={styles['dropdown-confirm']}>
          <span>
            {formatMessage({ id: 'dropdown.are-you-sure' })}
          </span>
          {' '}
          <button type="button" onClick={handleConfirm} className={styles['dropdown-confirm-option']}>
            {formatMessage({ id: 'dropdown.yes' })}
          </button>
          {' / '}
          <button type="button" onClick={handleReject} className={styles['dropdown-confirm-option']}>
            {formatMessage({ id: 'dropdown.no' })}
          </button>
        </div>
      ),
    }

    return contentMap[dropdownItemState];
  }

  return (
    <OutsideClickHandler onOutsideClick={() => {
      if (initialConfirmationState === "option") {
        setDropdownItemState("option")
      }
    }}>
      <DropdownItem
        {...dropdownItemProps}
        onClick={() => setDropdownItemState("confirmation")}
      >
        {renderContent()}
      </DropdownItem>
    </OutsideClickHandler>
  );
}
