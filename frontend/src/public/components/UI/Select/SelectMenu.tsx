import React from 'react';
import classnames from 'classnames';

import { ExpandIcon } from '../../icons';
import { IntlMessages } from '../../IntlMessages';
import { Dropdown } from '../Dropdown';
import { ISelectMenuProps } from './types';

import radioStyles from '../Fields/RadioButton/RadioButton.css';
import styles from './Select.css';

export function SelectMenu<T extends string>({
  toggleClassName,
  isDisabled,
  values,
  activeValue,
  toggleTextClassName,
  arrowClassName,
  menuClassName,
  hideSelectedOption,
  containerClassName,
  closeOnSelect,
  onChange,
  Icon,
  isFromCheckIfConditions,
  withRadio = false,
  positionFixed = false,
  activeValueLabelId,
}: ISelectMenuProps<T>) {
  const getIntlId = (value: T) => `sorting.${value}`;

  return (
    <Dropdown
      direction="right"
      className={classnames(
        styles['container'],
        isFromCheckIfConditions && styles['container--select-menu'],
        containerClassName,
      )}
      toggleProps={{
        className: classnames(styles['active-value'], toggleClassName, isDisabled && styles['active-value_disabled']),
      }}
      menuClassName={classnames(
        styles['dropdown-menu'],
        menuClassName,
        positionFixed && styles['dropdown-menu__position-fixed'],
        positionFixed && styles['dropdown-menu__position-fixed--select-menu'],
      )}
      menuPositionFixed={positionFixed}
      isDisabled={isDisabled}
      renderToggle={() => (
        <>
          {Icon && <Icon className={styles['icon']} />}
          <IntlMessages id={activeValueLabelId || getIntlId(activeValue)}>
            {(text) => <span className={classnames(styles['active-value__text'], toggleTextClassName)}>{text}</span>}
          </IntlMessages>
          <ExpandIcon className={classnames(styles['expand-icon'], arrowClassName)} />
        </>
      )}
    >
      {({ closeDropdown }) => values.map((value) => {
        if (hideSelectedOption && value === activeValue) return null;

        return (
          <button
            type="button"
            role="menuitemradio"
            aria-checked={value === activeValue}
            key={value}
            className={classnames(styles['value-item'], value === activeValue && styles['value-item__disabled'])}
            onClick={() => {
              if (value !== activeValue) onChange(value);
              if (closeOnSelect) closeDropdown();
            }}
          >
            {withRadio ? (
              <span className={classnames(radioStyles['radio'], value === activeValue && radioStyles['select-menu__radio--checked'])}>
                <span className={radioStyles['radio__box']} />
                <span className={radioStyles['radio__title']}><IntlMessages id={getIntlId(value)} /></span>
              </span>
            ) : <IntlMessages id={getIntlId(value)} />}
          </button>
        );
      })}
    </Dropdown>
  );
}
