import * as React from 'react';
import classnames from 'classnames';
import { DropdownItem, DropdownMenu, DropdownToggle, Dropdown } from 'reactstrap';

import { ExpandIcon } from '../../icons';
import { IntlMessages } from '../../IntlMessages';

import styles from './Select.css';
import radioStyles from '../Fields/RadioButton/RadioButton.css';

export interface ISelectMenuProps<T extends string> {
  withRadio?: boolean;
  activeValue: T;
  values: T[];
  toggleClassName?: string;
  toggleTextClassName?: string;
  arrowClassName?: string;
  menuClassName?: string;
  containerClassName?: string;
  isDisabled?: boolean;
  hideSelectedOption?: boolean;
  onChange(value: T): void;
  Icon?(props: React.SVGAttributes<SVGElement>): JSX.Element;
  isFromCheckIfConditions?: boolean;
  positionFixed?: boolean;
}

export const SelectMenu = <T extends string>({
  toggleClassName,
  isDisabled,
  values,
  activeValue,
  toggleTextClassName,
  arrowClassName,
  menuClassName,
  hideSelectedOption,
  containerClassName,
  onChange,
  Icon,
  isFromCheckIfConditions,
  withRadio = false,
  positionFixed = false,
}: ISelectMenuProps<T>) => {
  const [isDropdownOpen, setIsDropdownOpen] = React.useState(false);
  const getIntlId = (value: T) => `sorting.${value}`;

  const handleClickItem = (value: T) => () => {
    if (value !== activeValue) {
      onChange(value);
    }
  };

  const handleToggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  return (
    <Dropdown
      className={classnames(
        styles['container'],
        isFromCheckIfConditions && styles['container--select-menu'],
        'dropdown-menu-right dropdown',
        containerClassName,
      )}
      isOpen={isDropdownOpen}
      setActiveFromChild={isDropdownOpen}
      toggle={handleToggleDropdown}
    >
      <DropdownToggle
        tag="button"
        className={classnames(styles['active-value'], toggleClassName, isDisabled && styles['active-value_disabled'])}
      >
        {Icon && <Icon className={styles['icon']} />}
        <IntlMessages id={getIntlId(activeValue)}>
          {(text) => <span className={classnames(styles['active-value__text'], toggleTextClassName)}>{text}</span>}
        </IntlMessages>

        <ExpandIcon className={classnames(styles['expand-icon'], arrowClassName)} />
      </DropdownToggle>
      <DropdownMenu
        className={classnames(
          styles['dropdown-menu'],
          menuClassName,
          positionFixed && styles['dropdown-menu__position-fixed'],
          positionFixed && styles['dropdown-menu__position-fixed--select-menu'],
        )}
        positionFixed={positionFixed}
      >
        {(values as T[]).map((value) => {
          if (hideSelectedOption && value === activeValue) {
            return null;
          }

          return (
            <DropdownItem
              toggle={false}
              key={value}
              className={classnames('dropdown-item-sm', styles['value-item'], {
                [styles['value-item__disabled']]: value === activeValue,
              })}
              onClick={handleClickItem(value)}
            >
              {withRadio ? (
                <span
                  className={classnames(
                    radioStyles['radio'],
                    value === activeValue && radioStyles['select-menu__radio--checked'],
                  )}
                >
                  <span className={radioStyles['radio__box']}></span>
                  <span className={radioStyles['radio__title']}>
                    <IntlMessages id={getIntlId(value)} />
                  </span>
                </span>
              ) : (
                <IntlMessages id={getIntlId(value)} />
              )}
            </DropdownItem>
          );
        })}
      </DropdownMenu>
    </Dropdown>
  );
};
