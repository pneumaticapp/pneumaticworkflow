import * as React from 'react';
import classnames from 'classnames';
import { DropdownItem, DropdownMenu, DropdownToggle, Dropdown } from 'reactstrap';

import { ExpandIcon } from '../../icons';
import { IntlMessages } from '../../IntlMessages';

import styles from './Select.css';

export interface ISelectMenuProps<T extends string> {
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
      className={classnames(styles['container'], 'dropdown-menu-right dropdown', containerClassName)}
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
      <DropdownMenu className={classnames(styles['dropdown-menu'], menuClassName)}>
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
              <IntlMessages id={getIntlId(value)} />
            </DropdownItem>
          );
        })}
      </DropdownMenu>
    </Dropdown>
  );
};
