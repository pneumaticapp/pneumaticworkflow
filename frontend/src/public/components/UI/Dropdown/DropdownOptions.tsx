import React from 'react';
import classnames from 'classnames';

import { useCheckDevice } from '../../../hooks/useCheckDevice';
import { isArrayWithItems } from '../../../utils/helpers';
import { ArrowRightIcon } from '../../icons';
import { ConfirmableDropdownItem } from './ConfirmableDropdownItem';
import { Dropdown } from './Dropdown';
import { IDropdownOptionsProps } from './types';
import { getDropdownItemColorClass } from './utils';

import styles from './Dropdown.css';

export function DropdownOptions({ options, closeDropdown, isFromBreakdownItem }: IDropdownOptionsProps) {
  const { isMobile } = useCheckDevice();
  if (!Array.isArray(options)) return options.customSubOption || null;

  return (
    <>
      {options.map((option) => {
        if (option.isHidden) return null;

        const key = `${typeof option.label === 'string' ? option.label : option.mapKey}`;
        const content = typeof option.label === 'string' ? (
          <>
            <span className={styles['label']}>{option.label}</span>
            {option.Icon && <option.Icon className={styles['dropdown-item-icon']} />}
          </>
        ) : option.label;
        const itemClassName = classnames(
          styles['dropdown-item'],
          getDropdownItemColorClass(option.color),
          isMobile && isFromBreakdownItem && styles['dropdown-item-mobile'],
        );
        const subOptions = Array.isArray(option.subOptions) && isArrayWithItems(option.subOptions)
          ? option.subOptions
          : undefined;
        const hasSubmenu = option.customSubOption || subOptions;

        if (hasSubmenu) {
          return (
            <Dropdown
              key={`submenu-${key}`}
              options={subOptions || option}
              /* Submenus drop under their row inside the parent menu, as on production —
                 a right-hand fly-out would land outside it. */
              placement="bottom-start"
              className={option.className}
              toggleProps={{ className: itemClassName }}
              menuClassName={classnames(
                styles['dropdown__submenu'],
                option.customSubOption && styles['dropdown__custom-sub-options'],
              )}
              renderToggle={() => (
                <>
                  <span className={styles['label']}>{option.label}</span>
                  <ArrowRightIcon className={styles['dropdown-item-icon']} />
                </>
              )}
            >
              {subOptions
                ? ({ closeDropdown: closeSubmenu }) => (
                  <DropdownOptions
                    options={subOptions}
                    // Close this submenu as well as its parent, so the submenu's own open
                    // state can never outlive the chosen option.
                    closeDropdown={() => {
                      closeSubmenu();
                      closeDropdown();
                    }}
                  />
                )
                : option.customSubOption}
            </Dropdown>
          );
        }

        return (
          <React.Fragment key={`option-${key}`}>
            {option.withUpperline && <hr className={styles['line']} />}
            <ConfirmableDropdownItem
              className={classnames(itemClassName, option.className)}
              withConfirmation={option.withConfirmation}
              initialConfirmationState={option.initialConfirmationState}
              closeDropdown={closeDropdown}
              onClick={option.onClick ? () => {
                option.onClick?.(closeDropdown);
                closeDropdown();
              } : undefined}
            >
              {content}
            </ConfirmableDropdownItem>
          </React.Fragment>
        );
      })}
    </>
  );
}
