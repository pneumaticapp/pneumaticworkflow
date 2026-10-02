import React from 'react';
import classnames from 'classnames';

import { useCheckDevice } from '../../../hooks/useCheckDevice';
import { isArrayWithItems } from '../../../utils/helpers';
import { ArrowRightIcon } from '../../icons';
import { Tooltip } from '../Tooltip';
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
          option.isDisabled && styles['dropdown-item_disabled'],
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

        const optionNode = (
          <React.Fragment key={`option-${key}`}>
            {option.withUpperline && <hr className={styles['line']} />}
            <ConfirmableDropdownItem
              className={classnames(itemClassName, option.className)}
              withConfirmation={option.withConfirmation}
              initialConfirmationState={option.initialConfirmationState}
              closeDropdown={closeDropdown}
              onClick={!option.isDisabled && option.onClick ? () => {
                option.onClick?.(closeDropdown);
                closeDropdown();
              } : undefined}
            >
              {content}
            </ConfirmableDropdownItem>
          </React.Fragment>
        );

        if (option.isDisabled && option.disabledTooltip) {
          return (
            <Tooltip
              key={`disabled-${key}`}
              content={option.disabledTooltip}
              placement="top"
              interactive={false}
              contentClassName={styles['dropdown-item-tooltip']}
            >
              <div>{optionNode}</div>
            </Tooltip>
          );
        }

        return optionNode;
      })}
    </>
  );
}
