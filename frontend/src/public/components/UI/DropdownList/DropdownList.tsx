import * as React from 'react';
import { useState } from 'react';
import classnames from 'classnames';
import Select from 'react-select';
import OutsideClickHandler from 'react-outside-click-handler';
import { useIntl } from 'react-intl';

import { ControlSM, DropdownIndicator, MenuListLG, MenuListSM, MenuSM, Option } from './selectComponents';
import type { IDropdownListProps, TControlSize, TDropdownOptionBase } from './types';

import '../../../assets/css/library/react-select.css';
import styles from './DropdownList.css';

export function DropdownList<TOption extends TDropdownOptionBase>({
  controlSize = 'lg',
  label,
  title,
  className,
  isMulti,
  ...restProps
}: IDropdownListProps<TOption>) {
  const { messages, formatMessage } = useIntl();
  const [isOpen, setIsOpen] = useState(false);
  const [filterValue, setFilterValue] = useState('');
  const { errorMessage } = restProps;
  const errorText = errorMessage && messages[errorMessage] ? formatMessage({ id: errorMessage }) : errorMessage;

  const handleInputChange = (inputValue: string, action: any) => {
    if (action.action === 'set-value') {
      setFilterValue('');
    }
    if (action.action === 'input-change') {
      setFilterValue(inputValue);
    }
    if (restProps.onInputChange) {
      restProps.onInputChange(inputValue, action);
    }
  };

  const componentsMap: { [key in TControlSize]: any } = {
    lg: {
      Option,
      DropdownIndicator,
      MenuList: MenuListLG,
      IndicatorSeparator: () => null,
    },
    sm: {
      Menu: MenuSM,
      Option,
      Control: !restProps.staticMenu ? ControlSM(title || '', isOpen, setIsOpen) : () => null,
      ...(!restProps.staticMenu && { Input: () => null }),
      ValueContainer: () => null,
      MenuList: MenuListSM,
    },
  };

  if (label && controlSize === 'lg') {
    return (
      <div className={classnames('react-select', restProps.isDisabled && 'is-disabled', className)}>
        <div className={classnames(styles['dropdownlist-lg__control'], label && styles['is-label'])}>
          {label && (
            <p className={styles['dropdownlist-lg__label']}>
              {label}
              {restProps.isRequired && <span className={styles['is-required']}>*</span>}
            </p>
          )}

          <Select
            isMulti={isMulti}
            closeMenuOnSelect={!isMulti}
            hideSelectedOptions={false}
            controlShouldRenderValue={!isMulti}
            tabSelectsValue={false}
            isClearable={false}
            classNamePrefix="react-select"
            components={componentsMap[controlSize]}
            onInputChange={handleInputChange}
            className={classnames(errorMessage && styles['has-error'])}
            {...restProps}
          />

          {errorText && <p className={styles['error-text']}>{errorText}</p>}
        </div>
      </div>
    );
  }

  return (
    <div
      className={classnames(
        'react-select',
        restProps.isDisabled && 'is-disabled',
        className,
        restProps.staticMenu && 'is-static',
      )}
    >
      {label && (
        <p className={styles['dropdownlist-lg__label']}>
          {label}
          {restProps.isRequired && <span className={styles['is-required']}>*</span>}
        </p>
      )}
      <OutsideClickHandler onOutsideClick={() => setIsOpen(false)}>
        <Select
          isMulti={isMulti}
          closeMenuOnSelect={!isMulti}
          hideSelectedOptions={false}
          controlShouldRenderValue={!isMulti}
          tabSelectsValue={false}
          isClearable={false}
          classNamePrefix="react-select"
          components={componentsMap[controlSize]}
          inputValue={filterValue}
          onInputChange={handleInputChange}
          {...restProps}
          {...(controlSize === 'sm' && !restProps.staticMenu && { menuIsOpen: isOpen })}
          {...(restProps.staticMenu && { menuIsOpen: true })}
        />
      </OutsideClickHandler>
      {errorText && <p className={styles['error-text']}>{errorText}</p>}
    </div>
  );
}
